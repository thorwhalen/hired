# Honest resume↔JD alignment analysis — research synthesis

*For building an explainable, non-exaggerating alignment report (strong-match / adjacent-transferable / gap-hard / gap-learnable).*

## The one idea that runs through everything

Decompose the JD into atomic requirements → judge each one grounded in a quoted resume span → keep **"unknown" a first-class state distinct from "absent"** → aggregate deterministically → ask the candidate about the high-value unknowns. A single holistic "85% match" number correlates poorly with real recruiters, rewards keyword stuffing, and is least defensible. The honest report is *per-requirement, evidence-grounded, and explicit about what it doesn't know*.

## Existing tools — what to copy, what to avoid

Most "match score" products are keyword-overlap engines despite "AI" branding. Only one mainstream product (Huntr) documents a genuinely semantic approach.

**Copy from Huntr:** weight qualifications/responsibilities above keywords, cap keyword influence (<20%) to defeat stuffing, give per-requirement rationale, show categorical bands (Poor→Great) over false-precision percentages. **Copy from Careerflow/Rezi:** a partial/middle tier + per-requirement priority (must-have/preferred/optional).

**Avoid:** pure keyword-overlap % (vanity metric, rewards stuffing; a near-100 score is a red flag). **Reality check:** the "ATS auto-rejects 75% on keyword match" claim is largely a myth; real auto-rejects are knockout/eligibility questions and over-rigid employer filters. **Implication: the match score is a UX decision-aid, not a gate** — exactly the honest framing wanted. **Bias/legal:** keep a human as decision-maker; strip demographic signals (Amazon's scrapped recruiter, NYC Local Law 144).

## Technique stack for semantic person-job fit

Four complementary layers (not competitors):

| Family | Decision accuracy | Cost | Explainability | Hallucination | Role |
|---|---|---|---|---|---|
| Embedding similarity | low–med | lowest | low | none | retrieval/shortlist |
| Structured extraction + taxonomy | med–high | low | **highest** | low | auditable skill scoring |
| LLM-as-judge/rubric | med (high if grounded) | low | med | **high unless grounded** | decision aid + rationale |
| Hybrid RAG + grounding | **highest** | highest | **highest** | **lowest** | final defensible verdict |

Key facts shaping the design:
- **Don't compare whole-resume to whole-JD by cosine** (averaging dilutes; transformer embeddings are anisotropic). Chunk to requirement/passage level; prefer late-interaction (ColBERT MaxSim) for token attribution.
- **Structured extraction + skills taxonomy is the explainability backbone.** Extract resume→JSON Resume, JD→requirements; normalize skills to ESCO via SkillNER (MIT, local). Ontology hierarchy gives partial credit with the path as the explanation.
- **LLM-as-judge: binary-per-criterion, not 1–10.** Fine-grained Likert is "arbitrary and prone to randomness." Derive any number by weighting grounded binary verdicts; never ask the model for a raw 0–100. Mitigate bias with swap-and-average; validate the judge against human labels.
- **Grounding is the hallucination fix.** Decompose → retrieve resume spans → judge each requirement with a verbatim quote → gate with an NLI entailment check → aggregate deterministically. Separate the deterministic scoring layer from the generative explanation layer (LLM explains but never sets the score).

**Recommended stack — lightweight-first, LLM-optional, explainable:**
- **Layer 0 — Shortlist (always on, no secrets):** bi-encoder retrieval, chunked to requirement level.
- **Layer 1 — Auditable per-skill comparison (core, NO LLM):** extract → JSON Resume/JD requirements; normalize via taxonomy; field-by-field compare (skill coverage w/ partial credit, years-of-experience math, education/seniority gates). **This layer alone yields a complete, auditable, zero-hallucination, zero-API-cost report.**
- **Layer 2 — Grounded per-requirement judge (opt-in LLM, `ai` extra):** for requirements the taxonomy can't resolve, retrieve-then-judge with quote-then-answer + NLI gate + deterministic aggregation.

## Unknown vs absent — the honesty engine

The heart of "honest": **"not in the profile" is missing data, not a confirmed negative.**

**Three-state requirement match (open-world + Kleene K3 logic):** `MatchState ∈ {CONFIRMED, CONTRADICTED, UNKNOWN}`.
- `CONFIRMED` — positively established (resume span or candidate answer).
- `CONTRADICTED` — positively established *absence* (candidate said "no", OR a complete/closed field lacks it).
- `UNKNOWN` — not addressed in an open/incomplete field. **Default for anything not present. Never the silent result of "didn't find it."**

Aggregate with three-valued logic (the logic behind SQL NULL): `T AND U = U` (a merely-unknown requirement leaves the verdict unknown → *ask*, never auto-fail); `F AND U = F` (a contradicted hard requirement fails). **The bug to avoid:** SQL's `WHERE` lumps Unknown into False — never copy that; carry `unknown` all the way to the UI. Treating "no evidence" as "false" is the argument from ignorance; **asking the candidate is the act of looking** that soundly converts `unknown`→`false`.

**Per-field open/closed metadata (Local Closed-World Assumption):** open by default, locally closed on fields you exhaustively collect.
- **Closed fields** (degrees, certifications uploaded, work authorization): `missing → false` is sound.
- **Open fields** (free-text, soft skills, niche tooling): `missing → unknown`, and you ask.

**Calibrated confidence, not self-report:** LLM verbalized confidence and logprobs are systematically overconfident. The robust signal is multi-sample semantic consistency (sample 5–10×, cluster by meaning, high entropy = guessing). **Selective prediction / abstention:** set a risk-coverage target asymmetrically tight on the false-positive side so "never exaggerate" holds by construction; conformal prediction gives a provable bound (singleton {match}→auto-yes, {no-match}→auto-no, both→ask).

**Which question to ask, and when to stop:** rank UNKNOWN requirements by expected information gain w.r.t. the final decision ≈ `profile-uncertainty × requirement-criticality`. Ask vs guess when `P(wrong) × cost_wrong > cost_of_one_question` (cost_wrong for a false match set high). Stop when: decision-stable (no remaining unknown could flip the verdict), or confidence/coverage threshold crossed, or top question's info-gain < ε, or a hard budget cap.

## Report design

- **Verdict first (BLUF):** recommendation in 1–2 sentences, then reasoning, then evidence.
- **Two separate scores** — fit/relevance vs ATS-readability — never one blended number; banded (Poor→Great).
- **Every finding carries 3-level confidence + a quoted evidence span**; a finding with no attachable evidence is downgraded or dropped.
- **Cognitive-load discipline:** cap top-level reasons (≤5) and actions (≤3); progressive disclosure for detail.
- **Honesty builds trust** — willingness to say "don't apply" signals calibration.
- **Per-skill levels** on a shared 0–5 Dreyfus-aligned scale (`gap = required − candidate`). Adjacency is a match-*type*; closeability splits the two gap buckets.
- **Interview prep:** turn each gap into a talking point (STAR/CARLA); transferable points lead with a *bridge statement* (past-proof → present capability); gap points lead with a *ramp plan* (present-honesty → future plan, 90/10 framing). Reusable library of 6–8 STAR stories.

Report schema (verdict-first, drill-down): `AlignmentReport{ verdict, meta, score_summary{bucket_counts}, requirements[], blocking_gaps[], next_actions[], interview_prep{story_library}, clarifications[] }`. Per-requirement record carries: verbatim requirement text, skill_type, requirement_class (gate_keeper/differentiator/value_add), `match_state` (3-valued), `field_completeness` (open/closed), `bucket`, `match_type` (direct/adjacent/none), required/candidate level (0–5), gap_size, adjacency basis & transferability, closeability & close_method & time_to_close, confidence + uncertainty_reason, evidence{quote,source,locator}, impact, info_gain, needs_clarification, talking_point.

**0–5 scale:** 0 None · 1 Aware · 2 Beginner · 3 Competent · 4 Proficient · 5 Expert.

**Clarification routing (the "don't assume absence" mechanism):** an `UNKNOWN` on an open, decision-relevant field with high info-gain becomes a question — NOT a `gap_hard`. Only `CONTRADICTED` (or `UNKNOWN` on a closed field) becomes a confirmed gap.

## REFERENCES

[1] [Jobscan — match rate calc](https://support.jobscan.co/hc/en-us/articles/360055995534-How-is-the-resume-match-rate-calculated)
[2] [Teal — Job Matcher](https://help.tealhq.com/en/articles/12060992-using-the-job-matcher)
[3] [SkillSyncer review](https://resumeoptimizerpro.com/blog/skillsyncer-review)
[4] [ResyMatch](https://cultivatedculture.crunch.help/en/resymatch/what-is-resy-match-io)
[6] [Huntr — Job Match Score](https://help.huntr.co/en/articles/12241684-job-match-score)
[7] [Careerflow — resume skill score](https://help.careerflow.ai/en/articles/10030335-understanding-the-resume-skill-score)
[8] [srbhr/Resume-Matcher (OSS hybrid)](https://github.com/srbhr/Resume-Matcher) · [Hungreeee/Resume-Screening-RAG-Pipeline](https://github.com/Hungreeee/Resume-Screening-RAG-Pipeline)
[9] [HBS — Hidden Workers: Untapped Talent (2021)](https://www.hbs.edu/managing-the-future-of-work/Documents/research/hiddenworkers09032021.pdf)
[10] [Reuters — Amazon scraps biased AI recruiting tool](https://www.irishtimes.com/business/technology/amazon-scraps-secret-ai-recruiting-tool-that-showed-bias-against-women-1.3658651)
[12] [EEOC AI guidance (four-fifths)](https://www.littler.com/news-analysis/asap/eeoc-issues-guidance-use-artificial-intelligence-tools-employment-selection) · [NYC Local Law 144](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page)
[13] [LLM resume-fit vs human recruiters (MDPI Electronics 2025)](https://www.mdpi.com/2079-9292/14/24/4960)
[14] [Sentence-BERT (arXiv:1908.10084)](https://arxiv.org/abs/1908.10084) · [ColBERTv2 (arXiv:2112.01488)](https://arxiv.org/pdf/2112.01488) · [bge-m3 (arXiv:2402.03216)](https://arxiv.org/html/2402.03216v3)
[15] [Is cosine similarity meaningful? (arXiv:2403.05440)](https://arxiv.org/html/2403.05440v1) · [Don't use cosine similarity (Migdał)](https://p.migdal.pl/blog/2025/01/dont-use-cosine-similarity/)
[16] [ESCO](https://esco.ec.europa.eu/en/about-esco/what-esco) · [SkillNER](https://github.com/AnasAito/SkillNER) · [JSON Resume schema](https://jsonresume.org/schema)
[18] [Judging LLM-as-a-Judge / MT-Bench (arXiv:2306.05685)](https://arxiv.org/abs/2306.05685) · [G-Eval (arXiv:2303.16634)](https://arxiv.org/abs/2303.16634)
[21] [FActScore (arXiv:2305.14251)](https://arxiv.org/abs/2305.14251) · [SAFE/VeriScore (arXiv:2406.19276)](https://arxiv.org/html/2406.19276)
[22] [RAG (arXiv:2005.11401)](https://arxiv.org/abs/2005.11401) · [Anthropic Citations API](https://platform.claude.com/docs/en/build-with-claude/citations)
[23] [Null (SQL) / three-valued logic — Wikipedia](https://en.wikipedia.org/wiki/Null_(SQL))
[24] [Negation as failure](https://en.wikipedia.org/wiki/Negation_as_failure) · [Evidence of absence](https://en.wikipedia.org/wiki/Evidence_of_absence)
[25] [Open-world assumption](https://en.wikipedia.org/wiki/Open-world_assumption) · [Local Closed-World of Data Sources (Springer)](https://link.springer.com/chapter/10.1007/11546207_12)
[26] [On Calibration of Modern Neural Networks (arXiv:1706.04599)](https://arxiv.org/abs/1706.04599)
[28] [Semantic entropy / confabulation (Nature 2024)](https://www.nature.com/articles/s41586-024-07421-0) · [Self-Consistency (arXiv:2203.11171)](https://arxiv.org/abs/2203.11171)
[29] [Selective classification with guaranteed risk (arXiv:1705.08500)](https://arxiv.org/abs/1705.08500)
[30] [Conformal prediction intro (arXiv:2107.07511)](https://arxiv.org/abs/2107.07511) · [Conformal abstention bounds hallucination (arXiv:2405.01563)](https://arxiv.org/abs/2405.01563)
[31] [Asking Clarifying Questions / Qulac (arXiv:1907.06554)](https://arxiv.org/abs/1907.06554) · [ClariQ (arXiv:2009.11352)](https://arxiv.org/abs/2009.11352)
[32] [Active Learning Survey (Settles)](https://burrsettles.com/pub/settles.activelearning.pdf)
[33] [Horvitz — Mixed-Initiative UI (CHI 1999)](http://erichorvitz.com/chi99horvitz.pdf)
[36] [LLM career-interview slot-filling (arXiv:2412.16943)](https://arxiv.org/html/2412.16943v1)
[39] [AIHR — Skills Gap Analysis](https://www.aihr.com/blog/skills-gap-analysis/) · [Interview Guys transferability matrix](https://blog.theinterviewguys.com/career-change-resume-skills-transferability-matrix/)
[43] [MIT — STAR method](https://capd.mit.edu/resources/the-star-method-for-behavioral-interviews/) · [CARLA method](https://www.launchedbylinda.com/blog/carla)
