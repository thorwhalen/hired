"""
Minimal unit tests for hired.config
"""

from hired.config import ConfigStore, get_default_config, load_config
import tempfile
import json
import os


def test_config_store():
    c = ConfigStore({'a': 1})
    assert c['a'] == 1
    c['b'] = 2
    assert c['b'] == 2
    del c['a']
    assert 'a' not in c


def test_get_default_config():
    c = get_default_config()
    assert c['format'] == 'pdf'
    assert c['theme'] == 'default'


def test_load_config():
    d = {'foo': 'bar'}
    with tempfile.NamedTemporaryFile('w+', delete=False) as f:
        json.dump(d, f)
        f.close()
        c = load_config(f.name)
        assert c['foo'] == 'bar'
    os.unlink(f.name)
