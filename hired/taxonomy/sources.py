"""Fetch the ESCO and O*NET taxonomies into :class:`SkillNode` / :class:`Occupation`.

Network access is a seam: ``get_json(url, params) -> dict`` for the ESCO API and
``get_bytes(url) -> bytes`` for the O*NET archive, defaulting to ``requests``
(a core dependency) with timeouts and retries. Every page or archive fetched is
written to a ``cache`` mapping first, so an interrupted build resumes where it
stopped (the ESCO occupation pages are slow — tens of seconds each).

- **ESCO** (:func:`fetch_esco`): all skills (labels, alternative labels, skill
  type → KSAO kind, reuse level) and all occupations with their essential and
  optional skills, paged through the public search API (no key needed).
- **O*NET** (:func:`fetch_onet`): the text database archive. Technology examples
  (``Technology Skills.txt``; hot technologies essential, others optional) and the
  Skills / Knowledge / Abilities descriptors an occupation rates at or above
  ``min_importance`` on the importance scale.
"""

from __future__ import annotations

import io
import time
import zipfile
from collections.abc import Callable, MutableMapping
from typing import Any

from hired.taxonomy.base import Occupation, SkillNode, normalize_label

GetJson = Callable[[str, dict[str, Any]], dict[str, Any]]
GetBytes = Callable[[str], bytes]
Progress = Callable[[str], None]

ESCO_SEARCH_URL = "https://ec.europa.eu/esco/api/search"
ONET_ARCHIVE_URL = "https://www.onetcenter.org/dl_files/database/db_{version}_text.zip"
DFLT_ONET_VERSION = "30_0"

_ESCO_KIND = {"skill": "skill", "knowledge": "knowledge"}  # skill-type uri suffix
_ONET_KIND = {
    "Skills.txt": "skill",
    "Knowledge.txt": "knowledge",
    "Abilities.txt": "ability",
}


def _with_retries(fn: Callable[[], Any], *, retries: int, backoff: float) -> Any:
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == retries:
                raise
            time.sleep(backoff * 2**attempt)


def requests_get_json(
    url: str, params: dict[str, Any], *, timeout: float = 180, retries: int = 3
) -> dict[str, Any]:
    """Default ESCO fetcher: ``requests.get(...).json()`` with retries."""
    import requests

    def once():
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    return _with_retries(once, retries=retries, backoff=2.0)


def requests_get_bytes(url: str, *, timeout: float = 300, retries: int = 3) -> bytes:
    """Default O*NET fetcher: the archive's bytes, with retries."""
    import requests

    def once():
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content

    return _with_retries(once, retries=retries, backoff=2.0)


# --------------------------------------------------------------------------- #
# ESCO
# --------------------------------------------------------------------------- #
def _esco_id(uri: str) -> str:
    return "esco:" + uri.rstrip("/").rsplit("/", 1)[-1]


def _link_uris(record: dict[str, Any], rel: str) -> list[str]:
    """URIs of a relation, from ``_links`` (``full=true``) or a top-level list (brief)."""
    links = (record.get("_links") or {}).get(rel) or record.get(rel) or []
    if isinstance(links, (dict, str)):
        links = [links]
    return [
        link if isinstance(link, str) else link.get("uri")
        for link in links
        if isinstance(link, str) or link.get("uri")
    ]


