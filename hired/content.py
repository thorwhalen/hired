"""
Content generation logic and AI agent implementations.

Implement:
- DefaultAIAgent: Basic implementation using local LLM or API
- content source factories for common formats
- content extraction and filtering utilities
"""

from typing import Any
from collections.abc import Mapping, Iterable
from hired.base import (
    ContentSource,
    AIAgent,
    ResumeSchemaExtended,
)
from hired.util import _load_json_file, load_yaml


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
