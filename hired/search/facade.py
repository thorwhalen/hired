"""
Main facade for job search functionality.
"""

from typing import List, Dict, Optional, Union
from hired.search.base import JobSearchSource, SearchCriteria, JobResult
from hired.search.registry import get_registry


class JobSources:
    """
    Main facade for accessing job search sources.

    Provides both mapping interface (dict-like access) and attribute access
    to registered job sources.

    Examples:
        >>> sources = JobSources()
        >>> # List all available sources
        >>> sources.list()
        ['jobspy', 'usajobs', 'adzuna']

        >>> # Access via attribute
        >>> results = sources.jobspy.search(SearchCriteria(query="python developer"))

        >>> # Access via mapping
        >>> results = sources['indeed'].search(SearchCriteria(query="data scientist"))

        >>> # Search across multiple sources
        >>> results = sources.search_all(
        ...     SearchCriteria(query="software engineer", location="San Francisco")
        ... )
    """

    def __init__(self, registry=None):
        """
        Initialize JobSources facade.

        Args:
            registry: Optional SourceRegistry instance. If None, uses global registry.
        """
        self._registry = registry or get_registry()

    def list(self) -> List[str]:
        """
        List all registered sources.

        Returns:
            List of source names
        """
        return self._registry.list_sources()

    def list_available(self) -> List[str]:
        """
        List sources that are configured and ready to use.

        Returns:
            List of configured source names
        """
        return self._registry.list_available_sources()

    def list_unconfigured(self) -> List[str]:
        """
        List sources that need configuration.

        Returns:
            List of unconfigured source names
        """
        return self._registry.list_unconfigured_sources()

    def get_source(self, name: str) -> JobSearchSource:
        """
        Get a source by name.

        Args:
            name: Name of the source

        Returns:
            JobSearchSource instance

        Raises:
            KeyError: If source not found
        """
        return self._registry.get(name)

    def get_info(self, name: str) -> Dict[str, any]:
        """
        Get information about a source.

        Args:
            name: Name of the source

        Returns:
            Dictionary with source information including setup instructions
        """
        return self._registry.get_source_info(name)

    def search(
        self,
        source_name: str,
        criteria: SearchCriteria
    ) -> List[JobResult]:
        """
        Search using a specific source.

        Args:
            source_name: Name of the source to use
            criteria: Search criteria

        Returns:
            List of JobResult objects
        """
        source = self.get_source(source_name)
        return source.search(criteria)

    def search_all(
        self,
        criteria: SearchCriteria,
        sources: Optional[List[str]] = None,
        skip_unconfigured: bool = True
    ) -> List[JobResult]:
        """
        Search across multiple sources.

        Args:
            criteria: Search criteria
            sources: Optional list of source names. If None, uses all available sources.
            skip_unconfigured: If True, skip sources that are not configured

        Returns:
            Combined list of JobResult objects from all sources
        """
        if sources is None:
            if skip_unconfigured:
                sources = self.list_available()
            else:
                sources = self.list()

        results = []
        errors = {}

        for source_name in sources:
            try:
                source = self.get_source(source_name)

                # Skip if not configured and skip_unconfigured is True
                if skip_unconfigured and not source.is_configured():
                    continue

                source_results = source.search(criteria)
                results.extend(source_results)

            except Exception as e:
                errors[source_name] = str(e)

        # If there were errors, you might want to log them or raise a warning
        # For now, we'll just continue and return what we got
        if errors and not results:
            error_msg = "\n".join([f"  - {name}: {err}" for name, err in errors.items()])
            raise Exception(f"All sources failed:\n{error_msg}")

        return results

    def print_status(self) -> None:
        """Print the status of all registered sources."""
        all_sources = self.list()

        if not all_sources:
            print("No job search sources registered.")
            return

        print("Job Search Sources Status:")
        print("=" * 60)

        for source_name in sorted(all_sources):
            try:
                info = self.get_info(source_name)
                status = "✓ Ready" if info['is_configured'] else "✗ Needs Setup"
                auth = " (requires auth)" if info['requires_auth'] else ""

                print(f"\n{info['display_name']} ({source_name}): {status}{auth}")

                if not info['is_configured']:
                    print(f"\nSetup instructions:")
                    for line in info['setup_instructions'].split('\n'):
                        if line.strip():
                            print(f"  {line}")

            except Exception as e:
                print(f"\n{source_name}: Error - {str(e)}")

        print("\n" + "=" * 60)

    # Mapping interface (dict-like access)
    def __getitem__(self, name: str) -> JobSearchSource:
        """Get source by name using bracket notation."""
        return self.get_source(name)

    def __contains__(self, name: str) -> bool:
        """Check if a source exists."""
        return name in self._registry

    def keys(self) -> List[str]:
        """Get list of source names (dict-like interface)."""
        return self.list()

    # Attribute access
    def __getattr__(self, name: str) -> JobSearchSource:
        """
        Get source by name using attribute notation.

        Args:
            name: Name of the source

        Returns:
            JobSearchSource instance

        Raises:
            AttributeError: If source not found
        """
        # Avoid recursion for private attributes
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        try:
            return self.get_source(name)
        except KeyError:
            available = ", ".join(self.list())
            raise AttributeError(
                f"No source named '{name}'. Available sources: {available}"
            )

    def __dir__(self):
        """Return list of attributes including source names."""
        base_attrs = [
            'list', 'list_available', 'list_unconfigured',
            'get_source', 'get_info', 'search', 'search_all',
            'print_status', 'keys'
        ]
        return base_attrs + self.list()
