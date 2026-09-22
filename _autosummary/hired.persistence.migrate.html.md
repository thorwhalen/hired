# hired.persistence.migrate

One-time migration of legacy flat per-user data to the Storage v2 layout.

Storage v1 kept every store kind flat under `users/<user>/<kind>/` with
*extension-less* files. Storage v2 (see [`hired.persistence.base`](hired.persistence.base.html.md#module-hired.persistence.base)) splits the
data into a cross-JD `user/` subtree and per-engagement `jds/<jd_id>/`
subtrees, and gives every file a proper extension.

This module moves the data once, idempotently:

- `facts/` `qa/`           → `user/info/<kind>/<name>.json`
- `uploads/`                 → `user/raw/<name>`        (filename kept)
- `synopsis/synopsis.md`     → `user/info/synopsis.md`
- `jobs/` `reports/` `report_history/` `company/` `interview_prep/`
  : → `jds/<jd_id>/<kind>/<rel>.json`

Engagements are grouped by company **when company research seeds the slugs**: if a
`company/<slug>` entry exists (or a prior partial run already created
`jds/<slug>/`), all items whose key equals `<slug>` or starts with `<slug>-`
land in that company’s single workspace (so a company’s several role reports + its
shared research + prep stay together). Without any such seed, each top-level key
becomes its own engagement; pass a custom `company_of` to force grouping.

The migration is **resumable**: it is gated on “any legacy directory remains”, moves
files individually, refuses to overwrite an existing destination, and removes the
empty legacy directories only after every move succeeds. So an interrupted run
(crash, disk-full) is simply re-run — already-moved files are skipped and the
remaining ones complete. The *intelligence* of the package is unaffected — this is
deterministic file plumbing, run automatically via [`ensure_v2()`](#hired.persistence.migrate.ensure_v2) on first v2
access, or explicitly (with [`migrate_user_to_v2()`](#hired.persistence.migrate.migrate_user_to_v2), optionally `dry_run=True`).

### Functions

| [`ensure_v2`](#hired.persistence.migrate.ensure_v2)([user, root])                           | Migrate the user to v2 if a legacy layout is detected.       |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| [`is_legacy_layout`](#hired.persistence.migrate.is_legacy_layout)([user, root])                    | True iff any legacy v1 flat directory remains for this user. |
| [`migrate_user_to_v2`](#hired.persistence.migrate.migrate_user_to_v2)([user, root, company_of, ...]) | Migrate one user's flat v1 data to the v2 layout.            |

### hired.persistence.migrate.ensure_v2(user='me', , root=None)

Migrate the user to v2 if a legacy layout is detected. Returns True if migrated.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.persistence.migrate.is_legacy_layout(user='me', , root=None)

True iff any legacy v1 flat directory remains for this user.

Gated on the *presence of legacy dirs*, not on the existence of `user/` — a
fully-migrated user has had its legacy dirs removed, so this returns False;
a partially-migrated (interrupted) user still has some, so a re-run resumes.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.persistence.migrate.migrate_user_to_v2(user='me', , root=None, company_of=None, dry_run=False)

Migrate one user’s flat v1 data to the v2 layout. Returns the move plan.

Idempotent: a no-op (empty plan) if the user is already on v2 or has no
legacy data. With `dry_run=True` nothing is moved — the returned
`[(src, dst), ...]` plan can be inspected first.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
