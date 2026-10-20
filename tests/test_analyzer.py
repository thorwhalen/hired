"""Library-mode analyzer (#11): a fake injected LLM drives the whole pipeline.

No network, no secrets, no candidate data: synthetic facts and a scripted client.
"""

import json
from types import SimpleNamespace

import pytest

from hired.alignment import (
    Bucket,
    LLMAlignmentAnalyzer,
    MatchCalibrator,
    Recommendation,
    Requirement,
    RequirementClass,
    RequirementRecord,
    aggregate_verdict,
    analyze_jd,
    classify,
    quote_is_grounded,
    retrieve_facts,
)
from hired.alignment.base import Decision
from hired.candidate import CandidateKnowledgeBase
from hired.candidate.base import Fact, MatchState

JD = "We need Python. Kafka streaming is a must. A PhD in physics is required."

PY = Fact(id="f-py", statement="Built ML pipelines in Python for five years")
KAFKA = Fact(id="f-kafka", statement="Ran RabbitMQ message queues for event streaming")
NO_PHD = Fact(id="f-phd", statement="Does not hold a PhD in physics", is_negation=True)
FACTS = [PY, KAFKA, NO_PHD]

DECOMPOSITION = {
    "requirements": [
        {"text": "Python", "required_level": 3},
        {"text": "Kafka streaming", "required_level": 3},
        {
            "text": "PhD in physics",
            "skill_type": "credential",
            "requirement_class": "gate_keeper",
        },
    ]
}


class FakeLLM:
    """An OpenAI-style client whose answers come from ``judge(user_prompt)``."""

    def __init__(self, judge, *, entails=True):
        self.calls = []
        self._judge, self._entails = judge, entails
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, *, model, messages, **kwargs):
        system, user = messages[0]["content"], messages[1]["content"]
        self.calls.append((system, user, kwargs))
        if system.startswith("Split the job"):
            out = DECOMPOSITION
        elif system.startswith("Does the PREMISE"):
            out = {"entails": self._entails}
        else:
            out = self._judge(user)
        msg = SimpleNamespace(content=json.dumps(out))
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def honest_judge(user):
    if "REQUIREMENT: Python" in user:
        return {
            "fact_id": "f-py",
            "quote": "ML pipelines in Python",
            "match_state": "confirmed",
            "match_type": "direct",
            "candidate_level": 4,
            "explanation": "Five years of Python pipelines.",
        }
    if "REQUIREMENT: Kafka" in user:
        return {
            "fact_id": "f-kafka",
            "quote": "RabbitMQ message queues",
            "match_state": "confirmed",
            "match_type": "adjacent",
            "candidate_level": 2,
            "source_skill": "RabbitMQ",
            "adjacency_basis": "both are message brokers",
        }
    return {
        "fact_id": "f-phd",
        "quote": "Does not hold a PhD",
        "match_state": "contradicted",
        "closeability": "structurally_hard",
    }


def _by_text(report):
    return {r.requirement.text: r for r in report.requirements}


def test_full_pipeline_buckets_and_deterministic_verdict():
    llm = FakeLLM(honest_judge)
    report = LLMAlignmentAnalyzer(client=llm).analyze(JD, FACTS, job_id="ds")
    recs = _by_text(report)
    assert recs["Python"].bucket == Bucket.STRONG_MATCH
    assert recs["Python"].evidence.source_document_id == "f-py"
    assert recs["Kafka streaming"].bucket == Bucket.ADJACENT_TRANSFERABLE
    assert recs["PhD in physics"].match_state == MatchState.CONTRADICTED
    # the gate-keeper blocks, whatever the LLM's tone
    assert report.verdict.recommendation == Recommendation.DO_NOT_APPLY
    assert report.verdict.has_blocking_gaps


def test_ungrounded_quote_drops_to_unknown():
    def liar(user):
        out = honest_judge(user)
        if "REQUIREMENT: Python" in user:
            out = {**out, "quote": "Python expert, 10 years"}  # not in the fact
        return out

    report = LLMAlignmentAnalyzer(client=FakeLLM(liar)).analyze(JD, FACTS)
    py = _by_text(report)["Python"]
    assert py.match_state == MatchState.UNKNOWN
    assert py.bucket is None and py.needs_clarification
    assert py.evidence is None and "verbatim" in py.uncertainty_reason


