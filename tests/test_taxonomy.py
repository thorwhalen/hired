"""Skills taxonomy + adjacency (#10): fetch → graph → index, all offline."""

import io
import zipfile

import pytest

from hired.taxonomy import (
    SkillIndex,
    SkillNode,
    build_skill_index,
    load_skill_index,
    normalize_label,
    parse_onet_archive,
    relatedness_edges,
)
from hired.taxonomy.base import Occupation
from hired.taxonomy.sources import esco_occupation, esco_skill_node, onet_tech_id

ESCO = "http://data.europa.eu/esco/"


def _skill(uid, label, alts=(), kind="skill", reuse="cross-sector"):
    return {
        "uri": f"{ESCO}skill/{uid}",
        "title": label,
        "preferredLabel": {"en": label, "fr": "x"},
        "alternativeLabel": {"en": list(alts)},
        "_links": {
            "hasSkillType": [{"uri": f"{ESCO}skill-type/{kind}"}],
            "hasReuseLevel": [{"uri": f"{ESCO}skill-reuse-level/{reuse}"}],
        },
    }


def _occ(uid, label, essential, optional=()):
    return {
        "uri": f"{ESCO}occupation/{uid}",
        "title": label,
        "preferredLabel": {"en": label},
        "_links": {
            "hasEssentialSkill": [{"uri": f"{ESCO}skill/{s}"} for s in essential],
            "hasOptionalSkill": [{"uri": f"{ESCO}skill/{s}"} for s in optional],
        },
    }


SKILLS = [
    _skill("py", "Python (computer programming)", ["Python"]),
    _skill("ml", "machine learning", kind="knowledge"),
    _skill("dl", "deep learning"),
    _skill("tf", "TensorFlow"),
    _skill("cook", "cook meals", reuse="occupation-specific"),
    _skill("serve", "serve food"),
]
OCCUPATIONS = [
    _occ("ds1", "data scientist", ["py", "ml", "dl"]),
    _occ("ds2", "ML engineer", ["py", "ml", "tf", "dl"]),
    _occ("ds3", "research engineer", ["dl", "tf"], ["py"]),
    _occ("ds4", "AI engineer", ["dl", "tf", "ml"]),
    _occ("ck1", "cook", ["cook", "serve"]),
    _occ("ck2", "chef", ["cook", "serve"]),
    _occ("ck3", "line cook", ["cook"]),
]


def fake_esco():
    calls = []

    def get_json(url, params):
        calls.append(params)
        data = SKILLS if params["type"] == "skill" else OCCUPATIONS
        lim = params["limit"]
        off = params["offset"] * lim  # ESCO's offset is a page index
        return {"total": len(data), "_embedded": {"results": data[off : off + lim]}}

    get_json.calls = calls
    return get_json


def _tsv(header, rows):
    return "\n".join(["\t".join(header), *("\t".join(r) for r in rows)]) + "\n"


