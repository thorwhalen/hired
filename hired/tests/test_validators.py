"""
Tests for validation utilities.
"""

from hired.util import validate_resume_content_dict


def test_validate_resume_content_accepts_minimal():
    """Test that validation accepts a minimal valid resume."""
    minimal_resume = {
        'basics': {
            'name': 'John Doe',
            'email': 'john@example.com',
        },
    }
    # Should not raise an exception
    result = validate_resume_content_dict(minimal_resume)
    assert result == minimal_resume
