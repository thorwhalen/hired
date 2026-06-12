"""
Content generation logic and AI agent implementations.

Implement:
- DefaultAIAgent: Basic implementation using local LLM or API
- content source factories for common formats
- content extraction and filtering utilities
"""

import json
from typing import Any
from collections.abc import Mapping, Iterable
from hired.base import (
    ContentSource,
    AIAgent,
    ResumeSchemaExtended,
)
from hired.util import _load_json_file, load_yaml

DFLT_LLM_MODEL = 'gpt-4o-mini'


class FileContentSource:
    """Implements ContentSource for file-based data."""

    def __init__(self, path: str):
        self._path = path

    def read(self) -> Mapping[str, Any]:
        if self._path.endswith('.json'):
            return _load_json_file(self._path)
        elif self._path.endswith('.yaml') or self._path.endswith('.yml'):
            return load_yaml(self._path)
        else:
            raise ValueError(f'Unsupported file type: {self._path}')


class DictContentSource:
    """Implements ContentSource for dictionary data."""

    def __init__(self, data: Mapping[str, Any]):
        self._data = data

    def read(self) -> Mapping[str, Any]:
        return self._data


def _extract_relevant_experiences(
    candidate_data: Mapping[str, Any],
    job_requirements: Mapping[str, Any],
    *,
    max_items: int = 5,
) -> Iterable[dict]:
    # Stub: just return up to max_items from candidate_data['work']
    return candidate_data.get('work', [])[:max_items]


def _match_skills_to_job(
    candidate_skills: Iterable[str], job_keywords: Iterable[str]
) -> Iterable[str]:
    # Stub: return intersection
    return [s for s in candidate_skills if s in job_keywords]


class DefaultAIAgent:
    """Default AI agent implementation (mock)."""

    def __init__(self, *, model: str = 'default', api_key: str | None = None):
        self._model = model
        self._api_key = api_key

    def generate_content(
        self, candidate_info: Mapping[str, Any], job_info: Mapping[str, Any]
    ) -> ResumeSchemaExtended:
        # Convert candidate info to use the new models, allowing any extra fields
        return ResumeSchemaExtended(**candidate_info)


_LLM_SYSTEM_PROMPT = (
    "You are a resume-tailoring assistant. Given a candidate's full profile and "
    "a target job, produce a single one-page resume tailored to the job. "
    "Return ONLY a JSON object conforming to the JSON Resume schema "
    "(basics, work, education, skills, ...). Select and phrase the candidate's "
    "real experience to match the job; never invent facts."
)


def _mk_tailoring_prompt(
    candidate_info: Mapping[str, Any], job_info: Mapping[str, Any]
) -> str:
    return (
        "CANDIDATE PROFILE (JSON):\n"
        f"{json.dumps(dict(candidate_info), default=str)}\n\n"
        "TARGET JOB (JSON):\n"
        f"{json.dumps(dict(job_info), default=str)}\n\n"
        "Return the tailored resume as a JSON Resume object."
    )


class LLMResumeAgent:
    """AI agent that tailors a candidate's profile to a job via an LLM.

    Opt-in alternative to :class:`DefaultAIAgent` (which is a pass-through). It
    is **dependency-injected and lazy**: `openai` is imported only when an agent
    is used *without* an injected ``client``, so importing ``hired`` never
    requires `openai`, and no API key is read at construction time. Inject a
    ``client`` (anything exposing the OpenAI-style
    ``chat.completions.create``) to test without network or secrets.

    >>> class _FakeClient:  # doctest: +SKIP
    ...     class chat:
    ...         class completions:
    ...             @staticmethod
    ...             def create(**_):
    ...                 ...
    """

    def __init__(
        self,
        *,
        model: str = DFLT_LLM_MODEL,
        client: Any | None = None,
        api_key: str | None = None,
    ):
        self._model = model
        self._client = client
        self._api_key = api_key

    @property
    def client(self):
        if self._client is None:
            import openai  # lazy: only required when actually generating

            self._client = openai.OpenAI(api_key=self._api_key)
        return self._client

    def generate_content(
        self, candidate_info: Mapping[str, Any], job_info: Mapping[str, Any]
    ) -> ResumeSchemaExtended:
        response = self.client.chat.completions.create(
            model=self._model,
            messages=[
                {'role': 'system', 'content': _LLM_SYSTEM_PROMPT},
                {'role': 'user', 'content': _mk_tailoring_prompt(candidate_info, job_info)},
            ],
            response_format={'type': 'json_object'},
        )
        data = json.loads(response.choices[0].message.content)
        return ResumeSchemaExtended(**data)
