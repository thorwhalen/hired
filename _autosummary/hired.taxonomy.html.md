# hired.taxonomy

Skills taxonomy (ESCO + O\*NET) and skill adjacency for alignment’s Axis A.

Strengthens *transfer distance* beyond keyword match and LLM judgment with two
signals, blended as `alpha * cosine + (1 - alpha) * graph`:

- a **relatedness graph** learned from which skills occupations require together
  (ESCO occupation↔skill links, O\*NET technology and K/S/A ratings) — pure Python;
- **label embeddings** (the `embeddings` extra) for similarity and for skills
  absent from both taxonomies.

Nothing is vendored: build the taxonomy once into the data root, then query it:

```default
from hired.taxonomy import build_skill_index, load_skill_index
build_skill_index()                 # or `hired build-skill-index`; tens of minutes
idx = load_skill_index()
idx.suggest_adjacency("PyTorch", ["TensorFlow", "Excel"])
```

ESCO (© European Union) and O\*NET (USDOL/ETA) data are used under CC BY 4.0; see
`hired.taxonomy.base.ATTRIBUTION`, written next to the data as `NOTICE.md`.
Research basis: `misc/docs/research/skills-taxonomy-and-adjacency.md`.

### Functions

| [`build_skill_index`](#hired.taxonomy.build_skill_index)(\*[, sources, embeddings, ...])   | Fetch, compute and persist the taxonomy; return its `meta` summary.         |
|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`load_skill_index`](#hired.taxonomy.load_skill_index)(\*[, root, embedder])              | Load the built taxonomy (raises `FileNotFoundError` with the build hint).   |
| [`sentence_transformer_embedder`](#hired.taxonomy.sentence_transformer_embedder)([model_name, ...])    | An embedder backed by a local sentence-transformers model (loaded now).     |
| [`relatedness_edges`](#hired.taxonomy.relatedness_edges)(occupations, \*[, ...])           | Skill-relatedness edges (`SR` in `(min_score, 1]`) from co-occurrence.      |
| [`merge_edges`](#hired.taxonomy.merge_edges)(\*edge_sets)                            | Union of edge sets over disjoint id spaces (e.g. ESCO and O\*NET).          |
| [`transferability_band`](#hired.taxonomy.transferability_band)(score, \*[, bands])            | The `Transferability` band a proximity `score` falls in.                    |
| [`fetch_esco`](#hired.taxonomy.fetch_esco)(\*[, get_json, cache, page_size, ...])   | All ESCO skills and occupations (with their skill links).                   |
| [`fetch_onet`](#hired.taxonomy.fetch_onet)(\*[, get_bytes, cache, version, ...])    | O\*NET technology and K/S/A nodes, and occupations (downloads ~13 MB once). |
| [`parse_onet_archive`](#hired.taxonomy.parse_onet_archive)(data, \*[, min_importance])      | Nodes and occupations from the bytes of an O\*NET text-database archive.    |
| [`normalize_label`](#hired.taxonomy.normalize_label)(text)                               | Case-, accent- and punctuation-insensitive form of a label, for matching.   |
| [`taxonomy_dir`](#hired.taxonomy.taxonomy_dir)(\*subpaths[, root, make])              | Directory of the built taxonomy: `root` or `<data root>/taxonomy`.          |

### Classes

| [`SkillIndex`](#hired.taxonomy.SkillIndex)(nodes, edges, \*[, vectors, ...])      | Lookup and adjacency over taxonomy nodes, edges and (optional) vectors.   |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`Proximity`](#hired.taxonomy.Proximity)(a, b, score, graph, cosine, alpha)      | How close two skills are, with the evidence behind the number.            |
| [`Match`](#hired.taxonomy.Match)(node, score, how)                           | A taxonomy node matched to a piece of text.                               |
| [`SkillNode`](#hired.taxonomy.SkillNode)(\*, id, label[, alt_labels, kind, ...]) | One skill-like concept from a source taxonomy.                            |
| [`Occupation`](#hired.taxonomy.Occupation)(\*, id, label, source[, ...])          | An occupation and the skill nodes it requires or may use.                 |

### *class* hired.taxonomy.Match(node, score, how)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A taxonomy node matched to a piece of text.

### *class* hired.taxonomy.Occupation(\*, id, label, source, essential=<factory>, optional=<factory>)

Bases: `BaseModel`

An occupation and the skill nodes it requires or may use.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.taxonomy.Proximity(a, b, score, graph, cosine, alpha, a_node=None, b_node=None, via=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How close two skills are, with the evidence behind the number.

#### *property* basis *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

One readable line of evidence, for a record’s `adjacency_basis`.

#### transferability(\*\*kwargs)

The band `score` falls in (see [`transferability_band()`](#hired.taxonomy.transferability_band)).

* **Return type:**
  [`Transferability`](hired.alignment.base.html.md#hired.alignment.base.Transferability)

### *class* hired.taxonomy.SkillIndex(nodes, edges, , vectors=None, vector_ids=None, embedder=None, meta=None, bridge_k=3, bridge_min_score=0.5, graph_trust=0.2)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Lookup and adjacency over taxonomy nodes, edges and (optional) vectors.

```pycon
>>> from hired.taxonomy.base import SkillNode
>>> nodes = [SkillNode(id='s:py', label='Python (computer programming)',
...                    alt_labels=['Python'], source='s'),
...          SkillNode(id='s:ml', label='machine learning', source='s'),
...          SkillNode(id='s:cook', label='cooking', source='s')]
>>> idx = SkillIndex(nodes, {'s:py': [('s:ml', 0.6)], 's:ml': [('s:py', 0.6)]})
>>> idx.lookup('python')[0].node.id
's:py'
>>> p = idx.proximity('Python', 'machine learning')
>>> p.score, p.alpha, p.transferability().value
(0.6, 0.0, 'contextual')
>>> idx.proximity('Python', 'cooking').score
0.0
```

#### graph_score(a_id, b_id)

Relatedness of two nodes (direct, or via one shared neighbour) and the via id.

Equivalent nodes count fully; cross-source bridges count with their weight.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]

#### lookup(text, , k=5, min_score=0.5)

Nodes best matching `text`: exact label, alt label, token overlap, embedding.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Match`](hired.taxonomy.index.html.md#hired.taxonomy.index.Match)]

#### neighbors(text, , k=10)

The skills most related to `text` in the co-occurrence graph.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

#### proximity(a, b, , alpha=0.5)

Blended adjacency of two skill texts (or node ids).

* **Return type:**
  [`Proximity`](hired.taxonomy.index.html.md#hired.taxonomy.index.Proximity)

#### resolve(text, , min_score=0.5)

The single best node for `text` (or `None`).

* **Return type:**
  [`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### suggest_adjacency(requirement, candidate_skills, , k=3, alpha=0.5)

The candidate’s skills closest to `requirement`, strongest first.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Proximity`](hired.taxonomy.index.html.md#hired.taxonomy.index.Proximity)]

### *class* hired.taxonomy.SkillNode(\*, id, label, alt_labels=<factory>, source, kind='skill', reuse_level=None, uri=None)

Bases: `BaseModel`

One skill-like concept from a source taxonomy.

#### kind *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

“skill”, “knowledge”, “ability”, “technology”, “competence”, …

* **Type:**
  KSAO kind

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

#### reuse_level *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

ESCO skill-reuse level (“transversal”, “cross-sector”, “sector-specific”,
“occupation-specific”), when known — a transferability hint.

### hired.taxonomy.build_skill_index(, sources=('esco', 'onet'), embeddings=False, embedder=None, embedding_model='sentence-transformers/all-MiniLM-L6-v2', root=None, refresh=False, onet_version='30_0', graph_kwargs=None, get_json=None, get_bytes=None, progress=None)

Fetch, compute and persist the taxonomy; return its `meta` summary.

`embeddings=True` (or an explicit `embedder`) also stores one vector per
node label. `graph_kwargs` go to [`relatedness_edges()`](hired.taxonomy.graph.html.md#hired.taxonomy.graph.relatedness_edges).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.taxonomy.fetch_esco(, get_json=None, cache=None, page_size=100, language='en', progress=None)

All ESCO skills and occupations (with their skill links).

Occupation↔skill links are the union of both sides — an occupation’s
`hasEssential/OptionalSkill` and a skill’s `isEssential/OptionalForOccupation`
— so a record that only came back in brief form still gets its links.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)]]

### hired.taxonomy.fetch_onet(, get_bytes=None, cache=None, version='30_0', min_importance=3.5, progress=None)

O\*NET technology and K/S/A nodes, and occupations (downloads ~13 MB once).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)]]

### hired.taxonomy.load_skill_index(, root=None, embedder='auto', \*\*index_kwargs)

Load the built taxonomy (raises `FileNotFoundError` with the build hint).

`embedder="auto"` uses the stored embedding model for *query* text when the
taxonomy has vectors and the `embeddings` extra is installed (loaded on first
use); pass `None` to compare stored vectors only, or any embedder.
`index_kwargs` go to [`SkillIndex`](#hired.taxonomy.SkillIndex) (e.g. `bridge_k`).

* **Return type:**
  [`SkillIndex`](hired.taxonomy.index.html.md#hired.taxonomy.index.SkillIndex)

### hired.taxonomy.merge_edges(\*edge_sets)

Union of edge sets over disjoint id spaces (e.g. ESCO and O\*NET).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

### hired.taxonomy.normalize_label(text)

Case-, accent- and punctuation-insensitive form of a label, for matching.

```pycon
>>> normalize_label('  Machine-Learning (ML)! ')
'machine learning ml'
>>> normalize_label('Café')
'cafe'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.taxonomy.parse_onet_archive(data, , min_importance=3.5)

Nodes and occupations from the bytes of an O\*NET text-database archive.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)]]

### hired.taxonomy.relatedness_edges(occupations, , optional_weight=0.5, min_cooccurrence=2.0, top_k=30, min_score=0.0)

Skill-relatedness edges (`SR` in `(min_score, 1]`) from co-occurrence.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

### hired.taxonomy.sentence_transformer_embedder(model_name='sentence-transformers/all-MiniLM-L6-v2', , batch_size=256)

An embedder backed by a local sentence-transformers model (loaded now).

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]], [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.taxonomy.taxonomy_dir(\*subpaths, root=None, make=True)

Directory of the built taxonomy: `root` or `<data root>/taxonomy`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.taxonomy.transferability_band(score, , bands=((0.75, Transferability.DIRECT), (0.5, Transferability.CONTEXTUAL), (0.25, Transferability.FOUNDATIONAL)))

The `Transferability` band a proximity `score` falls in.

```pycon
>>> transferability_band(0.8).value, transferability_band(0.1).value
('direct', 'limited')
```

* **Return type:**
  [`Transferability`](hired.alignment.base.html.md#hired.alignment.base.Transferability)

### Modules

| [`base`](hired.taxonomy.base.html.md#module-hired.taxonomy.base)       | Schemas and on-disk layout for the skills taxonomy (ESCO + O\*NET).                                                                                                 |
|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`build`](hired.taxonomy.build.html.md#module-hired.taxonomy.build)     | Build the skills taxonomy into the data root, and load it back as a [`SkillIndex`](#hired.taxonomy.SkillIndex).                                    |
| [`embed`](hired.taxonomy.embed.html.md#module-hired.taxonomy.embed)     | The label-embedding seam (the `embeddings` extra).                                                                                                                  |
| [`graph`](hired.taxonomy.graph.html.md#module-hired.taxonomy.graph)     | Skill relatedness from occupational co-occurrence (pure Python, no numpy).                                                                                          |
| [`index`](hired.taxonomy.index.html.md#module-hired.taxonomy.index)     | Query a built skills taxonomy: resolve skill text, score adjacency (Axis A).                                                                                        |
| [`sources`](hired.taxonomy.sources.html.md#module-hired.taxonomy.sources) | Fetch the ESCO and O\*NET taxonomies into [`SkillNode`](#hired.taxonomy.SkillNode) / [`Occupation`](#hired.taxonomy.Occupation). |
