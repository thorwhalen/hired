"""Query a built skills taxonomy: resolve skill text, score adjacency (Axis A).

:class:`SkillIndex` answers *how close is the candidate's skill X to the job's
requirement Y?* by blending two signals::

    proximity = alpha * cosine(label vectors) + (1 - alpha) * graph relatedness

- **graph relatedness** (always available): the co-occurrence ``SR`` score of
  :mod:`hired.taxonomy.graph`, direct or through one shared neighbour (the
  ``via`` skill, which makes a readable adjacency basis). Labels that name the
  same concept in ESCO and O*NET are treated as one node.
- **cosine** (with the ``embeddings`` extra): similarity of label embeddings,
  which also covers skills absent from both taxonomies. Without vectors,
  ``alpha`` is effectively 0 and the score is graph-only — :class:`Proximity`
  records the ``alpha`` actually used.
- **bridges** across sources: the ESCO and O*NET graphs share no occupations,
  so a node is also linked to its closest nodes in the *other* sources (token
  overlap of labels, then embedding similarity), weighted by that closeness.
  Graph relatedness then propagates through the bridge. When the two skills
  still have no source in common, the graph has no say and the score falls
  back to cosine alone (``alpha`` 1), rather than reading the missing evidence
  as unrelatedness.

The index *suggests*; the analyst (skill or LLM) still decides the record's
``match_type`` / ``transferability``. :meth:`SkillIndex.suggest_adjacency` ranks
the candidate's skills against one requirement and proposes a
:class:`~hired.alignment.base.Transferability` band for each.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from hired.alignment.base import Transferability
from hired.taxonomy.base import SkillNode, normalize_label
from hired.taxonomy.embed import Embedder, unit_rows

#: Score floors for each transferability band, strongest first; below the last,
#: ``LIMITED``. Keyword-overridable wherever bands are used.
DFLT_TRANSFER_BANDS: tuple[tuple[float, Transferability], ...] = (
    (0.75, Transferability.DIRECT),
    (0.5, Transferability.CONTEXTUAL),
    (0.3, Transferability.FOUNDATIONAL),
)


def transferability_band(
    score: float,
    *,
    bands: Sequence[tuple[float, Transferability]] = DFLT_TRANSFER_BANDS,
) -> Transferability:
    """The :class:`Transferability` band a proximity ``score`` falls in.

    >>> transferability_band(0.8).value, transferability_band(0.1).value
    ('direct', 'limited')
    """
    for floor, band in bands:
        if score >= floor:
            return band
    return Transferability.LIMITED


@dataclass(frozen=True)
class Match:
    """A taxonomy node matched to a piece of text."""

    node: SkillNode
    score: float  # 1.0 for an exact label match
    how: str  # "id" | "label" | "alt_label" | "tokens" | "embedding"


@dataclass(frozen=True)
class Proximity:
    """How close two skills are, with the evidence behind the number."""

    a: str
    b: str
    score: float
    graph: float
    cosine: float | None
    alpha: float  # the weight actually given to cosine (0 when unavailable)
    a_node: SkillNode | None = None
    b_node: SkillNode | None = None
    via: SkillNode | None = None

    def transferability(self, **kwargs: Any) -> Transferability:
        """The band :attr:`score` falls in (see :func:`transferability_band`)."""
        return transferability_band(self.score, **kwargs)

    @property
    def basis(self) -> str:
        """One readable line of evidence, for a record's ``adjacency_basis``."""
        bits = []
        if self.a_node and self.b_node and self.a_node.id == self.b_node.id:
            bits.append(f"same taxonomy concept '{self.a_node.label}'")
        elif self.graph > 0 and self.via is not None:
            bits.append(
                f"both relate to '{self.via.label}' ({self.via.source}) "
                f"in occupations (relatedness {self.graph:.2f})"
            )
        elif self.graph > 0:
            bits.append(
                f"co-required by the same occupations (relatedness {self.graph:.2f})"
            )
        if self.cosine is not None:
            bits.append(f"label similarity {self.cosine:.2f}")
        names = " ↔ ".join(
            f"'{n.label}' ({n.source})" if n else f"'{t}' (not in taxonomy)"
            for t, n in ((self.a, self.a_node), (self.b, self.b_node))
        )
        return f"{names}: " + ("; ".join(bits) or "no shared evidence")


