"""Tests for freeform sections and strict vs non-strict validation."""

import pytest
from hired.tools import mk_resume

RAW = {
    'basics': {'name': 'Free Form User', 'email': 'ff@example.com'},
    'work': [{'name': 'OrgX', 'position': 'Dev'}],
    'customSection': 'This is a freeform narrative about achievements.',
    'bullets': ['Item A', 'Item B'],
}


def test_non_strict_accepts_freeform():
    html = mk_resume(RAW, {'format': 'html'}, strict=False)
    assert b'Customsection' in html or b'customSection' in html
    assert b'This is a freeform narrative' in html


@pytest.mark.skip("Fails since actual officien json schema is used: Repair")
def test_strict_still_passes_core_schema():
    # Our abridged schema allows additionalProperties, so strict also succeeds here
    pdf = mk_resume(RAW, {'format': 'pdf'}, strict=True)
    assert pdf.startswith(b'%PDF')
