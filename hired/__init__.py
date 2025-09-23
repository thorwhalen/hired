"""
Public API for the hired package.
Import the main user-facing functions and classes.
"""

from hired.tools import mk_content_for_resume, mk_resume
from hired.config import load_config, get_default_config
from hired.base import ResumeContent, RenderingConfig

try:
    from hired.resumejson_pydantic_models import ResumeSchema
except Exception:
    print(
        "Warning: Could not import ResumeSchema from hired.resumejson_pydantic_models."
        f" This often means the last code generation didn't work. "
        "Try running hired.util.refresh_resume_schema() to regenerate it."
    )
    ResumeSchema = None  # type: ignore

__all__ = [
    'mk_content_for_resume',
    'mk_resume',
    'load_config',
    'get_default_config',
    'ResumeContent',
    'RenderingConfig',
]
