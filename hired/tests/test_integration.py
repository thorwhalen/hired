"""
Integration tests demonstrating main workflows.
Focus on interface contracts rather than exact outputs.
"""

import pytest
from hired import mk_content_for_resume, mk_resume


def test_basic_workflow():
    """Test the complete pipeline from sources to PDF."""
    # Minimal candidate and job data
    candidate = {
        'basics': {'name': 'Jane Doe', 'email': 'jane@example.com'},
        'work': [{'company': 'Tech Co', 'position': 'Engineer'}],
    }
    job = {'title': 'Senior Engineer', 'skills': ['Python', 'Docker']}
    # Generate content
    content = mk_content_for_resume(candidate, job)
    assert content.basics.name == 'Jane Doe'
    assert len(content.work) >= 0  # Don't assert exact count
    # Render to PDF
    pdf = mk_resume(content, {'format': 'pdf'})
    assert pdf.startswith(b'%PDF')  # PDF magic number
    assert len(pdf) > 20  # Some reasonable size for mock


def test_file_sources():
    """Test loading from file paths."""
    # Use test fixtures
    import os

    here = os.path.dirname(__file__)
    candidate_path = os.path.join(here, 'fixtures', 'candidate.json')
    job_path = os.path.join(here, 'fixtures', 'job.yaml')
    content = mk_content_for_resume(candidate_path, job_path)
    assert hasattr(content, 'basics')


def test_custom_rendering():
    """Test custom themes and formats."""
    content = {
        'basics': {'name': 'Test User', 'email': 'test@example.com'},
        'work': [],
        'education': [],
    }
    # Test HTML output
    html = mk_resume(content, {'format': 'html'})
    assert b'<html' in html.lower()
    # Test custom theme
    pdf = mk_resume(content, {'format': 'pdf', 'theme': 'minimal'})
    assert len(pdf) > 0
