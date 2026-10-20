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
  so a node is also linked to its closest *connected* nodes in the other sources
  (label token overlap or embedding similarity, whichever is higher), weighted by
  that closeness. Graph relatedness then propagates through the bridge.
- **graph trust**: a graph score of 0 (no path among each node's strongest links)
  is missing evidence more often than unrelatedness, so cosine's weight grows as
  the graph evidence weakens: ``alpha`` is used as given from a graph score of
  ``graph_trust`` up, and rises linearly to 1 (cosine alone) at a graph score of 0,
  so weak evidence never ranks below none.

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
#: ``LIMITED``. Keyword-overridable wherever bands are used. Calibrated on the real
#: ESCO + O*NET build (MiniLM vectors, #10): clearly unrelated pairs (cooking~Python,
#: welding~accounting, carpentry~software testing) score 0.06-0.11 and loosely related
#: ones 0.2; Python~machine learning 0.27, Excel~financial analysis 0.39,
#: TensorFlow~deep learning 0.54, SQL~data analytics 0.63, Java~Python 0.66.
#: Ranking weight of a node's ``kind`` when free text resolves by token overlap or
#: embedding (exact label matches are unaffected): a short query such as "sales" or
#: "deep learning" names a skill more often than a product, so O*NET technology nodes
#: ("Sales software", "NeuralWare") rank behind skill/knowledge nodes (#58).
DFLT_KIND_WEIGHTS: dict[str, float] = {"technology": 0.8}

DFLT_TRANSFER_BANDS: tuple[tuple[float, Transferability], ...] = (
    (0.75, Transferability.DIRECT),
    (0.5, Transferability.CONTEXTUAL),
    (0.25, Transferability.FOUNDATIONAL),
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
        graph_trust: float = 0.2,
        kind_weights: dict[str, float] | None = None,
    ) -> None:
        self.nodes: dict[str, SkillNode] = {n.id: n for n in nodes}
        self._edges = edges
        self._vectors = vectors
        self._vector_row = {v: i for i, v in enumerate(vector_ids or [])}
        self.embedder = embedder
        self.meta: dict[str, Any] = meta or {}
        self.bridge_k = bridge_k
        self.bridge_min_score = bridge_min_score
        self.graph_trust = graph_trust
        self.kind_weights = DFLT_KIND_WEIGHTS if kind_weights is None else kind_weights
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
        """Nodes best matching ``text``: exact label, alt label, token overlap, embedding.

        Token and embedding matches are ranked by ``kind_weights`` times their
        similarity to ``text``: the label embedding's cosine when vectors exist
        (so a token overlap that is only a shared word ranks low), else the token
        score. ``Match.score`` stays the stage's own score.

        >>> from hired.taxonomy.base import SkillNode
        >>> idx = SkillIndex([
        ...     SkillNode(id='o:s', label='Sales software', source='o', kind='technology'),
        ...     SkillNode(id='e:s', label='sales activities', source='e'),
        ... ], {})
        >>> idx.resolve('sales').label
        'sales activities'
        """
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
        matches = self._token_matches(key, k=None, min_score=min_score)
        if not matches and self._unit_vectors is not None and self.embedder is not None:
            matches = self._embedding_matches(text, k=k, min_score=min_score)
        return self._ranked(text, matches)[:k]

    def _ranked(self, text: str, matches: list[Match]) -> list[Match]:
        """``matches`` by kind weight times similarity to ``text`` (see ``lookup``)."""
        similarity = {m.node.id: m.score for m in matches}
        if matches and matches[0].how == "tokens" and self._can_embed:
            query = unit_rows(self.embedder([text]))[0]
            for m in matches:
                if (row := self._vector_row.get(m.node.id)) is not None:
                    similarity[m.node.id] = float(self._unit_vectors[row] @ query)

        def rank(m: Match) -> tuple:
            weight = self.kind_weights.get(m.node.kind, 1.0)
            return (-weight * similarity[m.node.id], -m.score, m.node.label.lower())

        return sorted(matches, key=rank)

    @property
    def _can_embed(self) -> bool:
        return self._unit_vectors is not None and self.embedder is not None

    def _token_matches(
        self, key: str, *, k: int | None, min_score: float
    ) -> list[Match]:
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
        """Closest connected nodes in *other* sources, weighted by closeness (cached)."""
        if node_id in self._bridge_cache:
            return self._bridge_cache[node_id]
        node = self.nodes[node_id]
        k, floor = self.bridge_k, self.bridge_min_score

        def usable(other: str) -> bool:  # a bridge only helps if the graph goes on
            n = self.nodes.get(other)
            return (
                n is not None
                and n.source != node.source
                and bool(self._edges.get(other))
            )

        found: dict[str, float] = {}
        if k > 0:
            for label in (node.label, *node.alt_labels):
                for m in self._token_matches(
                    normalize_label(label), k=k * 8, min_score=floor
                ):
                    if usable(m.node.id):
                        found[m.node.id] = max(found.get(m.node.id, 0.0), m.score)
            row = self._vector_row.get(node_id)
            if row is not None and self._unit_vectors is not None:
                ids = list(self._vector_row)
                sims = self._unit_vectors @ self._unit_vectors[row]
                for i in sims.argsort()[::-1][: k * 50]:
                    if sims[i] < floor:
                        break
                    if usable(ids[i]):
                        found[ids[i]] = max(
                            found.get(ids[i], 0.0), round(float(sims[i]), 4)
                        )
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
                    if w > best:  # equivalent, or a bridge lands on the other side
                        best, via = w, None
                    continue
                if w * x_links.get(y, 0.0) > best:
                    best, via = w * x_links[y], None
                y_links = self._links(y)
                for mid in x_links.keys() & y_links.keys():
                    score = w * x_links[mid] * y_links[mid]
                    if score > best:
                        best, via = score, mid
        return round(best, 4), via

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
        if cosine is not None and self.graph_trust > 0 and graph < self.graph_trust:
            # weak graph evidence: cosine's weight rises to 1 as the graph score -> 0
            used = 1 - (1 - alpha) * graph / self.graph_trust
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