def fake_onet_archive() -> bytes:
    stat = ["O*NET-SOC Code", "Element ID", "Element Name", "Scale ID", "Data Value"]
    files = {
        "Occupation Data.txt": _tsv(
            ["O*NET-SOC Code", "Title", "Description"],
            [
                ["15-1", "Data Scientists", "d"],
                ["15-2", "Software Devs", "d"],
                ["35-1", "Cooks", "d"],
            ],
        ),
        "Technology Skills.txt": _tsv(
            [
                "O*NET-SOC Code",
                "Example",
                "Commodity Code",
                "Commodity Title",
                "Hot Technology",
                "In Demand",
            ],
            [
                ["15-1", "Python", "1", "x", "Y", "Y"],
                ["15-1", "C++", "1", "x", "N", "N"],
                ["15-2", "Python", "1", "x", "Y", "Y"],
                ["15-2", "C++", "1", "x", "Y", "N"],
            ],
        ),
        "Skills.txt": _tsv(
            stat,
            [
                ["15-1", "2.A.1.e", "Mathematics", "IM", "4.2"],
                ["15-1", "2.A.1.e", "Mathematics", "LV", "5.0"],
                ["35-1", "2.A.1.e", "Mathematics", "IM", "1.5"],
            ],
        ),
        "Knowledge.txt": _tsv(stat, []),
        "Abilities.txt": _tsv(
            stat, [["35-1", "1.A.2", "Manual Dexterity", "IM", "4.0"]]
        ),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(f"db_30_0_text/{name}", text)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
def test_normalize_label_keeps_tech_symbols():
    assert normalize_label("C++") == "c++"
    assert normalize_label("C#") == "c#"
    assert normalize_label("Node.js.") == "node.js"
    assert onet_tech_id("C++") != onet_tech_id("C#")


def test_esco_paging_uses_page_index_and_detects_truncation():
    from hired.taxonomy.sources import fetch_esco

    get_json = fake_esco()
    nodes, occs = fetch_esco(get_json=get_json, page_size=4)
    assert len(nodes) == len(SKILLS) and len(occs) == len(OCCUPATIONS)
    assert [c["offset"] for c in get_json.calls if c["type"] == "skill"] == [0, 1]

    def truncating(url, params):
        page = get_json(url, params)
        return page if params["offset"] == 0 else {"total": page["total"]}

    with pytest.raises(RuntimeError, match="returned 4 of 6 skills"):
        fetch_esco(get_json=truncating, page_size=4)


def test_esco_bad_record_is_isolated_and_degraded_to_brief():
    """ESCO 500s a whole full=true page when one record is malformed."""
    from hired.taxonomy.sources import fetch_esco

    good = fake_esco()
    bad_uri = SKILLS[3]["uri"]  # TensorFlow

    def flaky(url, params):
        page = good(url, params)
        items = page["_embedded"]["results"]
        if params.get("full") and any(r["uri"] == bad_uri for r in items):
            raise RuntimeError("500 Server Error")
        if not params.get("full"):  # brief form: plain strings, no _links
            page = {
                **page,
                "_embedded": {
                    "results": [
                        {
                            "uri": r["uri"],
                            "title": r["title"],
                            "preferredLabel": r["preferredLabel"]["en"],
                            "hasSkillType": [
                                lk["uri"] for lk in r["_links"].get("hasSkillType", [])
                            ],
                        }
                        for r in items
                    ]
                },
            }
        return page

    nodes, occs = fetch_esco(get_json=flaky, page_size=4)
    assert [n.label for n in nodes] == [r["title"] for r in SKILLS]
    tf = next(n for n in nodes if n.id == "esco:tf")
    assert tf.kind == "skill" and tf.alt_labels == []  # degraded but present


def test_occupation_links_include_the_skill_side():
    from hired.taxonomy.sources import fetch_esco

    skills = [dict(SKILLS[0]), *SKILLS[1:]]
    skills[0]["_links"] = {
        **skills[0]["_links"],
        "isEssentialForOccupation": [{"uri": f"{ESCO}occupation/ck1"}],
    }
    occs = [_occ("ck1", "cook", ["cook"])]

    def get_json(url, params):
        data = skills if params["type"] == "skill" else occs
        lim = params["limit"]
        off = params["offset"] * lim
        return {"total": len(data), "_embedded": {"results": data[off : off + lim]}}

    _, got = fetch_esco(get_json=get_json)
    assert got[0].essential == ["esco:cook", "esco:py"]


def test_esco_records_parse():
    node = esco_skill_node(SKILLS[1])
    assert (node.id, node.kind, node.reuse_level) == (
        "esco:ml",
        "knowledge",
        "cross-sector",
    )
    occ = esco_occupation(OCCUPATIONS[2])
    assert occ.essential == ["esco:dl", "esco:tf"] and occ.optional == ["esco:py"]


def test_relatedness_prefers_co_required_skills():
    occs = [esco_occupation(o) for o in OCCUPATIONS]
    edges = relatedness_edges(occs)
    tf = dict(edges["esco:tf"])
    assert tf["esco:dl"] > 0 and "esco:cook" not in tf
    assert dict(edges["esco:cook"]).get("esco:serve", 0) > 0
    # symmetric, bounded
    assert all(0 < s <= 1 for links in edges.values() for _, s in links)
    assert dict(edges["esco:dl"])["esco:tf"] == tf["esco:dl"]


def test_min_cooccurrence_drops_one_off_pairs():
    occs = [
        Occupation(id="o", label="", source="t", essential=["a", "b"]),
        Occupation(id="p", label="", source="t", essential=["c", "d"]),
    ]
    assert relatedness_edges(occs) == {}
    assert relatedness_edges(occs, min_cooccurrence=1)["a"][0][0] == "b"


def test_parse_onet_archive():
    nodes, occs = parse_onet_archive(fake_onet_archive())
    by_id = {n.id: n for n in nodes}
    assert by_id["onet:tech:c++"].kind == "technology"
    assert by_id["onet:2.A.1.e"].kind == "skill"
    assert by_id["onet:1.A.2"].kind == "ability"
    ds = next(o for o in occs if o.id == "onet:occ:15-1")
    assert "onet:tech:python" in ds.essential and "onet:tech:c++" in ds.optional
    assert "onet:2.A.1.e" in ds.essential  # IM 4.2 >= 3.5
    cooks = next(o for o in occs if o.id == "onet:occ:35-1")
    assert "onet:2.A.1.e" not in cooks.essential  # IM 1.5 below threshold


# --------------------------------------------------------------------------- #
@pytest.fixture
def built(tmp_path):
    root = str(tmp_path / "taxo")
    get_json = fake_esco()
    meta = build_skill_index(
        root=root,
        get_json=get_json,
        get_bytes=lambda url: fake_onet_archive(),
        graph_kwargs={"min_cooccurrence": 1},
    )
    return root, meta, get_json


def test_build_writes_index_and_attribution(built):
    root, meta, _ = built
    assert meta["sources"] == ["esco", "onet"]
    assert meta["nodes"] == len(SKILLS) + 4 and meta["embedding_model"] is None
    notice = open(f"{root}/NOTICE.md").read()
    assert "CC BY 4.0" in notice and "ESCO" in notice and "O*NET" in notice


def test_rebuild_is_offline_from_the_page_cache(built, tmp_path):
    root, meta, get_json = built
    n_calls = len(get_json.calls)

    def no_network(*a, **k):
        raise AssertionError("network used on a cached rebuild")

    assert (
        build_skill_index(
            root=root,
            get_json=no_network,
            get_bytes=no_network,
            graph_kwargs={"min_cooccurrence": 1},
        )["nodes"]
        == meta["nodes"]
    )
    assert len(get_json.calls) == n_calls


def test_load_missing_index_says_how_to_build(tmp_path):
    with pytest.raises(FileNotFoundError, match="build-skill-index"):
        load_skill_index(root=str(tmp_path / "nothing"))


def test_index_lookup_and_adjacency(built):
    idx = load_skill_index(root=built[0])
    assert idx.lookup("python")[0].node.id in {"esco:py", "onet:tech:python"}
    assert idx.lookup("Machine-Learning")[0].how == "label"
    assert idx.lookup("deep learning models")[0].how == "tokens"

    # same concept across sources: ESCO alt label "Python" == O*NET tech "Python"
    same = idx.proximity("Python", "onet:tech:python")
    assert same.score == 1.0 and "same taxonomy concept" in same.basis

    near = idx.proximity("TensorFlow", "deep learning")
    far = idx.proximity("TensorFlow", "cook meals")
    assert near.score > 0 and far.score == 0.0 and near.alpha == 0.0
    ranked = idx.suggest_adjacency("deep learning", ["cook meals", "TensorFlow"])
    assert ranked[0].a == "TensorFlow"
    assert ranked[0].score > ranked[1].score
    assert ranked[1].transferability().value == "limited"

    unknown = idx.proximity("underwater basket weaving", "TensorFlow")
    assert unknown.a_node is None and unknown.score == 0.0
    assert "not in taxonomy" in unknown.basis
    assert [n.id for n, _ in idx.neighbors("TensorFlow")][:1] != []


def test_two_hop_relatedness_names_the_via_skill():
    nodes = [SkillNode(id=i, label=i, source="t") for i in ("a", "mid", "b")]
    idx = SkillIndex(
        nodes,
        {"a": [("mid", 0.8)], "mid": [("a", 0.8), ("b", 0.5)], "b": [("mid", 0.5)]},
    )
    p = idx.proximity("a", "b")
    assert p.score == 0.4 and p.via.id == "mid" and "'mid'" in p.basis


def test_embeddings_blend_and_cover_unknown_skills(tmp_path):
    np = pytest.importorskip("numpy")
    vocab = [
        "python",
        "tensorflow",
        "deep",
        "learning",
        "machine",
        "cook",
        "serve",
        "meals",
        "food",
        "computer",
        "programming",
        "c++",
        "mathematics",
        "manual",
        "dexterity",
        "pytorch",
    ]

    def embed(texts):  # bag-of-words over a tiny vocabulary: deterministic, offline
        rows = []
        for t in texts:
            toks = normalize_label(t).split()
            rows.append([float(toks.count(w)) for w in vocab] + [1e-3])
        return np.asarray(rows)

    root = str(tmp_path / "taxo")
    meta = build_skill_index(
        root=root,
        get_json=fake_esco(),
        get_bytes=lambda url: fake_onet_archive(),
        embedder=embed,
        graph_kwargs={"min_cooccurrence": 1},
    )
    assert meta["embedding_model"] == "custom"
    idx = load_skill_index(root=root, embedder=embed)
    assert idx._vectors.dtype == np.float16

    p = idx.proximity("TensorFlow", "deep learning")
    assert p.alpha == 0.5 and p.cosine is not None
    assert p.score == pytest.approx(0.5 * max(p.cosine, 0) + 0.5 * p.graph, abs=1e-3)
    # not in either taxonomy, still comparable by embedding
    oov = idx.proximity("deep learning with pytorch", "deep learning")
    assert oov.a_node is not None or oov.cosine is not None
    assert idx.lookup("pytorch tensorflow")  # tokens or embedding fallback

    # stored vectors without a query embedder: node-to-node cosine still works
    idx2 = load_skill_index(root=root, embedder=None)
    assert idx2.proximity("TensorFlow", "deep learning").cosine == pytest.approx(
        p.cosine, abs=1e-3
    )


def test_cli_skill_commands(built, monkeypatch):
    import hired.taxonomy as taxonomy
    from hired import cli

    root = built[0]
    real = taxonomy.load_skill_index
    # patch the module object (a dotted-string target breaks once another test
    # has re-imported the `hired` package)
    monkeypatch.setattr(
        taxonomy, "load_skill_index", lambda **kw: real(root=root, **kw)
    )
    assert "TensorFlow" in cli.skill_lookup("tensorflow")[0]
    lines = cli.skill_adjacency("deep learning", "cook meals, TensorFlow")
    assert lines[0].split()[0] != "0.00" and "TensorFlow" in lines[0]


def test_taxonomy_import_is_light():
    import subprocess
    import sys

    code = (
        "import sys, hired, hired.taxonomy, hired.cli; "
        "bad = {'numpy', 'sentence_transformers', 'torch'} & set(sys.modules); "
        "assert not bad, bad"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def _two_source_index(**kwargs):
    """O*NET tech node with no ESCO link of its own; ESCO graph links its namesake."""
    nodes = [
        SkillNode(id="onet:tf", label="TensorFlow", source="onet", kind="technology"),
        SkillNode(id="onet:lone", label="TensorFlow Lite", source="onet"),
        SkillNode(id="esco:tf", label="TensorFlow framework", source="esco"),
        SkillNode(id="esco:dl", label="deep learning", source="esco"),
        SkillNode(id="esco:cook", label="cooking", source="esco"),
        SkillNode(id="esco:tfx", label="TensorFlow extended", source="esco"),
    ]
    edges = {
        "onet:tf": [("onet:lone", 0.3)],
        "onet:lone": [("onet:tf", 0.3)],
        "esco:tf": [("esco:dl", 0.8)],
        "esco:dl": [("esco:tf", 0.8)],
    }
    return SkillIndex(nodes, edges, **kwargs)


def test_cross_source_bridge_lets_the_graph_propagate():
    idx = _two_source_index()
    # esco:tfx matches as well, but has no edges: a bridge there would lead nowhere
    assert idx._bridges("onet:tf") == {"esco:tf": 0.5}
    p = idx.proximity("onet:tf", "deep learning")
    assert p.graph == pytest.approx(0.4)  # bridge 0.5 x ESCO link 0.8
    assert idx.proximity("onet:tf", "cooking").graph == 0.0
    no_bridge = _two_source_index(bridge_k=0)
    assert no_bridge.proximity("onet:tf", "deep learning").graph == 0.0


def test_a_silent_graph_falls_back_to_cosine():
    np = pytest.importorskip("numpy")
    vocab = ["tensorflow", "deep", "learning", "cooking", "framework"]

    def embed(texts):
        rows = []
        for t in texts:
            toks = normalize_label(t).split()
            rows.append([float(toks.count(w)) for w in vocab] + [1e-3])
        return np.asarray(rows)

    nodes = [
        SkillNode(id="onet:tf", label="TensorFlow deep learning", source="onet"),
        SkillNode(id="esco:dl", label="deep learning", source="esco"),
        SkillNode(id="esco:fw", label="deep learning framework", source="esco"),
    ]
    edges = {"esco:dl": [("esco:fw", 0.6)], "esco:fw": [("esco:dl", 0.6)]}
    idx = SkillIndex(nodes, edges, embedder=embed, bridge_k=0)
    silent = idx.proximity("onet:tf", "esco:dl")  # no path: cosine decides alone
    assert silent.alpha == 1.0 and silent.score == pytest.approx(silent.cosine, abs=1e-4)
    linked = idx.proximity("esco:dl", "esco:fw")  # a path: the blend stays
    assert linked.alpha == 0.5 and linked.graph == 0.6
    off = SkillIndex(nodes, edges, embedder=embed, bridge_k=0, graph_trust=0)
    assert off.proximity("onet:tf", "esco:dl").alpha == 0.5


def test_weak_graph_evidence_never_ranks_below_none():
    """Review of #43: cosine's weight rises smoothly as the graph score falls to 0."""
    np = pytest.importorskip("numpy")
    nodes = [SkillNode(id=i, label=i, source="s") for i in ("a", "b", "c")]
    vecs = {"a": [1.0, 0.0], "b": [0.6, 0.8], "c": [0.6, 0.8]}
    idx = SkillIndex(
        nodes,
        {"a": [("c", 0.01)], "c": [("a", 0.01)]},
        vectors=np.asarray([vecs[n.id] for n in nodes]),
        vector_ids=[n.id for n in nodes],
    )
    none, weak = idx.proximity("a", "b"), idx.proximity("a", "c")
    assert none.graph == 0 and none.alpha == 1.0
    assert weak.graph == 0.01 and abs(weak.score - none.score) < 0.05


def test_an_empty_page_is_not_cached_so_a_rerun_recovers(tmp_path):
    flaky = {"down": True}
    real = fake_esco()

    def get_json(url, params):
        if flaky["down"] and params["type"] == "skill" and params["offset"] == 0:
            return {"total": 3, "_embedded": {"results": []}}  # a transient empty page
        return real(url, params)

    root = str(tmp_path / "taxo")
    kwargs = dict(root=root, get_json=get_json, sources=["esco"])
    with pytest.raises(RuntimeError, match="rerun"):
        build_skill_index(**kwargs)
    flaky["down"] = False
    assert build_skill_index(**kwargs)["nodes"] > 0


def test_notice_credits_only_the_sources_used(tmp_path):
    from hired.taxonomy.base import attribution

    esco_only = attribution(["esco"])
    assert "ESCO" in esco_only and "O*NET" not in esco_only
    assert "not approved, endorsed, or tested" in attribution(["onet"], onet_version="29_1")
    assert "O*NET 29.1" in attribution(["onet"], onet_version="29_1")


def test_a_missing_embedder_fails_before_fetching(tmp_path, monkeypatch):
    import hired.taxonomy.build as build_mod

    def no_numpy():
        raise ImportError("numpy is needed")

    monkeypatch.setattr(build_mod, "require_numpy", no_numpy)
    calls = []
    with pytest.raises(ImportError):
        build_skill_index(
            root=str(tmp_path / "t"), embeddings=True, get_json=lambda u, p: calls.append(p)
        )
    assert calls == []


def test_resolve_prefers_skills_over_technology_and_reranks_by_embedding():
    """#58: short free text should not land on product/software nodes."""
    nodes = [
        SkillNode(id="onet:sw", label="Sales software", source="onet", kind="technology"),
        SkillNode(id="esco:sa", label="sales activities", source="esco"),
        SkillNode(id="esco:sm", label="sales methods", source="esco"),
    ]
    assert SkillIndex(nodes, {}).resolve("sales").id == "esco:sa"
    # kind_weights is the knob: neutral weights fall back to the label order
    neutral = SkillIndex(nodes, {}, kind_weights={})
    assert neutral.resolve("sales").id == "esco:sa"
    # with vectors, the token tie is broken by embedding similarity
    np = pytest.importorskip("numpy")
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8]])

    def embedder(texts):
        return np.array([[0.0, 1.0] for _ in texts])

    idx = SkillIndex(
        nodes, {}, vectors=vectors, vector_ids=["onet:sw", "esco:sa", "esco:sm"],
        embedder=embedder,
    )
    ranked = idx.lookup("sales")
    assert [m.node.id for m in ranked] == ["esco:sa", "esco:sm", "onet:sw"]
    assert ranked[0].how == "tokens" and ranked[0].score == 0.5
