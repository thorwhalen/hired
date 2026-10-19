"""Multi-tenant surface, report finalization/HTML rendering, and the ``hired`` CLI (#13)."""

import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

from hired.alignment import (
    AlignmentReport,
    Clarification,
    Closeability,
    MatchType,
    Recommendation,
    Requirement,
    RequirementClass,
    RequirementRecord,
    Verdict,
    finalize_report,
    render_report,
    render_report_html,
)
from hired.candidate import CandidateKnowledgeBase, Fact
from hired.candidate.base import MatchState
from hired.persistence import (
    JDStore,
    UserStore,
    list_users,
    resolve_user,
    validate_name,
)


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HIRED_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("HIRED_USER", raising=False)
    return tmp_path


# --------------------------------------------------------------------------- #
# Multi-tenancy
# --------------------------------------------------------------------------- #
def test_resolve_user_precedence(monkeypatch):
    assert resolve_user() == "me"
    monkeypatch.setenv("HIRED_USER", "carol")
    assert resolve_user() == "carol"
    assert resolve_user("alice") == "alice"
    assert CandidateKnowledgeBase().user == "carol"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        " ",
        "../x",
        "a/b",
        "a\\b",
        ".hidden",
        " pad",
        "C:evil",
        "x.",
        "con",
        "nul.txt",
        "a\x00b",
        "two words",
    ],
)
def test_validate_name_rejects_unsafe(bad):
    with pytest.raises(ValueError):
        validate_name(bad)


def test_user_names_are_lower_case_so_tenants_cannot_alias():
    # On case-insensitive filesystems ALICE/ and alice/ are one directory.
    CandidateKnowledgeBase("alice").add_fact(Fact(statement="alice only"))
    with pytest.raises(ValueError, match="lower-case"):
        CandidateKnowledgeBase("ALICE")
    with pytest.raises(ValueError):
        resolve_user("")  # an explicit empty name is not the default


def test_unsafe_ids_rejected_at_every_entry_point():
    with pytest.raises(ValueError):
        CandidateKnowledgeBase("../escape")
    with pytest.raises(ValueError):
        JDStore("alice", "../other")
    ws = CandidateKnowledgeBase("alice").jd("acme")
    with pytest.raises(ValueError):
        ws.save_report("../../pwn", {"x": 1})


def test_candidates_are_isolated_and_listed():
    assert list_users() == []
    alice, bob = CandidateKnowledgeBase("alice"), CandidateKnowledgeBase("bob")
    alice.add_fact(Fact(statement="alice fact"))
    bob.jd("acme", company="Acme")
    assert list_users() == ["alice", "bob"]
    assert [f.statement for f in alice.facts()] == ["alice fact"]
    assert list(bob.facts()) == []
    assert alice.jds() == [] and bob.jds() == ["acme"]


def test_injected_store_is_authoritative():
    kb = CandidateKnowledgeBase(store=UserStore("dana"))
    assert kb.user == "dana"
    with pytest.raises(ValueError):
        CandidateKnowledgeBase("erin", store=UserStore("dana"))


def test_ingest_source_supersedes_previous_ingest():
    kb = CandidateKnowledgeBase("alice")
    kb.add_source(b"I wrote Python for ten years.", name="cv.md")
    assert kb.pending_sources() == ["cv.md"]
    first, _ = kb.ingest_source("cv.md", [{"statement": "Python", "quote": "Python"}])
    assert kb.pending_sources() == []
    second, superseded = kb.ingest_source(
        "cv.md", [{"statement": "Python, 10 years", "quote": "nope, not there"}]
    )
    assert superseded == first
    assert [f.statement for f in kb.facts()] == ["Python, 10 years"]
    assert kb.get_fact(second[0]).provenance[0].quote is None  # unverified dropped


