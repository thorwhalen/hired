"""Test that HTMLRenderer honours a custom template file passed via RenderingConfig.custom_template."""

import tempfile
from hired.tools import mk_resume
from hired.base import RenderingConfig


def test_custom_template_file(tmp_path):
    # Prepare a minimal resume dict
    resume = {
        'basics': {'name': 'Custom Template User', 'email': 'ct@example.com'},
        'work': [],
        'education': [],
    }

    # Create a small Jinja2 template file that uses basics.name
    tpl = tmp_path / 'mytpl.html'
    tpl.write_text('<html><body><h1 id="name">{{ basics.name }}</h1></body></html>')

    cfg = RenderingConfig(format='html', custom_template=str(tpl))
    out = mk_resume(resume, cfg)
    assert b'Custom Template User' in out
    assert b'<h1' in out
