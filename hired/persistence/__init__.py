"""dol-based persistence foundation for hired.

All hired persistence lives **outside the repository** under a single canonical
data root (``~/.local/share/hired/`` by default, overridable via ``HIRED_DATA_DIR``).
Stores are ``MutableMapping`` views over the filesystem (via :mod:`dol`), and
domain repositories wrap them with validated, intention-revealing methods.

See ``misc/docs/DESIGN.md`` §3-4 for the full layout and rationale.
"""

from hired.persistence.base import (
    app_data_dir,
    json_store,
    bytes_store,
    text_store,
    migrate_legacy,
    CandidateMall,
)
from hired.persistence.repository import Repository

__all__ = [
    "app_data_dir",
    "json_store",
    "bytes_store",
    "text_store",
    "migrate_legacy",
    "CandidateMall",
    "Repository",
]
