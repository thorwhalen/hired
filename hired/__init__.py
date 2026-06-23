"""
Public API for the hired package.
Import the main user-facing functions and classes.
"""

from hired.tools import mk_content_for_resume, mk_resume
from hired.config import load_config, get_default_config
from hired.base import RenderingConfig, ResumeSchemaExtended
from hired.resumejson_pydantic_models import ResumeSchema

# AI content agents. DefaultAIAgent is a pass-through; LLMResumeAgent does real
# LLM tailoring but imports `openai` lazily (only on use), so importing hired
# never requires it.
from hired.content import DefaultAIAgent, LLMResumeAgent

from hired.renderers.html import html_to_pdf

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
from hired.cover_letter import (
    mk_cover_letter,
    CoverLetterData,
    generate_cover_letter_content,
)

# Application tracking
from hired.tracking import ApplicationTracker, Application

# Job utilities
from hired.job_utils import (
    JobAnalyzer,
    job_to_text,
    extract_job_keywords,
    get_job_skills,
)

# For backward compatibility, also import the old name
ResumeContent = ResumeSchemaExtended

__all__ = [
    # Resume generation
    "mk_content_for_resume",
    "mk_resume",
    "load_config",
    "get_default_config",
    "ResumeContent",  # Backward compatibility alias
    "ResumeSchema",
    "ResumeSchemaExtended",
    "RenderingConfig",
    # Job search
    "JobSources",
    "SearchCriteria",
    "JobResult",
    "JobSearchSource",
    "JobType",
    # Job matching
    "JobMatcher",
    "MatchScore",
    "quick_match",
    # ATS checking
    "ATSChecker",
    "ATSReport",
    "check_resume_ats",
    # Cover letters
    "mk_cover_letter",
    "CoverLetterData",
    "generate_cover_letter_content",
    # Application tracking
    "ApplicationTracker",
    "Application",
    # Job utilities
    "JobAnalyzer",
    "job_to_text",
    "extract_job_keywords",
    "get_job_skills",
    # AI content agents
    "DefaultAIAgent",
    "LLMResumeAgent",
    # Conversational resume agent (lazily loaded — see __getattr__)
    "ResumeSession",
    "ResumeExpertAgent",
    "LLMConfig",
    # Candidate knowledge base (lazily loaded — see __getattr__)
    "CandidateKnowledgeBase",
    "JDWorkspace",
    # JD alignment analysis (lazily loaded — see __getattr__)
    "AlignmentReport",
    "Requirement",
    "RequirementRecord",
    "classify",
    "render_report_markdown",
]

# The conversational agent lives in the large `hired.resume_agent` module. Expose
# its surface lazily (PEP 562) so a plain `import hired` stays light and pulls it
# in only when actually used.
_LAZY_FROM_RESUME_AGENT = {"ResumeSession", "ResumeExpertAgent", "LLMConfig"}

# The candidate-knowledge and alignment subsystems are also exposed lazily: a
# plain `import hired` does not need to pull in their schemas/stores until used.
# (Their full surfaces live in `hired.candidate` and `hired.alignment`.)
_LAZY_FROM_CANDIDATE = {"CandidateKnowledgeBase", "JDWorkspace"}
_LAZY_FROM_ALIGNMENT = {
    "AlignmentReport",
    "Requirement",
    "RequirementRecord",
    "classify",
    "render_report_markdown",
}


def __getattr__(name):
    import importlib

    if name in _LAZY_FROM_RESUME_AGENT:
        return getattr(importlib.import_module("hired.resume_agent"), name)
    if name in _LAZY_FROM_CANDIDATE:
        return getattr(importlib.import_module("hired.candidate"), name)
    if name in _LAZY_FROM_ALIGNMENT:
        return getattr(importlib.import_module("hired.alignment"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
