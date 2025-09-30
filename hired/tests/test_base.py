"""
Minimal unit tests for hired.base
"""

from hired.base import (
    RenderingConfig,
    ResumeSchemaExtended,
)
from hired.resumejson_pydantic_models import Basics

# For backward compatibility
ResumeContent = ResumeSchemaExtended


def test_resume_basics():
    basics = Basics(name='John Doe', email='john@example.com')
    assert basics.name == 'John Doe'
    assert basics.email == 'john@example.com'


def test_resume_content():
    basics = Basics(name='John Doe', email='john@example.com')
    content = ResumeSchemaExtended(basics=basics)
    assert content.basics.name == 'John Doe'


def test_rendering_config_defaults():
    config = RenderingConfig()
    assert config.format == 'pdf'
    assert config.theme == 'default'