# --------------------------------------------------------------------------- #
# Report finalization + rendering
# --------------------------------------------------------------------------- #
def _draft() -> AlignmentReport:
    gate = Requirement(
        id="r-gate",
        text="Security clearance",
        requirement_class=RequirementClass.GATE_KEEPER,
    )
    py = Requirement(id="r-py", text="Python <3>", required_level=3)
    unknown = Requirement(
        id="r-k8s", text="Kubernetes", requirement_class=RequirementClass.GATE_KEEPER
    )
    resolved = Requirement(id="r-sql", text="SQL")
    return AlignmentReport(
        job_id="ds",
        company="Acme",
        verdict=Verdict(recommendation=Recommendation.STRETCH, headline="Close call"),
        requirements=[
            RequirementRecord(
                requirement=gate,
                closeability=Closeability.STRUCTURALLY_HARD,
                match_state=MatchState.CONTRADICTED,
            ),
            RequirementRecord(
                requirement=py,
                match_state=MatchState.CONFIRMED,
                match_type=MatchType.DIRECT,
                candidate_level=5,
            ),
            RequirementRecord(
                requirement=unknown, uncertainty_reason="never mentioned"
            ),
            RequirementRecord(
                requirement=resolved,
                match_state=MatchState.CONFIRMED,
                match_type=MatchType.DIRECT,
                candidate_level=4,
            ),
        ],
        clarifications=[
            Clarification(requirement_id="r-k8s", question="Used Kubernetes?"),
            Clarification(requirement_id="r-sql", question="Used SQL?"),  # now resolved
        ],
        # stale: the analyst once flagged SQL as blocking, but it is now a match
        blocking_gaps=[RequirementRecord(requirement=resolved)],
    )


def test_finalize_report_rebuilds_derived_fields():
    final = finalize_report(_draft())
    assert final.score_summary.bucket_counts == {
        "strong_match": 2,
        "adjacent_transferable": 0,
        "gap_learnable": 0,
        "gap_hard": 1,
    }
    assert [r.requirement.id for r in final.blocking_gaps] == ["r-gate"]
    assert final.verdict.has_blocking_gaps
    assert [(c.requirement_id, c.question) for c in final.clarifications] == [
        ("r-k8s", "Used Kubernetes?")
    ]
    assert final.clarifications[0].info_gain > 0
    assert final.created_at
    # idempotent, and accepts the JSON form
    again = finalize_report(final.model_dump(mode="json"))
    assert again.model_dump() == final.model_dump()


def test_finalize_keeps_analyst_links_when_draft_has_no_ids():
    data = _draft().model_dump(mode="json")
    for rec in data["requirements"] + data["blocking_gaps"]:
        del rec["requirement"]["id"]  # a hand/LLM-written draft often omits ids
    data["blocking_gaps"].append(
        {
            "requirement": {"text": "Lives in Paris"},
            "match_state": "contradicted",
            "closeability": "structurally_hard",
        }
    )
    final = finalize_report(data)
    texts = [r.requirement.text for r in final.blocking_gaps]
    # gate-keeper derived; resolved SQL dropped (matched by text); unmatched kept
    assert texts == ["Security clearance", "Lives in Paris"]
    # drafted questions whose ids match nothing are kept, not blanked
    assert {c.question for c in final.clarifications} >= {
        "Used Kubernetes?",
        "Used SQL?",
    }


def test_report_history_never_overwrites():
    ws = CandidateKnowledgeBase("alice").jd("acme")
    for i in range(3):
        ws.save_report("ds", {"created_at": "2026-01-01T00:00:00/x", "v": i})
    versions = ws.report_versions("ds")
    assert len(versions) == 2 and all(v.count("/") == 1 for v in versions)
    assert sorted(ws.store.report_history[v]["v"] for v in versions) == [0, 1]


def test_render_html_is_escaped_and_complete():
    page = render_report_html(finalize_report(_draft()))
    assert page.startswith("<!doctype html>")
    assert "Python &lt;3&gt;" in page and "Python <3>" not in page
    for heading in (
        "Blocking gaps",
        "Strong match",
        "Gap — hard to learn",
        "Not yet known",
        "Questions to clarify",
    ):
        assert heading in page
    assert "prefers-color-scheme: dark" in page


def test_render_report_dispatch():
    report = finalize_report(_draft())
    assert render_report(report).startswith("# Alignment: ds — Acme")
    assert "## ❓ Not yet known" in render_report(report, "md")
    assert render_report(report.model_dump(mode="json"), "html").startswith("<!doctype")
    with pytest.raises(ValueError, match="Unknown report format"):
        render_report(report, "docx")


# --------------------------------------------------------------------------- #
# CLI operations (plain functions)
# --------------------------------------------------------------------------- #
def _write_json(path, obj):
    path.write_text(json.dumps(obj))
    return str(path)


