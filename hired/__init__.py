"""
Public API for the hired package.
Import the main user-facing functions and classes.
"""

from hired.tools import mk_content_for_resume, mk_resume
from hired.config import load_config, get_default_config
from hired.base import RenderingConfig, ResumeSchemaExtended
from hired.resumejson_pydantic_models import ResumeSchema

# Job search functionality
from hired.search import (
    JobSources,
    SearchCriteria,
    JobResult,
    JobSearchSource,
    JobType,
)

# For backward compatibility, also import the old name
ResumeContent = ResumeSchemaExtended

__all__ = [
    # Resume generation
    'mk_content_for_resume',
    'mk_resume',
    'load_config',
    'get_default_config',
    'ResumeContent',  # Backward compatibility alias
    'ResumeSchema',
    'ResumeSchemaExtended',
    'RenderingConfig',
    # Job search
    'JobSources',
    'SearchCriteria',
    'JobResult',
    'JobSearchSource',
    'JobType',
]
