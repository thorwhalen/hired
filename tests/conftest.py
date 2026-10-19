"""Shared test fixtures: isolate every test from the caller's ``$HIRED_USER``."""

import pytest


@pytest.fixture(autouse=True)
def _no_ambient_hired_user(monkeypatch):
    # resolve_user() honours $HIRED_USER, so a developer's own setting would
    # otherwise redirect the default-candidate tests to another tenant.
    monkeypatch.delenv("HIRED_USER", raising=False)
