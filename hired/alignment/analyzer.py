"""Library-mode autonomous alignment analysis, driven by an injected LLM.

The non-interactive counterpart of the ``hired-align`` skill: given a job
description's text and a candidate's facts, produce a *draft*
:class:`~hired.alignment.base.AlignmentReport` that
:meth:`~hired.candidate.workspace.JDWorkspace.save_alignment` finalizes and
persists. The pipeline is a grounded per-requirement judge:

1. **decompose** — the LLM splits the JD into atomic :class:`Requirement` records;
2. **retrieve** — the most relevant facts are pulled from the knowledge base
   (lexical overlap by default; inject ``retrieve`` for anything better);
3. **quote-then-answer** — the LLM must quote a verbatim span of a cited fact
   *before* it states a match;
4. **gate** — a quote that is not verbatim in the cited fact, a CONTRADICTED
   judgment not backed by a negation fact, or (with ``nli``) a quote that does
   not entail the requirement, drops the judgment to UNKNOWN: it becomes a
   question for the candidate, never an invented match or gap;
5. **aggregate** — the verdict and fit band are computed deterministically from
   the records (:func:`aggregate_verdict`). The LLM explains; it never sets the score.

Like :class:`~hired.content.LLMResumeAgent`, the analyzer is lazy and injectable:
``openai`` (the ``ai`` extra) is imported only when no ``client`` is given, and no
key is read at construction. ``client`` is anything exposing the OpenAI-style
``chat.completions.create``.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from hired.alignment.assemble import is_blocking
from hired.alignment.base import (
    AlignmentReport,
    Bucket,
    Evidence,
    FitBand,
    Recommendation,
    Requirement,
    RequirementClass,
    RequirementRecord,
    ScoreSummary,
    Verdict,
)
from hired.alignment.calibration import (
    MatchCalibrator,
    apply_calibration,
    confidence_level,
    semantic_consistency,
)
from hired.alignment.rubric import classify
from hired.candidate.base import Fact, MatchState

if TYPE_CHECKING:
    from hired.candidate.workspace import JDWorkspace

DFLT_ANALYZER_MODEL = "gpt-4o-mini"
DFLT_TOP_K = 5
DFLT_N_SAMPLES = 1

# How much each requirement class weighs in the coverage score, and how much
# credit each bucket earns. Unresolved (UNKNOWN, open) records are left out.
DFLT_CLASS_WEIGHTS: Mapping[RequirementClass, float] = {
    RequirementClass.GATE_KEEPER: 3.0,
    RequirementClass.DIFFERENTIATOR: 2.0,
    RequirementClass.VALUE_ADD: 1.0,
}
DFLT_BUCKET_CREDIT: Mapping[Bucket, float] = {
    Bucket.STRONG_MATCH: 1.0,
    Bucket.ADJACENT_TRANSFERABLE: 0.5,
    Bucket.GAP_LEARNABLE: 0.25,
    Bucket.GAP_HARD: 0.0,
}
DFLT_APPLY_AT = 0.7
DFLT_STRETCH_AT = 0.4
# Lower edges of the fit bands, by coverage, highest first.
DFLT_FIT_BANDS: Sequence[tuple[float, FitBand]] = (
    (0.85, FitBand.GREAT),
    (0.7, FitBand.GOOD),
    (0.5, FitBand.FAIR),
    (0.3, FitBand.WEAK),
    (0.0, FitBand.POOR),
)
_MAX_KEY_REASONS = 5

_STOPWORDS = frozenset(
    "a an and as at be by for from has have in is it of on or the to with "
    "experience years year strong knowledge ability skills skill using work".split()
)


# --- retrieval ---------------------------------------------------------------


def _tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9+#.]+", text.lower()) if len(t) > 1
    } - _STOPWORDS


def _fact_text(fact: Fact) -> str:
    quotes = " ".join(p.quote or "" for p in fact.provenance)
    return " ".join([fact.statement, quotes, *fact.tags])


def retrieve_facts(
    requirement: Requirement, facts: Iterable[Fact], *, k: int = DFLT_TOP_K
) -> list[Fact]:
    """The ``k`` facts sharing the most words with the requirement (none if none do).

    Lexical, so it misses an adjacent skill named in different words (RabbitMQ
    for Kafka); inject a semantic ``retrieve`` into the analyzer for that.

    >>> from hired.candidate.base import Fact
    >>> fs = [Fact(statement='Ran Kafka clusters'), Fact(statement='Speaks French')]
    >>> [f.statement for f in retrieve_facts(Requirement(text='Kafka streaming'), fs)]
    ['Ran Kafka clusters']
    """
    want = _tokens(requirement.text)
    scored = []
    for i, fact in enumerate(facts):
        have = _tokens(_fact_text(fact))
        overlap = len(want & have)
        if overlap:
            scored.append((overlap / math.sqrt(len(have)), -i, fact))
    scored.sort(key=lambda t: t[:2], reverse=True)
    return [fact for *_, fact in scored[:k]]


# --- the grounding gate -------------------------------------------------------


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def quote_is_grounded(quote: str, fact: Fact) -> bool:
    """True when ``quote`` is a verbatim span (modulo case/whitespace) of ``fact``.

    >>> quote_is_grounded('kafka  CLUSTERS', Fact(statement='Ran Kafka clusters'))
    True
    >>> quote_is_grounded('Kafka expert', Fact(statement='Ran Kafka clusters'))
    False
    """
    q = _norm(quote)
    if not q:
        return False
    spans = [fact.statement, *(p.quote or "" for p in fact.provenance)]
    return any(q in _norm(s) for s in spans)


def _gate(
    judgment: Mapping[str, Any],
    requirement: Requirement,
    facts_by_id: Mapping[str, Fact],
    *,
    entails: Callable[[str, str], bool] | None,
) -> tuple[dict[str, Any], str | None]:
    """Return the judgment, downgraded to UNKNOWN if its grounding fails, and why."""
    j = dict(judgment)
    state = MatchState(j.get("match_state", MatchState.UNKNOWN))
    if state == MatchState.UNKNOWN:
        return j, j.get("uncertainty_reason")
    fact = facts_by_id.get(str(j.get("fact_id", "")))
    quote = str(j.get("quote") or "")
    reason = None
    if fact is None or not quote_is_grounded(quote, fact):
        reason = "the cited quote is not verbatim in any retrieved fact"
    elif state == MatchState.CONTRADICTED and not fact.is_negation:
        reason = "a contradiction needs a negation fact; silence is not absence"
    elif (
        state == MatchState.CONFIRMED
        and entails is not None
        and not entails(quote, requirement.text)
    ):
        reason = "the quote does not entail the requirement"
    if reason:
        j.update(match_state=MatchState.UNKNOWN.value, match_type="none")
    return j, reason


# --- deterministic aggregation -----------------------------------------------


def coverage(
    records: Iterable[RequirementRecord],
    *,
    class_weights: Mapping[RequirementClass, float] = DFLT_CLASS_WEIGHTS,
    bucket_credit: Mapping[Bucket, float] = DFLT_BUCKET_CREDIT,
) -> tuple[float, float]:
    """``(coverage, resolved_share)``: weighted bucket credit over resolved records,
    and the weighted share of records that are resolved at all.

    Records must be classified (see :func:`~hired.alignment.rubric.classify`).
    """
    earned = resolved = total = 0.0
    for r in records:
        w = class_weights.get(r.requirement.requirement_class, 1.0)
        total += w
        if r.bucket is not None:
            resolved += w
            earned += w * bucket_credit.get(r.bucket, 0.0)
    return (earned / resolved if resolved else 0.0), (
        resolved / total if total else 0.0
    )


def aggregate_verdict(
    records: Sequence[RequirementRecord],
    *,
    apply_at: float = DFLT_APPLY_AT,
    stretch_at: float = DFLT_STRETCH_AT,
    fit_bands: Sequence[tuple[float, FitBand]] = DFLT_FIT_BANDS,
    class_weights: Mapping[RequirementClass, float] = DFLT_CLASS_WEIGHTS,
    bucket_credit: Mapping[Bucket, float] = DFLT_BUCKET_CREDIT,
) -> tuple[Verdict, FitBand]:
    """The verdict and fit band, computed from classified records alone.

    A blocking gap (a gate-keeper that is a hard gap or contradicted) means
    *do not apply*; otherwise the weighted coverage picks the recommendation.
    Confidence comes from how much of the JD is resolved, not from the LLM.

    >>> from hired.alignment.base import MatchType
    >>> rec = classify(RequirementRecord(requirement=Requirement(text='Python'),
    ...     match_state='confirmed', match_type=MatchType.DIRECT, candidate_level=4))
    >>> verdict, band = aggregate_verdict([rec])
    >>> verdict.recommendation.value, band.value, verdict.confidence.value
    ('apply', 'great', 'high')
    """
    cov, resolved = coverage(
        records, class_weights=class_weights, bucket_credit=bucket_credit
    )
    blockers = [r for r in records if is_blocking(r)]
    if blockers:
        rec = Recommendation.DO_NOT_APPLY
    elif cov >= apply_at:
        rec = Recommendation.APPLY
    elif cov >= stretch_at:
        rec = Recommendation.STRETCH
    else:
        rec = Recommendation.DO_NOT_APPLY
    band = next((b for edge, b in fit_bands if cov >= edge), fit_bands[-1][1])
    n_open = sum(1 for r in records if r.bucket is None)
    reasons = [f"Blocking gap: {r.requirement.text}" for r in blockers]
    reasons += [
        f"{r.bucket.value.replace('_', ' ')}: {r.requirement.text}"
        for r in records
        if r.bucket is not None and r not in blockers
    ]
    verdict = Verdict(
        recommendation=rec,
        confidence=confidence_level(resolved),
        confidence_basis=(
            f"{resolved:.0%} of the weighted requirements resolved; "
            f"{n_open} open question(s)"
        ),
        headline=f"{rec.value.replace('_', ' ')}: {cov:.0%} weighted coverage",
        key_reasons=reasons[:_MAX_KEY_REASONS],
        has_blocking_gaps=bool(blockers),
    )
    return verdict, band


# --- the LLM side --------------------------------------------------------------

_DECOMPOSE_PROMPT = (
    "Split the job description into atomic requirements. Copy each requirement's "
    "text verbatim from the JD. Return ONLY a JSON object "
    '{"requirements": [{"text": str, "skill_type": one of technical|domain_knowledge|'
    'soft_skill|credential, "requirement_class": one of gate_keeper|differentiator|'
    'value_add, "required_level": int 0-5}]}.'
)

_JUDGE_PROMPT = (
    "You judge whether a candidate meets ONE job requirement, using ONLY the "
    "numbered facts given. First copy a verbatim quote from one fact, then answer. "
    "If no fact settles it, answer unknown: never assume absence. Answer "
    "contradicted only when a fact says the candidate lacks it. Return ONLY a JSON "
    'object {"fact_id": str, "quote": str, "match_state": confirmed|contradicted|'
    'unknown, "match_type": direct|adjacent|none, "candidate_level": int 0-5, '
    '"source_skill": str|null, "adjacency_basis": str|null, "closeability": '
    "quick_win|learnable|requires_experience|structurally_hard|null, "
    '"ai_leverage": high|medium|low|none, "explanation": str}.'
)

_ENTAIL_PROMPT = (
    "Does the PREMISE, on its own, establish the HYPOTHESIS about the candidate? "
    'Return ONLY a JSON object {"entails": true|false}.'
)

_JUDGMENT_FIELDS = (
    "match_state",
    "match_type",
    "candidate_level",
    "source_skill",
    "adjacency_basis",
    "closeability",
    "ai_leverage",
)


def _facts_block(facts: Sequence[Fact]) -> str:
    return "\n".join(
        f"[{f.id}]{' (NEGATION)' if f.is_negation else ''} {f.statement}"
        for f in facts
    )


class LLMAlignmentAnalyzer:
    """Draft an alignment report from JD text and facts, with an injected LLM.

    ``n_samples`` > 1 judges each requirement several times and feeds the
    agreement into :func:`~hired.alignment.calibration.apply_calibration` (with
    ``calibrator``, the conformal ask/auto-decide rule). ``nli`` adds an
    entailment check on every confirmed quote; ``entails`` replaces the default
    (an LLM call) with any ``(premise, hypothesis) -> bool``. ``retrieve``
    replaces the lexical :func:`retrieve_facts`.

    >>> class _Fake:  # doctest: +SKIP
    ...     class chat:
    ...         class completions:
    ...             @staticmethod
    ...             def create(**_): ...
    >>> LLMAlignmentAnalyzer(client=_Fake()).analyze(jd_text, facts)  # doctest: +SKIP
    """

    def __init__(
        self,
        *,
        model: str = DFLT_ANALYZER_MODEL,
        client: Any | None = None,
        api_key: str | None = None,
        n_samples: int = DFLT_N_SAMPLES,
        temperature: float | None = None,
        calibrator: MatchCalibrator | None = None,
        retrieve: Callable[..., list[Fact]] = retrieve_facts,
        top_k: int = DFLT_TOP_K,
        nli: bool = False,
        entails: Callable[[str, str], bool] | None = None,
    ) -> None:
        if n_samples < 1:
            raise ValueError(f"n_samples must be >= 1, got {n_samples}")
        self._model = model
        self._client = client
        self._api_key = api_key
        self.n_samples = n_samples
        self.temperature = temperature
        self.calibrator = calibrator
        self.retrieve = retrieve
        self.top_k = top_k
        self.entails = entails or (self.llm_entails if nli else None)

    @property
    def client(self) -> Any:
        if self._client is None:
            import openai  # lazy: only required when actually analysing

            self._client = openai.OpenAI(api_key=self._api_key)
        return self._client

    def _ask_json(self, system: str, user: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        response = self.client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            **kwargs,
        )
        return json.loads(response.choices[0].message.content)

    # --- steps --------------------------------------------------------------
    def decompose(self, jd_text: str) -> list[Requirement]:
        """The JD's atomic requirements, as the LLM extracts them."""
        data = self._ask_json(_DECOMPOSE_PROMPT, f"JOB DESCRIPTION:\n{jd_text}")
        return [
            Requirement.model_validate({**r, "id": r.get("id") or f"req-{i + 1}"})
            for i, r in enumerate(data.get("requirements", []))
        ]

    def llm_entails(self, premise: str, hypothesis: str) -> bool:
        """The LLM's yes/no on whether ``premise`` establishes ``hypothesis``."""
        data = self._ask_json(
            _ENTAIL_PROMPT, f"PREMISE: {premise}\nHYPOTHESIS: {hypothesis}"
        )
        return bool(data.get("entails"))

    def judge(
        self, requirement: Requirement, facts: Sequence[Fact]
    ) -> RequirementRecord:
        """One gated, optionally sampled-and-calibrated record for ``requirement``."""
        if not facts:
            return RequirementRecord(
                requirement=requirement,
                uncertainty_reason="no fact in the knowledge base mentions this",
            )
        by_id = {f.id: f for f in facts}
        prompt = (
            f"REQUIREMENT: {requirement.text}\n\nFACTS:\n{_facts_block(facts)}"
        )
        gated = [
            _gate(
                self._ask_json(_JUDGE_PROMPT, prompt),
                requirement,
                by_id,
                entails=self.entails,
            )
            for _ in range(self.n_samples)
        ]
        states = [MatchState(j.get("match_state", "unknown")) for j, _ in gated]
        majority = semantic_consistency(states).majority
        judgment, reason = next(g for g, s in zip(gated, states) if s == majority)
        record = _record_from(requirement, judgment, by_id, reason=reason)
        if self.n_samples > 1:
            apply_calibration(record, states, calibrator=self.calibrator)
        return record

    def analyze(
        self,
        jd_text: str,
        facts: Iterable[Fact],
        *,
        job_id: str = "job",
        job_title: str = "",
        company: str = "",
        requirements: Sequence[Requirement] | None = None,
    ) -> AlignmentReport:
        """A draft report: decompose (unless ``requirements`` given), judge, aggregate."""
        facts = list(facts)
        reqs = (
            list(requirements) if requirements is not None else self.decompose(jd_text)
        )
        records = [
            classify(self.judge(r, self.retrieve(r, facts, k=self.top_k)))
            for r in reqs
        ]
        verdict, band = aggregate_verdict(records)
        return AlignmentReport(
            job_id=job_id,
            job_title=job_title,
            company=company,
            verdict=verdict,
            score_summary=ScoreSummary(fit_band=band),
            requirements=records,
        )


