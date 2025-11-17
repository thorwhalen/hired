"""
Base classes and interfaces for job search functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    """Standardized job types across all sources."""
    FULL_TIME = "fulltime"
    PART_TIME = "parttime"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    VOLUNTEER = "volunteer"
    OTHER = "other"


@dataclass
class CompensationInfo:
    """Compensation information for a job."""
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    interval: Optional[str] = None  # e.g., "yearly", "monthly", "hourly"


@dataclass
class LocationInfo:
    """Location information for a job."""
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    raw: Optional[str] = None  # Raw location string from source


@dataclass
class JobResult:
    """
    Standardized job result across all sources.

    This provides a unified interface regardless of which source
    the job was retrieved from.
    """
    # Required fields
    title: str
    source: str  # Name of the source (e.g., "indeed", "usajobs")

    # Common optional fields
    company: Optional[str] = None
    company_url: Optional[str] = None
    job_url: Optional[str] = None
    location: Optional[LocationInfo] = None
    is_remote: Optional[bool] = None
    description: Optional[str] = None
    job_type: Optional[JobType] = None
    compensation: Optional[CompensationInfo] = None
    date_posted: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    application_deadline: Optional[datetime] = None

    # Additional metadata
    skills: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)

    # Source-specific data
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert JobResult to dictionary."""
        result = {
            'title': self.title,
            'source': self.source,
            'company': self.company,
            'company_url': self.company_url,
            'job_url': self.job_url,
            'is_remote': self.is_remote,
            'description': self.description,
            'job_type': self.job_type.value if self.job_type else None,
            'skills': self.skills,
            'benefits': self.benefits,
            'emails': self.emails,
        }

        if self.location:
            result['location'] = {
                'city': self.location.city,
                'state': self.location.state,
                'country': self.location.country,
                'postal_code': self.location.postal_code,
                'raw': self.location.raw,
            }

        if self.compensation:
            result['compensation'] = {
                'min_amount': self.compensation.min_amount,
                'max_amount': self.compensation.max_amount,
                'currency': self.compensation.currency,
                'interval': self.compensation.interval,
            }

        if self.date_posted:
            result['date_posted'] = self.date_posted.isoformat()
        if self.date_updated:
            result['date_updated'] = self.date_updated.isoformat()
        if self.application_deadline:
            result['application_deadline'] = self.application_deadline.isoformat()

        return result


@dataclass
class SearchCriteria:
    """
    Standardized search criteria across all sources.

    Different sources may not support all criteria, but this provides
    a consistent interface for users.
    """
    # Required
    query: str  # Free-form text query

    # Optional location filters
    location: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    distance_miles: Optional[int] = None

    # Job type and arrangement
    job_type: Optional[JobType] = None
    is_remote: Optional[bool] = None

    # Temporal filters
    posted_within_days: Optional[int] = None

    # Pagination
    results_wanted: int = 20
    offset: int = 0

    # Compensation
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None

    # Additional filters
    keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)

    # Source-specific parameters
    source_params: Dict[str, Any] = field(default_factory=dict)


class SourceConfigError(Exception):
    """Raised when a source is not properly configured."""
    pass


class JobSearchSource(ABC):
    """
    Abstract base class for job search sources.

    All job search sources must implement this interface to be
    registered in the system.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this source (e.g., 'indeed', 'usajobs')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the display name of this source (e.g., 'Indeed', 'USAJobs')."""
        pass

    @property
    @abstractmethod
    def requires_auth(self) -> bool:
        """Return True if this source requires authentication/API keys."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if this source is properly configured.

        Returns:
            True if the source is ready to use, False otherwise.
        """
        pass

    @abstractmethod
    def get_setup_instructions(self) -> str:
        """
        Return setup instructions for this source.

        Should include:
        - Where to get API keys if needed
        - Environment variables or config file settings
        - URLs for documentation

        Returns:
            Multi-line string with setup instructions.
        """
        pass

    @abstractmethod
    def search(self, criteria: SearchCriteria) -> List[JobResult]:
        """
        Search for jobs using the given criteria.

        Args:
            criteria: SearchCriteria object with search parameters

        Returns:
            List of JobResult objects

        Raises:
            SourceConfigError: If the source is not properly configured
            Exception: For other errors during search
        """
        pass

    def validate_configured(self) -> None:
        """
        Validate that the source is configured, raise error if not.

        Raises:
            SourceConfigError: If the source is not properly configured
        """
        if not self.is_configured():
            instructions = self.get_setup_instructions()
            raise SourceConfigError(
                f"{self.display_name} is not properly configured.\n\n"
                f"{instructions}"
            )
