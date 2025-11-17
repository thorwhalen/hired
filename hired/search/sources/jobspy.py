"""
JobSpy source adapter.

Wraps the python-jobspy package to search across multiple job boards
(LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google) concurrently.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from hired.search.base import (
    JobSearchSource,
    JobResult,
    SearchCriteria,
    JobType,
    LocationInfo,
    CompensationInfo,
    SourceConfigError,
)


class JobSpySource(JobSearchSource):
    """
    JobSpy source implementation.

    Uses python-jobspy to scrape jobs from multiple sources simultaneously.
    Does not require API keys, but may be subject to rate limiting.
    """

    def __init__(
        self,
        sites: Optional[List[str]] = None,
        proxies: Optional[List[str]] = None
    ):
        """
        Initialize JobSpy source.

        Args:
            sites: List of site names to search. Options: 'indeed', 'linkedin',
                   'zip_recruiter', 'glassdoor', 'google'. If None, searches all.
            proxies: Optional list of proxies in format 'user:pass@host:port'
        """
        self._sites = sites or ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'google']
        self._proxies = proxies
        self._jobspy_available = self._check_jobspy_available()

    def _check_jobspy_available(self) -> bool:
        """Check if python-jobspy package is available."""
        try:
            import jobspy  # noqa
            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "jobspy"

    @property
    def display_name(self) -> str:
        return "JobSpy (Multi-Source Scraper)"

    @property
    def requires_auth(self) -> bool:
        return False

    def is_configured(self) -> bool:
        return self._jobspy_available

    def get_setup_instructions(self) -> str:
        return """
JobSpy Setup Instructions:
=========================

JobSpy does not require API keys, but you need to install the python-jobspy package.

Installation:
    pip install python-jobspy

Features:
    - Scrapes jobs from multiple sources: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google
    - No API keys required
    - Concurrent scraping across all sources

Note:
    - LinkedIn is rate-limited around the 10th page with one IP
    - Consider using proxies for large-scale scraping
    - Indeed is the most reliable source with no rate limiting

Documentation:
    https://github.com/speedyapply/JobSpy
    https://pypi.org/project/python-jobspy/
"""

    def _map_job_type(self, job_type_str: Optional[str]) -> Optional[JobType]:
        """Map JobSpy job type to our JobType enum."""
        if not job_type_str:
            return None

        mapping = {
            'fulltime': JobType.FULL_TIME,
            'parttime': JobType.PART_TIME,
            'contract': JobType.CONTRACT,
            'internship': JobType.INTERNSHIP,
            'temporary': JobType.TEMPORARY,
        }
        return mapping.get(job_type_str.lower(), JobType.OTHER)

    def _convert_jobspy_result(self, row: Dict[str, Any], site: str) -> JobResult:
        """Convert a JobSpy result row to JobResult."""
        # Extract location info
        location = None
        if any([row.get('location'), row.get('city'), row.get('state'), row.get('country')]):
            # Check if location is a dict or string
            loc_data = row.get('location', {})
            if isinstance(loc_data, dict):
                location = LocationInfo(
                    city=loc_data.get('city'),
                    state=loc_data.get('state'),
                    country=loc_data.get('country'),
                    postal_code=loc_data.get('postal_code'),
                    raw=loc_data.get('raw'),
                )
            else:
                location = LocationInfo(
                    city=row.get('city'),
                    state=row.get('state'),
                    country=row.get('country'),
                    raw=str(loc_data) if loc_data else None,
                )

        # Extract compensation info
        compensation = None
        comp_data = row.get('compensation') or row.get('salary')
        if comp_data and isinstance(comp_data, dict):
            compensation = CompensationInfo(
                min_amount=comp_data.get('min_amount'),
                max_amount=comp_data.get('max_amount'),
                currency=comp_data.get('currency'),
                interval=comp_data.get('interval'),
            )

        # Parse date posted
        date_posted = None
        if row.get('date_posted'):
            try:
                if isinstance(row['date_posted'], str):
                    date_posted = datetime.fromisoformat(row['date_posted'].replace('Z', '+00:00'))
                elif isinstance(row['date_posted'], datetime):
                    date_posted = row['date_posted']
            except (ValueError, AttributeError):
                pass

        return JobResult(
            title=row.get('title', 'Unknown'),
            source=site,
            company=row.get('company'),
            company_url=row.get('company_url'),
            job_url=row.get('job_url'),
            location=location,
            is_remote=row.get('is_remote'),
            description=row.get('description'),
            job_type=self._map_job_type(row.get('job_type')),
            compensation=compensation,
            date_posted=date_posted,
            emails=row.get('emails', []) if isinstance(row.get('emails'), list) else [],
            raw_data=row,
        )

    def search(self, criteria: SearchCriteria) -> List[JobResult]:
        """
        Search for jobs using JobSpy.

        Args:
            criteria: Search criteria

        Returns:
            List of JobResult objects
        """
        self.validate_configured()

        try:
            from jobspy import scrape_jobs
        except ImportError:
            raise SourceConfigError(
                "python-jobspy is not installed. "
                "Install it with: pip install python-jobspy"
            )

        # Build JobSpy parameters
        params = {
            'search_term': criteria.query,
            'results_wanted': criteria.results_wanted,
        }

        # Add optional parameters
        if criteria.location:
            params['location'] = criteria.location

        if criteria.distance_miles:
            params['distance'] = criteria.distance_miles

        if criteria.is_remote is not None:
            params['is_remote'] = criteria.is_remote

        if criteria.job_type:
            # Map our JobType to JobSpy format
            job_type_map = {
                JobType.FULL_TIME: 'fulltime',
                JobType.PART_TIME: 'parttime',
                JobType.CONTRACT: 'contract',
                JobType.INTERNSHIP: 'internship',
            }
            if criteria.job_type in job_type_map:
                params['job_type'] = job_type_map[criteria.job_type]

        if criteria.posted_within_days:
            params['hours_old'] = criteria.posted_within_days * 24

        # Use configured sites or allow override via source_params
        sites = criteria.source_params.get('sites', self._sites)
        params['site_name'] = sites

        # Add proxies if configured
        if self._proxies:
            params['proxies'] = self._proxies

        # Add any additional source-specific parameters
        for key, value in criteria.source_params.items():
            if key not in ['sites'] and key not in params:
                params[key] = value

        # Perform the search
        try:
            df = scrape_jobs(**params)

            if df is None or df.empty:
                return []

            # Convert to list of JobResult objects
            results = []
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                site = row_dict.get('site', 'unknown')
                try:
                    job_result = self._convert_jobspy_result(row_dict, site)
                    results.append(job_result)
                except Exception as e:
                    # Log error but continue processing other results
                    # You might want to add proper logging here
                    continue

            return results

        except Exception as e:
            raise Exception(f"JobSpy search failed: {str(e)}")


# Create a default instance
_default_jobspy_source = JobSpySource()


def get_jobspy_source() -> JobSpySource:
    """Get the default JobSpy source instance."""
    return _default_jobspy_source
