"""Schemas and on-disk layout for the skills taxonomy (ESCO + O*NET).

A taxonomy is two things:

- **nodes** — skills (and, for O*NET, technologies, knowledge areas, abilities),
  each a :class:`SkillNode` with a stable id (``esco:<uuid>``,
  ``onet:tech:<slug>``, ``onet:<element-id>``), a preferred label, alternative
  labels, and a KSAO ``kind``;
- **occupations** — each an :class:`Occupation` listing the nodes it requires
  (``essential``) or may use (``optional``). Skill *adjacency* is learned from
  which skills occupations require together (see :mod:`hired.taxonomy.graph`).

The built taxonomy is shared reference data, not candidate data, so it lives at
``<data root>/taxonomy/`` (not under ``users/``). It is built on demand by
:func:`hired.taxonomy.build_skill_index` — nothing is vendored into the package.

Attribution (both sources are CC BY 4.0) is in :data:`ATTRIBUTION` and is written
next to the data as ``NOTICE.md``.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

from pydantic import BaseModel, Field

from hired.persistence.base import app_data_dir

TAXONOMY_DIR = "taxonomy"

# --- file layout (single source of truth) ----------------------------------- #
NODES_FILE = "nodes.json"
OCCUPATIONS_FILE = "occupations.json"
EDGES_FILE = "edges.json"
VECTORS_FILE = "vectors.npy"
VECTOR_IDS_FILE = "vector_ids.json"
META_FILE = "meta.json"
NOTICE_FILE = "NOTICE.md"
RAW_DIR = "raw"  # cached source pages/archives, so an interrupted build resumes

_ESCO_CREDIT = """\
- **ESCO** — European Skills, Competences, Qualifications and Occupations.
  © European Union, https://esco.ec.europa.eu/. Retrieved through the ESCO API.
  Licence notice: https://esco.ec.europa.eu/en/copyright-notice-esco-skills-competences
"""

_ONET_CREDIT = """\
- **O*NET** — O*NET {version} Database by the U.S. Department of Labor, Employment
  and Training Administration (USDOL/ETA). Used under the CC BY 4.0 license.
  O*NET® is a trademark of USDOL/ETA. This data was modified (see below); USDOL/ETA
  has not approved, endorsed, or tested these modifications.
  https://www.onetcenter.org/database.html
"""


def attribution(
    sources: tuple[str, ...] | list[str] = ("esco", "onet"), *, onet_version: str = "30.0"
) -> str:
    """The CC BY 4.0 notice for the sources a build used (written as ``NOTICE.md``)."""
    credits = ([_ESCO_CREDIT] if "esco" in sources else []) + (
        [_ONET_CREDIT.format(version=onet_version.replace("_", "."))]
        if "onet" in sources
        else []
    )
    return (
        "# Skills taxonomy — attribution\n\n"
        "This directory holds data derived from the sources below, licensed under\n"
        "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/):\n\n"
        + "".join(credits)
        + "\nChanges made: labels were normalised, occupation↔skill links were used to\n"
        "compute skill-relatedness scores, and (optionally) label embeddings were added.\n"
    )


ATTRIBUTION = attribution()


def taxonomy_dir(*subpaths: str, root: str | None = None, make: bool = True) -> str:
    """Directory of the built taxonomy: ``root`` or ``<data root>/taxonomy``."""
    base = root or app_data_dir(TAXONOMY_DIR, make=make)
    path = os.path.join(base, *subpaths)
    if make:
        os.makedirs(path, exist_ok=True)
    return path


def normalize_label(text: str) -> str:
    """Case-, accent- and punctuation-insensitive form of a label, for matching.

    >>> normalize_label('  Machine-Learning (ML)! ')
    'machine learning ml'
    >>> normalize_label('Café')
    'cafe'
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # keep a few symbols that carry meaning in tech names (C++, C#, .NET, Node.js)
    text = re.sub(r"[^\w+#.]+", " ", text.lower())
    text = re.sub(r"(?<!\w)\.|\.(?!\w)", " ", text)  # drop sentence dots only
    return " ".join(text.replace("_", " ").split())


class SkillNode(BaseModel):
    """One skill-like concept from a source taxonomy."""

    id: str
    label: str
    alt_labels: list[str] = Field(default_factory=list)
    source: str  # "esco" | "onet"
    #: KSAO kind: "skill", "knowledge", "ability", "technology", "competence", ...
    kind: str = "skill"
    #: ESCO skill-reuse level ("transversal", "cross-sector", "sector-specific",
    #: "occupation-specific"), when known — a transferability hint.
    reuse_level: str | None = None
    uri: str | None = None


class Occupation(BaseModel):
    """An occupation and the skill nodes it requires or may use."""

    id: str
    label: str
    source: str
    essential: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)


def dump_models(models: "list[BaseModel]") -> list[dict[str, Any]]:
    """JSON-able dicts for a list of models, without empty/default noise."""
    return [m.model_dump(mode="json", exclude_defaults=True) for m in models]