def test_contradiction_needs_a_negation_fact():
    def assumes_absence(user):
        if "REQUIREMENT: Kafka" in user:
            return {
                "fact_id": "f-kafka",
                "quote": "RabbitMQ",
                "match_state": "contradicted",
            }
        return honest_judge(user)

    report = LLMAlignmentAnalyzer(client=FakeLLM(assumes_absence)).analyze(JD, FACTS)
    assert _by_text(report)["Kafka streaming"].match_state == MatchState.UNKNOWN


def test_no_retrieved_fact_skips_the_llm():
    llm = FakeLLM(honest_judge)
    rec = LLMAlignmentAnalyzer(client=llm).judge(Requirement(text="Rust"), [])
    assert rec.match_state == MatchState.UNKNOWN and not llm.calls


def test_nli_gate_rejects_non_entailing_quotes():
    llm = FakeLLM(honest_judge, entails=False)
    report = LLMAlignmentAnalyzer(client=llm, nli=True).analyze(JD, FACTS)
    assert _by_text(report)["Python"].match_state == MatchState.UNKNOWN
    # an injected entailment checker replaces the LLM one
    report = LLMAlignmentAnalyzer(
        client=FakeLLM(honest_judge), entails=lambda p, h: True
    ).analyze(JD, FACTS)
    assert _by_text(report)["Python"].bucket == Bucket.STRONG_MATCH


def test_sampling_feeds_calibration():
    answers = iter(["confirmed", "confirmed", "unknown"])

    def wobbly(user):
        return {**honest_judge("REQUIREMENT: Python"), "match_state": next(answers)}

    cal = MatchCalibrator(match_threshold=0.5, no_match_threshold=0.5)
    an = LLMAlignmentAnalyzer(
        client=FakeLLM(wobbly), n_samples=3, temperature=1.0, calibrator=cal
    )
    rec = an.judge(Requirement(text="Python"), [PY])
    assert rec.match_state == MatchState.CONFIRMED  # the majority
    assert rec.match_score == pytest.approx(2 / 3)
    assert rec.confidence.value == "medium"
    assert rec.calibrated_decision == Decision.AUTO_MATCH
    assert an.client.calls[0][2]["temperature"] == 1.0


def test_given_requirements_skip_decomposition():
    llm = FakeLLM(honest_judge)
    report = LLMAlignmentAnalyzer(client=llm).analyze(
        JD, FACTS, requirements=[Requirement(text="Python")]
    )
    assert [r.requirement.text for r in report.requirements] == ["Python"]
    assert not any(s.startswith("Split") for s, *_ in llm.calls)
    assert report.verdict.recommendation == Recommendation.APPLY


def test_aggregate_verdict_ignores_unresolved_and_bands_coverage():
    strong = classify(
        RequirementRecord(
            requirement=Requirement(text="Python"),
            match_state="confirmed",
            match_type="direct",
            candidate_level=5,
        )
    )
    unknown = classify(RequirementRecord(requirement=Requirement(text="Go")))
    verdict, band = aggregate_verdict([strong, unknown])
    assert verdict.recommendation == Recommendation.APPLY
    assert verdict.confidence.value == "low"  # half the JD is still open
    assert "1 open question" in verdict.confidence_basis
    hard = classify(
        RequirementRecord(
            requirement=Requirement(text="Scala"),
            match_state="contradicted",
            closeability="structurally_hard",
        )
    )
    verdict, band = aggregate_verdict([hard])
    assert verdict.recommendation == Recommendation.DO_NOT_APPLY
    assert band.value == "poor"


def test_retrieve_and_grounding_helpers():
    got = retrieve_facts(Requirement(text="Python pipelines"), FACTS, k=1)
    assert got == [PY]
    assert quote_is_grounded("does NOT hold", NO_PHD)
    assert not quote_is_grounded("", PY)


def test_analyze_jd_persists_through_save_alignment(tmp_path, monkeypatch):
    monkeypatch.setenv("HIRED_DATA_DIR", str(tmp_path))
    kb = CandidateKnowledgeBase()
    kb.add_facts(FACTS)
    ws = kb.jd("acme", company="Acme")
    report = analyze_jd(
        ws,
        JD,
        job_id="staff-ds",
        analyzer=LLMAlignmentAnalyzer(client=FakeLLM(honest_judge)),
    )
    assert ws.reports() == ["staff-ds"]
    assert report.company == "Acme" and report.created_at
    assert [r.requirement.text for r in report.blocking_gaps] == ["PhD in physics"]
    assert report.score_summary.bucket_counts["strong_match"] == 1


