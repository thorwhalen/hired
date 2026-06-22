# Building a candidate-knowledge system: elicitation, active questioning, epistemic state, and a personal knowledge store

*A grounded design report for a system that accumulates knowledge about a job candidate over time and uses active question-selection against job descriptions.*

---

## 0. The problem, framed

You are building a system whose core loop is:

> **analyze a job description → identify what is uncertain about the candidate → ask the MOST informative questions first → record Q&A → update a reusable knowledge base.**

This is, almost exactly, the problem that **knowledge engineering** was invented to solve in the 1980s — extracting from a human expert (here, the candidate) knowledge they hold but cannot easily articulate — combined with the **active-learning / value-of-information** problem of choosing *which* query to spend a turn on, layered on a **personal-knowledge / agent-memory** substrate that has to model *what we know we don't know* without ever treating silence as a "no."

The four traditions that ground the design are:

1. **Knowledge elicitation** (expert systems / requirements engineering) — *how* to ask.
2. **Active learning + value of information** (ML + decision theory) — *which* to ask first.
3. **Open-world knowledge representation + provenance** (semantic web / databases) — *how to record what we know, what we don't, and where it came from.*
4. **Personal-knowledge / LLM-agent memory** (Zettelkasten, MemGPT/Letta, Mem0, generative agents) — *how to store, link, retrieve, and supersede facts over time.*

A single empirical anchor sets the stakes for the whole design: cognitive-task-analysis studies found that **experts omit on average ~70% of the knowledge steps they actually use** when simply asked to describe their work [1]. A candidate who is asked "tell me about your experience" will, predictably, under-report. The system's job is to recover the missing 70% — efficiently, and without ever inferring a *lack* of a skill from the candidate's *silence* about it.

---

## PART I — RESEARCH SYNTHESIS

### 1. Knowledge elicitation: how to ask

#### 1.1 The core lesson from knowledge engineering

The difficulty of getting knowledge out of experts to build knowledge-based systems was named the **"knowledge acquisition bottleneck"** by Hayes-Roth et al. (1983) and motivated the whole field of elicitation methods [2]. Two findings from that literature drive everything downstream:

- **Compiled knowledge.** Through experience, originally-explicit knowledge becomes "routinised or automatised" — experts give "black box replies such as 'I don't know how I do that'" [2]. A senior engineer genuinely cannot list, on demand, the heuristics that make them senior.
- **Post-hoc rationalization.** Experts often supply a valid decision and then a *spurious* justification of how they reached it [2]. Self-assessment ("how good are you at leadership?") invites exactly this fabrication.

The consequence is a hard rule: **never rely on a single open-ended prompt; run a *programme* of complementary techniques, each matched to a different knowledge type** [2]. Shadbolt & Smart classify techniques as *natural/non-contrived* (interviews, protocol analysis) vs *contrived* (sorting, rating, constrained tasks) [2]; Hoffman's "differential access hypothesis" holds that different techniques are differentially effective at eliciting different *kinds* of knowledge [2].

#### 1.2 The techniques, and how each translates to a text LLM agent

| Technique | What it elicits | Translates to LLM agent? | How |
|---|---|---|---|
| **Fixed-probe structured interview** | Rules, scope, exceptions | **Excellent** — probes are deterministic | Each probe has a defined function: *"Why would you do that?"* converts an assertion into a rule; *"How would you do that?"* decomposes it; *"When? / Is it always the case?"* finds scope; *"What if it were not the case that [X]?"* finds exceptions [2]. In Shadbolt & Burton's comparison, structured interviews had the **highest** expert agreement on extracted rules (~61%) [3]. |
| **Laddering** | Concept/skill hierarchy, transferable competencies | **Excellent — the highest-value adaptation** | Builds a node-and-arc graph by moving **DOWN** (*"Can you give an example of [item]?"*), **ACROSS** (*"What alternatives to [item] are there?"*), **UP** (*"What do these have in common / what are they examples of?"*), plus discrimination probes (*"How can you tell it's [item]?"*, *"What's the key difference between [item1] and [item2]?"*) [2]. Applies to "actions, tasks, goals, resources," not just concepts [2]. Found **most productive** even across changing domains [4]. Values-laddering repeats *"Why is that important to you?"* to climb an attribute→consequence→value chain [5]. |
| **Critical Decision Method (CDM)** | Tacit judgment in real past projects | **Excellent for experience depth** | Klein/Calderwood/MacGregor (1989): a retrospective interview applying cognitive probes to a *specific non-routine event* [6][7]. Multi-pass: recount one incident → build a timeline → find decision points → deepen each with probes for **Cues** ("what were you seeing/hearing?"), **Goals** ("specific objectives at the time?"), **Options** ("what else did you consider?"), **Anticipation**, **Errors** ("how might a novice have behaved differently?"), **Hypotheticals** ("if a key feature had been different, what would you have done?") [2]. A descendant of Flanagan's Critical Incident Technique [7]. |
| **Twenty-questions / limited-information** | Problem-solving strategy, seniority | **Good (inverted)** | Give the candidate a sketchy target problem; what they ask for, and in what order, reveals how they prioritize information and their expertise level [2]. |
| **Teachback** | Verification / refinement | **Excellent** | The elicitor explains the elicited knowledge back to the expert, who checks and amends it [2]. Natural confirmation loop before a fact is committed. |
| **Repertory grid / triadic elicitation** | Distinguishing skill *dimensions* | **Partial — logic yes, matrix no** | From Kelly's (1955) personal construct theory [2][8]. Present three elements (e.g., three of the candidate's projects); ask how two are alike and differ from the third; the contrast becomes a bipolar *construct*; rate the rest on it [2]. Forces a **minimal set of discriminating dimensions** and "often leads to discovery rather than documentation" [8]. Cluster analysis of the grid surfaces categories the expert never articulated [2]. The *dialogue logic* is reproducible; the full power (cluster analysis of a rating matrix) needs a structured back-end. |
| **Card / concept sorting** | Attribute dimensions among a fixed set | **Partial** | Repeatedly sort concept cards into piles, labelling each pile's *dimension* (a property/attribute) [2]. The "re-sort by a different dimension" move surfaces multiple attribute axes (impact, autonomy, domain). |
| **Think-aloud / protocol analysis** | Procedural "when and how" of using knowledge | **Limited for a candidate agent** | Ericsson & Simon's foundational method [2][9]. **The critical caveat that governs the whole design lives here** (see below). |
| **Concept mapping** | Propositions, efficiently | **Good** | Reported ~2 useful propositions per session-minute (Hoffman et al. 2001) [2]. |

