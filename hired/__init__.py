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

# Job matching and scoring
from hired.matching import JobMatcher, MatchScore, quick_match

# ATS checking
from hired.ats_checker import ATSChecker, ATSReport, check_resume_ats

# Cover letter generation
from hired.cover_letter import mk_cover_letter, CoverLetterData, generate_cover_letter_content

# Application tracking
from hired.tracking import ApplicationTracker, Application

# Job utilities
from hired.job_utils import JobAnalyzer, job_to_text, extract_job_keywords, get_job_skills

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
    # Job matching
    'JobMatcher',
    'MatchScore',
    'quick_match',
    # ATS checking
    'ATSChecker',
    'ATSReport',
    'check_resume_ats',
    # Cover letters
    'mk_cover_letter',
    'CoverLetterData',
    'generate_cover_letter_content',
    # Application tracking
    'ApplicationTracker',
    'Application',
    # Job utilities
    'JobAnalyzer',
    'job_to_text',
    'extract_job_keywords',
    'get_job_skills',
]
