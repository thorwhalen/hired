"""CI-safe tests for the AI agent seam and HTML->PDF rendering.

All tests run with only core dependencies and no secrets/network: the LLM is a
mock client and the PDF path is exercised via the no-WeasyPrint fallback.
"""

import json

import hired
from hired import mk_content_for_resume, DefaultAIAgent, LLMResumeAgent
from hired.renderers import html as html_mod


MINIMAL_CANDIDATE = {"basics": {"name": "John Doe", "email": "john@example.com"}}
JOB = {"job_description": "Senior Python Developer at TechCorp"}


def test_mk_content_uses_default_agent():
    content = mk_content_for_resume(MINIMAL_CANDIDATE, JOB)
    assert content.basics.name == "John Doe"


def test_mk_content_dependency_injection_seam():
    """A custom agent is used verbatim (the DI seam)."""

    class RecordingAgent:
        def __init__(self):
            self.calls = []

        def generate_content(self, candidate, job):
            self.calls.append((candidate, job))
            return hired.ResumeSchemaExtended(**candidate)

    agent = RecordingAgent()
    mk_content_for_resume(MINIMAL_CANDIDATE, JOB, agent=agent)
    assert len(agent.calls) == 1


def test_llm_resume_agent_with_injected_client_no_network():
    """LLMResumeAgent works with an injected fake client — no openai, no network."""

    tailored = {"basics": {"name": "John Doe", "email": "john@example.com",
                           "label": "Senior Python Developer"}}

    class _Msg:
        content = json.dumps(tailored)

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    assert kwargs["response_format"] == {"type": "json_object"}
                    return _Resp()

    agent = LLMResumeAgent(client=FakeClient())
    content = agent.generate_content(MINIMAL_CANDIDATE, JOB)
    assert content.basics.label == "Senior Python Developer"


def test_html_to_pdf_fallback_without_weasyprint(monkeypatch):
    """The minimal-PDF fallback produces valid PDF bytes when WeasyPrint is absent."""
    monkeypatch.setattr(html_mod, "weasyprint", None)
    pdf = html_mod.html_to_pdf("<html><body>Hello</body></html>", None)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")


def test_default_and_llm_agents_share_protocol():
    # Both implement generate_content(candidate, job) -> ResumeSchemaExtended.
    assert hasattr(DefaultAIAgent(), "generate_content")
    assert hasattr(LLMResumeAgent(), "generate_content")
