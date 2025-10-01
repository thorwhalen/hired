"""
High-level orchestration functions - the main API.

These are the primary user-facing functions that coordinate
the entire pipeline.
"""

from typing import Any, Mapping
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


def mk_content_for_resume(
    candidate_info_src: ContentSource | str | dict,
    job_info_src: ContentSource | str | dict,
    *,
    agent: Any | None = None,
    validate: bool = True,
    strict: bool = False,
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
    content: ResumeSchemaExtended | dict,
    template_path: str | Path,
    css_path: str | Path | None = None,
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
