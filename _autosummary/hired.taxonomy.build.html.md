# hired.taxonomy.build

Build the skills taxonomy into the data root, and load it back as a `SkillIndex`.

[`build_skill_index()`](#hired.taxonomy.build.build_skill_index) fetches the sources (ESCO via its API, O\*NET via its
archive — see [`hired.taxonomy.sources`](hired.taxonomy.sources.html.md#module-hired.taxonomy.sources)), computes skill relatedness from
occupational co-occurrence ([`hired.taxonomy.graph`](hired.taxonomy.graph.html.md#module-hired.taxonomy.graph)), optionally embeds every
label (the `embeddings` extra), and writes the result under
`<data root>/taxonomy/` with a `NOTICE.md` carrying the CC BY 4.0
attribution. Raw pages and archives are cached under `taxonomy/raw/`, so an
interrupted build resumes and a rebuild is offline (`refresh=True` re-fetches).

A full ESCO fetch takes tens of minutes (the occupation pages are slow); O\*NET is
one ~13 MB download. Nothing here runs at import time.

### Functions

| [`build_skill_index`](#hired.taxonomy.build.build_skill_index)(\*[, sources, embeddings, ...])   | Fetch, compute and persist the taxonomy; return its `meta` summary.       |
|------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`load_skill_index`](#hired.taxonomy.build.load_skill_index)(\*[, root, embedder])              | Load the built taxonomy (raises `FileNotFoundError` with the build hint). |

### hired.taxonomy.build.build_skill_index(, sources=('esco', 'onet'), embeddings=False, embedder=None, embedding_model='sentence-transformers/all-MiniLM-L6-v2', root=None, refresh=False, onet_version='30_0', graph_kwargs=None, get_json=None, get_bytes=None, progress=None)

Fetch, compute and persist the taxonomy; return its `meta` summary.

`embeddings=True` (or an explicit `embedder`) also stores one vector per
node label. `graph_kwargs` go to [`relatedness_edges()`](hired.taxonomy.graph.html.md#hired.taxonomy.graph.relatedness_edges).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.taxonomy.build.load_skill_index(, root=None, embedder='auto', \*\*index_kwargs)

Load the built taxonomy (raises `FileNotFoundError` with the build hint).

`embedder="auto"` uses the stored embedding model for *query* text when the
taxonomy has vectors and the `embeddings` extra is installed (loaded on first
use); pass `None` to compare stored vectors only, or any embedder.
`index_kwargs` go to `SkillIndex` (e.g. `bridge_k`).

* **Return type:**
  [`SkillIndex`](hired.taxonomy.index.html.md#hired.taxonomy.index.SkillIndex)
