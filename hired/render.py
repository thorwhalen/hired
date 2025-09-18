"""
Rendering pipeline and theme management.

Implement:
- HTMLRenderer: Jinja2 + WeasyPrint for PDF
- LaTeXRenderer: LaTeX-based rendering
- Theme management system
"""

from typing import Mapping, Any
from collections.abc import Mapping as ABCMapping
from hired.base import Renderer, ResumeContent, RenderingConfig


# Minimal theme registry
class ThemeRegistry(ABCMapping):
    """Registry for available themes, implemented as a Mapping."""

    def __init__(self):
        self._themes = {
            'default': {'template': '<html>{{ content }}</html>', 'css': ''},
            'minimal': {'template': '<html>{{ content }}</html>', 'css': ''},
        }

    def __getitem__(self, theme_name: str) -> dict:
        return self._themes[theme_name]

    def __iter__(self):
        return iter(self._themes)

    def __len__(self) -> int:
        return len(self._themes)


class HTMLRenderer:
    """Renders resume to HTML/PDF using Jinja2 and WeasyPrint (mocked)."""

    def __init__(self, *, theme_registry: ThemeRegistry | None = None):
        self._themes = theme_registry or ThemeRegistry()

    def render(self, content: ResumeContent, config: RenderingConfig) -> bytes:
        theme = self._themes[config.theme]
        html = self._render_to_html(content, theme)
        if config.format == 'pdf':
            return self._html_to_pdf(html, theme['css'])
        else:
            return html.encode('utf-8')

    def _render_to_html(self, content: ResumeContent, theme: dict) -> str:
        # Minimal: just dump basics as HTML
        basics = content.basics.model_dump()
        html = f"<html><body><h1>{basics.get('name','')}</h1><p>{basics.get('email','')}</p></body></html>"
        return html

    def _html_to_pdf(self, html: str, css: str) -> bytes:
        # Mock: just return PDF magic number and HTML
        return b'%PDF' + html.encode('utf-8')


def _get_renderer_for_format(format: str) -> Renderer:
    if format == 'pdf' or format == 'html':
        return HTMLRenderer()
    raise NotImplementedError(f'Format {format} not supported')
