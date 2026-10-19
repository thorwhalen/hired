"""Skills taxonomy (ESCO + O*NET) and skill adjacency for alignment's Axis A.

Strengthens *transfer distance* beyond keyword match and LLM judgment with two
signals, blended as ``alpha * cosine + (1 - alpha) * graph``:

- a **relatedness graph** learned from which skills occupations require together
  (ESCO occupation↔skill links, O*NET technology and K/S/A ratings) — pure Python;
- **label embeddings** (the ``embeddings`` extra) for similarity and for skills
  absent from both taxonomies.

Nothing is vendored: build the taxonomy once into the data root, then query it::

    from hired.taxonomy import build_skill_index, load_skill_index
    build_skill_index()                 # or `hired build-skill-index`; tens of minutes
    idx = load_skill_index()
    idx.suggest_adjacency("PyTorch", ["TensorFlow", "Excel"])

ESCO (© European Union) and O*NET (USDOL/ETA) data are used under CC BY 4.0; see
:data:`hired.taxonomy.base.ATTRIBUTION`, written next to the data as ``NOTICE.md``.
Research basis: ``misc/docs/research/skills-taxonomy-and-adjacency.md``.
"""

from hired.taxonomy.base import (
    ATTRIBUTION,
    Occupation,
    SkillNode,
    normalize_label,
    taxonomy_dir,
)
from hired.taxonomy.build import build_skill_index, load_skill_index
from hired.taxonomy.embed import Embedder, sentence_transformer_embedder
from hired.taxonomy.graph import merge_edges, relatedness_edges
from hired.taxonomy.index import (
    DFLT_TRANSFER_BANDS,
    Match,
    Proximity,
    SkillIndex,
    transferability_band,
)
from hired.taxonomy.sources import fetch_esco, fetch_onet, parse_onet_archive

__all__ = [
    "build_skill_index",
    "load_skill_index",
    "SkillIndex",
    "Proximity",
    "Match",
    "SkillNode",
    "Occupation",
    "Embedder",
    "sentence_transformer_embedder",
    "relatedness_edges",
    "merge_edges",
    "transferability_band",
    "DFLT_TRANSFER_BANDS",
    "fetch_esco",
    "fetch_onet",
    "parse_onet_archive",
    "normalize_label",
    "taxonomy_dir",
    "ATTRIBUTION",
]