#### 1.3 The governing caveat: report concrete events, don't ask for self-explanation

Ericsson & Simon's central result: when a person merely **verbalizes thoughts already in focus** (think-aloud / reporting concrete events), "no changes in the sequence of thought processes have been found compared to participants completing the same tasks silently" [9]. But when you ask a person to **describe or explain** their thinking to another, you *change the course of thought* and usually alter (often improve, i.e., distort) performance [9].

**Design implication:** prefer **concrete-incident probes** (*"walk me through what you actually did on project X"*) over **abstract self-assessment** (*"how good are you at leadership?"*). The latter invites the exact post-hoc rationalization the literature warns about [2][9]. Every CDM and laddering-DOWN probe satisfies this; "rate yourself 1-10 on X" violates it.

#### 1.4 What the (young) LLM-elicitation literature says

Controlled studies of LLM-conducted requirements-elicitation interviews report that LLMs achieve **lower recall than human interviewers**, with the largest gaps on *implicit / non-functional* content, and tend to produce **"repetitive or generic questions"** when answers lack specificity — concluding LLMs are "best suited as assistants augmenting human-led elicitation" [10]. *(These are recent preprints; treat specific percentages as directional, not settled.)* The robust takeaway: an LLM left to free-form will ask shallow, generic questions — **which is precisely why you need an explicit question-selection engine** (Part II) rather than trusting the model to "just ask good questions."

#### 1.5 Ten concrete question-generation strategies

1. **Laddering-UP** — after a specific accomplishment: *"What broader capability does that demonstrate?"* → generalizes into transferable skills matching the JD.
2. **Laddering-DOWN** — for any vague claim ("strong in data engineering"): *"Can you give a specific example where you did that?"* → converts assertion into evidence.
3. **Laddering-ACROSS / discrimination** — *"What's the key difference between how *you* approached X versus the standard way?"* → surfaces distinctive strengths.
4. **CDM decision-point** — *"At that moment, what cues told you to act? What other options did you consider and reject, and why?"* → tacit judgment, STAR-ready stories.
5. **CDM hypothetical** — *"If [a key constraint] had been different, what would you have done?"* → depth, adaptability.
6. **Fixed-probe scope** — *"When does that approach *not* apply?"* → separates rule-followers from genuine experts.
7. **Triadic contrast** — present three of the candidate's own projects: *"Which two are most alike, and how do they differ from the third?"* → the candidate's own skill dimensions.
8. **Re-sort** — *"Group your projects another way — by a different dimension."* → multiple attribute axes.
9. **Twenty-questions inversion** — sketchy target problem: *"What would you need to know first?"* → expertise level.
10. **Teachback verification** — *"Here's how I'd summarize your strength in X — correct or refine me."* → confirm + amend before committing to the store.

---

### 2. Active learning & optimal question selection: which to ask first

#### 2.1 The tower of theory

All of this answers one question: *which query reduces uncertainty most, cheaply?*

- **Uncertainty sampling** — query the instance the model is least certain about: *least-confident*, *margin* (gap between top-two class probabilities), or *entropy* `H = −Σ pᵢ log pᵢ`, maximized by a uniform distribution [11]. Cheapest, most robust default. You do **not** need a model that outputs true probabilities — any confidence score can be used as a pseudo-probability heuristically [11].
- **Query-by-committee** — query where an ensemble of diverse models *disagrees* most; a small committee suffices [11].
- **Expected model change / expected error reduction** — query the answer that would most change the model, or most reduce error on the *remaining* unknowns; principled but requires simulating each answer, hence expensive [11].
- **Value of Information (VoI)** — the decision-theoretic ceiling (Raiffa & Schlaifer, 1961) [12]. **EVPI** = expected loss under current info − expected loss under perfect info, an upper bound on any information's value [13]. The operational rule: **acquire information only if VoI − cost > 0** (Expected Net Gain of Sampling = EVSI − cost) [14][15].
- **Expected Information Gain (EIG) / Bayesian experimental design** — `EIG(q) = H[prior] − E_answer[H[posterior | answer]]` = the **mutual information** between the latent quantity (here, true job-fit) and the answer [16]. EIG-as-mutual-information is the standard objective in Bayesian experimental design [17].
- **The 20-questions / decision-tree / Huffman result** — the optimal question order is exactly **greedy maximum-information-gain splitting**: `IG = H(T) − H(T|a)`, the same quantity as mutual information [18]. ID3/C4.5 grow trees this way [18]. Optimal yes/no questioning is equivalent to source coding and obeys the Huffman bound `H(X) ≤ L < H(X)+1` [18].

#### 2.2 LLM agents already operationalize this — and it works

- **Active Task Disambiguation** (Kobalczyk et al., 2025) frames clarifying-question selection as Bayesian experimental design, selecting questions that maximize information gain over the *solution* space rather than reasoning only within the question space [19].
- **BED-LLM** iteratively picks the question maximizing an EIG estimate computed from the LLM's own predicted answer distribution over a filtered belief set; on 20-Questions it reached **91% success vs 68% for an entropy baseline and 14% for naive QA** [20]. This is the empirical hook: **explicit EIG-driven question choice crushes "just let the LLM ask"** — directly corroborating §1.4's finding that unguided LLMs ask generic questions.

#### 2.3 The implementable, lightweight heuristic (no probabilities required)

