"""
USAJobs source adapter.

Accesses the official US Government jobs API (https://developer.usajobs.gov/).
Requires a free API key obtained from the USAJobs Developer Portal.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from hired.search.base import (
    JobSearchSource,
    JobResult,
    SearchCriteria,
    JobType,
    LocationInfo,
    CompensationInfo,
    SourceConfigError,
)


class USAJobsSource(JobSearchSource):
    """
    USAJobs API source implementation.

    Searches US Government job postings via the official USAJobs API.
    Requires a free API key from https://developer.usajobs.gov/.
    """

    API_BASE_URL = "https://data.usajobs.gov/api/search"

    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        """
        Initialize USAJobs source.

        Args:
            api_key: USAJobs API key. If not provided, reads from USAJOBS_API_KEY env var.
            email: Email address. If not provided, reads from USAJOBS_EMAIL env var.
        """
        self._api_key = api_key or os.environ.get('USAJOBS_API_KEY')
        self._email = email or os.environ.get('USAJOBS_EMAIL')

    @property
    def name(self) -> str:
        return "usajobs"

    @property
    def display_name(self) -> str:
        return "USAJobs (US Government)"

    @property
    def requires_auth(self) -> bool:
        return True

    def is_configured(self) -> bool:
        return bool(self._api_key and self._email)

    def get_setup_instructions(self) -> str:
        return """
USAJobs Setup Instructions:
==========================

USAJobs requires a free API key from the USAJobs Developer Portal.

Steps:
    1. Visit https://developer.usajobs.gov/
    2. Click "Request API Key" and fill out the application form
    3. You'll receive an API key via email
    4. Set the following environment variables:

       export USAJOBS_API_KEY="your-api-key-here"
       export USAJOBS_EMAIL="your-email@example.com"

    OR provide them when initializing:

       from hired.search.sources.usajobs import USAJobsSource
       source = USAJobsSource(api_key="your-key", email="your-email")

Features:
    - Access to all US Federal Government job postings
    - Free API with generous rate limits
    - Well-documented and stable API

Documentation:
    https://developer.usajobs.gov/api-reference/
    https://developer.usajobs.gov/general/quick-start
