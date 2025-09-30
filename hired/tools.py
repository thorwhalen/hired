"""
High-level orchestration functions - the main API.

These are the primary user-facing functions that coordinate
the entire pipeline.
"""

from typing import Any, Mapping
from hired.base import (
    RenderingConfig,
    ContentSource,
    ResumeSchemaExtended,
)
from hired.content import FileContentSource, DictContentSource, DefaultAIAgent
from hired.util import validate_resume_content_dict, ensure_resume_content_dict
from hired.render import _get_renderer_for_format
from hired.config import ConfigStore


def mk_content_for_resume(
    candidate_info_src: ContentSource | str | dict,
    job_info_src: ContentSource | str | dict,
    *,
    agent: Any | None = None,
    validate: bool = True,
    strict: bool = False
) -> ResumeSchemaExtended:
    """
    Generate resume content from candidate and job information.
    """

    def _to_source(src):
        if isinstance(src, dict):
            return DictContentSource(src)
        elif isinstance(src, str):
            return FileContentSource(src)
        return src

    candidate = _to_source(candidate_info_src).read()
    job = _to_source(job_info_src).read()
    agent = agent or DefaultAIAgent()
    content = agent.generate_content(candidate, job)
    if validate:
        content_dict = (
            content.model_dump() if hasattr(content, 'model_dump') else content
        )
        assert validate_resume_content_dict(content_dict), "Validation failed"
    return content


def mk_resume(
    content: ResumeSchemaExtended | dict,
    rendering: RenderingConfig | dict | None = None,
    *,
    output_path: str | None = None,
    strict: bool = False
) -> bytes:
    """
    Render resume content to final format.
    """
    if isinstance(content, dict):
        # Use ResumeSchemaExtended which allows extra fields
        validate_resume_content_dict(content)
        content = ResumeSchemaExtended(**content)
    elif hasattr(content, 'model_dump'):
        # Already a pydantic model, validate the dict form
        content_dict = content.model_dump()
        validate_resume_content_dict(content_dict)

    if rendering is None:
        rendering = RenderingConfig()
    elif isinstance(rendering, dict):
        rendering = RenderingConfig(**rendering)
    renderer = _get_renderer_for_format(rendering.format)
    result = renderer.render(content, rendering)
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(result)
    return result
