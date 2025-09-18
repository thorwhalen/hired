"""
Minimal unit tests for hired.base
"""

from hired.base import (
    ResumeBasics,
    ResumeWork,
    ResumeEducation,
    ResumeContent,
    RenderingConfig,
)


def test_resume_basics():
    basics = ResumeBasics(name='Alice', email='alice@example.com')
    assert basics.name == 'Alice'
    assert basics.email == 'alice@example.com'


def test_resume_content():
    basics = ResumeBasics(name='Bob', email='bob@example.com')
    work = [ResumeWork(company='X', position='Y')]
    education = [ResumeEducation(institution='U', area='CS')]
    content = ResumeContent(basics=basics, work=work, education=education)
    assert content.basics.name == 'Bob'
    assert content.work[0].company == 'X'
    assert content.education[0].institution == 'U'


def test_rendering_config_defaults():
    config = RenderingConfig()
    assert config.format == 'pdf'
    assert config.theme == 'default'
