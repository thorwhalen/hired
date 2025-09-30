import json
import importlib

import pytest

from hired.renderers.html import HTMLRenderer, ThemeRegistry
from hired.util import resume_json_example


def _load_resume():
    return json.loads(resume_json_example.read_text())


@pytest.mark.skipif(
    importlib.util.find_spec('weasyprint') is None, reason='WeasyPrint not installed'
)
def test_pdf_includes_theme_css(monkeypatch):
    """Ensure that when rendering to PDF, the theme's CSS is passed to WeasyPrint."""
    content = _load_resume()
    registry = ThemeRegistry()
    # prefer startbootstrap which we packaged and which includes styles.css
    theme_name = 'startbootstrap'
    if theme_name not in registry:
        pytest.skip('startbootstrap theme not available in registry')

    renderer = HTMLRenderer(theme_registry=registry)

    # Capture the CSS passed into WeasyPrint
    captured = {'css_strings': None}

    # Create a fake weasyprint module API with HTML(...).write_pdf(stylesheets=[CSS(string=...)] )
    class FakeCSS:
        def __init__(self, string=None):
            self.string = string

    class FakeHTML:
        def __init__(self, string=None):
            self.string = string

        def write_pdf(self, stylesheets=None):
            # stylesheets is a list of weasyprint.CSS objects or None
            if stylesheets:
                # join captured css strings
                captured['css_strings'] = '\n'.join(
                    getattr(s, 'string', '') for s in stylesheets
                )
            else:
                captured['css_strings'] = ''
            return b'%PDF-FAKE'

    fake_weasy = type('W', (), {'HTML': FakeHTML, 'CSS': FakeCSS})

    # Monkeypatch the weasyprint reference inside the renderer module
    import hired.renderers.html as html_mod

    monkeypatch.setattr(html_mod, 'weasyprint', fake_weasy)

    # Build config-like object
    cfg = type(
        'C',
        (),
        {
            'format': 'pdf',
            'theme': theme_name,
            'custom_template': None,
            'custom_css': None,
        },
    )()

    pdf_bytes = renderer.render(content, cfg)
    assert pdf_bytes.startswith(b'%PDF')
    # Ensure we captured CSS from theme
    css_text = captured.get('css_strings', '') or ''
    assert 'font-family: Arial' in css_text