Model job-fit as a weighted sum over attributes `a` (skills, years, location, clearance, …). For each attribute keep a JD-derived **weight `wₐ`** (importance for *this* job), a **current estimate `μₐ ∈ [0,1]`** of how well the candidate meets it, and an **uncertainty `uₐ`**. For each candidate question `q` probing attribute `a`:

```
score(q) = w_a × uncertainty(a) × expected_fit_swing(q) / cost(q)
```

- **`w_a`** — normalized JD importance (LLM rates each requirement: must-have = 1.0 … nice-to-have = 0.2).
- **`uncertainty(a)`** — *without* probabilities: LLM self-rates confidence 0-1, use `u = 1 − confidence`. *With* probabilities: binary entropy `H(μ) = −μ log μ − (1−μ) log(1−μ)`, peaking at `μ = 0.5`. This is the **uncertainty-sampling** term [11].
- **`expected_fit_swing(q)`** — enumerate the plausible answers, score fit under each, take `E[|Δfit|]` (or variance across answers). A question whose answer can't change the decision scores ~0. This is the **EIG / expected-model-change** term [11][16].
- **`cost(q)`** — turns/intrusiveness; encodes **VoI-net-of-cost** (skip if `score < threshold`) [14][15].

This multiplicative form is exactly the survey-endorsed **heterogeneity × representativeness** product `O = H·R` [11], with JD-importance standing in for representativeness and cost in the denominator. The `wₐ` factor is the literature's explicit fix for the failure mode "high-uncertainty attribute that barely matters for this job" [11].

**With embeddings/probabilities**, upgrade to BED-LLM-style proper EIG: maintain a belief over candidate fit-profiles; for each `q` compute `EIG = H[prior fit] − Σ_answers p(answer)·H[posterior | answer]`; rank by `EIG/cost`; ask the top one; update; repeat — greedy 20-questions splitting [20]. **The point of the design is that the *same scoring interface* works with or without the probabilistic machinery.**

---

### 3. Epistemic state: has / lacks / unknown, with confidence and provenance

This is the section the user flagged as critical, and it has the cleanest formal grounding.

#### 3.1 The one decision that matters: what does silence mean?

- **Closed-world assumption (CWA)** — "what is not known to be true must be false" [21]. Used by SQL, Prolog, Datalog, via **negation as failure** (`not p` succeeds when `p` fails to derive) [22].
- **Open-world assumption (OWA)** — an unstated fact is **unknown, never automatically false**; "lack of knowledge does not imply falsity" [21]. Used by RDF(S)/OWL, designed for *incomplete* knowledge [23].