def _record_from(
    requirement: Requirement,
    judgment: Mapping[str, Any],
    facts_by_id: Mapping[str, Fact],
    *,
    reason: str | None,
) -> RequirementRecord:
    fields = {k: judgment[k] for k in _JUDGMENT_FIELDS if judgment.get(k) is not None}
    fact = facts_by_id.get(str(judgment.get("fact_id", "")))
    evidence = None
    if fact is not None and reason is None and judgment.get("quote"):
        evidence = Evidence(
            quote=str(judgment["quote"]),
            source_document_id=fact.id,
            locator=fact.provenance[0].locator if fact.provenance else "",
        )
    return RequirementRecord.model_validate(
        {
            "requirement": requirement,
            **fields,
            "evidence": evidence,
            "uncertainty_reason": reason,
            "talking_point": judgment.get("explanation") or None,
        }
    )


def analyze_jd(
    workspace: JDWorkspace,
    jd_text: str,
    *,
    job_id: str,
    job_title: str = "",
    analyzer: LLMAlignmentAnalyzer | None = None,
    requirements: Sequence[Requirement] | None = None,
) -> AlignmentReport:
    """Analyse ``jd_text`` against the workspace candidate's facts and persist it.

    The draft goes through :meth:`JDWorkspace.save_alignment` (finalize + archive +
    save), the one path from a draft to a stored report. ``analyzer`` defaults to
    an :class:`LLMAlignmentAnalyzer` on the ``ai`` extra.
    """
    analyzer = analyzer or LLMAlignmentAnalyzer()
    draft = analyzer.analyze(
        jd_text,
        workspace.kb.facts(),
        job_id=job_id,
        job_title=job_title,
        company=workspace.meta.get("company") or "",
        requirements=requirements,
    )
    return workspace.save_alignment(draft)
