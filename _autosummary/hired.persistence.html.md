# hired.persistence

dol-based persistence foundation for hired (Storage v2).

All hired persistence lives **outside the repository** under a single canonical
data root (`~/.local/share/hired/` by default, overridable via `HIRED_DATA_DIR`).
Stores are `MutableMapping` views over the filesystem (via `dol`) with
filesystem codecs that keep keys extension-less while writing properly-extensioned
files. Per-candidate data is split two levels deep: a cross-JD `user/` subtree
([`UserStore`](#hired.persistence.UserStore)) and per-engagement `jds/<jd_id>/` subtrees ([`JDStore`](#hired.persistence.JDStore)).

See `misc/docs/DESIGN.md` §4 for the full layout and rationale.

### Functions

| [`app_data_dir`](#hired.persistence.app_data_dir)(\*subpaths[, make])                  | Return the canonical hired data directory, joined with `subpaths`.           |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`user_base`](#hired.persistence.user_base)([user, root])                           | Filesystem base for a candidate: `<root>` or `<data>/users/<user>`.          |
| [`list_jds`](#hired.persistence.list_jds)([user, root])                            | Engagement ids under `users/<user>/jds/` (sorted; empty if none).            |
| [`json_store`](#hired.persistence.json_store)(rootdir)                               | A `MutableMapping` of JSON-able values: bare-id keys, `<id>.json` files.     |
| [`markdown_store`](#hired.persistence.markdown_store)(rootdir)                           | A `MutableMapping` of `str` values: bare keys, `<key>.md` files.             |
| [`bytes_store`](#hired.persistence.bytes_store)(rootdir)                              | A `MutableMapping` of raw `bytes`; keys are real filenames (extension kept). |
| [`migrate_legacy`](#hired.persistence.migrate_legacy)(legacy_path, target_path)          | One-time copy of a legacy store into the canonical root.                     |
| [`ensure_v2`](#hired.persistence.ensure_v2)([user, root])                           | Migrate the user to v2 if a legacy layout is detected.                       |
| [`is_legacy_layout`](#hired.persistence.is_legacy_layout)([user, root])                    | True iff any legacy v1 flat directory remains for this user.                 |
| [`migrate_user_to_v2`](#hired.persistence.migrate_user_to_v2)([user, root, company_of, ...]) | Migrate one user's flat v1 data to the v2 layout.                            |

### Classes

| [`UserStore`](#hired.persistence.UserStore)([user, root])          | Per-candidate cross-JD storage: raw sources + agent-maintained `info`.   |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`JDStore`](#hired.persistence.JDStore)(user, jd_id, \*[, root]) | Per-engagement storage under `users/<user>/jds/<jd_id>/`.                |
| [`Repository`](#hired.persistence.Repository)(store, \*[, model])   | Validated CRUD over a `MutableMapping` for a single pydantic model type. |

### *class* hired.persistence.JDStore(user, jd_id, , root=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Per-engagement storage under `users/<user>/jds/<jd_id>/`.

An engagement is one *or a group of* related JDs of the same company; it
holds the parsed jobs, alignment reports (+ archived history), company
research, and interview-prep briefings for that company’s role(s).

```pycon
>>> import tempfile, os
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> jd = JDStore('me', 'acme')
>>> jd.reports['role-1'] = {'verdict': {'recommendation': 'apply'}}
>>> jd.reports['role-1']['verdict']['recommendation']
'apply'
>>> jd.write_meta({'company': 'Acme'})
>>> jd.read_meta()['company']
'Acme'
```

### *class* hired.persistence.Repository(store, , model=None)

Bases: [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[`M`]

Validated CRUD over a `MutableMapping` for a single pydantic model type.

Subclasses set `model` and [`key_of()`](#hired.persistence.Repository.key_of). The store holds plain
JSON-able dicts; models are validated on the way in and out.

#### key_of(item)

Derive the storage key for an item (defaults to its `id` field).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* hired.persistence.UserStore(user='me', , root=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Per-candidate cross-JD storage: raw sources + agent-maintained `info`.

`raw` is a bytes store; `facts` and `qa` are json stores; `synopsis`
is a single markdown file accessed via `read_synopsis()` /
`write_synopsis()`.

```pycon
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
```

### hired.persistence.app_data_dir(\*subpaths, make=True)

Return the canonical hired data directory, joined with `subpaths`.

The directory is created when `make` is true (the default).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> import os, tempfile
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> root = app_data_dir()
>>> os.path.isdir(root)
True
>>> app_data_dir('users', 'me').endswith(os.path.join('users', 'me'))
True
```

### hired.persistence.bytes_store(rootdir)

A `MutableMapping` of raw `bytes`; keys are real filenames (extension kept).

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### hired.persistence.ensure_v2(user='me', , root=None)

Migrate the user to v2 if a legacy layout is detected. Returns True if migrated.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.persistence.is_legacy_layout(user='me', , root=None)

True iff any legacy v1 flat directory remains for this user.

Gated on the *presence of legacy dirs*, not on the existence of `user/` — a
fully-migrated user has had its legacy dirs removed, so this returns False;
a partially-migrated (interrupted) user still has some, so a re-run resumes.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.persistence.json_store(rootdir)

A `MutableMapping` of JSON-able values: bare-id keys, `<id>.json` files.

Built on `JsonFiles` (dict↔JSON value codec) + a `.json` key codec. Missing
intermediate directories are created on write, so nested keys (e.g. `"job/stamp"`)
work transparently.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### hired.persistence.list_jds(user='me', , root=None)

Engagement ids under `users/<user>/jds/` (sorted; empty if none).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.persistence.markdown_store(rootdir)

A `MutableMapping` of `str` values: bare keys, `<key>.md` files.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### hired.persistence.migrate_legacy(legacy_path, target_path)

One-time copy of a legacy store into the canonical root.

If `target_path` does not yet exist but `legacy_path` does, copy it
(file or directory) so historical data is preserved when storage roots are
unified. No-op otherwise. Returns True iff a copy happened.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.persistence.migrate_user_to_v2(user='me', , root=None, company_of=None, dry_run=False)

Migrate one user’s flat v1 data to the v2 layout. Returns the move plan.

Idempotent: a no-op (empty plan) if the user is already on v2 or has no
legacy data. With `dry_run=True` nothing is moved — the returned
`[(src, dst), ...]` plan can be inspected first.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]

### hired.persistence.user_base(user='me', , root=None)

Filesystem base for a candidate: `<root>` or `<data>/users/<user>`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Modules

| [`base`](hired.persistence.base.html.md#module-hired.persistence.base)             | Canonical data root, filesystem codecs, and the two-level candidate layout.     |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| [`migrate`](hired.persistence.migrate.html.md#module-hired.persistence.migrate)       | One-time migration of legacy flat per-user data to the Storage v2 layout.       |
| [`repository`](hired.persistence.repository.html.md#module-hired.persistence.repository) | A small repository base that maps validated domain models to a key-value store. |
