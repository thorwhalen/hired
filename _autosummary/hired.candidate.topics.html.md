# hired.candidate.topics

Topic dossiers — “a little, or a whole lot” about any subject the candidate shares.

A dossier lives under `user/info/topics/<slug>/` and holds an `overview.md`
(the human/agent-readable summary and *entry point*) plus optional detail
files/media under `files/`. A one-sentence note and a multi-file collection use
the same shape, so the synopsis can always link to an overview and the agent knows
where deeper detail lives. Reach a dossier via
`kb.topic(name)` / `kb.add_note(name, ...)`.

### Classes

| [`TopicDossier`](#hired.candidate.topics.TopicDossier)(base_dir, \*[, name])   | One subject's dossier: an `overview.md` plus optional attached files.   |
|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------|

### *class* hired.candidate.topics.TopicDossier(base_dir, , name=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One subject’s dossier: an `overview.md` plus optional attached files.

```pycon
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
```

#### add_file(filename, data)

Attach a detail file / media blob to the dossier.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### add_note(text)

Append a note to the overview (creating it, titled, if absent).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### exists()

True once the dossier has an overview or any attached file.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### files()

Names of attached detail files.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### *property* overview *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

The dossier’s overview markdown (the entry point), or `None`.
