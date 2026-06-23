"""Tests for cross-session knowledge: raw sources, Q&A→facts, topic dossiers.

All persistence is redirected to a temp dir via ``HIRED_DATA_DIR``.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HIRED_DATA_DIR", str(tmp_path))
    yield tmp_path


# --------------------------------------------------------------------------- #
# Raw sources + digests
# --------------------------------------------------------------------------- #
def test_add_source_from_bytes_records_digest():
    from hired.candidate import CandidateKnowledgeBase
    from hired.candidate.state import load_state, sha256_hex

    kb = CandidateKnowledgeBase()
    key = kb.add_source(b"%PDF resume bytes", name="cv.pdf")
    assert key == "cv.pdf"
    assert kb.get_source("cv.pdf") == b"%PDF resume bytes"
    assert "cv.pdf" in kb.sources()

    state = load_state(kb._store)
    assert "cv.pdf" in state.sources
    assert state.sources["cv.pdf"].sha256 == sha256_hex(b"%PDF resume bytes")
    assert state.sources["cv.pdf"].size == len(b"%PDF resume bytes")


def test_add_source_from_path(tmp_path):
    from hired.candidate import CandidateKnowledgeBase

    p = tmp_path / "bio.md"
    # write exact bytes so the assertion is newline-stable across platforms
    p.write_bytes(b"# Bio\nThor builds ML systems.")
    kb = CandidateKnowledgeBase()
    key = kb.add_source(str(p))
    assert key == "bio.md"
    assert kb.get_source("bio.md") == b"# Bio\nThor builds ML systems."


def test_save_upload_alias_still_works():
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    kb.save_upload("old.txt", b"legacy")
    assert kb.get_upload("old.txt") == b"legacy"
    assert "old.txt" in kb.uploads()


# --------------------------------------------------------------------------- #
# Q&A → facts distillation
# --------------------------------------------------------------------------- #
def test_record_qa_distills_and_backlinks_facts():
    from hired.candidate import CandidateKnowledgeBase, QAEntry, SourceKind

    kb = CandidateKnowledgeBase()
    entry = QAEntry(
        question="Largest team led?",
        answer="I led a data-science team of 12 at Acme.",
    )
    qa_id = kb.record_qa(
        entry,
        derived_facts=[
            {
                "statement": "Led a data-science team of 12 at Acme.",
                "category": "experience",
                "quote": "led a data-science team of 12 at Acme",
                "tags": ["leadership"],
            }
        ],
    )
    # Q&A persisted, with a back-link to the derived fact
    stored = next(q for q in kb.qa_entries() if q.id == qa_id)
    assert len(stored.derived_fact_ids) == 1
    fid = stored.derived_fact_ids[0]
    # the fact exists, has QA provenance pointing back at the Q&A entry
    fact = kb.get_fact(fid)
    assert fact.provenance[0].source_kind == SourceKind.QA
    assert fact.provenance[0].source_id == qa_id
    # quote verified against the answer text (it is a verbatim substring)
    assert fact.provenance[0].quote is not None


def test_record_qa_without_facts_is_plain_history():
    from hired.candidate import CandidateKnowledgeBase, QAEntry

    kb = CandidateKnowledgeBase()
    kb.record_qa(QAEntry(question="Q?", answer="A."))
    assert [q.answer for q in kb.qa_entries()] == ["A."]
    assert list(kb.facts()) == []


# --------------------------------------------------------------------------- #
# Topic dossiers
# --------------------------------------------------------------------------- #
def test_topic_dossier_note_and_files(tmp_path):
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    dossier = kb.add_note(
        "Open-source work",
        "Maintains the `dol` data-access library.",
        files={"stars.txt": b"1200"},
    )
    assert "open-source-work" in kb.topics()  # slugged
    assert dossier.overview.splitlines()[0] == "# Open-source work"
    assert "dol" in dossier.overview
    assert dossier.files() == ["stars.txt"]
    assert dossier.get_file("stars.txt") == b"1200"

    # appending another note grows the same dossier (a little, or a whole lot)
    kb.add_note("Open-source work", "Also created the `hired` suite.")
    assert "hired" in kb.topic("Open-source work").overview

    # on-disk shape: overview.md + files/
    tdir = tmp_path / "users" / "me" / "user" / "info" / "topics" / "open-source-work"
    assert (tdir / "overview.md").is_file()
    assert (tdir / "files" / "stars.txt").is_file()


def test_synopsis_includes_topics_index():
    from hired.candidate import CandidateKnowledgeBase, Fact, FactCategory

    kb = CandidateKnowledgeBase()
    kb.add_fact(Fact(statement="Knows Python", category=FactCategory.SKILL))
    kb.add_note("Patents", "Holds 3 US patents on anomaly detection.")
    text = kb.regenerate_synopsis()
    assert "## topics" in text
    assert "patents" in text
    assert "info/topics/patents/" in text