def _suffix(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def _text(record: dict[str, Any], field: str, language: str) -> Any:
    """A language-keyed field (``full=true``), or the plain value (brief records)."""
    value = record.get(field)
    return value.get(language) if isinstance(value, dict) else value


def esco_skill_node(record: dict[str, Any], *, language: str = "en") -> SkillNode:
    """A :class:`SkillNode` from one ESCO search result (full or brief)."""
    label = _text(record, "preferredLabel", language) or record["title"]
    types = [_suffix(u) for u in _link_uris(record, "hasSkillType")]
    reuse = [_suffix(u) for u in _link_uris(record, "hasReuseLevel")]
    alts = _text(record, "alternativeLabel", language) or []
    return SkillNode(
        id=_esco_id(record["uri"]),
        label=label,
        alt_labels=[alts] if isinstance(alts, str) else list(alts),
        source="esco",
        kind=_ESCO_KIND.get(types[0], types[0]) if types else "skill",
        reuse_level=reuse[0] if reuse else None,
        uri=record["uri"],
    )


def esco_occupation(record: dict[str, Any], *, language: str = "en") -> Occupation:
    """An :class:`Occupation` from one ESCO search result (full or brief)."""
    return Occupation(
        id=_esco_id(record["uri"]),
        label=_text(record, "preferredLabel", language) or record["title"],
        source="esco",
        essential=[_esco_id(u) for u in _link_uris(record, "hasEssentialSkill")],
        optional=[_esco_id(u) for u in _link_uris(record, "hasOptionalSkill")],
    )


def _smaller_page_size(size: int) -> int:
    """The largest proper divisor of ``size`` (so split pages tile the same items)."""
    return next((d for d in range(size // 2, 0, -1) if size % d == 0), 1)


def _search_items(
    concept_type: str,
    page_no: int,
    page_size: int,
    *,
    get_json: GetJson,
    language: str,
    progress: Progress | None,
) -> dict[str, Any]:
    """One search page (``full=true``); on a server error, split it into smaller pages.

    The ESCO API fails a whole ``full=true`` page with HTTP 500 when one record in
    it is malformed (e.g. a skill with two skill types). Splitting isolates that
    record; a single item that still fails is taken in its brief (non-full) form.
    """
    params = {
        "type": concept_type,
        "language": language,
        "limit": page_size,
        "offset": page_no,
    }
    try:
        return get_json(ESCO_SEARCH_URL, {**params, "full": "true"})
    except Exception:
        if page_size == 1:
            if progress:
                progress(
                    f"ESCO {concept_type} #{page_no}: full record fails; using brief"
                )
            return get_json(ESCO_SEARCH_URL, params)
    sub = _smaller_page_size(page_size)
    total, results = 0, []
    for i in range(page_size // sub):
        part = _search_items(
            concept_type,
            page_no * (page_size // sub) + i,
            sub,
            get_json=get_json,
            language=language,
            progress=progress,
        )
        total = part.get("total", total)
        got = (part.get("_embedded") or {}).get("results") or []
        results += got
        if len(got) < sub:
            break
    return {"total": total, "_embedded": {"results": results}}


def _esco_pages(
    concept_type: str,
    *,
    get_json: GetJson,
    cache: MutableMapping[str, Any] | None,
    page_size: int,
    language: str,
    progress: Progress | None,
):
    """Yield every ESCO search page of ``concept_type``, caching each one.

    Note: the ESCO API's ``offset`` is a *page index* (``offset=2, limit=100`` is
    items 200-299), not an item offset. Raises if fewer items arrive than the
    API's ``total`` — a silently truncated taxonomy would look valid.
    """
    page_no, total, seen = 0, None, 0
    while total is None or seen < total:
        key = f"esco-{language}-{concept_type}-p{page_no:05d}-n{page_size}"
        page = cache.get(key) if cache is not None else None
        if page is None:
            page = _search_items(
                concept_type,
                page_no,
                page_size,
                get_json=get_json,
                language=language,
                progress=progress,
            )
            results = (page.get("_embedded") or {}).get("results") or []
            if cache is not None and results:  # an empty page may be transient
                cache[key] = page
        total = page.get("total", 0)
        results = (page.get("_embedded") or {}).get("results") or []
        if not results:
            break
        seen += len(results)
        if progress:
            progress(f"ESCO {concept_type}s: {seen}/{total}")
        yield results
        page_no += 1
    if total and seen < total:
        raise RuntimeError(
            f"ESCO returned {seen} of {total} {concept_type}s (empty page "
            f"{page_no}); rerun to resume from the cached pages"
        )


def fetch_esco(
    *,
    get_json: GetJson | None = None,
    cache: MutableMapping[str, Any] | None = None,
    page_size: int = 100,
    language: str = "en",
    progress: Progress | None = None,
) -> tuple[list[SkillNode], list[Occupation]]:
    """All ESCO skills and occupations (with their skill links).

    Occupation↔skill links are the union of both sides — an occupation's
    ``hasEssential/OptionalSkill`` and a skill's ``isEssential/OptionalForOccupation``
    — so a record that only came back in brief form still gets its links.
    """
    get_json = get_json or requests_get_json
    kw = dict(
        get_json=get_json,
        cache=cache,
        page_size=page_size,
        language=language,
        progress=progress,
    )
    nodes: list[SkillNode] = []
    from_skills: dict[str, tuple[set[str], set[str]]] = {}
    for page in _esco_pages("skill", **kw):
        for record in page:
            node = esco_skill_node(record, language=language)
            nodes.append(node)
            for rel, side in (
                ("isEssentialForOccupation", 0),
                ("isOptionalForOccupation", 1),
            ):
                for occ_uri in _link_uris(record, rel):
                    links = from_skills.setdefault(_esco_id(occ_uri), (set(), set()))
                    links[side].add(node.id)
    occupations = []
    for page in _esco_pages("occupation", **kw):
        for record in page:
            occ = esco_occupation(record, language=language)
            essential, optional = from_skills.get(occ.id, (set(), set()))
            occ.essential = sorted(set(occ.essential) | essential)
            occ.optional = sorted((set(occ.optional) | optional) - set(occ.essential))
            occupations.append(occ)
    return nodes, occupations


# --------------------------------------------------------------------------- #
# O*NET
# --------------------------------------------------------------------------- #
def onet_tech_id(example: str) -> str:
    """Stable node id for an O*NET technology example (``C++`` → ``onet:tech:c++``)."""
    return "onet:tech:" + normalize_label(example).replace(" ", "-")


def _rows(archive: zipfile.ZipFile, filename: str) -> list[dict[str, str]]:
    name = next((n for n in archive.namelist() if n.endswith("/" + filename)), None)
    if name is None:
        raise ValueError(f"O*NET archive has no {filename!r}")
    lines = archive.read(name).decode("utf-8", errors="replace").splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:] if line]


def parse_onet_archive(
    data: bytes, *, min_importance: float = 3.5
) -> tuple[list[SkillNode], list[Occupation]]:
    """Nodes and occupations from the bytes of an O*NET text-database archive."""
    archive = zipfile.ZipFile(io.BytesIO(data))
    occupations = {
        row["O*NET-SOC Code"]: Occupation(
            id="onet:occ:" + row["O*NET-SOC Code"], label=row["Title"], source="onet"
        )
        for row in _rows(archive, "Occupation Data.txt")
    }
    nodes: dict[str, SkillNode] = {}

    for row in _rows(archive, "Technology Skills.txt"):
        occ = occupations.get(row["O*NET-SOC Code"])
        if occ is None:
            continue
        node_id = onet_tech_id(row["Example"])
        nodes.setdefault(
            node_id,
            SkillNode(
                id=node_id, label=row["Example"], source="onet", kind="technology"
            ),
        )
        bucket = occ.essential if row.get("Hot Technology") == "Y" else occ.optional
        if node_id not in bucket:
            bucket.append(node_id)

    for filename, kind in _ONET_KIND.items():
        for row in _rows(archive, filename):
            occ = occupations.get(row["O*NET-SOC Code"])
            if occ is None or row.get("Scale ID") != "IM":
                continue
            node_id = "onet:" + row["Element ID"]
            nodes.setdefault(
                node_id,
                SkillNode(
                    id=node_id, label=row["Element Name"], source="onet", kind=kind
                ),
            )
            if float(row["Data Value"]) >= min_importance:
                occ.essential.append(node_id)

    return list(nodes.values()), list(occupations.values())


def fetch_onet(
    *,
    get_bytes: GetBytes | None = None,
    cache: MutableMapping[str, bytes] | None = None,
    version: str = DFLT_ONET_VERSION,
    min_importance: float = 3.5,
    progress: Progress | None = None,
) -> tuple[list[SkillNode], list[Occupation]]:
    """O*NET technology and K/S/A nodes, and occupations (downloads ~13 MB once)."""
    key = f"onet-db_{version}_text.zip"
    data = cache.get(key) if cache is not None else None
    if data is None:
        if progress:
            progress(f"O*NET {version}: downloading archive")
        data = (get_bytes or requests_get_bytes)(
            ONET_ARCHIVE_URL.format(version=version)
        )
        if cache is not None:
            cache[key] = data
    if progress:
        progress(f"O*NET {version}: parsing")
    return parse_onet_archive(data, min_importance=min_importance)
