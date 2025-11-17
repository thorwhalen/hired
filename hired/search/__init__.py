"""
Job search functionality for the hired package.

This module provides a unified interface for searching jobs across
multiple sources (Indeed, LinkedIn, USAJobs, Adzuna, etc.).

Example usage:
    >>> from hired.search import JobSources, SearchCriteria
    >>>
    >>> # Create job sources facade
    >>> sources = JobSources()
    >>>
    >>> # List available sources
    >>> print(sources.list_available())
    >>>
    >>> # Search using a specific source
    >>> criteria = SearchCriteria(
    ...     query="python developer",
    ...     location="San Francisco, CA",
    ...     results_wanted=20
    ... )
    >>> results = sources.jobspy.search(criteria)
    >>>
    >>> # Or search across all sources
    >>> all_results = sources.search_all(criteria)
"""

from hired.search.base import (
    JobSearchSource,
    JobResult,
    SearchCriteria,
    JobType,
    LocationInfo,
    CompensationInfo,
    SourceConfigError,
)
from hired.search.registry import SourceRegistry, get_registry, register_source
from hired.search.facade import JobSources

# Import and register all built-in sources
from hired.search.sources.jobspy import JobSpySource, get_jobspy_source
from hired.search.sources.usajobs import USAJobsSource, get_usajobs_source
from hired.search.sources.adzuna import AdzunaSource, get_adzuna_source


def _register_default_sources():
    """Register all default job search sources."""
    # Only register if not already registered
    registry = get_registry()

    if 'jobspy' not in registry:
        register_source(get_jobspy_source(), JobSpySource)

    if 'usajobs' not in registry:
        register_source(get_usajobs_source(), USAJobsSource)

    if 'adzuna' not in registry:
        register_source(get_adzuna_source(), AdzunaSource)


# Auto-register default sources on module import
_register_default_sources()


__all__ = [
    # Main user-facing classes
    'JobSources',
    'SearchCriteria',
    'JobResult',

    # Base classes for extending
    'JobSearchSource',
    'JobType',
    'LocationInfo',
    'CompensationInfo',

    # Registry
    'SourceRegistry',
    'get_registry',
    'register_source',

    # Built-in source classes
    'JobSpySource',
    'USAJobsSource',
    'AdzunaSource',

    # Exceptions
    'SourceConfigError',
]