def test_cli_end_to_end(data_dir):
    from hired import cli

    cv = data_dir / "cv.md"
    cv.write_text("I built ML pipelines in Python.")
    recs = _write_json(
        data_dir / "facts.json",
        [
            {
                "statement": "Builds ML pipelines",
                "category": "skill",
                "quote": "built ML pipelines",
            }
        ],
    )
    out = cli.ingest(recs, source=str(cv), user="alice")
    assert out == {"user": "alice", "source": "cv.md", "added": 1, "superseded": 0}
    assert cli.users() == ["alice"]
    assert cli.facts(user="alice", category="skill") == ["Builds ML pipelines"]
    assert cli.status(user="alice")["needs_refresh"] is False

    draft = _write_json(data_dir / "draft.json", _draft().model_dump(mode="json"))
    line = cli.analyze(draft, "acme", user="alice")
    assert line.startswith("acme/ds: stretch") and "blocking=1" in line
    assert cli.jds(user="alice") == ["acme"]
    assert cli.reports("acme", user="alice") == ["ds"]
    assert cli.report("acme", user="alice").startswith("# Alignment: ds")

    html_path = str(data_dir / "out" / "r.html")
    (data_dir / "out").mkdir()
    assert cli.report("acme", fmt="html", output=html_path, user="alice") == html_path
    assert open(html_path).read().startswith("<!doctype html>")

    # re-analyze archives the prior version
    cli.analyze(draft, "acme", user="alice")
    assert len(CandidateKnowledgeBase("alice").jd("acme").report_versions("ds")) == 1


def test_cli_analyze_validates_before_writing_and_report_names_missing_job(data_dir):
    from hired import cli

    draft = _write_json(data_dir / "d.json", _draft().model_dump(mode="json"))
    with pytest.raises(ValueError, match="job id"):
        cli.analyze(draft, "acme", job_id="../x", company="Acme", user="alice")
    assert CandidateKnowledgeBase("alice").jds() == []  # no orphan engagement
    cli.analyze(draft, "acme", user="alice")
    with pytest.raises(ValueError, match="No report 'nope'"):
        cli.report("acme", "nope", user="alice")
    out = data_dir / "r.html"
    cli.report("acme", fmt="html", output=str(out), user="alice")
    assert "⛔" in out.read_text(encoding="utf-8")


def test_cli_read_commands_do_not_create_candidates():
    from hired import cli

    with pytest.raises(ValueError, match="No candidate 'ghost'"):
        cli.status(user="ghost")
    with pytest.raises(ValueError, match="No candidate"):
        cli.report("acme", user="ghost")
    assert cli.users() == []
    CandidateKnowledgeBase("alice")
    with pytest.raises(ValueError, match="No engagement 'nope'"):
        cli.reports("nope", user="alice")
    assert CandidateKnowledgeBase("alice").jds() == []


def test_cli_ingest_rejects_unknown_source_and_non_list(data_dir):
    from hired import cli

    recs = _write_json(data_dir / "f.json", [{"statement": "x"}])
    with pytest.raises(ValueError, match="Unknown source"):
        cli.ingest(recs, source="missing.pdf", user="alice")
    bad = _write_json(data_dir / "bad.json", {"statement": "x"})
    with pytest.raises(ValueError, match="JSON list"):
        cli.ingest(bad, user="alice")
    assert cli.ingest(recs, user="alice")["added"] == 1  # external provenance


# --------------------------------------------------------------------------- #
# The `hired` command (cw adapter)
# --------------------------------------------------------------------------- #
def _run(argv):
    from hired.__main__ import main

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def test_main_dispatches_with_user_flag(data_dir, monkeypatch):
    pytest.importorskip("cw")
    recs = _write_json(data_dir / "f.json", [{"statement": "knows SQL"}])
    code, out, _ = _run(["ingest", recs, "--user", "alice"])
    assert code == 0 and json.loads(out)["added"] == 1
    monkeypatch.setenv("HIRED_USER", "alice")
    code, out, _ = _run(["facts"])
    assert (code, out) == (0, "knows SQL\n")


def test_main_reports_user_errors_without_traceback():
    pytest.importorskip("cw")
    code, _, err = _run(["status", "--user", "ghost"])
    assert code == 2 and err.startswith("hired: No candidate 'ghost'")
    assert "Traceback" not in err
