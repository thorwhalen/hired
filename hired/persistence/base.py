"""Canonical data root, store factories, and the candidate store-of-stores.

The canonical root is resolved by :func:`app_data_dir`, honoring (in order):

1. the ``HIRED_DATA_DIR`` environment variable (used by tests and power users),
2. ``$XDG_DATA_HOME/hired`` (the XDG Base Directory spec),
3. ``~/.local/share/hired`` (the XDG default).

Leaf stores are ``MutableMapping`` views: :func:`json_store` for structured
records, :func:`bytes_store` for raw uploads, :func:`text_store` for
human-readable projections. :class:`CandidateMall` groups the per-candidate
stores and resolves the default candidate (``"me"``).
"""

from __future__ import annotations

import os
import shutil
from collections.abc import MutableMapping
from pathlib import Path

from dol import Files, JsonFiles, TextFiles, mk_dirs_if_missing

DFLT_USER = 'me'
_ENV_VAR = 'HIRED_DATA_DIR'


def migrate_legacy(legacy_path, target_path) -> bool:
    """One-time copy of a legacy store into the canonical root.

    If ``target_path`` does not yet exist but ``legacy_path`` does, copy it
    (file or directory) so historical data is preserved when storage roots are
    unified. No-op otherwise. Returns True iff a copy happened.
    """
    legacy, target = Path(legacy_path), Path(target_path)
    if target.exists() or not legacy.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if legacy.is_dir():
        shutil.copytree(legacy, target)
    else:
        shutil.copy2(legacy, target)
    return True


def app_data_dir(*subpaths: str, make: bool = True) -> str:
    """Return the canonical hired data directory, joined with ``subpaths``.

    The directory is created when ``make`` is true (the default).

    >>> import os, tempfile
    >>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
    >>> root = app_data_dir()
    >>> os.path.isdir(root)
    True
    >>> app_data_dir('users', 'me').endswith(os.path.join('users', 'me'))
    True
    """
    base = os.environ.get(_ENV_VAR)
    if not base:
        xdg = os.environ.get('XDG_DATA_HOME')
        base = (
            os.path.join(xdg, 'hired')
            if xdg
            else os.path.join(os.path.expanduser('~'), '.local', 'share', 'hired')
        )
    path = os.path.join(base, *subpaths)
    if make:
        os.makedirs(path, exist_ok=True)
    return path


def json_store(rootdir: str) -> MutableMapping:
    """A ``MutableMapping`` of JSON-serializable values, one file per key.

    Missing intermediate directories are created on write, so nested keys
    (e.g. ``"a/b"``) work transparently.
    """
    os.makedirs(rootdir, exist_ok=True)
    return mk_dirs_if_missing(JsonFiles(rootdir))


def bytes_store(rootdir: str) -> MutableMapping:
    """A ``MutableMapping`` of raw ``bytes`` values (for uploads)."""
    os.makedirs(rootdir, exist_ok=True)
    return mk_dirs_if_missing(Files(rootdir))


def text_store(rootdir: str) -> MutableMapping:
    """A ``MutableMapping`` of ``str`` values (for human-readable projections)."""
    os.makedirs(rootdir, exist_ok=True)
    return mk_dirs_if_missing(TextFiles(rootdir))


# The per-candidate sub-stores and the factory that builds each kind. Keeping
# this as data (not hardcoded properties) keeps the mall open for extension.
_STORE_KINDS: dict[str, str] = {
    'uploads': 'bytes',
    'facts': 'json',
    'qa': 'json',
    'jobs': 'json',
    'reports': 'json',
    'synopsis': 'text',
}
_STORE_FACTORIES = {'json': json_store, 'bytes': bytes_store, 'text': text_store}


class CandidateMall(MutableMapping):
    """A store-of-stores for one candidate's data kinds.

    ``mall['facts']`` is the facts store; ``mall['facts', key]`` is a shorthand
    for ``mall['facts'][key]``. Data lives under
    ``<root>/users/<user>/<kind>/``.

    >>> import tempfile, os
    >>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
    >>> mall = CandidateMall()           # default user "me"
    >>> sorted(mall.keys())
    ['facts', 'jobs', 'qa', 'reports', 'synopsis', 'uploads']
    >>> mall['facts']['f1'] = {'statement': 'knows Python'}
    >>> mall['facts', 'f1']
    {'statement': 'knows Python'}
    """

    def __init__(self, user: str = DFLT_USER, *, root: str | None = None):
        self.user = user
        self._root = root
        self._cache: dict[str, MutableMapping] = {}

    def _kind_dir(self, kind: str) -> str:
        base = self._root or app_data_dir('users', self.user)
        return os.path.join(base, kind)

    def __getitem__(self, key):
        if isinstance(key, tuple):  # mall['facts', 'f1'] -> mall['facts']['f1']
            kind, inner = key
            return self[kind][inner]
        if key not in _STORE_KINDS:
            raise KeyError(
                f"Unknown store kind {key!r}. Available: {sorted(_STORE_KINDS)}"
            )
        if key not in self._cache:
            factory = _STORE_FACTORIES[_STORE_KINDS[key]]
            self._cache[key] = factory(self._kind_dir(key))
        return self._cache[key]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            kind, inner = key
            self[kind][inner] = value
            return
        raise TypeError(
            'Assign to a sub-store, not the mall: use mall[kind][key] = value'
        )

    def __delitem__(self, key):
        if isinstance(key, tuple):
            kind, inner = key
            del self[kind][inner]
            return
        raise TypeError('Delete from a sub-store: del mall[kind][key]')

    def __iter__(self):
        return iter(_STORE_KINDS)

    def __len__(self) -> int:
        return len(_STORE_KINDS)
