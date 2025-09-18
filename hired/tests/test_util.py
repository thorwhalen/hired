"""
Minimal unit tests for hired.util
"""

import tempfile
import os
from hired.util import _merge_dicts, _load_json_file


def test_merge_dicts():
    a = {'x': 1, 'y': 2}
    b = {'y': 3, 'z': 4}
    merged = _merge_dicts(a, b)
    assert merged['x'] == 1
    assert merged['y'] == 3
    assert merged['z'] == 4


def test_load_json_file():
    d = {'foo': 'bar'}
    with tempfile.NamedTemporaryFile('w+', delete=False) as f:
        import json

        json.dump(d, f)
        f.close()
        loaded = _load_json_file(f.name)
    os.unlink(f.name)
    assert loaded == d
