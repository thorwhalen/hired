"""Pin the import-safety contract.

`import hired` and the core resume/search/workflow surface must work with only
the core dependencies installed and **no secrets in the environment**. The heavy
optional integrations (openai, weasyprint, rendercv, jobspy, langchain) must be
imported lazily / on use only, and the conversational agent surface is exposed
lazily so a plain import stays light.
"""

import importlib.util
import sys

import pytest


def test_import_hired_does_not_require_openai():
    import hired  # noqa: F401

    # Importing hired (and constructing the LLM agent) must not import openai.
    hired.LLMResumeAgent()
    if importlib.util.find_spec("openai") is None:
        assert "openai" not in sys.modules


def test_import_hired_with_no_secrets(monkeypatch):
    for var in ("OPENAI_API_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY", "USAJOBS_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    # Re-import cleanly with the env stripped.
    sys.modules.pop("hired", None)
    sys.modules.pop("hired.search", None)
    import hired

    assert callable(hired.mk_content_for_resume)
    assert callable(hired.mk_resume)
    assert hired.JobSources is not None


def test_lazy_agent_surface_resolves():
    import hired

    # These live in the large hired.resume_agent module, exposed lazily.
    assert hired.ResumeSession.__name__ == "ResumeSession"
    assert hired.ResumeExpertAgent.__name__ == "ResumeExpertAgent"
    assert hired.LLMConfig.__name__ == "LLMConfig"


def test_lazy_candidate_alignment_surface_resolves():
    import hired

    # The candidate-knowledge + alignment subsystems are exposed lazily and need
    # only core deps + dol (no openai, no secrets).
    assert hired.CandidateKnowledgeBase.__name__ == "CandidateKnowledgeBase"
    assert hired.AlignmentReport.__name__ == "AlignmentReport"
    assert hired.Requirement.__name__ == "Requirement"
    assert callable(hired.classify)
    assert callable(hired.render_report_markdown)


def test_candidate_alignment_use_does_not_require_openai(monkeypatch, tmp_path):
    monkeypatch.setenv("HIRED_DATA_DIR", str(tmp_path))
    import hired

    kb = hired.CandidateKnowledgeBase()
    from hired.candidate import Fact

    kb.add_fact(Fact(statement="knows Python"))
    assert kb.regenerate_synopsis()
    if importlib.util.find_spec("openai") is None:
        assert "openai" not in sys.modules


def test_unknown_attribute_raises_attribute_error():
    import hired

    with pytest.raises(AttributeError):
        _ = hired.no_such_thing
