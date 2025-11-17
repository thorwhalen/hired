"""
Registry system for managing job search sources.
"""

from typing import Dict, List, Type, Optional
from hired.search.base import JobSearchSource


class SourceRegistry:
    """
    Registry for job search sources.

    Provides a plugin system where sources can be registered
    and retrieved by name.
    """

    def __init__(self):
        self._sources: Dict[str, JobSearchSource] = {}
        self._source_classes: Dict[str, Type[JobSearchSource]] = {}

    def register(
        self,
        source: JobSearchSource,
        source_class: Optional[Type[JobSearchSource]] = None
    ) -> None:
        """
        Register a job search source.

        Args:
            source: Instance of a JobSearchSource implementation
            source_class: Optional class of the source for reference
        """
        name = source.name
        if name in self._sources:
            raise ValueError(f"Source '{name}' is already registered")

        self._sources[name] = source
        if source_class:
            self._source_classes[name] = source_class

    def unregister(self, name: str) -> None:
        """
        Unregister a source by name.

        Args:
            name: Name of the source to unregister
        """
        if name in self._sources:
            del self._sources[name]
        if name in self._source_classes:
            del self._source_classes[name]

    def get(self, name: str) -> JobSearchSource:
        """
        Get a source by name.

        Args:
            name: Name of the source

        Returns:
            JobSearchSource instance

        Raises:
            KeyError: If source not found
        """
        if name not in self._sources:
            available = ", ".join(self._sources.keys())
            raise KeyError(
                f"Source '{name}' not found. Available sources: {available}"
            )
        return self._sources[name]

    def list_sources(self) -> List[str]:
        """
        List all registered source names.

        Returns:
            List of source names
        """
        return list(self._sources.keys())

    def list_available_sources(self) -> List[str]:
        """
        List sources that are properly configured and ready to use.

        Returns:
            List of source names that are configured
        """
        return [
            name for name, source in self._sources.items()
            if source.is_configured()
        ]

    def list_unconfigured_sources(self) -> List[str]:
        """
        List sources that are registered but not configured.

        Returns:
            List of source names that need configuration
        """
        return [
            name for name, source in self._sources.items()
            if not source.is_configured()
        ]

    def get_source_info(self, name: str) -> Dict[str, any]:
        """
        Get information about a source.

        Args:
            name: Name of the source

        Returns:
            Dictionary with source information
        """
        source = self.get(name)
        return {
            'name': source.name,
            'display_name': source.display_name,
            'requires_auth': source.requires_auth,
            'is_configured': source.is_configured(),
            'setup_instructions': source.get_setup_instructions(),
        }

    def __contains__(self, name: str) -> bool:
        """Check if a source is registered."""
        return name in self._sources

    def __len__(self) -> int:
        """Return number of registered sources."""
        return len(self._sources)


# Global registry instance
_global_registry = SourceRegistry()


def get_registry() -> SourceRegistry:
    """Get the global source registry."""
    return _global_registry


def register_source(
    source: JobSearchSource,
    source_class: Optional[Type[JobSearchSource]] = None
) -> None:
    """
    Register a source with the global registry.

    Args:
        source: Instance of a JobSearchSource implementation
        source_class: Optional class of the source for reference
    """
    _global_registry.register(source, source_class)
