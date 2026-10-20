"""Skill relatedness from occupational co-occurrence (pure Python, no numpy).

Two skills are *related* when occupations require them together more often than
chance predicts. For skills ``i`` and ``j`` over ``N`` occupations, with
``n_i`` the (weighted) number of occupations using ``i`` and ``C_ij`` the
(weighted) number using both::

    RCA_ij = C_ij / (n_i * n_j / N)          # observed / expected co-occurrence
    SR_ij  = (RCA_ij - 1) / (RCA_ij + 1)     # in (-1, 1); clipped to [0, 1]

``SR`` is the skill-relatedness measure of Neffke & Henning (2013), which the
research note recommends (``misc/docs/research/skills-taxonomy-and-adjacency.md``).
Essential links weigh ``1``, optional ones ``optional_weight``. Pairs seen in
fewer than ``min_cooccurrence`` occupations are dropped (one shared occupation
between two rare skills gives a huge, meaningless ratio), and each skill keeps
only its ``top_k`` strongest links.

>>> from hired.taxonomy.base import Occupation
>>> occs = [Occupation(id=f'o{i}', label='', source='t', essential=es)
...         for i, es in enumerate([['py', 'ml'], ['py', 'ml'], ['py', 'web'],
...                                 ['cook', 'serve'], ['cook', 'serve']])]
>>> edges = relatedness_edges(occs)
>>> edges['py'][0][0], edges['py'][0][1] > 0
('ml', True)
>>> 'cook' in dict(edges['py'])
False
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

from hired.taxonomy.base import Occupation

#: ``{node_id: [(other_id, score), ...]}``, strongest first.
Edges = dict[str, list[tuple[str, float]]]


def _weighted_skills(occ: Occupation, optional_weight: float) -> dict[str, float]:
    weights = {s: optional_weight for s in occ.optional}
    weights.update({s: 1.0 for s in occ.essential})  # essential wins
    return weights


def relatedness_edges(
    occupations: Iterable[Occupation],
    *,
    optional_weight: float = 0.5,
    min_cooccurrence: float = 2.0,
    top_k: int = 30,
    min_score: float = 0.0,
) -> Edges:
    """Skill-relatedness edges (``SR`` in ``(min_score, 1]``) from co-occurrence."""
    n_occ = 0
    usage: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()
    for occ in occupations:
        weights = _weighted_skills(occ, optional_weight)
        if not weights:
            continue
        n_occ += 1
        usage.update(weights)
        ids = sorted(weights)
        for a_pos, a in enumerate(ids):
            wa = weights[a]
            for b in ids[a_pos + 1 :]:
                pairs[a, b] += wa * weights[b]

    edges: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), observed in pairs.items():
        if observed < min_cooccurrence:
            continue
        expected = usage[a] * usage[b] / n_occ
        rca = observed / expected
        score = (rca - 1) / (rca + 1)
        if score <= min_score:
            continue
        score = round(score, 4)
        edges[a].append((b, score))
        edges[b].append((a, score))
    return {
        node: sorted(links, key=lambda x: (-x[1], x[0]))[:top_k]
        for node, links in edges.items()
    }


def merge_edges(*edge_sets: Edges) -> Edges:
    """Union of edge sets over disjoint id spaces (e.g. ESCO and O*NET)."""
    merged: Edges = {}
    for edges in edge_sets:
        for node, links in edges.items():
            merged.setdefault(node, []).extend(links)
    return merged