def test_constructing_reads_no_key_and_imports_no_openai():
    an = LLMAlignmentAnalyzer()
    assert an._client is None  # openai is imported only on first use
    with pytest.raises(ValueError):
        LLMAlignmentAnalyzer(n_samples=0)
    _ = RequirementClass  # re-exported surface stays importable


def test_malformed_llm_output_degrades_to_unknown_not_a_crash():
    replies = iter(
        [
            "not json at all",
            '```json\n{"fact_id": "f-py", "quote": "ML pipelines in Python", '
            '"match_state": "PARTIAL", "closeability": "soonish"}\n```',
        ]
    )

    class Raw(FakeLLM):
        def _create(self, *, model, messages, **kwargs):
            msg = SimpleNamespace(content=next(replies))
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    an = LLMAlignmentAnalyzer(client=Raw(honest_judge))
    for _ in range(2):
        rec = an.judge(Requirement(text="Python"), [PY])
        assert rec.match_state == MatchState.UNKNOWN and rec.evidence is None


def test_bad_decomposition_items_are_skipped_or_defaulted():
    global DECOMPOSITION
    saved = DECOMPOSITION
    DECOMPOSITION = {
        "requirements": [
            "Python",
            {"skill_type": "technical"},
            {"text": "Go", "requirement_class": "must_have"},
        ]
    }
    try:
        reqs = LLMAlignmentAnalyzer(client=FakeLLM(honest_judge)).decompose(JD)
    finally:
        DECOMPOSITION = saved
    assert [(r.text, r.requirement_class) for r in reqs] == [
        ("Go", RequirementClass.DIFFERENTIATOR)
    ]
    with pytest.raises(ValueError, match="no requirements"):
        LLMAlignmentAnalyzer(client=FakeLLM(honest_judge)).analyze(
            JD, FACTS, requirements=[]
        )


def test_confirmed_on_a_negation_fact_and_ties_stay_unknown():
    def confirms_negation(user):
        return {"fact_id": "f-phd", "quote": "a PhD in physics", "match_state": "confirmed"}

    an = LLMAlignmentAnalyzer(client=FakeLLM(confirms_negation))
    assert an.judge(Requirement(text="PhD physics"), [NO_PHD]).match_state == (
        MatchState.UNKNOWN
    )
    answers = iter(["confirmed", "unknown"])

    def split(user):
        return {**honest_judge("REQUIREMENT: Python"), "match_state": next(answers)}

    rec = LLMAlignmentAnalyzer(client=FakeLLM(split), n_samples=2).judge(
        Requirement(text="Python"), [PY]
    )
    assert rec.match_state == MatchState.UNKNOWN and rec.match_score == 0.5


def test_small_kb_passes_every_fact_and_large_kb_stays_lexical():
    from hired.candidate.base import Fact

    rabbit = Fact(statement="Ran RabbitMQ in production")
    req = Requirement(text="Kafka streaming")
    assert retrieve_facts(req, [rabbit], k=5) == [rabbit]  # fits in k: passed
    assert retrieve_facts(req, [rabbit], k=5, small_kb_passes_all=False) == []
    many = [rabbit] + [Fact(statement=f"Skill number {i}") for i in range(5)]
    assert retrieve_facts(req, many, k=5) == []  # beyond k: lexical only


def test_embedding_retriever_reaches_adjacent_skills_and_caches():
    from hired.alignment import make_embedding_retriever
    from hired.candidate.base import Fact

    calls = []

    def embed(texts):
        calls.append(list(texts))
        queue = lambda t: float("kafka" in t.lower() or "rabbitmq" in t.lower())
        return [[queue(t), float("french" in t.lower())] for t in texts]

    rabbit, french = Fact(statement="Ran RabbitMQ"), Fact(statement="Speaks French")
    many = [french, rabbit] + [Fact(statement=f"Other {i}") for i in range(10)]
    retrieve = make_embedding_retriever(embed)
    assert retrieve(Requirement(text="Kafka"), many, k=1) == [rabbit]
    assert retrieve(Requirement(text="French"), many, k=1) == [french]
    assert sum(len(c) for c in calls) == len(many) + 2  # facts embedded once
