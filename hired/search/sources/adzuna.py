"""
Adzuna source adapter.

Accesses the Adzuna Jobs API (https://developer.adzuna.com/).
Requires a free API key (app_id and app_key) from the Adzuna Developer Portal.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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


class AdzunaSource(JobSearchSource):
    """
    Adzuna API source implementation.

    Searches international job postings via the Adzuna Jobs API.
    Requires a free API key from https://developer.adzuna.com/.
    """

    API_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        country: str = "us"
    ):
        """
        Initialize Adzuna source.

        Args:
            app_id: Adzuna app ID. If not provided, reads from ADZUNA_APP_ID env var.
            app_key: Adzuna app key. If not provided, reads from ADZUNA_APP_KEY env var.
            country: Country code (default: 'us'). Options: us, uk, ca, au, de, fr, etc.
        """
        self._app_id = app_id or os.environ.get('ADZUNA_APP_ID')
        self._app_key = app_key or os.environ.get('ADZUNA_APP_KEY')
        self._country = country

    @property
    def name(self) -> str:
        return "adzuna"

    @property
    def display_name(self) -> str:
        return "Adzuna (International)"

    @property
    def requires_auth(self) -> bool:
        return True

    def is_configured(self) -> bool:
        return bool(self._app_id and self._app_key)

    def get_setup_instructions(self) -> str:
        return """
Adzuna Setup Instructions:
=========================

Adzuna requires a free API key from the Adzuna Developer Portal.

Steps:
    1. Visit https://developer.adzuna.com/
    2. Click "Sign Up" and create an account
    3. After registration, you'll receive an app_id and app_key
    4. Set the following environment variables:

       export ADZUNA_APP_ID="your-app-id"
       export ADZUNA_APP_KEY="your-app-key"

    OR provide them when initializing:

       from hired.search.sources.adzuna import AdzunaSource
       source = AdzunaSource(app_id="your-id", app_key="your-key")

Features:
    - Access to job postings from multiple countries
    - Free tier with generous rate limits
    - Rich salary data and company information
    - Supports US, UK, Canada, Australia, Germany, France, and more

Documentation:
    https://developer.adzuna.com/overview
    https://developer.adzuna.com/docs/search
