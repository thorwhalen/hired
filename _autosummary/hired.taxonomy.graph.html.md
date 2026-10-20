# hired.taxonomy.graph

Skill relatedness from occupational co-occurrence (pure Python, no numpy).

Two skills are *related* when occupations require them together more often than
chance predicts. For skills `i` and `j` over `N` occupations, with
`n_i` the (weighted) number of occupations using `i` and `C_ij` the
(weighted) number using both:

```default
RCA_ij = C_ij / (n_i * n_j / N)          # observed / expected co-occurrence
SR_ij  = (RCA_ij - 1) / (RCA_ij + 1)     # in (-1, 1); clipped to [0, 1]
```

`SR` is the skill-relatedness measure of Neffke & Henning (2013), which the
research note recommends (`misc/docs/research/skills-taxonomy-and-adjacency.md`).
Essential links weigh `1`, optional ones `optional_weight`. Pairs seen in
fewer than `min_cooccurrence` occupations are dropped (one shared occupation
between two rare skills gives a huge, meaningless ratio), and each skill keeps
only its `top_k` strongest links.

```pycon
>>> from hired.taxonomy.base import Occupation
>>> occs = [Occupation(id=f'o{i}', label='', source='t', essential=es)
...         for i, es in enumerate([['py', 'ml'], ['py', 'ml'], ['py', 'web'],
...                                 ['cook', 'serve'], ['cook', 'serve']])]
>>> edges = relatedness_edges(occs)
>>> edges['py'][0][0], edges['py'][0][1] > 0
('ml', True)
>>> 'cook' in dict(edges['py'])
False
```

### Module Attributes

| [`Edges`](#hired.taxonomy.graph.Edges)   | `{node_id: [(other_id, score), ...]}`, strongest first.   |
|----------------------------------------------------------|-----------------------------------------------------------|

### Functions

| [`merge_edges`](#hired.taxonomy.graph.merge_edges)(\*edge_sets)                  | Union of edge sets over disjoint id spaces (e.g. ESCO and O\*NET).     |
|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`relatedness_edges`](#hired.taxonomy.graph.relatedness_edges)(occupations, \*[, ...]) | Skill-relatedness edges (`SR` in `(min_score, 1]`) from co-occurrence. |

### hired.taxonomy.graph.Edges

`{node_id: [(other_id, score), ...]}`, strongest first.

alias of [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

### hired.taxonomy.graph.merge_edges(\*edge_sets)

Union of edge sets over disjoint id spaces (e.g. ESCO and O\*NET).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

### hired.taxonomy.graph.relatedness_edges(occupations, , optional_weight=0.5, min_cooccurrence=2.0, top_k=30, min_score=0.0)

Skill-relatedness edges (`SR` in `(min_score, 1]`) from co-occurrence.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]]
