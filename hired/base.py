"""
Core data models and protocols for the hired package.

Define:
- ResumeContent: Pydantic model matching JSON Resume schema
- RenderingConfig: Configuration for rendering pipeline
- ContentSource: Protocol for data sources (candidate/job info)
- AIAgent: Protocol for content generation agents
- Renderer: Protocol for resume renderers
"""

from typing import Protocol, Any, Mapping, List, Dict, Type, Optional
from dataclasses import dataclass
from pydantic import BaseModel, field_validator, ConfigDict


class ContentSource(Protocol):
    """Protocol for sources that provide candidate or job information."""

    def read(self) -> Mapping[str, Any]: ...


class AIAgent(Protocol):
    """Protocol for AI agents that generate resume content."""

    def generate_content(
        self, candidate_info: Mapping[str, Any], job_info: Mapping[str, Any]
    ) -> 'ResumeContent': ...


class Renderer(Protocol):
    """Protocol for resume renderers."""

    def render(self, content: 'ResumeContent', config: 'RenderingConfig') -> bytes: ...


class RendererRegistry:
    """Registry for managing multiple renderer implementations."""

    def __init__(self):
        self._renderers: Dict[str, Type[Renderer]] = {}
        self._instances: Dict[str, Renderer] = {}

    def register(self, format_name: str, renderer_class: Type[Renderer]) -> None:
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

    def list_formats(self) -> List[str]:
        """List all registered format names."""
        return list(self._renderers.keys())

    def is_registered(self, format_name: str) -> bool:
        """Check if a format is registered."""
        return format_name in self._renderers


# Global renderer registry instance
_renderer_registry = RendererRegistry()


def register_renderer(format_name: str):
    """Decorator for registering renderer classes."""

    def decorator(renderer_class: Type[Renderer]):
        _renderer_registry.register(format_name, renderer_class)
        return renderer_class

    return decorator


def get_renderer_registry() -> RendererRegistry:
    """Get the global renderer registry."""
    return _renderer_registry


# Pydantic models for JSON Resume schema sections
class ResumeBasics(BaseModel):
    name: str
    email: str
    phone: str | None = None
    url: str | None = None
    summary: str | None = None
    location: dict[str, Any] | None = None
    profiles: list[dict[str, Any]] | None = None
    label: str | None = None
    image: str | None = None


class ResumeWork(BaseModel):
    # JSON Resume allows either 'name' (organization name) or 'company' in some ecosystems
    company: str | None = None
    name: str | None = None
    position: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None
    startDate: str | None = None
    endDate: str | None = None

    @field_validator('company', mode='before')
    @classmethod
    def ensure_company(cls, v, info):  # type: ignore[override]
        # If company missing but 'name' present in raw data, pydantic will populate 'name'; we mirror it into company
        if v is None:
            raw = info.data  # remaining raw values
            name_val = raw.get('name') if isinstance(raw, dict) else None
            if name_val:
                return name_val
        return v


class ResumeEducation(BaseModel):
    institution: str = ''
    area: str = ''
    studyType: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    gpa: str | None = None
    courses: list[str] | None = None
    url: str | None = None


class ResumeContent(BaseModel):
    """Complete resume content following JSON Resume schema with support for extra/freeform sections.

    Unknown top-level keys (non core) can be captured in extra_sections mapping when desired.
    """

    basics: ResumeBasics
    work: List[ResumeWork] = []
    education: List[ResumeEducation] = []
    extra_sections: dict[str, Any] = {}

    model_config = ConfigDict(extra='allow')


@dataclass
class RenderingConfig:
    """Configuration for resume rendering."""

    format: str = 'pdf'  # pdf, html, latex, docx
    theme: str = 'default'
    custom_css: str | None = None
    custom_template: str | None = None
