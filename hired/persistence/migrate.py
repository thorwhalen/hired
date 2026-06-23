"""One-time migration of legacy flat per-user data to the Storage v2 layout.

Storage v1 kept every store kind flat under ``users/<user>/<kind>/`` with
*extension-less* files. Storage v2 (see :mod:`hired.persistence.base`) splits the
data into a cross-JD ``user/`` subtree and per-engagement ``jds/<jd_id>/``
subtrees, and gives every file a proper extension.

This module moves the data once, idempotently:

- ``facts/`` ``qa/``           → ``user/info/<kind>/<name>.json``
- ``uploads/``                 → ``user/raw/<name>``        (filename kept)
- ``synopsis/synopsis.md``     → ``user/info/synopsis.md``
- ``jobs/`` ``reports/`` ``report_history/`` ``company/`` ``interview_prep/``
                               → ``jds/<jd_id>/<kind>/<rel>.json``

Engagements are grouped by company **when company research seeds the slugs**: if a
``company/<slug>`` entry exists (or a prior partial run already created
``jds/<slug>/``), all items whose key equals ``<slug>`` or starts with ``<slug>-``
land in that company's single workspace (so a company's several role reports + its
shared research + prep stay together). Without any such seed, each top-level key
becomes its own engagement; pass a custom ``company_of`` to force grouping.

The migration is **resumable**: it is gated on "any legacy directory remains", moves
files individually, refuses to overwrite an existing destination, and removes the
empty legacy directories only after every move succeeds. So an interrupted run
(crash, disk-full) is simply re-run — already-moved files are skipped and the
remaining ones complete. The *intelligence* of the package is unaffected — this is
deterministic file plumbing, run automatically via :func:`ensure_v2` on first v2
access, or explicitly (with :func:`migrate_user_to_v2`, optionally ``dry_run=True``).
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone

from hired.persistence.base import (
    COMPANY,
    INFO_DIR,
    JD_JSON_KINDS,
    JDS_DIR,
    META_FILE,
    RAW_DIR,
    SYNOPSIS_FILE,
    USER_DIR,
    USER_INFO_JSON_KINDS,
    DFLT_USER,
    user_base,
)

_LEGACY_UPLOADS = "uploads"
_LEGACY_SYNOPSIS = "synopsis"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _files_under(root: str):
    """Yield (posix-relpath, fullpath) for non-hidden files under ``root``."""
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            if name.startswith("."):  # skip .DS_Store and friends
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            yield rel, full


_LEGACY_MARKERS = (
    *USER_INFO_JSON_KINDS,
    *JD_JSON_KINDS,
    _LEGACY_UPLOADS,
    _LEGACY_SYNOPSIS,
)


def is_legacy_layout(user: str = DFLT_USER, *, root: str | None = None) -> bool:
    """True iff any legacy v1 flat directory remains for this user.

    Gated on the *presence of legacy dirs*, not on the existence of ``user/`` — a
    fully-migrated user has had its legacy dirs removed, so this returns False;
    a partially-migrated (interrupted) user still has some, so a re-run resumes.
    """
    base = user_base(user, root=root)
    return any(os.path.isdir(os.path.join(base, k)) for k in _LEGACY_MARKERS)


def _default_company_of(base: str):
    """Build the key→engagement grouper, seeded from company research + existing engagements.

    Seeding from both legacy ``company/`` keys and already-created ``jds/`` ids makes
    the grouping stable across a resumed migration (the prior run's ``jds/<slug>/``
    reveal the intended grouping even if ``company/`` was already moved).
    """
    seeds: set[str] = set()
    for d in (os.path.join(base, COMPANY), os.path.join(base, JDS_DIR)):
        if os.path.isdir(d):
            seeds.update(n for n in os.listdir(d) if not n.startswith("."))
    companies = sorted(seeds, key=len, reverse=True)

    def company_of(key: str) -> str:
        for c in companies:
            if key == c or key.startswith(c + "-"):
                return c
        return key

    return company_of


def _move(src: str, dst: str, *, dry_run: bool, plan: list) -> None:
    # Refuse to collapse two sources onto one destination (silent data loss), and
    # refuse to overwrite a pre-existing file. On a resumed run already-moved
    # sources are gone (so never re-yielded), so a hit here is a genuine collision.
    if any(d == dst for _s, d in plan) or (not dry_run and os.path.exists(dst)):
        raise ValueError(f"migration destination collision: {dst!r}")
    plan.append((src, dst))
    if dry_run:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


def migrate_user_to_v2(
    user: str = DFLT_USER,
    *,
    root: str | None = None,
    company_of=None,
    dry_run: bool = False,
) -> list[tuple[str, str]]:
    """Migrate one user's flat v1 data to the v2 layout. Returns the move plan.

    Idempotent: a no-op (empty plan) if the user is already on v2 or has no
    legacy data. With ``dry_run=True`` nothing is moved — the returned
    ``[(src, dst), ...]`` plan can be inspected first.
    """
    base = user_base(user, root=root)
    if not is_legacy_layout(user, root=root):
        return []

    company_of = company_of or _default_company_of(base)
    info = os.path.join(base, USER_DIR, INFO_DIR)
    plan: list[tuple[str, str]] = []
    touched_jds: set[str] = set()

    # user/info/<kind>/<name>.json  (facts, qa)
    for kind in USER_INFO_JSON_KINDS:
        src_dir = os.path.join(base, kind)
        for rel, full in _files_under(src_dir):
            _move(
                full,
                os.path.join(info, kind, rel + ".json"),
                dry_run=dry_run,
                plan=plan,
            )

    # user/raw/<name>  (uploads keep their real filename + extension)
    for rel, full in _files_under(os.path.join(base, _LEGACY_UPLOADS)):
        _move(
            full, os.path.join(base, USER_DIR, RAW_DIR, rel), dry_run=dry_run, plan=plan
        )

    # user/info/synopsis.md  (legacy synopsis/synopsis.md)
    for rel, full in _files_under(os.path.join(base, _LEGACY_SYNOPSIS)):
        # the canonical file maps to info/synopsis.md; anything else keeps its own
        # relative name so two sources never collapse onto synopsis.md
        dst_name = SYNOPSIS_FILE if rel == SYNOPSIS_FILE else rel
        _move(full, os.path.join(info, dst_name), dry_run=dry_run, plan=plan)

    # jds/<jd_id>/<kind>/<rel>.json  (jobs, reports, report_history, company, interview_prep)
    for kind in JD_JSON_KINDS:
        for rel, full in _files_under(os.path.join(base, kind)):
            jd_id = company_of(rel.split("/", 1)[0])
            touched_jds.add(jd_id)
            dst = os.path.join(base, JDS_DIR, jd_id, kind, rel + ".json")
            _move(full, dst, dry_run=dry_run, plan=plan)

    if not dry_run:
        # engagement meta + remove now-empty legacy dirs
        for jd_id in touched_jds:
            meta_path = os.path.join(base, JDS_DIR, jd_id, META_FILE)
            if not os.path.exists(meta_path):
                from hired.persistence.base import write_json_file

                write_json_file(
                    meta_path,
                    {
                        "jd_id": jd_id,
                        "company": jd_id,
                        "label": jd_id,
                        "created": _utcnow(),
                        "migrated_from": "v1-flat",
                    },
                )
        for kind in _LEGACY_MARKERS:
            shutil.rmtree(os.path.join(base, kind), ignore_errors=True)

    return plan


def ensure_v2(user: str = DFLT_USER, *, root: str | None = None) -> bool:
    """Migrate the user to v2 if a legacy layout is detected. Returns True if migrated."""
    if is_legacy_layout(user, root=root):
        migrate_user_to_v2(user, root=root)
        return True
    return False
