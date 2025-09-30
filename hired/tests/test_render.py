"""
Minimal unit tests for hired.render
"""

from hired.renderers.html import ThemeRegistry, HTMLRenderer
from hired.base import RenderingConfig, ResumeSchemaExtended
from hired.resumejson_pydantic_models import Basics

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
