"""
Public API for the hired package.
Import the main user-facing functions and classes.
"""

from hired.tools import mk_content_for_resume, mk_resume
from hired.config import load_config, get_default_config
from hired.base import ResumeContent, RenderingConfig

__all__ = [
    'mk_content_for_resume',
    'mk_resume',
    'load_config',
    'get_default_config',
    'ResumeContent',
    'RenderingConfig',
]
