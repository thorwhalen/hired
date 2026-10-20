# PYTHON_ARGCOMPLETE_OK
"""The ``hired`` command: candidate knowledge + JD alignment from the shell.

Projects :data:`hired.cli.CLI_FUNCS` onto a parser with ``cw`` (the ``cli``
extra: ``pip install 'hired[cli]'``). Examples::

    hired users
    hired add-source cv.pdf --user alice
    hired ingest facts.json --source cv.pdf --user alice
    hired analyze draft_report.json acme --user alice
    hired align acme staff-ds.txt --user alice   # LLM analysis; needs the ai extra
    hired report acme --fmt html --output acme.html --user alice

``--user`` defaults to ``$HIRED_USER``, else ``me``.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any, TextIO

_MISSING_CW = (
    "The hired CLI needs the 'cw' package. Install it with:\n"
    "    pip install 'hired[cli]'"
)


def _egress(result: Any, *, out: TextIO | None = None, err: TextIO | None = None):
    """Mappings print as JSON; strings as-is; lists one item per line."""
    out = out or sys.stdout
    if result is None:
        return 0
    if isinstance(result, Mapping):
        out.write(json.dumps(result, indent=2, default=str) + "\n")
    elif isinstance(result, (list, tuple)):
        out.writelines(f"{x}\n" for x in result)
    else:
        text = str(result)
        out.write(text if text.endswith("\n") else text + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the ``hired`` command (returns the exit code)."""
    try:
        import cw
    except ImportError:
        print(_MISSING_CW, file=sys.stderr)
        return 1
    from hired.cli import CLI_FUNCS

    try:
        return cw.dispatch(CLI_FUNCS, argv, egress=_egress, prog="hired")
    except UnicodeError:
        raise  # an encoding bug, not a user error: keep the traceback
    except (ValueError, FileNotFoundError) as e:
        # Expected user errors (unknown candidate/engagement/report/format, invalid
        # id, malformed JSON or draft, missing file): one line, no traceback.
        print(f"hired: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
