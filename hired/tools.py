"""
High-level orchestration functions - the main API.

These are the primary user-facing functions that coordinate
the entire pipeline.
"""

from typing import Any, TYPE_CHECKING, Union
from collections.abc import Mapping
from pathlib import Path
from hired.base import (
    RenderingConfig,
    ContentSource,
    ResumeSchemaExtended,
)
from hired.content import FileContentSource, DictContentSource, DefaultAIAgent
from hired.util import (
    validate_resume_content_dict,
    ensure_resume_content_dict,
    normalize_and_validate_resume,
)
from hired.render import _get_renderer_for_format
from hired.config import ConfigStore

if TYPE_CHECKING:
    from hired.search.base import JobResult


def mk_content_for_resume(
    candidate_info_src: Union[ContentSource, str, dict],
    job_info_src: Union[ContentSource, str, dict, 'JobResult'],
    *,
    agent: Union[Any, None] = None,
    validate: bool = True,
    strict: bool = False,
) -> ResumeSchemaExtended:
    """
    Generate resume content from candidate and job information.

    Args:
        candidate_info_src: Candidate information as ContentSource, file path, or dict
        job_info_src: Job information as ContentSource, file path, dict, or JobResult
        agent: Optional AI agent for content generation
        validate: Whether to validate the generated content
        strict: Whether to use strict validation

    Returns:
        ResumeSchemaExtended object with generated content

    Examples:
        >>> # Using file paths
        >>> content = mk_content_for_resume("candidate.json", "job.txt")
        >>>
        >>> # Using JobResult from job search
        >>> from hired import JobSources, SearchCriteria
        >>> sources = JobSources()
        >>> jobs = sources.jobspy.search(SearchCriteria(query="python developer"))
        >>> content = mk_content_for_resume(candidate_dict, jobs[0])
    """

    def _to_source(src):
        # Check if it's a JobResult
        if hasattr(src, 'title') and hasattr(src, 'source'):
            # It's a JobResult, convert to text
            from hired.job_utils import job_to_text
            job_text = job_to_text(src)
            return DictContentSource({'job_description': job_text})
        elif isinstance(src, dict):
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
    content: Union[ResumeSchemaExtended, dict],
    rendering: Union[RenderingConfig, dict, None] = None,
    *,
    output_path: Union[str, None] = None,
    strict: bool = False,
) -> bytes:
    """
    Render resume content to final format.
    """
    # Normalize and validate in a single place. Accept dicts or pydantic models.
    if isinstance(content, dict):
        content = normalize_and_validate_resume(content, strict=strict)
    elif hasattr(content, 'model_dump'):
        # Convert to dict and re-normalize; this will validate and prune None
        content_dict = content.model_dump()
        content = normalize_and_validate_resume(content_dict, strict=strict)

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


def render_resume_with_template_and_css(
    content: Union[ResumeSchemaExtended, dict],
    template_path: Union[str, Path],
    css_path: Union[str, Path, None] = None,
    *,
    format='pdf',
    strict: bool = False,
) -> bytes:
    """Render a resume dict (or pydantic model) to PDF using a specific
    HTML template file and optional CSS file.

    Args:
        content: Resume content as a dict or ResumeSchemaExtended instance.
        template_path: Path to an HTML/Jinja template file to render from.
        css_path: Optional path to a CSS file; its contents will be passed to
            the renderer as `custom_css` so PDF rendering picks up the styles.
        format: Output format, 'pdf' or 'html'. Default is 'pdf'.
        strict: If True, enable stricter schema validation.

    Returns:
        PDF file bytes.
    """
    from pathlib import Path

    # Normalize input content (mk_resume will also normalize, but do it here
    # to provide clearer error messages earlier).
    content = ensure_resume_content_dict(content)
    if isinstance(content, dict):
        content = normalize_and_validate_resume(content, strict=strict)
    elif hasattr(content, 'model_dump'):
        content = normalize_and_validate_resume(content.model_dump(), strict=strict)

    tpl_path = Path(template_path)
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template file not found: {tpl_path}")

    css_text = None
    if css_path is not None:
        css_path = Path(css_path)
        if not css_path.exists():
            raise FileNotFoundError(f"CSS file not found: {css_path}")
        css_text = css_path.read_text(encoding='utf-8')

    rendering = RenderingConfig(
        format=format,
        theme='default',
        custom_template=str(tpl_path),
        custom_css=css_text,
    )

    return mk_resume(content, rendering, strict=strict)
