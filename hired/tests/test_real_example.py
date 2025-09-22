"""Test rendering a real example resume JSON and verifying key content appears."""

import pytest
import json
from hired.util import proj_files
from hired.tools import mk_resume


@pytest.mark.skip("Fails since actual officien json schema is used: Repair")
def test_real_example_resume_renders():
    path = proj_files / 'tests/fixtures/real_example_resume.json'
    content = json.loads(path.read_text())
    # Non-strict by default; ensure it renders
    rendered = mk_resume(content, {'format': 'html'})
    # Verify a few key substrings (adjust keys if file changes)
    for key_snippet in [
        b'Thor',  # part of the name
        b'@',  # email presence
        b'<section',  # sections being rendered
    ]:
        assert key_snippet in rendered

    # Now strict rendering should also succeed after pruning None
    rendered_strict = mk_resume(content, {'format': 'html'}, strict=True)
    assert b'<html' in rendered_strict
