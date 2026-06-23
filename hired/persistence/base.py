"""Canonical data root, filesystem codecs, and the two-level candidate layout.

The canonical root is resolved by :func:`app_data_dir`, honoring (in order):

1. the ``HIRED_DATA_DIR`` environment variable (used by tests and power users),
2. ``$XDG_DATA_HOME/hired`` (the XDG Base Directory spec),
3. ``~/.local/share/hired`` (the XDG default).

**Storage v2 — two-level layout.** Per-candidate data is split into *what is true
about the candidate* (cross-JD, reusable) and *work on a specific company's role(s)*::

    users/<user>/
      user/                      # the candidate — single source of truth
        raw/                     # raw sources the user provided (bytes; real filenames)
        info/                    # agent-maintained, operable knowledge (agent CRUDs here)
          facts/  <id>.json
          qa/     <id>.json
          topics/ <topic>/...    # per-subject dossiers (Phase 2)
          synopsis.md            # regenerated overview (singleton)
          state.json             # refresh bookkeeping (Phase 3)
      jds/<jd_id>/               # one engagement = 1+ related JDs of the same company
        meta.json
        jobs/ reports/ report_history/ company/ interview_prep/   (<key>.json)

**Codecs (the extension fix).** Keys stay domain-oriented and *extension-less* on the
``MutableMapping`` facade; file extensions live only on the filesystem side, applied by
:mod:`dol` key codecs, and values are dicts in Python / JSON on disk via value codecs:

- :func:`json_store` — :class:`dol.Jsons`: bare-id keys, ``<id>.json`` files, dict values.
- :func:`markdown_store` — bare keys, ``<key>.md`` files, ``str`` values (``.md`` only).
- :func:`bytes_store` — :class:`dol.Files`: keys are real filenames (extension kept, as
  the extension is the meaningful domain key for an upload like ``cv.pdf``).

:class:`UserStore` groups the user-level stores; :class:`JDStore` groups one engagement's
stores. Singletons (``synopsis.md``, ``state.json``, ``meta.json``) are single files —
their accessors carry the extension in the path, never in a store key.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import MutableMapping
from functools import cached_property

from dol import Files, Jsons, KeyCodecs, TextFiles, filt_iter, mk_dirs_if_missing

DFLT_USER = "me"
_ENV_VAR = "HIRED_DATA_DIR"

# --- layout names (single source of truth; no magic strings) --------------- #
USERS_DIR = "users"
USER_DIR = "user"  # users/<user>/user/   (the candidate themselves)
INFO_DIR = "info"  # users/<user>/user/info/
RAW_DIR = "raw"  # users/<user>/user/raw/
JDS_DIR = "jds"  # users/<user>/jds/

# user-level info collections (json stores under user/info/<kind>/)
FACTS = "facts"
QA = "qa"
TOPICS = "topics"  # Phase 2 (dossier subtree)

# user-level singletons (single files under user/info/)
SYNOPSIS_FILE = "synopsis.md"
STATE_FILE = "state.json"  # Phase 3

# per-engagement collections (json stores under jds/<jd_id>/<kind>/)
JOBS = "jobs"
REPORTS = "reports"
REPORT_HISTORY = "report_history"
COMPANY = "company"
INTERVIEW_PREP = "interview_prep"

# per-engagement singleton
META_FILE = "meta.json"

# The json-store kinds at each level (used by migration + tests as the SSOT).
USER_INFO_JSON_KINDS = (FACTS, QA)
JD_JSON_KINDS = (JOBS, REPORTS, REPORT_HISTORY, COMPANY, INTERVIEW_PREP)


def migrate_legacy(legacy_path, target_path) -> bool:
    """One-time copy of a legacy store into the canonical root.

    If ``target_path`` does not yet exist but ``legacy_path`` does, copy it
    (file or directory) so historical data is preserved when storage roots are
    unified. No-op otherwise. Returns True iff a copy happened.
    """
    from pathlib import Path

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
        xdg = os.environ.get("XDG_DATA_HOME")
        base = (
            os.path.join(xdg, "hired")
            if xdg
            else os.path.join(os.path.expanduser("~"), ".local", "share", "hired")
        )
    path = os.path.join(base, *subpaths)
    if make:
        os.makedirs(path, exist_ok=True)
    return path


# --------------------------------------------------------------------------- #
# Store factories (codec-bearing: extensions on the filesystem side only)
# --------------------------------------------------------------------------- #
def json_store(rootdir: str) -> MutableMapping:
    """A ``MutableMapping`` of JSON-able values: bare-id keys, ``<id>.json`` files.

    Missing intermediate directories are created on write, so nested keys
    (e.g. ``"job/stamp"``) work transparently.
    """
    os.makedirs(rootdir, exist_ok=True)
    return mk_dirs_if_missing(Jsons(rootdir))


def markdown_store(rootdir: str) -> MutableMapping:
    """A ``MutableMapping`` of ``str`` values: bare keys, ``<key>.md`` files.

    Only ``.md`` files are visible (so a directory holding both markdown and
    other artifacts exposes just the markdown view).
    """
    os.makedirs(rootdir, exist_ok=True)
    base = filt_iter.suffixes(".md")(TextFiles(rootdir))
    return mk_dirs_if_missing(KeyCodecs.suffixed(".md")(base))


def bytes_store(rootdir: str) -> MutableMapping:
    """A ``MutableMapping`` of raw ``bytes``; keys are real filenames (extension kept)."""
    os.makedirs(rootdir, exist_ok=True)
    return mk_dirs_if_missing(Files(rootdir))


# --------------------------------------------------------------------------- #
# Single-file accessors (for singletons that are not collections)
# --------------------------------------------------------------------------- #
def _read_json_file(path: str):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _write_json_file(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=4)


def _read_text_file(path: str):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None


def _write_text_file(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def user_base(user: str = DFLT_USER, *, root: str | None = None) -> str:
    """Filesystem base for a candidate: ``<root>`` or ``<data>/users/<user>``."""
    return root or app_data_dir(USERS_DIR, user)


def list_jds(user: str = DFLT_USER, *, root: str | None = None) -> list[str]:
    """Engagement ids under ``users/<user>/jds/`` (sorted; empty if none)."""
    jds_dir = os.path.join(user_base(user, root=root), JDS_DIR)
    if not os.path.isdir(jds_dir):
        return []
    return sorted(n for n in os.listdir(jds_dir) if not n.startswith("."))


# --------------------------------------------------------------------------- #
# Store-of-stores: user level and engagement level
# --------------------------------------------------------------------------- #
class UserStore:
    """Per-candidate cross-JD storage: raw sources + agent-maintained ``info``.

    ``raw`` is a bytes store; ``facts`` and ``qa`` are json stores; ``synopsis``
    is a single markdown file accessed via :meth:`read_synopsis` /
    :meth:`write_synopsis`.

    >>> import tempfile, os
    >>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
    >>> us = UserStore()                       # default user "me"
    >>> us.facts['f1'] = {'statement': 'knows Python'}
    >>> us.facts['f1']
    {'statement': 'knows Python'}
    >>> us.raw['cv.pdf'] = b'%PDF-1.4'
    >>> us.raw['cv.pdf']
    b'%PDF-1.4'
    >>> us.write_synopsis('# me')
    >>> us.read_synopsis()
    '# me'
    """

    def __init__(self, user: str = DFLT_USER, *, root: str | None = None):
        self.user = user
        self._root = root

    @property
    def base(self) -> str:
        return user_base(self.user, root=self._root)

    def _info(self, *parts: str) -> str:
        return os.path.join(self.base, USER_DIR, INFO_DIR, *parts)

    @cached_property
    def raw(self) -> MutableMapping:
        return bytes_store(os.path.join(self.base, USER_DIR, RAW_DIR))

    @cached_property
    def facts(self) -> MutableMapping:
        return json_store(self._info(FACTS))

    @cached_property
    def qa(self) -> MutableMapping:
        return json_store(self._info(QA))

    # --- synopsis singleton (info/synopsis.md) ---------------------------- #
    def read_synopsis(self) -> str | None:
        return _read_text_file(self._info(SYNOPSIS_FILE))

    def write_synopsis(self, text: str) -> None:
        _write_text_file(self._info(SYNOPSIS_FILE), text)

    # --- refresh state singleton (info/state.json) ------------------------ #
    def read_state(self) -> dict | None:
        return _read_json_file(self._info(STATE_FILE))

    def write_state(self, state: dict) -> None:
        _write_json_file(self._info(STATE_FILE), state)


class JDStore:
    """Per-engagement storage under ``users/<user>/jds/<jd_id>/``.

    An engagement is one *or a group of* related JDs of the same company; it
    holds the parsed jobs, alignment reports (+ archived history), company
    research, and interview-prep briefings for that company's role(s).

    >>> import tempfile, os
    >>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
    >>> jd = JDStore('me', 'acme')
    >>> jd.reports['role-1'] = {'verdict': {'recommendation': 'apply'}}
    >>> jd.reports['role-1']['verdict']['recommendation']
    'apply'
    >>> jd.write_meta({'company': 'Acme'})
    >>> jd.read_meta()['company']
    'Acme'
    """

    def __init__(self, user: str, jd_id: str, *, root: str | None = None):
        self.user = user
        self.jd_id = jd_id
        self._root = root

    @property
    def base(self) -> str:
        return os.path.join(user_base(self.user, root=self._root), JDS_DIR, self.jd_id)

    @cached_property
    def jobs(self) -> MutableMapping:
        return json_store(os.path.join(self.base, JOBS))

    @cached_property
    def reports(self) -> MutableMapping:
        return json_store(os.path.join(self.base, REPORTS))

    @cached_property
    def report_history(self) -> MutableMapping:
        return json_store(os.path.join(self.base, REPORT_HISTORY))

    @cached_property
    def company(self) -> MutableMapping:
        return json_store(os.path.join(self.base, COMPANY))

    @cached_property
    def interview_prep(self) -> MutableMapping:
        return json_store(os.path.join(self.base, INTERVIEW_PREP))

    # --- engagement meta singleton (jds/<id>/meta.json) ------------------- #
    def read_meta(self) -> dict:
        return _read_json_file(os.path.join(self.base, META_FILE)) or {}

    def write_meta(self, meta: dict) -> None:
        _write_json_file(os.path.join(self.base, META_FILE), meta)
