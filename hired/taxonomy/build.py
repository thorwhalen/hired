"""Build the skills taxonomy into the data root, and load it back as a :class:`SkillIndex`.

:func:`build_skill_index` fetches the sources (ESCO via its API, O*NET via its
archive — see :mod:`hired.taxonomy.sources`), computes skill relatedness from
occupational co-occurrence (:mod:`hired.taxonomy.graph`), optionally embeds every
label (the ``embeddings`` extra), and writes the result under
``<data root>/taxonomy/`` with a ``NOTICE.md`` carrying the CC BY 4.0
attribution. Raw pages and archives are cached under ``taxonomy/raw/``, so an
interrupted build resumes and a rebuild is offline (``refresh=True`` re-fetches).

A full ESCO fetch takes tens of minutes (the occupation pages are slow); O*NET is
one ~13 MB download. Nothing here runs at import time.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Sequence
from typing import Any

from hired.persistence.base import (
    bytes_store,
    json_store,
    read_json_file,
    write_json_file,
    write_text_file,
)
from hired.taxonomy.base import (
    ATTRIBUTION,
    EDGES_FILE,
    META_FILE,
    NODES_FILE,
    NOTICE_FILE,
    OCCUPATIONS_FILE,
    RAW_DIR,
    VECTOR_IDS_FILE,
    VECTORS_FILE,
    SkillNode,
    dump_models,
    taxonomy_dir,
)
from hired.taxonomy.embed import (
    DFLT_EMBEDDING_MODEL,
    Embedder,
    require_numpy,
    sentence_transformer_embedder,
)
from hired.taxonomy.graph import merge_edges, relatedness_edges
from hired.taxonomy.index import SkillIndex
from hired.taxonomy.sources import (
    DFLT_ONET_VERSION,
    GetBytes,
    GetJson,
    Progress,
    fetch_esco,
    fetch_onet,
)

SOURCES = ("esco", "onet")

_NOT_BUILT = (
    "No skills taxonomy at {path}. Build it once (downloads ESCO + O*NET, "
    "tens of minutes):\n    hired build-skill-index\n"
    "or, in Python: hired.taxonomy.build_skill_index()"
)


def build_skill_index(
    *,
    sources: Sequence[str] = SOURCES,
    embeddings: bool = False,
    embedder: Embedder | None = None,
    embedding_model: str = DFLT_EMBEDDING_MODEL,
    root: str | None = None,
    refresh: bool = False,
    onet_version: str = DFLT_ONET_VERSION,
    graph_kwargs: dict[str, Any] | None = None,
    get_json: GetJson | None = None,
    get_bytes: GetBytes | None = None,
    progress: Progress | None = None,
) -> dict[str, Any]:
    """Fetch, compute and persist the taxonomy; return its ``meta`` summary.

    ``embeddings=True`` (or an explicit ``embedder``) also stores one vector per
    node label. ``graph_kwargs`` go to :func:`~hired.taxonomy.graph.relatedness_edges`.
    """
    unknown = set(sources) - set(SOURCES)
    if unknown or not sources:
        raise ValueError(
            f"sources must be a non-empty subset of {SOURCES}, got {sources!r}"
        )
    raw_dir = taxonomy_dir(RAW_DIR, root=root)
    if refresh:
        shutil.rmtree(raw_dir, ignore_errors=True)
        raw_dir = taxonomy_dir(RAW_DIR, root=root)

    nodes: list[SkillNode] = []
    occupations = []
    edge_sets = []
    for source in sources:
        if source == "esco":
            src_nodes, src_occs = fetch_esco(
                get_json=get_json, cache=json_store(raw_dir), progress=progress
            )
        else:
            src_nodes, src_occs = fetch_onet(
                get_bytes=get_bytes,
                cache=bytes_store(raw_dir),
                version=onet_version,
                progress=progress,
            )
        nodes += src_nodes
        occupations += src_occs
        edge_sets.append(relatedness_edges(src_occs, **(graph_kwargs or {})))
    edges = merge_edges(*edge_sets)

    path = taxonomy_dir(root=root)
    write_json_file(os.path.join(path, NODES_FILE), dump_models(nodes))
    write_json_file(os.path.join(path, OCCUPATIONS_FILE), dump_models(occupations))
    write_json_file(os.path.join(path, EDGES_FILE), edges)
    write_text_file(os.path.join(path, NOTICE_FILE), ATTRIBUTION)

    model_name = None
    if embeddings or embedder is not None:
        if progress:
            progress(f"embedding {len(nodes)} labels")
        model_name = None if embedder is not None else embedding_model
        embed = embedder or sentence_transformer_embedder(embedding_model)
        np = require_numpy()
        vectors = np.asarray(embed([n.label for n in nodes]), dtype="float16")
        np.save(os.path.join(path, VECTORS_FILE), vectors)
        write_json_file(os.path.join(path, VECTOR_IDS_FILE), [n.id for n in nodes])
    else:
        for stale in (VECTORS_FILE, VECTOR_IDS_FILE):
            if os.path.exists(os.path.join(path, stale)):
                os.remove(os.path.join(path, stale))

    from hired.candidate.base import _utcnow

    meta = {
        "built_at": _utcnow(),
        "sources": list(sources),
        "onet_version": onet_version if "onet" in sources else None,
        "nodes": len(nodes),
        "occupations": len(occupations),
        "linked_nodes": len(edges),
        "edges": sum(len(v) for v in edges.values()) // 2,
        "embedding_model": model_name or ("custom" if embedder else None),
    }
    write_json_file(os.path.join(path, META_FILE), meta)
    return meta


def load_skill_index(
    *, root: str | None = None, embedder: Embedder | str | None = "auto"
) -> SkillIndex:
    """Load the built taxonomy (raises ``FileNotFoundError`` with the build hint).

    ``embedder="auto"`` uses the stored embedding model for *query* text when the
    taxonomy has vectors and the ``embeddings`` extra is installed (loaded on first
    use); pass ``None`` to compare stored vectors only, or any embedder.
    """
    path = taxonomy_dir(root=root, make=False)
    raw_nodes = read_json_file(os.path.join(path, NODES_FILE))
    if raw_nodes is None:
        raise FileNotFoundError(_NOT_BUILT.format(path=path))
    edges = {
        k: [tuple(link) for link in v]
        for k, v in (read_json_file(os.path.join(path, EDGES_FILE)) or {}).items()
    }
    meta = read_json_file(os.path.join(path, META_FILE)) or {}
    vectors = vector_ids = None
    if os.path.exists(os.path.join(path, VECTORS_FILE)):
        vectors = require_numpy().load(os.path.join(path, VECTORS_FILE))
        vector_ids = read_json_file(os.path.join(path, VECTOR_IDS_FILE))
    if embedder == "auto":
        embedder = (
            _lazy_embedder(meta.get("embedding_model")) if vectors is not None else None
        )
    return SkillIndex(
        [SkillNode.model_validate(n) for n in raw_nodes],
        edges,
        vectors=vectors,
        vector_ids=vector_ids,
        embedder=embedder,
        meta=meta,
    )


def _lazy_embedder(model_name: str | None) -> Embedder | None:
    """An embedder that loads ``model_name`` on first call (None if not a known model)."""
    if not model_name or model_name == "custom":
        return None
    loaded: list[Embedder] = []

    def embed(texts):
        if not loaded:
            loaded.append(sentence_transformer_embedder(model_name))
        return loaded[0](texts)

    return embed
