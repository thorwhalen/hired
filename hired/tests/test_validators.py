"""
Minimal unit tests for hired.validators
"""

from hired.validators import validate_resume_content


def test_validate_resume_content_accepts_minimal():
    # Accepts any dict for now (empty schema)
    assert validate_resume_content({'basics': {'name': 'A', 'email': 'a@b'}})
