# hired.taxonomy.index

Query a built skills taxonomy: resolve skill text, score adjacency (Axis A).

[`SkillIndex`](#hired.taxonomy.index.SkillIndex) answers \*how close is the candidate’s skill X to the job’s
requirement Y?\* by blending two signals:

```default
proximity = alpha * cosine(label vectors) + (1 - alpha) * graph relatedness
```

- **graph relatedness** (always available): the co-occurrence `SR` score of
  [`hired.taxonomy.graph`](hired.taxonomy.graph.html.md#module-hired.taxonomy.graph), direct or through one shared neighbour (the
  > `via` skill, which makes a readable adjacency basis). Labels that name the
  > same concept in ESCO and O\*NET are treated as one node.
- **cosine** (with the `embeddings` extra): similarity of label embeddings,
  which also covers skills absent from both taxonomies. Without vectors,
  `alpha` is effectively 0 and the score is graph-only — [`Proximity`](#hired.taxonomy.index.Proximity)
  records the `alpha` actually used.
- **bridges** across sources: the ESCO and O\*NET graphs share no occupations,
  so a node is also linked to its closest *connected* nodes in the other sources
  (label token overlap or embedding similarity, whichever is higher), weighted by
  that closeness. Graph relatedness then propagates through the bridge.
- **graph trust**: a graph score of 0 (no path among each node’s strongest links)
  is missing evidence more often than unrelatedness, so cosine’s weight grows as
  the graph evidence weakens: `alpha` is used as given from a graph score of
  `graph_trust` up, and rises linearly to 1 (cosine alone) at a graph score of 0,
  so weak evidence never ranks below none.

The index *suggests*; the analyst (skill or LLM) still decides the record’s
`match_type` / `transferability`. [`SkillIndex.suggest_adjacency()`](#hired.taxonomy.index.SkillIndex.suggest_adjacency) ranks
the candidate’s skills against one requirement and proposes a
[`Transferability`](hired.alignment.base.html.md#hired.alignment.base.Transferability) band for each.

### Module Attributes

| [`DFLT_TRANSFER_BANDS`](#hired.taxonomy.index.DFLT_TRANSFER_BANDS)   | Score floors for each transferability band, strongest first; below the last, `LIMITED`.   |
|------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|

### Functions

| [`transferability_band`](#hired.taxonomy.index.transferability_band)(score, \*[, bands])   | The `Transferability` band a proximity `score` falls in.   |
|---------------------------------------------------------------------------------------------|------------------------------------------------------------|

### Classes

| [`Match`](#hired.taxonomy.index.Match)(node, score, how)                      | A taxonomy node matched to a piece of text.                             |
|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [`Proximity`](#hired.taxonomy.index.Proximity)(a, b, score, graph, cosine, alpha) | How close two skills are, with the evidence behind the number.          |
| [`SkillIndex`](#hired.taxonomy.index.SkillIndex)(nodes, edges, \*[, vectors, ...]) | Lookup and adjacency over taxonomy nodes, edges and (optional) vectors. |

### hired.taxonomy.index.DFLT_TRANSFER_BANDS *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[float](https://docs.python.org/3/builtins/functions.html#float), [Transferability](hired.alignment.base.html.md#hired.alignment.base.Transferability)], ...]* *= ((0.75, Transferability.DIRECT), (0.5, Transferability.CONTEXTUAL), (0.25, Transferability.FOUNDATIONAL))*

Score floors for each transferability band, strongest first; below the last,
`LIMITED`. Keyword-overridable wherever bands are used. Calibrated on the real
ESCO + O\*NET build (MiniLM vectors, #10): clearly unrelated pairs (cooking~Python,
welding~accounting, carpentry~software testing) score 0.06-0.11 and loosely related
ones 0.2; Python~machine learning 0.27, Excel~financial analysis 0.39,
TensorFlow~deep learning 0.54, SQL~data analytics 0.63, Java~Python 0.66.

### *class* hired.taxonomy.index.Match(node, score, how)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A taxonomy node matched to a piece of text.

### *class* hired.taxonomy.index.Proximity(a, b, score, graph, cosine, alpha, a_node=None, b_node=None, via=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How close two skills are, with the evidence behind the number.

#### *property* basis *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

One readable line of evidence, for a record’s `adjacency_basis`.

#### transferability(\*\*kwargs)

The band `score` falls in (see [`transferability_band()`](#hired.taxonomy.index.transferability_band)).

* **Return type:**
  [`Transferability`](hired.alignment.base.html.md#hired.alignment.base.Transferability)

### *class* hired.taxonomy.index.SkillIndex(nodes, edges, , vectors=None, vector_ids=None, embedder=None, meta=None, bridge_k=3, bridge_min_score=0.5, graph_trust=0.2)

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
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Match`](#hired.taxonomy.index.Match)]

#### neighbors(text, , k=10)

The skills most related to `text` in the co-occurrence graph.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

#### proximity(a, b, , alpha=0.5)

Blended adjacency of two skill texts (or node ids).

* **Return type:**
  [`Proximity`](#hired.taxonomy.index.Proximity)

#### resolve(text, , min_score=0.5)

The single best node for `text` (or `None`).

* **Return type:**
  [`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### suggest_adjacency(requirement, candidate_skills, , k=3, alpha=0.5)

The candidate’s skills closest to `requirement`, strongest first.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Proximity`](#hired.taxonomy.index.Proximity)]

### hired.taxonomy.index.transferability_band(score, , bands=((0.75, Transferability.DIRECT), (0.5, Transferability.CONTEXTUAL), (0.25, Transferability.FOUNDATIONAL)))

The `Transferability` band a proximity `score` falls in.

```pycon
>>> transferability_band(0.8).value, transferability_band(0.1).value
('direct', 'limited')
```

* **Return type:**
  [`Transferability`](hired.alignment.base.html.md#hired.alignment.base.Transferability)
