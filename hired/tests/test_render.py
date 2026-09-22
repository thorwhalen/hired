"""
Minimal unit tests for hired.render
"""

from hired.renderers.html import ThemeRegistry, HTMLRenderer
from hired.base import RenderingConfig, ResumeSchemaExtended
from hired.resumejson_pydantic_models import Basics, WorkItem, Skill, Project

# For backward compatibility
ResumeContent = ResumeSchemaExtended


def test_theme_registry():
    reg = ThemeRegistry()
    assert 'default' in reg
    assert isinstance(reg['default'], dict)


def test_html_renderer_html():
    basics = Basics(name='A', email='a@example.com')
    content = ResumeSchemaExtended(basics=basics)
    config = RenderingConfig(format='html')
    renderer = HTMLRenderer()
    html = renderer.render(content, config)
    assert b'<html' in html


def test_html_renderer_pdf():
    basics = Basics(name='A', email='a@example.com')
    content = ResumeSchemaExtended(basics=basics)
    config = RenderingConfig(format='pdf')
    renderer = HTMLRenderer()
    pdf = renderer.render(content, config)
    assert pdf.startswith(b'%PDF')


def test_html_renderer_full_sections():
    """Regression test for #14: skills/projects/publications/languages and
    basics.summary/label/profiles and work[].summary/highlights must render,
    and work items must key off `name` (JSON Resume schema), not `company`.
    """
    basics = Basics(
        name='Jane Doe',
        email='jane@example.com',
        label='Software Engineer',
        summary='A concise professional summary.',
    )
    content = ResumeSchemaExtended(
        basics=basics,
        work=[
            WorkItem(
                name='Acme Corp',
                position='Engineer',
                summary='Led the widget team.',
                highlights=['Shipped widget v2'],
            )
        ],
        skills=[Skill(name='Python', keywords=['pandas', 'numpy'])],
        projects=[Project(name='Cool Project', description='A cool project.')],
    )
    config = RenderingConfig(format='html', theme='default')
    renderer = HTMLRenderer()
    html = renderer.render(content, config).decode('utf-8')

    # basics extras
    assert 'Software Engineer' in html
    assert 'A concise professional summary.' in html
    # work: name (not the stale `company` field), summary, highlights
    assert 'Acme Corp' in html
    assert 'Led the widget team.' in html
    assert 'Shipped widget v2' in html
    # previously-dropped core sections
    assert 'Python' in html
    assert 'pandas' in html
    assert 'Cool Project' in html
    assert 'A cool project.' in html
