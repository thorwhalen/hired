"""
Core data models and protocols for the hired package.

Define:
- RenderingConfig: Configuration for rendering pipeline
- ContentSource: Protocol for data sources (candidate/job info)
- AIAgent: Protocol for content generation agents
- Renderer: Protocol for resume renderers
- ResumeSchemaExtended: Extended version of ResumeSchema that allows extra fields
"""

from typing import Protocol, Any, List, Dict, Type, Optional
from collections.abc import Mapping
from dataclasses import dataclass
from pydantic import ConfigDict
from hired.resumejson_pydantic_models import ResumeSchema


class ContentSource(Protocol):
    """Protocol for sources that provide candidate or job information."""

    def read(self) -> Mapping[str, Any]: ...


class AIAgent(Protocol):
    """Protocol for AI agents that generate resume content."""

    def generate_content(
        self, candidate_info: Mapping[str, Any], job_info: Mapping[str, Any]
    ) -> 'ResumeSchemaExtended': ...


class Renderer(Protocol):
    """Protocol for resume renderers."""

    def render(
        self, content: 'ResumeSchemaExtended', config: 'RenderingConfig'
    ) -> bytes: ...


class RendererRegistry:
    """Registry for managing multiple renderer implementations."""

    def __init__(self):
        self._renderers: dict[str, type[Renderer]] = {}
        self._instances: dict[str, Renderer] = {}

    def register(self, format_name: str, renderer_class: type[Renderer]) -> None:
        """Register a renderer class for a specific format."""
        self._renderers[format_name] = renderer_class

    def get_renderer(self, format_name: str) -> Renderer:
        """Get a renderer instance for the specified format."""
        if format_name not in self._renderers:
            raise ValueError(f"No renderer registered for format: {format_name}")

        # Cache instances for reuse
        if format_name not in self._instances:
            self._instances[format_name] = self._renderers[format_name]()

        return self._instances[format_name]

    def list_formats(self) -> list[str]:
        """List all registered format names."""
        return list(self._renderers.keys())

    def is_registered(self, format_name: str) -> bool:
        """Check if a format is registered."""
        return format_name in self._renderers


# Global renderer registry instance
_renderer_registry = RendererRegistry()


def register_renderer(format_name: str):
    """Decorator for registering renderer classes."""

    def decorator(renderer_class: type[Renderer]):
        _renderer_registry.register(format_name, renderer_class)
        return renderer_class

    return decorator


def get_renderer_registry() -> RendererRegistry:
    """Get the global renderer registry."""
    return _renderer_registry


class ResumeSchemaExtended(ResumeSchema):
    """Extended version of ResumeSchema that allows extra fields for custom sections.

    This class inherits all the validation and structure from ResumeSchema
    but allows additional fields to be stored for custom sections.
    """

    model_config = ConfigDict(extra='allow')


@dataclass
class RenderingConfig:
    """Configuration for resume rendering."""

    format: str = 'pdf'  # pdf, html, latex, docx
    theme: str = 'default'
    custom_css: str | None = None
    custom_template: str | None = None
