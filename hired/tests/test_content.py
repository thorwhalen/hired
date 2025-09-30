"""
Minimal unit tests for hired.content
"""

from hired.content import FileContentSource, DictContentSource, DefaultAIAgent
from hired.resumejson_pydantic_models import Basics, WorkItem, EducationItem
from hired.base import ResumeSchemaExtended

# For backward compatibility
ResumeContent = ResumeSchemaExtended
import tempfile
import json


def test_dict_content_source():
    d = {'foo': 'bar'}
    src = DictContentSource(d)
    assert src.read() == d


def test_file_content_source_json():
    d = {'foo': 'bar'}
    import os

    with tempfile.NamedTemporaryFile('w+', suffix='.json', delete=False) as f:
        json.dump(d, f)
        f.close()
        src = FileContentSource(f.name)
        assert src.read() == d
    os.unlink(f.name)


def test_default_ai_agent():
    agent = DefaultAIAgent()
    candidate = {
        'basics': {'name': 'A', 'email': 'a@example.com'},
        'work': [],
        'education': [],
    }
    job = {'title': 'X'}
    content = agent.generate_content(candidate, job)
    assert content.basics.name == 'A'
    assert content.basics.email == 'a@example.com'
