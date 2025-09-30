import json
from pathlib import Path

from hired.renderers.html import HTMLRenderer, ThemeRegistry
from hired.util import resume_json_example


def _load_resume():
    return json.loads(resume_json_example.read_text())


def test_render_packaged_themes_to_html(tmp_path):
    content = _load_resume()
    # Use the registry to discover themes
    registry = ThemeRegistry()
    renderer = HTMLRenderer(theme_registry=registry)

    name = content.get('basics', {}).get('name', 'Resume')

    # Render each theme that we just added if present in registry
    for candidate in ['startbootstrap', 'elegant', 'awesomecv-lite']:
        if candidate not in registry:
            # registry may register only available ones
            continue
        cfg = type(
            'C',
            (),
            {
                'format': 'html',
                'theme': candidate,
                'custom_template': None,
                'custom_css': None,
            },
        )()
        html_bytes = renderer.render(content, cfg)
        html = html_bytes.decode('utf-8')
        assert name in html
