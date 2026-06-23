"""Topic dossiers — "a little, or a whole lot" about any subject the candidate shares.

A dossier lives under ``user/info/topics/<slug>/`` and holds an ``overview.md``
(the human/agent-readable summary and *entry point*) plus optional detail
files/media under ``files/``. A one-sentence note and a multi-file collection use
the same shape, so the synopsis can always link to an overview and the agent knows
where deeper detail lives. Reach a dossier via
``kb.topic(name)`` / ``kb.add_note(name, ...)``.
"""

from __future__ import annotations

import os

from hired.persistence.base import bytes_store, read_text_file, write_text_file

_OVERVIEW = "overview.md"
_FILES = "files"


class TopicDossier:
    """One subject's dossier: an ``overview.md`` plus optional attached files.

    >>> import tempfile, os
    >>> d = TopicDossier(os.path.join(tempfile.mkdtemp(), 'patents'), name='Patents')
    >>> d.add_note('Holds 3 US patents on anomaly detection.')
    >>> d.overview.splitlines()[0]
    '# Patents'
    >>> d.add_file('cert.txt', b'patent cert')
    >>> d.files()
    ['cert.txt']
    >>> d.get_file('cert.txt')
    b'patent cert'
    """

    def __init__(self, base_dir: str, *, name: str | None = None):
        self._dir = base_dir
        self.name = name or os.path.basename(base_dir.rstrip(os.sep))

    @property
    def overview(self) -> str | None:
        """The dossier's overview markdown (the entry point), or ``None``."""
        return read_text_file(os.path.join(self._dir, _OVERVIEW))

    def set_overview(self, text: str) -> None:
        write_text_file(
            os.path.join(self._dir, _OVERVIEW),
            text if text.endswith("\n") else text + "\n",
        )

    def add_note(self, text: str) -> None:
        """Append a note to the overview (creating it, titled, if absent)."""
        current = self.overview or f"# {self.name}\n"
        self.set_overview(current.rstrip() + "\n\n" + text.strip() + "\n")

    def add_file(self, filename: str, data: bytes) -> None:
        """Attach a detail file / media blob to the dossier."""
        self._file_store()[filename] = data

    def get_file(self, filename: str) -> bytes:
        return self._file_store()[filename]

    def files(self) -> list[str]:
        """Names of attached detail files."""
        return sorted(self._file_store())

    def exists(self) -> bool:
        """True once the dossier has an overview or any attached file."""
        return os.path.isdir(self._dir) and (
            self.overview is not None or bool(self.files())
        )

    def _file_store(self):
        return bytes_store(os.path.join(self._dir, _FILES))
