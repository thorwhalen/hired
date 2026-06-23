"""Tests for the soft/hard refresh subsystem (deterministic mechanism; fake ingest).

No LLM is used — an injected ``ingest_fn`` supplies the extraction, so these tests
exercise the package's deterministic change-detection + apply logic end to end.
"""

import pytest


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HIRED_DATA_DIR", str(tmp_path))
    yield tmp_path


def _fact_record_for(item):
    """A fake extractor: one fact per item, quoting its (text) content."""
    text = item.content.decode() if isinstance(item.content, bytes) else item.content
    return [{"statement": f"derived from {item.key}", "category": "experience",
             "quote": text.strip() or None}]


def test_pending_and_needs_refresh_detects_new_source():
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    assert kb.needs_refresh() is False
    kb.add_source(b"Built ML systems in Python.", name="cv.txt")
    # added but not yet ingested -> pending
    assert kb.pending_sources() == ["cv.txt"]
    assert kb.needs_refresh() is True


def test_soft_refresh_applies_only_pending_sources():
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    kb.add_source(b"source one", name="a.txt")
    report = kb.refresh("soft", ingest_fn=_fact_record_for)
    assert report.applied
    assert len(report.added_fact_ids) == 1
    assert kb.pending_sources() == []  # now ingested
    assert kb.needs_refresh() is False

    # a second, unchanged refresh does nothing (no pending work)
    report2 = kb.refresh("soft", ingest_fn=_fact_record_for)
    assert report2.added_fact_ids == []

    # adding a new source makes exactly that one pending
    kb.add_source(b"source two", name="b.txt")
    assert kb.pending_sources() == ["b.txt"]
    report3 = kb.refresh("soft", ingest_fn=_fact_record_for)
    assert len(report3.added_fact_ids) == 1
    # fact store iterates in filesystem order (not insertion order) — compare as a set
    assert sorted(f.statement for f in kb.facts()) == [
        "derived from a.txt",
        "derived from b.txt",
    ]


def test_changed_source_supersedes_prior_facts():
    from hired.candidate import CandidateKnowledgeBase
    from hired.candidate.base import FactStatus

    kb = CandidateKnowledgeBase()
    kb.add_source(b"version one", name="cv.txt")
    kb.refresh("soft", ingest_fn=_fact_record_for)
    first = list(kb.facts())
    assert len(first) == 1

    # change the source content -> it becomes pending again
    kb.add_source(b"version two", name="cv.txt")
    assert kb.pending_sources() == ["cv.txt"]
    report = kb.refresh("soft", ingest_fn=_fact_record_for)
    assert len(report.superseded_fact_ids) == 1
    # only the fresh fact is asserted; the stale one is superseded (hidden)
    asserted = list(kb.facts())
    assert len(asserted) == 1
    assert kb.get_fact(report.superseded_fact_ids[0]).status == FactStatus.SUPERSEDED


def test_apply_false_is_non_destructive_preview():
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    kb.add_source(b"some resume text", name="cv.txt")
    report = kb.refresh("soft", ingest_fn=_fact_record_for, apply=False)
    assert report.applied is False
    assert len(report.proposals) == 1
    assert report.proposals[0].records[0]["statement"] == "derived from cv.txt"
    # nothing was written
    assert list(kb.facts()) == []
    assert kb.pending_sources() == ["cv.txt"]


def test_hard_refresh_rederives_all_sources_with_supersession():
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    kb.add_source(b"alpha", name="a.txt")
    kb.add_source(b"beta", name="b.txt")
    kb.refresh("soft", ingest_fn=_fact_record_for)
    assert len(list(kb.facts())) == 2

    # hard refresh re-derives EVERY source, superseding the prior source-derived facts
    report = kb.refresh("hard", ingest_fn=_fact_record_for)
    assert len(report.superseded_fact_ids) == 2
    assert len(report.added_fact_ids) == 2
    assert len(list(kb.facts())) == 2  # 2 fresh asserted (old 2 superseded)

    from hired.candidate.state import load_state
    assert load_state(kb._store).last_hard_refresh is not None


def test_pending_qa_distilled_on_refresh():
    from hired.candidate import CandidateKnowledgeBase, QAEntry, SourceKind

    kb = CandidateKnowledgeBase()
    # recorded WITHOUT derived facts -> undistilled -> pending
    kb.record_qa(QAEntry(question="Team size?", answer="I led a team of 12."))
    assert len(kb.pending_qa()) == 1

    report = kb.refresh("soft", ingest_fn=_fact_record_for)
    assert len(report.added_fact_ids) == 1
    assert kb.pending_qa() == []  # now back-linked
    fact = kb.get_fact(report.added_fact_ids[0])
    assert fact.provenance[0].source_kind == SourceKind.QA


def test_refresh_without_ingest_fn_just_lists_pending():
    from hired.candidate import CandidateKnowledgeBase

    kb = CandidateKnowledgeBase()
    kb.add_source(b"x", name="a.txt")
    report = kb.refresh("soft")  # no ingest_fn
    assert report.applied is False
    assert [i.key for i in report.pending] == ["a.txt"]
    assert list(kb.facts()) == []  # nothing extracted/written