**For a candidate-knowledge system the OWA is the mandatory default.** If no source says the candidate knows Kubernetes, the system records *unknown* — not *lacks Kubernetes*. Inferring non-existence from absence of evidence is the recognized **argument-from-ignorance** fallacy [24] — and it is precisely the false negative the user wants to avoid. ("Who has *not* edited this article?" is, under OWA, **unknown** — not derivable from a table's silence [21].)

#### 3.2 Two ingredients make has/lacks/unknown first-class

1. **Three-valued logic (TRUE / FALSE / UNKNOWN).** SQL implements exactly this via NULL semantics, corresponding to **Kleene's strong three-valued logic** [25]. The crucial behavior: a predicate that is UNKNOWN is **excluded from positive matches** rather than counted as a negative — SQL returns only TRUE rows, dropping both FALSE *and* UNKNOWN [25]. Your matching logic must do the same: UNKNOWN attributes belong in neither the has-set nor the lacks-set.
2. **Classical (strong) negation, modeled separately from negation-as-failure.** "Candidate explicitly stated they have *no* security clearance" is a *positive epistemic commitment* (`¬p` proven) and is fundamentally different from "no source mentions clearance" (merely not provable) [22]. Strong negation requires explicit proof of falsity; weak negation (NAF) is just "not shown" with an autoepistemic reading ("p is not known / not believed") [22].

#### 3.3 Confidence and provenance on each fact

- **Uncertain knowledge graphs** model a fact as a weighted quadruple `(s, p, o, confidence ∈ [0,1])` [26]. Surveys recommend tracking **separate** confidence dimensions — *extraction confidence* (algorithm reliability), *source confidence* (source trustworthiness), *source reliability* — rather than one conflated number [26], and interpreting the score as **plausibility**, with "typicality" a function of plausibility × number of supporting evidences [26].
- **Provenance** is standardized by the **W3C PROV data model**: core types **Entity / Activity / Agent**, related by `wasGeneratedBy`, `used`, `wasDerivedFrom`, `wasAttributedTo`, `wasAssociatedWith` [27]. PROV's stated purpose is exactly ours: provenance is "crucial in deciding whether information is to be trusted" [27].
- **Statement-level metadata** (confidence, provenance, temporal validity per individual fact) is what RDF reification and, more compactly, **RDF-star** (`<< s p o >>`) exist to attach [28]. You don't need RDF — but the *pattern* (annotate the statement, not just store the triple) is the reusable insight.

#### 3.4 The recommended fact record

| Field | Purpose | Grounding |
|---|---|---|
| `subject, predicate, object` | the claim, e.g. `(candidate, knows, Kubernetes)` | KG triple [26] |
| `polarity` | `asserted_present` / `asserted_absent` — strong/classical negation, an explicit commitment | NAF vs classical negation [22] |
| `epistemic_status` | `KNOWN_TRUE` / `KNOWN_FALSE` / `UNKNOWN` — **default `UNKNOWN`** | 3VL / Kleene [25] |
| `confidence` | score in [0,1] (plausibility) | uncertain KG [26] |
| `extraction_confidence`, `source_confidence`, `source_reliability` | keep separate, don't conflate | KG uncertainty survey [26] |
| `provenance` | `wasGeneratedBy` (extraction activity), `wasDerivedFrom` (source doc + span), `wasAttributedTo` (source agent) | W3C PROV [27] |

**Default semantics that prevent false-negatives-from-silence:** absence of a record ⟹ `epistemic_status = UNKNOWN`, *never* `asserted_absent`. Only an explicit signal ("candidate stated they have no Python experience") sets `polarity = asserted_absent`, with its own confidence and provenance. Matching/ATS logic treats UNKNOWN as "not yet evidenced," exactly as SQL excludes UNKNOWN from a positive match [25]. This lets the system answer honestly: *"do we **know** the candidate lacks X?"* (a recorded `asserted_absent`) vs *"we just haven't asked about X"* (the default `UNKNOWN`) — which is the trigger for a question (Part II).

---

### 4. Personal-knowledge & agent-memory patterns: store, link, retrieve, supersede

Four patterns transfer cleanly from PKM and LLM-agent memory.

#### 4.1 Note granularity → one atomic fact per record

The Zettelkasten **"Principle of Atomicity"** is "one knowledge building block per note" — a note is atomic when you can't remove anything without breaking the idea, *and* nothing is missing (substance, not length) [29]. Mem0 independently extracts "atomic facts" [30]. The two converge on the same unit: **one self-contained claim per record** ("8 years Python," "prefers remote," "led a 5-person team"). Atomicity exists *to serve linking* — "the very idea of links implies components to link" [29] — and is what makes superseding and selective retrieval tractable. A paragraph blob is none of these.

#### 4.2 Linking → typed edges between candidate, skill, role, company

Both Zettelkasten ("a link with a phrase explaining why" [29]) and the graph memory systems (Mem0's graph variant, GraphRAG, Graphiti) model knowledge as nodes + **labeled** edges, not free text. A lightweight entity graph (`candidate —has_skill→ skill`, `candidate —worked_at→ company`, `skill —evidenced_by→ project`) enables traversal queries ("all evidence for Rust + remote preference") that pure text search can't answer. GraphRAG's lesson: graphs pay off for *broad, multi-hop* questions and are **overkill for single-fact lookup** [31] — so the graph is a complement to, not a replacement for, simple retrieval.

#### 4.3 Indexing → lexical-first, embeddings only when measured

**This is the strongest practical recommendation.** Candidate data is dominated by *exact tokens* — names, skills, company names, certifications, tool/framework names — exactly where **BM25 (lexical) beats embeddings**, and where embeddings' paraphrase advantage barely helps [32]. For a small corpus, embeddings are "often overkill — the complexity/cost is more noticeable than the subtle semantic gain"; the recommended path is **"start with BM25, prove it's not enough with real queries, then add vectors surgically"** [33]. **SQLite's built-in FTS5** gives BM25-ranked full-text search with no separate vector-DB infrastructure [34]. Add dense embeddings only for genuinely semantic queries ("leadership experience," "good culture fit") once you observe real retrieval failures; if you add both, combine as hybrid. **Do not stand up a vector DB on day one.**

#### 4.4 Updating / superseding → invalidate-and-version, don't overwrite

The reusable vocabulary comes from the agent-memory systems:

- **Mem0** matches each new fact against the top-*k* semantically similar existing facts and has an LLM choose **ADD / UPDATE / DELETE / NOOP**: ADD if new, UPDATE if complementary, DELETE if *contradicted*, NOOP if redundant [30]. It keeps an **audit trail** logging old/new/event/timestamp [30].
- **Zep / Graphiti** use a **bi-temporal** model — `t_valid`/`t_invalid` (when true in the world) and `t_created`/`t_expired` (when the system learned/invalidated it) — and on a contradiction **invalidates** the old fact (sets `t_invalid`) rather than deleting it, always preferring newer info while preserving history [35].

**For candidate data, prefer Graphiti's bi-temporal invalidation over Mem0's hard DELETE.** When a candidate's status changes ("interviewing" → "hired") or they correct a fact, mark the old fact invalid rather than erasing it. This preserves history, supports "as of last month" queries, and — critically — keeps the provenance chain intact for auditability. Mem0's ADD/UPDATE/DELETE/NOOP is the right *decision frame*; bi-temporal versioning is the right *storage mechanic*.

**Skip** the recency/importance scoring of generative agents [36] and the OS-style context paging of MemGPT/Letta [37][38] *unless* the store directly feeds a live conversational agent. For a queryable candidate store, **atomic facts + typed links + BM25-first indexing + bi-temporal supersession** is the lean, defensible core.

---

### 5. Fact extraction & synthesis: documents + Q&A → structured facts with provenance

#### 5.1 Extraction approach

- **Schema-guided (closed) IE, not OpenIE.** OpenIE extracts `(subject; relation; object)` with no predefined schema [39]; closed IE conforms extracted facts to a predefined schema, trading coverage for precision and **queryability** [39]. For a candidate store with known predicates (`has_skill`, `worked_at`, `achieved`), closed IE is correct — facts land in queryable slots.
- **LLM structured outputs.** Constrain the model to emit JSON matching a Pydantic schema; `instructor` patches the client to enforce the schema and **retry on validation failure**, `outlines` constrains generation [40][41]. Extracting typed facts into a schema is far less error-prone than parsing free prose [42].

#### 5.2 Provenance is the non-negotiable invariant

The root cause of fact hallucination is **lack of provenance**: triplets produced without links to their textual origin are plausible but unsupported; ground every element to a specific **source span** and hallucinations become detectable [43]. Mechanically enforcing that each fact's verbatim quote is a substring of its source means **"LLMs cannot cite text they haven't seen"** — anti-hallucination by construction, not by probabilistic detection [44]. The robust loop is **search → extract → generate → validate**, flagging any uncited claim for review [42].

#### 5.3 Atomicity + decontextualization

- An **atomic claim** describes a single entity/relation (operationally ≤1 relation per claim) [45].
- **Decontextualization** rewrites the claim to stand alone — resolving pronouns to proper nouns, relative references to absolute — so it is "correctly interpretable without any additional context" [45][46]. ("It cut latency 40%" → "The candidate's caching redesign on Project Acme cut p99 latency 40%.")
- Quality is measurable along **atomicity, fluency, decontextualization, faithfulness, focus (≈precision), coverage (≈recall)** [45]. The **FactScore / decompose-then-verify** pipeline — decompose → retrieve evidence per claim → verify — is the standard shape [47][48].

#### 5.4 The KBC precedent: the structured store is ground truth

Weak-supervision/KBC systems show how to treat the structured store as authoritative: **Snorkel**'s labeling functions + data programming learn each function's accuracy with no ground truth and emit *probabilistic* labels [49]; **DeepDive** frames KB construction as factor-graph inference producing **calibrated** marginal probabilities (facts predicted at probability ~p are true ~p of the time) [50]. The reusable idea: derive the human-readable synopsis *from* the fact store with calibrated confidence, never hand-edit it into drift.

#### 5.5 The synopsis as a projection (not a parallel document)

Maintain the human-readable profile as a **regenerated projection** of the fact store, not a hand-edited sibling. Use **incremental/refine** synthesis (carry and update one global summary) but guard against its known **early-error-propagation / earlier-segment-over-weighting** drift [51] by regenerating each section deterministically from its backing facts and embedding fact-ids as anchors. Spacy's official guidance frames the lightweight-first split: **rules (regex/gazetteer/PhraseMatcher) for finite, structured targets** (emails, dates, employers, a known-skills list), **statistical/LLM models for the open prose**, with rules running first to constrain the model [52].

---

## PART II — RECOMMENDED DESIGN

Everything below is implementable in pure Python (`pydantic` + `sqlite3`/FTS5) with **optional** LLM and embeddings. The design is layered so each optional capability slots into a stable interface.

### (a) The question-selection engine

**Inputs:** a parsed JD → list of weighted requirements; the current candidate knowledge store.

**Algorithm (per JD analysis):**

```
1. PARSE JD → requirements R = [(attribute_a, weight w_a)]      # w_a: must-have 1.0 … nice-to-have 0.2
2. For each a in R, look up the store:
     μ_a   = current best estimate of fit on a   ∈ [0,1]        # UNKNOWN → μ ill-defined → max uncertainty
     u_a   = uncertainty(a)                                     # 1 - confidence, or binary entropy H(μ_a)
3. GENERATE candidate questions Q for the high-(w_a·u_a) attributes,
     using the §1.5 strategies (laddering / CDM / discrimination), NOT free-form.
4. SCORE each q:
     score(q) = w_a · u_a · expected_fit_swing(q) / cost(q)
   - expected_fit_swing(q): enumerate plausible answers, score fit under each, take E[|Δfit|] (or variance)
5. ASK the top-scoring question (or top-k as a short batch).
6. RECORD the answer (loop c), UPDATE μ_a and u_a, re-score, repeat
     until max(score) < threshold  (VoI − cost ≤ 0) or a turn budget is hit.
```

- **Why this shape:** it is a lightweight, no-probabilities-required reduction of EIG/VoI [16][14], structurally identical to the survey's endorsed `heterogeneity × representativeness` product [11], and the `w_a` factor is the literature's explicit guard against asking about uncertain-but-irrelevant attributes [11].
- **The UNKNOWN→question link:** the engine asks about attribute `a` precisely when the store's `epistemic_status` for `a` is `UNKNOWN` *and* `w_a` is high — never because the candidate "lacks" it. Silence drives questioning, not negative scoring.
- **Optional upgrade:** with embeddings/probabilities, replace step 4's heuristic with proper EIG over a belief set (BED-LLM style [20]) — same interface, swappable scorer. BED-LLM's 91%-vs-68%-vs-14% result [20] is the justification for doing explicit selection at all rather than letting the LLM free-ask [10].
- **Stop rule:** keep asking only while `VoI − cost > 0` [14][15]; this naturally limits questions to the few that actually move *this* job's assessment.

### (b) The fact / knowledge schema

```python
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class EpistemicStatus(str, Enum):
    KNOWN_TRUE  = "known_true"
    KNOWN_FALSE = "known_false"
    UNKNOWN     = "unknown"          # DEFAULT — absence of a record means this

class Polarity(str, Enum):
    ASSERTED_PRESENT = "asserted_present"   # classical/strong: candidate HAS it
    ASSERTED_ABSENT  = "asserted_absent"    # classical/strong: candidate explicitly LACKS it
    # (no record at all  ==  UNKNOWN, never asserted_absent)

class Provenance(BaseModel):                       # W3C PROV-aligned [27]
    source_doc_id: str                             # wasDerivedFrom
    char_start: int | None = None                  # exact span (anti-hallucination [43][44])
    char_end:   int | None = None
    quote: str                                     # verbatim — must be a substring of the source
    source_kind: str                               # cv_bullet | qa_answer | uploaded_doc
    extraction_activity: str                       # wasGeneratedBy (e.g. "llm_extract@v2" / "regex_rule")
    attributed_to: str                             # wasAttributedTo (candidate | recruiter | document)
    created_at: datetime

class Fact(BaseModel):
    id: str                                        # stable hash(subject,predicate,object)
    subject: str                                   # usually the candidate
    predicate: str                                 # has_skill | worked_at | achieved | prefers ...
    object: str                                    # the value
    fact_type: str                                 # skill_claim | experience | credential | preference
    polarity: Polarity = Polarity.ASSERTED_PRESENT
    epistemic_status: EpistemicStatus = EpistemicStatus.UNKNOWN
    # split confidence, never conflated [26]:
    confidence: float = Field(ge=0.0, le=1.0)      # overall plausibility
    extraction_confidence: float = 1.0             # algorithm reliability
    source_confidence: float = 1.0                 # source trustworthiness
    evidence: list[Provenance]                      # ≥1; more evidence → higher typicality [26]
    # bi-temporal supersession [35]:
    valid_from: datetime | None = None             # t_valid (true in the world)
    valid_until: datetime | None = None            # t_invalid (set on supersession, NOT deleted)
    recorded_at: datetime                          # t_created (system learned it)
    superseded_by: str | None = None               # id of the replacing fact
```

**Invariants:** (1) default `epistemic_status = UNKNOWN`; a missing fact is unknown, never absent. (2) `asserted_absent` requires an explicit negative statement *with its own provenance*. (3) every fact carries ≥1 `Provenance` with a verbatim `quote` that is a substring of its source — facts failing this check are rejected or down-confidenced [43][44]. (4) supersession sets `valid_until` + `superseded_by`; nothing is hard-deleted [35].

### (c) The Q&A persistence + extraction + indexing loop

```
RECORD (per answer):
  1. Persist the raw Q&A turn verbatim  (question, answer, timestamp, which attribute a it targeted)
     → this transcript IS a source document with its own doc_id (provenance anchor)

EXTRACT (lightweight-first):
  2. CHUNK: one CV bullet / one Q&A answer = one chunk (keeps spans short, one-fact-per-record natural)
  3. RULES FIRST: regex + gazetteer/PhraseMatcher for finite/structured targets
       (emails, dates, employers, known-skills list) — free, deterministic [52]
  4. LLM (optional) for the open prose: emit Fact objects under the Pydantic schema (closed IE [39][40]),
       copying an exact `quote` span, one fact per claim
  5. ATOMIZE + DECONTEXTUALIZE: split compound bullets to ≤1 relation; resolve pronouns/relative refs [45][46]
  6. VERIFY: assert each `quote` is a substring of its source; drop or down-confidence orphans [44]

MERGE (Mem0 ADD/UPDATE/DELETE/NOOP decision frame [30], bi-temporal mechanic [35]):
  7. Match each new fact against top-k similar existing facts (string-key first; embeddings only if needed):
       ADD   → no equivalent exists
       UPDATE→ complementary: raise confidence / add evidence
       SUPERSEDE (not DELETE) → contradicted: set old.valid_until, old.superseded_by; insert new
       NOOP  → redundant
  8. Append to the audit trail (old, new, event, timestamp) [30]

INDEX:
  9. Insert into SQLite FTS5 (BM25) over subject/predicate/object/quote — zero extra infra [34]
 10. (optional) Add dense embeddings + typed graph edges ONLY when lexical retrieval demonstrably fails [32][33]

SYNTHESIZE:
 11. Regenerate the human-readable synopsis as a PROJECTION of the fact store (incremental/refine),
       each section deterministically backed by fact-ids; never hand-edit [49][50][51]
```

### (d) Retrieval for reuse across jobs

The store is **job-agnostic**; only the *scoring* is job-specific. For each new JD:

1. **Lexical-first retrieval (default):** BM25 over FTS5 keyed on the JD's requirement terms (skills, tools, titles) — fast, exact, no embeddings [32][34]. This pulls the candidate facts relevant to *this* JD.
2. **Graph traversal (when multi-hop):** follow typed edges (`skill —evidenced_by→ project —at→ company`) to assemble evidence chains for a requirement — the GraphRAG "local search" pattern, worth it only for broad/multi-hop questions [31].
3. **Embedding/hybrid (optional, measured):** add dense retrieval only for semantic JD phrases ("cross-functional leadership") that lexical search misses [32][33].
4. **Feed the question-selection engine (a):** for each JD requirement, look up the store; `UNKNOWN` + high weight → generate a question; `asserted_present/absent` with sufficient confidence → no question needed. **Reuse is automatic:** a fact elicited for job #1 satisfies the same requirement in job #7 without re-asking — the candidate is asked each thing roughly once, and only when it matters for some job.
5. **Honesty in the fit report:** present three buckets — *evidenced strengths* (`asserted_present`, high confidence), *known gaps* (`asserted_absent`), and *not yet assessed* (`UNKNOWN`) — never collapsing the third into the second [25].

---

## 6. Design summary (the load-bearing decisions)

1. **Don't trust free-form questioning.** Unguided LLMs ask generic, low-recall questions [10]; explicit information-gain selection (BED-LLM) wins decisively [20]. Build the question-selection engine (a).
2. **Score questions by `w_a · u_a · expected_fit_swing / cost`** — a no-probabilities reduction of EIG/VoI [11][16][14] — so you ask first about what most changes *this* JD's assessment. Same interface upgrades to proper EIG with embeddings.
3. **Generate questions with elicitation techniques, not ad-hoc** — laddering, CDM, triadic contrast, teachback [2][4][6] — and always probe concrete incidents, never abstract self-assessment [9].
4. **Open-world by default.** `UNKNOWN` is the absence semantics; `asserted_absent` requires an explicit negative with provenance; UNKNOWN is excluded from both has- and lacks-sets [21][24][25]. This is the false-negative guard.
5. **One atomic fact per record, with split confidence + W3C-PROV provenance + bi-temporal supersession** [26][27][29][35]. Never overwrite; invalidate-and-version.
6. **Lexical-first (SQLite FTS5/BM25); embeddings and graph are optional, measured upgrades** [32][33][34]. The corpus size rarely justifies a vector DB on day one.
7. **The synopsis is a regenerated projection of the fact store** [49][50], kept in sync by construction, not by hand.

---

## REFERENCES

1. [The use of cognitive task analysis to reveal the instructional limitations of experts (PubMed)](https://pubmed.ncbi.nlm.nih.gov/24667500/) — Peer-reviewed; experts omit ~70% of the knowledge steps they use.
2. [Knowledge Elicitation: Methods, Tools and Techniques (Shadbolt & Smart, 2015)](http://paulsmart.cognosys.co.uk/pubs/2015/Knowledge%20Elicitation.pdf) — The canonical knowledge-engineering chapter (Evaluation of Human Work, 4th ed., CRC Press); verbatim probe templates. **Highest authority.**
3. [Knowledge Elicitation: comparative evaluation (ePrints Southampton)](https://eprints.soton.ac.uk/359638/) — Official repository record corroborating the structured-interview vs twenty-questions comparison.
4. [Laddering: technique and tool use in knowledge acquisition (Corbridge, Rugg, Major, Shadbolt & Burton — ePrints Soton)](https://eprints.soton.ac.uk/252304/) — Seminal empirical study establishing laddering's productivity.
5. [Laddering: A Research Interview Technique for Uncovering Core Values (UXmatters)](https://www.uxmatters.com/mt/archives/2009/07/laddering-a-research-interview-technique-for-uncovering-core-values.php) — Reputable practitioner write-up of values-laddering.
6. [Critical Decision Method (Gary Klein)](https://www.gary-klein.com/cdm) — Description by CDM's co-originator. **Authoritative primary.**
7. [Use of the Critical Decision Method to Elicit Expert Knowledge (Hoffman, Crandall & Shadbolt, 1998, Human Factors)](https://journals.sagepub.com/doi/10.1518/001872098779480442) — Peer-reviewed definitive academic treatment of CDM.
8. [Repertory grid (overview)](https://grokipedia.com/page/Repertory_grid) — Kelly's repertory grid and triadic elicitation; corroborates the primary Shadbolt & Smart treatment (traces to Kelly 1955).
9. [How to Study Thinking in Everyday Life: Contrasting Think-Aloud Protocols With Descriptions and Explanations (Ericsson & Simon, 1998)](https://cecas.clemson.edu/cedar/wp-content/uploads/2016/07/Ericsson.pdf) — Primary source; think-aloud (non-reactive) vs explain/describe (reactive). **Highest authority.**
10. [LLMREI: Automating Requirements Elicitation Interviews with LLMs (arXiv)](https://arxiv.org/pdf/2507.02564) — LLM elicitation interviews: lower recall on implicit content, generic-question tendency. *Recent preprint; treat figures as directional.*
11. [Active Learning: A Survey (Aggarwal et al., Ch. 22, Data Classification)](http://charuaggarwal.net/active-survey.pdf) — Authoritative survey; uncertainty sampling, QBC, expected model change/error reduction, the H·R hybrid. **High authority.**
12. [Value of Information (history: Raiffa & Schlaifer 1961)](https://grokipedia.com/page/Value_of_information) — VoI origins in Bayesian decision theory.
13. [Expected Value of Perfect Information](https://grokipedia.com/page/Expected_value_of_perfect_information) — EVPI definition and upper-bound property.
14. [Rationalising data collection using Value of Information analysis (arXiv:2409.00049)](https://arxiv.org/pdf/2409.00049) — The "collect iff VoI − cost > 0" rule.
15. [Value of Information Analysis for Research Decisions — ISPOR Task Force, Value in Health](https://www.valueinhealthjournal.com/article/S1098-3015(20)30027-9/fulltext) — Peer-reviewed; EVPI/EVSI/ENGS net-of-cost. **High authority.**
16. [Expected Information Gain (EIG)](https://www.emergentmind.com/topics/expected-information-gain-eig) — The three equivalent EIG formulations (posterior-entropy / KL / mutual-information).
17. [Modern Bayesian Experimental Design (arXiv:2302.14545)](https://arxiv.org/pdf/2302.14545) — Authoritative survey; EIG = mutual information as the standard BED objective. **High authority.**
18. [Information gain (decision tree) — Wikipedia](https://en.wikipedia.org/wiki/Information_gain_(decision_tree)) — IG = H(T)−H(T|a), mutual-information equivalence, 20-questions/ID3 intuition.
19. [Active Task Disambiguation with LLMs (Kobalczyk et al., 2025, arXiv:2502.04485)](https://arxiv.org/abs/2502.04485) — Clarifying-question selection as Bayesian experimental design. **High (van der Schaar lab).**
20. [BED-LLM: Intelligent Information Gathering with LLMs and Bayesian Experimental Design (arXiv:2508.21184)](https://arxiv.org/html/2508.21184v1) — EIG-driven questioning; 91% vs 68% vs 14% on 20-Questions.
21. [Open-world assumption — Wikipedia](https://en.wikipedia.org/wiki/Open-world_assumption) — Formal OWA/CWA distinction and the "unknown vs false" consequence.
22. [Negation as failure — Wikipedia](https://en.wikipedia.org/wiki/Negation_as_failure) — NAF, weak vs strong/classical negation, autoepistemic reading, link to CWA.
23. [Web Ontology Language — Wikipedia](https://en.wikipedia.org/wiki/Web_Ontology_Language) — RDF(S)/OWL are built on the open-world assumption.
24. [On Reliable Algorithmic Absence-Based Inference (Philosophy & Technology, Springer, 2025)](https://link.springer.com/article/10.1007/s13347-025-00929-x) — Peer-reviewed; when inferring from absence of evidence is/isn't valid (argument-from-ignorance).
25. [Null (SQL) — Wikipedia](https://en.wikipedia.org/wiki/Null_(SQL)) — SQL three-valued logic (TRUE/FALSE/UNKNOWN), NULL-as-marker, Kleene correspondence, UNKNOWN excluded from positive matches.
26. [Uncertainty Management in the Construction of Knowledge Graphs: a Survey (arXiv:2405.16929)](https://arxiv.org/html/2405.16929v2) — Weighted triples (s,p,o,confidence); separate extraction/source/reliability confidence; plausibility/typicality. **High authority.**
27. [PROV-DM: The PROV Data Model — W3C Recommendation](https://www.w3.org/TR/prov-dm/) — The authoritative W3C provenance standard (Entity/Activity/Agent + relations).
28. [RDF-star and SPARQL-star — GraphDB documentation](https://graphdb.ontotext.com/documentation/10.8/rdf-sparql-star.html) — Compact statement-level annotation (confidence/provenance per triple).
29. [The Complete Guide to Atomic Note-Taking — zettelkasten.de](https://zettelkasten.de/atomicity/guide/) — Canonical Zettelkasten source; atomicity principle and its link to connection. **Primary methodology.**
30. [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory (Chhikara et al., 2025, arXiv:2504.19413)](https://arxiv.org/html/2504.19413v1) — Two-phase extract/update, ADD/UPDATE/DELETE/NOOP, audit trail. **Primary paper.**
31. [Microsoft GraphRAG — official docs](https://microsoft.github.io/graphrag/) — Leiden clustering, community summaries, local vs global search; graph benefit scoped to broad/thematic questions. **Primary (vendor).**
32. [Sparse vs Dense vs Hybrid Retrieval (Abhik Sarkar)](https://www.abhik.ai/concepts/embeddings/sparse-vs-dense) — BM25 wins on exact tokens/identifiers; embeddings on paraphrase; hybrid as default.
33. [When to Ditch Your Vector DB for Simple BM25 (Thinking Loop)](https://medium.com/@ThinkingLoop/when-to-ditch-your-vector-db-for-simple-bm25-b4f044f1076b) — Lightweight-first: start with BM25, add vectors surgically.
34. [memweave: Zero-Infra Agent Memory with Markdown and SQLite (Towards Data Science)](https://towardsdatascience.com/memweave-zero-infra-ai-agent-memory-with-markdown-and-sqlite-no-vector-database-required/) — SQLite FTS5 (BM25) as a no-infra lexical index.
35. [Zep: A Temporal Knowledge Graph Architecture for Agent Memory (Rasmussen et al., 2025, arXiv:2501.13956)](https://arxiv.org/html/2501.13956v1) — Bi-temporal model; invalidate-don't-delete on contradiction. **Primary paper.**
36. [Generative Agents: Interactive Simulacra of Human Behavior (Park et al., 2023)](https://ar5iv.labs.arxiv.org/html/2304.03442) — Memory stream + recency·importance·relevance retrieval; reflection. **Primary paper.**
37. [MemGPT: Towards LLMs as Operating Systems (Packer et al., 2023, arXiv:2310.08560)](https://arxiv.org/pdf/2310.08560) — Tiered main/external context; self-editing memory via function calls. **Primary paper.**
38. [Letta Docs — Memory Blocks](https://docs.letta.com/guides/agents/memory-blocks/) — Production MemGPT successor; labeled in-context blocks, read-only pinning. **Primary (vendor docs).**
39. [A Survey on Neural Open Information Extraction (arXiv:2205.11725)](https://arxiv.org/pdf/2205.11725) — Authoritative OpenIE vs closed/schema-guided IE definitions.
40. [The guide to structured outputs and function calling with LLMs (Agenta)](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms) — Schema-constrained LLM extraction.
41. [How to Use Pydantic for LLMs (Pydantic official)](https://pydantic.dev/articles/llm-intro) — Pydantic-as-schema for LLM I/O; validation + retry. **Primary (maintainers).**
42. [Reduce hallucinations in search-grounded LLM responses (Firecrawl)](https://www.firecrawl.dev/glossary/web-search-apis/reduce-hallucinations-search-grounded-llm-responses) — The search→extract→generate→validate loop.
43. [Grounded Knowledge Graph Extraction via LLMs: Anchor-Constrained Framework with Provenance Tracking (MDPI Computers, 2025)](https://www.mdpi.com/2073-431X/15/3/178) — Provenance→anti-hallucination argument; character-level anchoring. Peer-reviewed.
44. [Citation-Grounded Code Comprehension (arXiv:2512.12117)](https://arxiv.org/html/2512.12117v1) — Mechanical citation-enforcement as architectural anti-hallucination.
45. [Claim Extraction for Fact-Checking: Data, Models, and Automated Metrics (arXiv:2502.04955)](https://arxiv.org/html/2502.04955v1) — Atomicity, decontextualization, the six quality metrics.
46. [DnDScore: Decomposition and Decontextualization for Factuality Verification (arXiv:2412.13175)](https://arxiv.org/html/2412.13175) — Atomic-subclaim + decontextualized-form verification.
47. [Fact in Fragments: Atomic Fact Extraction and Verification (arXiv:2506.07446)](https://arxiv.org/html/2506.07446v1) — Decompose-then-verify pipeline.
48. [FaStfact: Faster, Stronger Long-Form Factuality Evaluations (arXiv:2510.12839)](https://arxiv.org/html/2510.12839) — Decompose→retrieve-evidence→verify workflow.
49. [Snorkel: Rapid Training Data Creation with Weak Supervision (PMC7075849 / VLDB Journal)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7075849/) — Labeling functions, data programming, probabilistic labels. **Canonical.**
50. [DeepDive: Web-scale Knowledge-base Construction (Stanford VLDS)](https://www-cs.stanford.edu/people/chrismre/papers/deepdive_vlds.pdf) — Factor-graph KBC, distant supervision, calibrated marginals. **Primary.**
51. [LangChain summarization: map-reduce vs refine (Toolify)](https://www.toolify.ai/ai-news/langchain-summarization-mapreduce-vs-refine-methods-3395910) — Incremental-synthesis strategies and refine's drift limitations.
52. [Rule-based matching (spaCy official docs)](https://spacy.io/usage/rule-based-matching) — Rules vs statistical models and how to hybridize. **Primary (vendor).**

---

### A note on source quality

Most load-bearing claims rest on **standards** (W3C PROV), **peer-reviewed** work (Shadbolt & Smart, Ericsson & Simon, Hoffman et al., the active-learning and KG-uncertainty surveys, Snorkel/DeepDive), or **primary system papers** (MemGPT, Mem0, Zep/Graphiti, generative agents). The LLM-elicitation and LLM-clarifying-question papers [10][19][20] are recent preprints — credible and quantified, but young; their specific percentages are treated as directional, while their qualitative finding (explicit information-gain selection beats unguided LLM questioning) is corroborated across multiple sources and is safe to build on. Practitioner blogs [32][33][34][40][42][51] are used only for pipeline-shape and engineering-default claims, not for hard numbers.
