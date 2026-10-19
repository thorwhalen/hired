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
