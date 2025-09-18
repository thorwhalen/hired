"""
Minimal unit tests for hired.render
"""

from hired.render import ThemeRegistry, HTMLRenderer
from hired.base import (
    ResumeContent,
    ResumeBasics,
    ResumeWork,
    ResumeEducation,
    RenderingConfig,
)


def test_theme_registry():
    reg = ThemeRegistry()
    assert 'default' in reg
    assert isinstance(reg['default'], dict)


def test_html_renderer_html():
    basics = ResumeBasics(name='A', email='a@b')
    content = ResumeContent(basics=basics, work=[], education=[])
    config = RenderingConfig(format='html')
    renderer = HTMLRenderer()
    html = renderer.render(content, config)
    assert b'<html' in html


def test_html_renderer_pdf():
    basics = ResumeBasics(name='A', email='a@b')
    content = ResumeContent(basics=basics, work=[], education=[])
    config = RenderingConfig(format='pdf')
    renderer = HTMLRenderer()
    pdf = renderer.render(content, config)
    assert pdf.startswith(b'%PDF')
