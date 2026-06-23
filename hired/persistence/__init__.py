"""dol-based persistence foundation for hired (Storage v2).

All hired persistence lives **outside the repository** under a single canonical
data root (``~/.local/share/hired/`` by default, overridable via ``HIRED_DATA_DIR``).
Stores are ``MutableMapping`` views over the filesystem (via :mod:`dol`) with
filesystem codecs that keep keys extension-less while writing properly-extensioned
files. Per-candidate data is split two levels deep: a cross-JD ``user/`` subtree
(:class:`UserStore`) and per-engagement ``jds/<jd_id>/`` subtrees (:class:`JDStore`).

See ``misc/docs/DESIGN.md`` §4 for the full layout and rationale.
"""

from hired.persistence.base import (
    DFLT_USER,
    JDStore,
    UserStore,
    app_data_dir,
    bytes_store,
    json_store,
    list_jds,
    markdown_store,
    migrate_legacy,
    user_base,
)
from hired.persistence.migrate import ensure_v2, is_legacy_layout, migrate_user_to_v2
from hired.persistence.repository import Repository

__all__ = [
    'app_data_dir',
    'user_base',
    'list_jds',
    'json_store',
    'markdown_store',
    'bytes_store',
    'migrate_legacy',
    'UserStore',
    'JDStore',
    'DFLT_USER',
    'Repository',
    'ensure_v2',
    'is_legacy_layout',
    'migrate_user_to_v2',
]
