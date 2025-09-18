"""
Core data models and protocols for the hired package.

Define:
- ResumeContent: Pydantic model matching JSON Resume schema
- RenderingConfig: Configuration for rendering pipeline
- ContentSource: Protocol for data sources (candidate/job info)
- AIAgent: Protocol for content generation agents
- Renderer: Protocol for resume renderers
"""

from typing import Protocol, Any, Mapping, List
from dataclasses import dataclass
from pydantic import BaseModel


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


# Pydantic models for JSON Resume schema sections
class ResumeBasics(BaseModel):
    name: str
    email: str
    # ... add more fields as needed


class ResumeWork(BaseModel):
    company: str
    position: str
    # ... add more fields as needed


class ResumeEducation(BaseModel):
    institution: str = ''
    area: str = ''
    # ... add more fields as needed


class ResumeContent(BaseModel):
    """Complete resume content following JSON Resume schema."""

    basics: ResumeBasics
    work: List[ResumeWork] = []
    education: List[ResumeEducation] = []
    # ... other fields as needed


@dataclass
class RenderingConfig:
    """Configuration for resume rendering."""

    format: str = 'pdf'  # pdf, html, latex, docx
    theme: str = 'default'
    custom_css: str | None = None
    custom_template: str | None = None