"""

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Adzuna API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            API response as dictionary

        Raises:
            SourceConfigError: If authentication fails
            Exception: For other API errors
        """
        # Add authentication parameters
        params['app_id'] = self._app_id
        params['app_key'] = self._app_key

        url = f"{self.API_BASE_URL}/{self._country}{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 401 or response.status_code == 403:
                raise SourceConfigError(
                    "Adzuna authentication failed. "
                    "Please check your app_id and app_key.\n\n"
                    f"{self.get_setup_instructions()}"
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("Adzuna API request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Adzuna API request failed: {str(e)}")

    def _map_job_type(self, contract_type: Optional[str]) -> Optional[JobType]:
        """Map Adzuna contract type to our JobType enum."""
        if not contract_type:
            return None

        type_mapping = {
            'permanent': JobType.FULL_TIME,
            'full_time': JobType.FULL_TIME,
            'part_time': JobType.PART_TIME,
            'contract': JobType.CONTRACT,
            'temporary': JobType.TEMPORARY,
            'internship': JobType.INTERNSHIP,
        }

        contract_lower = contract_type.lower()
        return type_mapping.get(contract_lower, JobType.OTHER)

    def _parse_salary(self, result: Dict[str, Any]) -> Optional[CompensationInfo]:
        """Parse Adzuna salary information."""
        salary_min = result.get('salary_min')
        salary_max = result.get('salary_max')

        if salary_min is None and salary_max is None:
            return None

        return CompensationInfo(
            min_amount=salary_min,
            max_amount=salary_max,
            currency='USD' if self._country == 'us' else None,
            interval='yearly'
        )

    def _parse_location(self, result: Dict[str, Any]) -> Optional[LocationInfo]:
        """Parse Adzuna location information."""
        location_data = result.get('location', {})

        if not location_data:
            return None

        # Adzuna provides various location fields
        display_name = location_data.get('display_name')
        area = location_data.get('area', [])

        # Try to parse structured location
        city = None
        state = None
        country = None

        if isinstance(area, list) and len(area) > 0:
            # area is typically [city, state, country] or similar
            if len(area) >= 1:
                city = area[0]
            if len(area) >= 2:
                state = area[1]
            if len(area) >= 3:
                country = area[2]

        return LocationInfo(
            city=city,
            state=state,
            country=country or self._country.upper(),
            raw=display_name,
        )

    def _convert_adzuna_result(self, result: Dict[str, Any]) -> JobResult:
        """Convert an Adzuna result to JobResult."""
        # Extract basic info
        title = result.get('title', 'Unknown')
        company = result.get('company', {}).get('display_name')
        description = result.get('description', '')

        # Remove HTML tags from description if present
        if description:
            import re
            description = re.sub(r'<[^>]+>', '', description)

        # Parse dates
        date_posted = None
        created_date = result.get('created')
        if created_date:
            try:
                date_posted = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Check for remote work
        is_remote = False
        category_tag = result.get('category', {}).get('tag', '')
        if 'remote' in category_tag.lower() or 'remote' in description.lower()[:200]:
            is_remote = True

        return JobResult(
            title=title,
            source=self.name,
            company=company,
            job_url=result.get('redirect_url'),
            location=self._parse_location(result),
            is_remote=is_remote,
            description=description,
            job_type=self._map_job_type(result.get('contract_type')),
            compensation=self._parse_salary(result),
            date_posted=date_posted,
            raw_data=result,
        )

    def search(self, criteria: SearchCriteria) -> List[JobResult]:
        """
        Search for jobs using Adzuna API.

        Args:
            criteria: Search criteria

        Returns:
            List of JobResult objects
        """
        self.validate_configured()

        # Build API parameters
        params = {
            'what': criteria.query,
            'results_per_page': min(criteria.results_wanted, 50),  # API max is 50
            'page': (criteria.offset // criteria.results_wanted) + 1,
        }

        # Add location filter
        if criteria.location:
            params['where'] = criteria.location
        elif criteria.city or criteria.state:
            location_parts = []
            if criteria.city:
                location_parts.append(criteria.city)
            if criteria.state:
                location_parts.append(criteria.state)
            params['where'] = ', '.join(location_parts)

        # Add distance filter (Adzuna uses miles)
        if criteria.distance_miles:
            params['distance'] = criteria.distance_miles

        # Add salary filter
        if criteria.min_salary:
            params['salary_min'] = criteria.min_salary
        if criteria.max_salary:
            params['salary_max'] = criteria.max_salary

        # Add date filter (Adzuna uses max_days_old)
        if criteria.posted_within_days:
            params['max_days_old'] = criteria.posted_within_days

        # Add contract type filter
        if criteria.job_type:
            type_mapping = {
                JobType.FULL_TIME: 'permanent',
                JobType.PART_TIME: 'part_time',
                JobType.CONTRACT: 'contract',
                JobType.TEMPORARY: 'temporary',
            }
            if criteria.job_type in type_mapping:
                params['contract'] = type_mapping[criteria.job_type]

        # Add any source-specific parameters
        country = criteria.source_params.get('country', self._country)
        for key, value in criteria.source_params.items():
            if key not in ['country'] and key not in params:
                params[key] = value

        # Make the API request
        try:
            # Update country if specified in source_params
            original_country = self._country
            if country != self._country:
                self._country = country

            response_data = self._make_request('/search/1', params)

            # Restore original country
            self._country = original_country

            results_data = response_data.get('results', [])

            if not results_data:
                return []

            # Convert to JobResult objects
            results = []
            for result in results_data:
                try:
                    job_result = self._convert_adzuna_result(result)
                    results.append(job_result)
                except Exception as e:
                    # Log error but continue processing
                    continue

            return results

        except SourceConfigError:
            raise
        except Exception as e:
            raise Exception(f"Adzuna search failed: {str(e)}")


# Create a default instance
_default_adzuna_source = AdzunaSource()


def get_adzuna_source() -> AdzunaSource:
    """Get the default Adzuna source instance."""
    return _default_adzuna_source
