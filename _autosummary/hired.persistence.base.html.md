# hired.persistence.base

Canonical data root, filesystem codecs, and the two-level candidate layout.

The canonical root is resolved by [`app_data_dir()`](#hired.persistence.base.app_data_dir), honoring (in order):

1. the `HIRED_DATA_DIR` environment variable (used by tests and power users),
2. `$XDG_DATA_HOME/hired` (the XDG Base Directory spec),
3. `~/.local/share/hired` (the XDG default).

**Storage v2 — two-level layout.** Per-candidate data is split into \*what is true
about the candidate\* (cross-JD, reusable) and *work on a specific company’s role(s)*:

```default
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
```

**Codecs (the extension fix).** Keys stay domain-oriented and *extension-less* on the
`MutableMapping` facade; file extensions live only on the filesystem side, applied by
`dol` key codecs, and values are dicts in Python / JSON on disk via value codecs:

- [`json_store()`](#hired.persistence.base.json_store) — `JsonFiles` + a `.json` key codec: bare-id keys, `<id>.json`
  files, dict values.
- [`markdown_store()`](#hired.persistence.base.markdown_store) — `TextFiles` + a `.md` key codec: bare keys, `<key>.md`
  files, `str` values.
- [`bytes_store()`](#hired.persistence.base.bytes_store) — `dol.Files`: keys are real filenames (extension kept, as
  the extension is the meaningful domain key for an upload like `cv.pdf`).

The key codec uses only dol’s core `wrap_kvs` (not `affix_key_codec`/`filt_iter`,
which has a Windows-specific bug in dol 0.3.x) and normalizes path separators, so stores
behave identically on POSIX and Windows.

[`UserStore`](#hired.persistence.base.UserStore) groups the user-level stores; [`JDStore`](#hired.persistence.base.JDStore) groups one engagement’s
stores. Singletons (`synopsis.md`, `state.json`, `meta.json`) are single files —
their accessors carry the extension in the path, never in a store key.

### Module Attributes

| [`JsonStore`](#hired.persistence.base.JsonStore)    | A store of JSON-able values (dicts in Python, JSON on disk), keyed by bare ids.   |
|---------------------------------------------------------------|-----------------------------------------------------------------------------------|
| [`TextStore`](#hired.persistence.base.TextStore)    | A store of `str` values (e.g. markdown files), keyed by bare names.               |
| [`BytesStore`](#hired.persistence.base.BytesStore)   | A store of raw `bytes`, keyed by real filenames.                                  |
| [`USER_ENV_VAR`](#hired.persistence.base.USER_ENV_VAR) | Environment variable naming the active candidate when no `user` is passed.        |

### Functions

| [`app_data_dir`](#hired.persistence.base.app_data_dir)(\*subpaths[, make])         | Return the canonical hired data directory, joined with `subpaths`.           |
|-------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`bytes_store`](#hired.persistence.base.bytes_store)(rootdir)                     | A `MutableMapping` of raw `bytes`; keys are real filenames (extension kept). |
| [`json_store`](#hired.persistence.base.json_store)(rootdir)                      | A `MutableMapping` of JSON-able values: bare-id keys, `<id>.json` files.     |
| [`list_jds`](#hired.persistence.base.list_jds)([user, root])                   | Engagement ids under `users/<user>/jds/` (sorted; empty if none).            |
| [`list_users`](#hired.persistence.base.list_users)()                             | Candidates with data under the data root's `users/` (sorted; empty if none). |
| [`markdown_store`](#hired.persistence.base.markdown_store)(rootdir)                  | A `MutableMapping` of `str` values: bare keys, `<key>.md` files.             |
| [`migrate_legacy`](#hired.persistence.base.migrate_legacy)(legacy_path, target_path) | One-time copy of a legacy store into the canonical root.                     |
| [`read_json_file`](#hired.persistence.base.read_json_file)(path)                     | Read a JSON file, or return `None` if it does not exist.                     |
| [`read_text_file`](#hired.persistence.base.read_text_file)(path)                     | Read a text file, or return `None` if it does not exist.                     |
| [`resolve_user`](#hired.persistence.base.resolve_user)([user])                     | The candidate an operation targets: `user`, else `$HIRED_USER`, else `"me"`. |
| [`user_base`](#hired.persistence.base.user_base)([user, root])                  | Filesystem base for a candidate: `<root>` or `<data>/users/<user>`.          |
| [`validate_name`](#hired.persistence.base.validate_name)(name, \*[, kind])          | Return `name` if it is a safe, portable single path segment, else raise.     |
| [`write_json_file`](#hired.persistence.base.write_json_file)(path, obj)               | Write `obj` as indented JSON, creating parent dirs as needed.                |
| [`write_text_file`](#hired.persistence.base.write_text_file)(path, text)              | Write `text` to a file, creating parent dirs as needed.                      |

### Classes

| [`JDStore`](#hired.persistence.base.JDStore)(user, jd_id, \*[, root])   | Per-engagement storage under `users/<user>/jds/<jd_id>/`.              |
|-------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`UserStore`](#hired.persistence.base.UserStore)([user, root])            | Per-candidate cross-JD storage: raw sources + agent-maintained `info`. |

### hired.persistence.base.BytesStore

A store of raw `bytes`, keyed by real filenames.

alias of [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### *class* hired.persistence.base.JDStore(user, jd_id, , root=None)

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

### hired.persistence.base.JsonStore

A store of JSON-able values (dicts in Python, JSON on disk), keyed by bare ids.

alias of [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.persistence.base.TextStore

A store of `str` values (e.g. markdown files), keyed by bare names.

alias of [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.persistence.base.USER_ENV_VAR *= 'HIRED_USER'*

Environment variable naming the active candidate when no `user` is passed.

### *class* hired.persistence.base.UserStore(user=None, , root=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Per-candidate cross-JD storage: raw sources + agent-maintained `info`.

`raw` is a bytes store; `facts` and `qa` are json stores; `synopsis`
is a single markdown file accessed via `read_synopsis()` /
`write_synopsis()`.

```pycon
>>> import tempfile, os
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> us = UserStore()           # default user: $HIRED_USER, else "me"
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

### hired.persistence.base.app_data_dir(\*subpaths, make=True)

Return the canonical hired data directory, joined with `subpaths`.

The directory is created when `make` is true (the default).

```pycon
>>> import os, tempfile
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> root = app_data_dir()
>>> os.path.isdir(root)
True
>>> app_data_dir('users', 'me').endswith(os.path.join('users', 'me'))
True
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.persistence.base.bytes_store(rootdir)

A `MutableMapping` of raw `bytes`; keys are real filenames (extension kept).

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### hired.persistence.base.json_store(rootdir)

A `MutableMapping` of JSON-able values: bare-id keys, `<id>.json` files.

Built on `JsonFiles` (dict↔JSON value codec) + a `.json` key codec. Missing
intermediate directories are created on write, so nested keys (e.g. `"job/stamp"`)
work transparently.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.persistence.base.list_jds(user=None, , root=None)

Engagement ids under `users/<user>/jds/` (sorted; empty if none).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.persistence.base.list_users()

Candidates with data under the data root’s `users/` (sorted; empty if none).

```pycon
>>> import os, tempfile
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> list_users()
[]
>>> _ = UserStore('alice').facts
>>> list_users()
['alice']
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.persistence.base.markdown_store(rootdir)

A `MutableMapping` of `str` values: bare keys, `<key>.md` files.

* **Return type:**
  [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.persistence.base.migrate_legacy(legacy_path, target_path)

One-time copy of a legacy store into the canonical root.

If `target_path` does not yet exist but `legacy_path` does, copy it
(file or directory) so historical data is preserved when storage roots are
unified. No-op otherwise. Returns True iff a copy happened.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.persistence.base.read_json_file(path)

Read a JSON file, or return `None` if it does not exist.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

### hired.persistence.base.read_text_file(path)

Read a text file, or return `None` if it does not exist.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### hired.persistence.base.resolve_user(user=None)

The candidate an operation targets: `user`, else `$HIRED_USER`, else `"me"`.

This is the *only* place the single-tenant default lives; every user-scoped
entry point passes its `user` argument through here. An explicitly given
name (even `""`) is validated, never silently replaced by the default.

```pycon
>>> import os
>>> _ = os.environ.pop('HIRED_USER', None)
>>> resolve_user()
'me'
>>> resolve_user('alice')
'alice'
>>> os.environ['HIRED_USER'] = 'bob'
>>> resolve_user()
'bob'
>>> del os.environ['HIRED_USER']
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.persistence.base.user_base(user=None, , root=None)

Filesystem base for a candidate: `<root>` or `<data>/users/<user>`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.persistence.base.validate_name(name, , kind='name')

Return `name` if it is a safe, portable single path segment, else raise.

User, engagement and job ids become directory or file names, so they are
restricted to ASCII letters, digits and `._-` (starting with a letter or
digit, not ending in `.`), and may not be a Windows device name. That rules
out separators, `..`, drive prefixes (`C:x`), hidden names and NUL bytes —
so one id can never address another candidate’s (or an arbitrary) directory.
`kind="user"` also requires lower case (see `_USER_PATTERN`).

```pycon
>>> validate_name('acme-2024')
'acme-2024'
>>> validate_name('../bob', kind='engagement id')
Traceback (most recent call last):
  ...
ValueError: Invalid engagement id '../bob': use ASCII letters, digits and '._-', starting with a letter or digit and not ending in '.'
>>> validate_name('Alice', kind='user')
Traceback (most recent call last):
  ...
ValueError: Invalid user 'Alice': use lower-case ASCII letters, digits and '._-', starting with a letter or digit and not ending in '.'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.persistence.base.write_json_file(path, obj)

Write `obj` as indented JSON, creating parent dirs as needed.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### hired.persistence.base.write_text_file(path, text)

Write `text` to a file, creating parent dirs as needed.

Uses `newline=""` so stored files keep `\n` verbatim on every platform
(no `\r\n` translation on Windows), keeping the data store consistent.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
