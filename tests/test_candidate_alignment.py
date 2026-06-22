"""Tests for the candidate-knowledge + JD-alignment subsystem (epic #4, Phase 1).

All persistence is redirected to a temp dir via ``HIRED_DATA_DIR`` so nothing
touches the real data root, and no real candidate data is used.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv('HIRED_DATA_DIR', str(tmp_path))
    yield tmp_path


# --------------------------------------------------------------------------- #
# Persistence foundation
# --------------------------------------------------------------------------- #
def test_app_data_dir_honors_env(tmp_path):
    from hired.persistence import app_data_dir

    root = app_data_dir()
    assert str(root).startswith(str(tmp_path))
    assert os.path.isdir(root)
    assert app_data_dir('users', 'me').endswith(os.path.join('users', 'me'))


def test_candidate_mall_roundtrip_and_kinds():
    from hired.persistence import CandidateMall

    mall = CandidateMall()
    assert sorted(mall.keys()) == [
        'facts', 'jobs', 'qa', 'reports', 'synopsis', 'uploads'
    ]
    mall['facts']['f1'] = {'statement': 'x'}
    assert mall['facts', 'f1'] == {'statement': 'x'}
    mall['uploads']['cv.bin'] = b'bytes'
    assert mall['uploads']['cv.bin'] == b'bytes'


def test_repository_validates_models():
    from pydantic import BaseModel
    from hired.persistence import Repository, json_store, app_data_dir

    class Thing(BaseModel):
        id: str
        n: int

    repo = Repository(json_store(app_data_dir('things')), model=Thing)
    repo.add(Thing(id='t1', n=7))
    assert repo.get('t1').n == 7
    assert [t.id for t in repo.values()] == ['t1']


# --------------------------------------------------------------------------- #
# Candidate knowledge base
# --------------------------------------------------------------------------- #
def test_kb_add_query_and_open_world_negation():
    from hired.candidate import CandidateKnowledgeBase, Fact, FactCategory

    kb = CandidateKnowledgeBase()
    kb.add_fact(Fact(statement='Knows Python', category=FactCategory.SKILL,
                     tags=['python']))
    kb.add_fact(Fact(statement='Has not done X', category=FactCategory.SKILL,
                     is_negation=True))
    skills = list(kb.facts(category=FactCategory.SKILL))
    assert len(skills) == 2
    # Open-world: a negation is an explicit assertion, not silence.
    negs = [f for f in kb.facts() if f.is_negation]
    assert [f.statement for f in negs] == ['Has not done X']
    # Tag filter
    assert [f.statement for f in kb.facts(tags=['python'])] == ['Knows Python']


def test_kb_supersession_hides_old_fact():
    from hired.candidate import CandidateKnowledgeBase, Fact

    kb = CandidateKnowledgeBase()
    old_id = kb.add_fact(Fact(statement='5 years experience'))
    kb.supersede(old_id, Fact(statement='6 years experience'))
    current = [f.statement for f in kb.facts()]
    assert current == ['6 years experience']  # superseded one hidden by default


def test_ingest_quote_invariant_drops_unverifiable_quote():
    from hired.candidate import CandidateKnowledgeBase, SourceKind
    from hired.candidate.ingest import ingest_facts

    kb = CandidateKnowledgeBase()
    source = 'Built ML systems in Python.'
    good = ingest_facts(
        kb,
        [{'statement': 'Built ML', 'quote': 'Built ML systems in Python'}],
        source_kind=SourceKind.UPLOAD, source_text=source,
    )
    assert kb.get_fact(good[0]).provenance[0].quote is not None

    bad = ingest_facts(
        kb,
        [{'statement': 'Claims Z', 'quote': 'not present anywhere'}],
        source_kind=SourceKind.UPLOAD, source_text=source,
    )
    assert kb.get_fact(bad[0]).provenance[0].quote is None  # dropped


def test_ingest_strict_mode_raises_on_bad_quote():
    from hired.candidate import CandidateKnowledgeBase, SourceKind
    from hired.candidate.ingest import ingest_facts

    kb = CandidateKnowledgeBase()
    with pytest.raises(ValueError):
        ingest_facts(
            kb,
            [{'statement': 'x', 'quote': 'nope'}],
            source_kind=SourceKind.UPLOAD, source_text='abc',
            drop_unverified_quotes=False,
        )


def test_synopsis_is_regenerated_projection():
    from hired.candidate import CandidateKnowledgeBase, Fact, FactCategory

    kb = CandidateKnowledgeBase()
    kb.add_fact(Fact(statement='Knows Python', category=FactCategory.SKILL))
    text = kb.regenerate_synopsis()
    assert 'Knows Python' in text and '## skill' in text


# --------------------------------------------------------------------------- #
# Alignment rubric (the two-axis truth table + AI-leverage)
# --------------------------------------------------------------------------- #
def _mk(**kw):
    from hired.alignment import (Requirement, RequirementRecord, classify,
                                 MatchType, AILeverage, SkillType,
                                 RequirementClass, FieldCompleteness)
    from hired.candidate.base import MatchState

    req = Requirement(
        text=kw.get('text', 'req'),
        required_level=kw.get('req', 4),
        skill_type=kw.get('stype', SkillType.TECHNICAL),
        requirement_class=kw.get('rclass', RequirementClass.DIFFERENTIATOR),
    )
    return classify(RequirementRecord(
        requirement=req,
        match_state=kw.get('state', MatchState.UNKNOWN),
        match_type=kw.get('mtype', MatchType.NONE),
        candidate_level=kw.get('cand', 0),
        closeability=kw.get('close'),
        ai_leverage=kw.get('ai', AILeverage.NONE),
        field_completeness=kw.get('fc', FieldCompleteness.OPEN),
    ))


def test_rubric_truth_table():
    from hired.alignment import (Bucket, MatchType, Closeability, AILeverage,
                                 SkillType, FieldCompleteness)
    from hired.candidate.base import MatchState

    assert _mk(state=MatchState.CONFIRMED, mtype=MatchType.DIRECT, cand=5).bucket \
        == Bucket.STRONG_MATCH
    assert _mk(state=MatchState.CONFIRMED, mtype=MatchType.ADJACENT, cand=2).bucket \
        == Bucket.ADJACENT_TRANSFERABLE
    assert _mk(state=MatchState.CONTRADICTED, close=Closeability.LEARNABLE).bucket \
        == Bucket.GAP_LEARNABLE
    # Tacit/soft gap is NOT rescued by AI leverage.
    assert _mk(state=MatchState.CONTRADICTED, close=Closeability.REQUIRES_EXPERIENCE,
               stype=SkillType.SOFT_SKILL, ai=AILeverage.HIGH).bucket == Bucket.GAP_HARD
    # Codified gap IS softened by high AI leverage.
    assert _mk(state=MatchState.CONTRADICTED, close=Closeability.REQUIRES_EXPERIENCE,
               ai=AILeverage.HIGH).bucket == Bucket.GAP_LEARNABLE


def test_unknown_open_routes_to_clarification_not_gap():
    from hired.candidate.base import MatchState

    rec = _mk(state=MatchState.UNKNOWN)  # open field
    assert rec.bucket is None
    assert rec.needs_clarification is True


def test_unknown_closed_is_a_real_gap():
    from hired.alignment import Bucket, Closeability, FieldCompleteness
    from hired.candidate.base import MatchState

    rec = _mk(state=MatchState.UNKNOWN, fc=FieldCompleteness.CLOSED,
              close=Closeability.STRUCTURALLY_HARD)
    assert rec.bucket == Bucket.GAP_HARD
    assert rec.needs_clarification is False


# --------------------------------------------------------------------------- #
# Elicitation
# --------------------------------------------------------------------------- #
def test_elicitation_ranks_and_detects_stability():
    from hired.alignment import (rank_clarifications, is_decision_stable,
                                 RequirementClass)
    from hired.candidate.base import MatchState

    gate = _mk(state=MatchState.UNKNOWN, rclass=RequirementClass.GATE_KEEPER)
    diff = _mk(state=MatchState.UNKNOWN, rclass=RequirementClass.DIFFERENTIATOR)
    nice = _mk(state=MatchState.UNKNOWN, rclass=RequirementClass.VALUE_ADD)
    recs = [diff, gate, nice]
    clar = rank_clarifications(recs)
    # value-add is not decision-relevant -> not asked; gate ranks above diff.
    asked = [c.requirement_id for c in clar]
    assert gate.requirement.id == asked[0]
    assert nice.requirement.id not in asked
    assert is_decision_stable(recs) is False
    # When nothing askable remains, it's stable.
    from hired.candidate.base import MatchState as MS
    resolved = [_mk(state=MS.CONFIRMED, mtype=__import__(
        'hired.alignment', fromlist=['MatchType']).MatchType.DIRECT, cand=5)]
    assert is_decision_stable(resolved) is True


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #
def test_report_renders_markdown():
    from hired.alignment import (AlignmentReport, Verdict, Recommendation,
                                 ScoreSummary, FitBand, render_report_markdown,
                                 MatchType)
    from hired.candidate.base import MatchState

    rep = AlignmentReport(
        job_id='j1', job_title='Head of DS', company='Acme',
        verdict=Verdict(recommendation=Recommendation.STRETCH,
                        headline='Strong core.', key_reasons=['Deep ML']),
        score_summary=ScoreSummary(fit_band=FitBand.GOOD,
                                   bucket_counts={'strong_match': 1}),
        requirements=[_mk(state=MatchState.CONFIRMED, mtype=MatchType.DIRECT,
                          cand=5, text='Python')],
    )
    md = render_report_markdown(rep)
    assert '# Alignment: Head of DS — Acme' in md
    assert 'Verdict: STRETCH' in md
    assert '✅ Strong match' in md and 'Python' in md