"""

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the USAJobs API.

        Args:
            params: Query parameters

        Returns:
            API response as dictionary

        Raises:
            SourceConfigError: If authentication fails
            Exception: For other API errors
        """
        headers = {
            'Host': 'data.usajobs.gov',
            'User-Agent': self._email,
            'Authorization-Key': self._api_key,
        }

        try:
            response = requests.get(
                self.API_BASE_URL,
                params=params,
                headers=headers,
                timeout=30
            )

            if response.status_code == 401:
                raise SourceConfigError(
                    "USAJobs authentication failed. "
                    "Please check your API key and email.\n\n"
                    f"{self.get_setup_instructions()}"
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("USAJobs API request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"USAJobs API request failed: {str(e)}")

    def _map_job_type(self, position_type: str) -> JobType:
        """Map USAJobs position type to our JobType enum."""
        # USAJobs uses numeric codes, but we'll handle string descriptions too
        type_mapping = {
            'permanent': JobType.FULL_TIME,
            'term': JobType.CONTRACT,
            'temporary': JobType.TEMPORARY,
            'internship': JobType.INTERNSHIP,
            'recent graduate': JobType.FULL_TIME,
        }

        position_lower = position_type.lower()
        for key, value in type_mapping.items():
            if key in position_lower:
                return value

        return JobType.OTHER

    def _parse_salary(self, salary_data: Dict[str, Any]) -> Optional[CompensationInfo]:
        """Parse USAJobs salary information."""
        if not salary_data:
            return None

        try:
            min_amount = salary_data.get('MinimumRange')
            max_amount = salary_data.get('MaximumRange')

            # Convert string to float if needed
            if isinstance(min_amount, str):
                min_amount = float(min_amount.replace(',', '').replace('$', ''))
            if isinstance(max_amount, str):
                max_amount = float(max_amount.replace(',', '').replace('$', ''))

            return CompensationInfo(
                min_amount=min_amount,
                max_amount=max_amount,
                currency='USD',
                interval='yearly'  # USAJobs salaries are typically annual
            )
        except (ValueError, AttributeError, TypeError):
            return None

    def _convert_usajobs_result(self, item: Dict[str, Any]) -> JobResult:
        """Convert a USAJobs result to JobResult."""
        match_data = item.get('MatchedObjectDescriptor', {})

        # Extract position info
        position_title = match_data.get('PositionTitle', 'Unknown')
        organization = match_data.get('OrganizationName', 'US Government')

        # Extract location
        locations = match_data.get('PositionLocation', [])
        location = None
        is_remote = False

        if locations:
            # Use the first location
            loc_data = locations[0] if isinstance(locations, list) else locations
            location = LocationInfo(
                city=loc_data.get('CityName'),
                state=loc_data.get('StateProvince'),
                country=loc_data.get('CountryCode', 'US'),
            )

        # Check for remote work
        remote_indicator = match_data.get('PositionRemoteIndicator')
        if remote_indicator or str(match_data.get('PositionOfferingTypeCode', '')).startswith('15'):
            is_remote = True

        # Extract URLs
        position_uri = match_data.get('PositionURI', '')
        apply_uri = match_data.get('ApplyURI', [])
        job_url = position_uri or (apply_uri[0] if apply_uri else '')

        # Extract salary
        salary_data = match_data.get('PositionRemuneration', [])
        compensation = None
        if salary_data:
            salary_info = salary_data[0] if isinstance(salary_data, list) else salary_data
            compensation = self._parse_salary(salary_info)

        # Parse dates
        date_posted = None
        application_deadline = None

        pub_start = match_data.get('PublicationStartDate')
        if pub_start:
            try:
                date_posted = datetime.fromisoformat(pub_start.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        app_close = match_data.get('ApplicationCloseDate')
        if app_close:
            try:
                application_deadline = datetime.fromisoformat(app_close.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Extract description and qualifications
        description_parts = []
        if match_data.get('UserArea', {}).get('Details', {}).get('MajorDuties'):
            description_parts.append(match_data['UserArea']['Details']['MajorDuties'])
        if match_data.get('QualificationSummary'):
            description_parts.append('\n\nQualifications:\n' + match_data['QualificationSummary'])

        description = '\n\n'.join(description_parts) if description_parts else None

        # Job type
        position_schedule = match_data.get('PositionSchedule', [])
        job_type = None
        if position_schedule:
            schedule = position_schedule[0] if isinstance(position_schedule, list) else position_schedule
            job_type = self._map_job_type(schedule.get('Name', ''))

        return JobResult(
            title=position_title,
            source=self.name,
            company=organization,
            job_url=job_url,
            location=location,
            is_remote=is_remote,
            description=description,
            job_type=job_type,
            compensation=compensation,
            date_posted=date_posted,
            application_deadline=application_deadline,
            raw_data=item,
        )

    def search(self, criteria: SearchCriteria) -> List[JobResult]:
        """
        Search for jobs using USAJobs API.

        Args:
            criteria: Search criteria

        Returns:
            List of JobResult objects
        """
        self.validate_configured()

        # Build API parameters
        params = {
            'Keyword': criteria.query,
            'ResultsPerPage': min(criteria.results_wanted, 500),  # API max is 500
        }

        # Add location filters
        if criteria.location:
            params['LocationName'] = criteria.location
        elif criteria.city and criteria.state:
            params['LocationName'] = f"{criteria.city}, {criteria.state}"

        # Add posted date filter
        if criteria.posted_within_days:
            params['DatePosted'] = criteria.posted_within_days

        # Add remote filter
        if criteria.is_remote:
            params['RemoteIndicator'] = 'True'

        # Add pagination
        if criteria.offset > 0:
            page = (criteria.offset // criteria.results_wanted) + 1
            params['Page'] = page

        # Add any source-specific parameters
        for key, value in criteria.source_params.items():
            if key not in params:
                params[key] = value

        # Make the API request
        try:
            response_data = self._make_request(params)

            search_result = response_data.get('SearchResult', {})
            items = search_result.get('SearchResultItems', [])

            if not items:
                return []

            # Convert to JobResult objects
            results = []
            for item in items:
                try:
                    job_result = self._convert_usajobs_result(item)
                    results.append(job_result)
                except Exception as e:
                    # Log error but continue processing
                    continue

            return results

        except SourceConfigError:
            raise
        except Exception as e:
            raise Exception(f"USAJobs search failed: {str(e)}")


# Create a default instance
_default_usajobs_source = USAJobsSource()


def get_usajobs_source() -> USAJobsSource:
    """Get the default USAJobs source instance."""
    return _default_usajobs_source