class SkillIndex:
    """Lookup and adjacency over taxonomy nodes, edges and (optional) vectors.

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
    """

    def __init__(
        self,
        nodes: Iterable[SkillNode],
        edges: dict[str, list[tuple[str, float]]],
        *,
        vectors: Any = None,
        vector_ids: Sequence[str] | None = None,
        embedder: Embedder | None = None,
        meta: dict[str, Any] | None = None,
        bridge_k: int = 3,
        bridge_min_score: float = 0.5,
        cross_source_fallback: bool = True,
    ) -> None:
        self.nodes: dict[str, SkillNode] = {n.id: n for n in nodes}
        self._edges = edges
        self._vectors = vectors
        self._vector_row = {v: i for i, v in enumerate(vector_ids or [])}
        self.embedder = embedder
        self.meta: dict[str, Any] = meta or {}
        self.bridge_k = bridge_k
        self.bridge_min_score = bridge_min_score
        self.cross_source_fallback = cross_source_fallback
        self._bridge_cache: dict[str, dict[str, float]] = {}

    def __len__(self) -> int:
        return len(self.nodes)

    # --- label indexes (built on first use) --------------------------------
    @cached_property
    def _by_label(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for n in self.nodes.values():
            out.setdefault(normalize_label(n.label), []).append(n.id)
        return out

    @cached_property
    def _by_alt(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for n in self.nodes.values():
            for alt in n.alt_labels:
                out.setdefault(normalize_label(alt), []).append(n.id)
        return out

    @cached_property
    def _by_token(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for n in self.nodes.values():
            for label in (n.label, *n.alt_labels):
                for tok in normalize_label(label).split():
                    out.setdefault(tok, set()).add(n.id)
        return out

    @cached_property
    def _unit_vectors(self):
        return None if self._vectors is None else unit_rows(self._vectors)

    # --- lookup ------------------------------------------------------------
    def lookup(self, text: str, *, k: int = 5, min_score: float = 0.5) -> list[Match]:
        """Nodes best matching ``text``: exact label, alt label, token overlap, embedding."""
        if text in self.nodes:
            return [Match(self.nodes[text], 1.0, "id")]
        key = normalize_label(text)
        exact = [
            Match(self.nodes[i], 1.0, "label") for i in self._by_label.get(key, [])
        ]
        exact += [
            Match(self.nodes[i], 1.0, "alt_label")
            for i in self._by_alt.get(key, [])
            if i not in {m.node.id for m in exact}
        ]
        if exact:
            return exact[:k]
        matches = self._token_matches(key, k=k, min_score=min_score)
        if not matches and self._unit_vectors is not None and self.embedder is not None:
            matches = self._embedding_matches(text, k=k, min_score=min_score)
        return matches

    def _token_matches(self, key: str, *, k: int, min_score: float) -> list[Match]:
        query = set(key.split())
        if not query:
            return []
        candidates = set().union(*(self._by_token.get(t, set()) for t in query))
        scored = []
        for node_id in candidates:
            node = self.nodes[node_id]
            best = max(
                len(query & (toks := set(normalize_label(lbl).split())))
                / len(query | toks)
                for lbl in (node.label, *node.alt_labels)
            )
            if best >= min_score:
                scored.append(Match(node, round(best, 4), "tokens"))
        return sorted(scored, key=lambda m: (-m.score, m.node.label))[:k]

    def _embedding_matches(self, text: str, *, k: int, min_score: float) -> list[Match]:
        query = unit_rows(self.embedder([text]))[0]
        sims = self._unit_vectors @ query
        ids = list(self._vector_row)
        order = sims.argsort()[::-1][:k]
        return [
            Match(self.nodes[ids[i]], round(float(sims[i]), 4), "embedding")
            for i in order
            if sims[i] >= min_score and ids[i] in self.nodes
        ]

    def resolve(self, text: str, *, min_score: float = 0.5) -> SkillNode | None:
        """The single best node for ``text`` (or ``None``)."""
        found = self.lookup(text, k=1, min_score=min_score)
        return found[0].node if found else None

    # --- graph -------------------------------------------------------------
    def _equivalents(self, node_id: str) -> set[str]:
        """Ids naming the same concept (shared label, or one's label is the other's alt)."""
        node = self.nodes[node_id]
        keys = {normalize_label(node.label)}
        same = {node_id}
        for key in keys:
            same.update(self._by_label.get(key, []))
            same.update(self._by_alt.get(key, []))
        for alt in node.alt_labels:
            same.update(self._by_label.get(normalize_label(alt), []))
        return same

    def _links(self, node_id: str) -> dict[str, float]:
        return dict(self._edges.get(node_id, ()))

    def _bridges(self, node_id: str) -> dict[str, float]:
        """Closest nodes in *other* sources, weighted by label closeness (cached)."""
        if node_id in self._bridge_cache:
            return self._bridge_cache[node_id]
        node = self.nodes[node_id]
        k, floor = self.bridge_k, self.bridge_min_score
        found: dict[str, float] = {}
        for label in (node.label, *node.alt_labels):
            key = normalize_label(label)
            for m in self._token_matches(key, k=k * 4, min_score=floor):
                if m.node.source != node.source:
                    found[m.node.id] = max(found.get(m.node.id, 0.0), m.score)
        row = self._vector_row.get(node_id)
        if len(found) < k and row is not None and self._unit_vectors is not None:
            ids = list(self._vector_row)
            sims = self._unit_vectors @ self._unit_vectors[row]
            for i in sims.argsort()[::-1][: k * 4]:
                other = ids[i]
                if sims[i] < floor:
                    break
                if other in self.nodes and self.nodes[other].source != node.source:
                    found.setdefault(other, round(float(sims[i]), 4))
        top = dict(sorted(found.items(), key=lambda kv: -kv[1])[:k])
        self._bridge_cache[node_id] = top
        return top

    def _weighted_equivalents(self, node_id: str) -> dict[str, float]:
        """Equivalent ids (weight 1) plus their cross-source bridges (weight < 1)."""
        out = dict.fromkeys(self._equivalents(node_id), 1.0)
        for x in list(out):
            for other, w in self._bridges(x).items():
                if w > out.get(other, 0.0):
                    out[other] = w
        return out

    def _sources(self, ids: Iterable[str]) -> set[str]:
        return {self.nodes[i].source for i in ids if i in self.nodes}

    def graph_score(self, a_id: str, b_id: str) -> tuple[float, str | None]:
        """Relatedness of two nodes (direct, or via one shared neighbour) and the via id.

        Equivalent nodes count fully; cross-source bridges count with their weight.
        """
        a_set = self._weighted_equivalents(a_id)
        b_set = self._weighted_equivalents(b_id)
        best, via = 0.0, None
        for x, wx in a_set.items():
            x_links = self._links(x)
            for y, wy in b_set.items():
                w = wx * wy
                if x == y:
                    if w > best:  # a bridge lands on the other side itself
                        best, via = w, (None if w == 1.0 else x)
                    continue
                if w * x_links.get(y, 0.0) > best:
                    best, via = w * x_links[y], None
                y_links = self._links(y)
                for mid in x_links.keys() & y_links.keys():
                    score = w * x_links[mid] * y_links[mid]
                    if score > best:
                        best, via = score, mid
        return round(best, 4), via

    def graph_comparable(self, a_id: str, b_id: str) -> bool:
        """Whether the graph can speak to this pair: some source holds both sides."""
        return bool(
            self._sources(self._weighted_equivalents(a_id))
            & self._sources(self._weighted_equivalents(b_id))
        )

    def neighbors(self, text: str, *, k: int = 10) -> list[tuple[SkillNode, float]]:
        """The skills most related to ``text`` in the co-occurrence graph."""
        node = self.resolve(text)
        if node is None:
            return []
        merged: dict[str, float] = {}
        for x in self._equivalents(node.id):
            for other, score in self._edges.get(x, ()):
                merged[other] = max(merged.get(other, 0.0), score)
        ranked = sorted(merged.items(), key=lambda kv: -kv[1])[:k]
        return [(self.nodes[i], s) for i, s in ranked if i in self.nodes]

    # --- cosine ------------------------------------------------------------
    def _vector(self, text: str, node: SkillNode | None):
        if node is not None and self._unit_vectors is not None:
            row = self._vector_row.get(node.id)
            if row is not None:
                return self._unit_vectors[row]
        if self.embedder is not None:
            return unit_rows(self.embedder([text]))[0]
        return None

    # --- proximity ---------------------------------------------------------
    def proximity(self, a: str, b: str, *, alpha: float = 0.5) -> Proximity:
        """Blended adjacency of two skill texts (or node ids)."""
        a_node, b_node = self.resolve(a), self.resolve(b)
        graph, via = (
            self.graph_score(a_node.id, b_node.id) if a_node and b_node else (0.0, None)
        )
        va, vb = self._vector(a, a_node), self._vector(b, b_node)
        cosine = None if va is None or vb is None else round(float(va @ vb), 4)
        used = alpha if cosine is not None else 0.0
        if (
            cosine is not None
            and self.cross_source_fallback
            and graph == 0.0
            and not (a_node and b_node and self.graph_comparable(a_node.id, b_node.id))
        ):
            used = 1.0  # no source holds both: missing graph evidence, not unrelatedness
        score = used * max(cosine or 0.0, 0.0) + (1 - used) * graph
        return Proximity(
            a=a,
            b=b,
            score=round(score, 4),
            graph=graph,
            cosine=cosine,
            alpha=used,
            a_node=a_node,
            b_node=b_node,
            via=self.nodes.get(via) if via else None,
        )

    def suggest_adjacency(
        self,
        requirement: str,
        candidate_skills: Iterable[str],
        *,
        k: int = 3,
        alpha: float = 0.5,
    ) -> list[Proximity]:
        """The candidate's skills closest to ``requirement``, strongest first."""
        scored = [
            self.proximity(skill, requirement, alpha=alpha)
            for skill in candidate_skills
        ]
        return sorted(scored, key=lambda p: -p.score)[:k]
