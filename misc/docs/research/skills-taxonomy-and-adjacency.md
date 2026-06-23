# Skill-alignment analysis: a grounded framework for four-bucket requirement classification

*Research synthesis for classifying each job requirement into: (1) strong match, (2) adjacent/transferable, (3) hard-to-learn gap, (4) learnable gap.*

## The core structural insight

The classification is governed by **two orthogonal axes**, not one:

- **Axis A — Transfer distance:** how close is the candidate's experience to the requirement? (Drives the match↔gap split, and the "adjacent" bucket.)
- **Axis B — Trainability:** if there's a gap, is it a *knowledge/skill* gap (learnable) or an *ability/aptitude/tacit* gap (hard to learn)?

Bucket 1 = near on A. Bucket 2 = mid-distance on A. Buckets 3 & 4 = far on A, split by B. This two-axis structure is independently supported by I-O psychology (KSAO), career counseling (Fine/Bolles), labor economics (skill-space networks), and learning science (tacit/explicit + near/far transfer).

## Skills taxonomies — what to integrate

| Taxonomy | Coverage | Graph structure | Free static dataset? | License | Verdict |
|---|---|---|---|---|---|
| **ESCO** (EU) | ~13,500 skills, ~3,000 occupations | Richest: native skill→skill relations, broader/narrower hierarchy, essential/optional occupation↔skill edges, 4-level skill-reuse tag | Yes — CSV/RDF/JSON-LD, URI-keyed edge files | CC BY 4.0 | **Primary choice.** Already a graph, no API key. |
| **O*NET** (US DOL) | 1,016 occupations | Occupation↔descriptor weighted bipartite (Skills/Abilities/Knowledge/Work Activities) + Related Occupations. No native skill→skill hierarchy | Yes — one ZIP | CC BY 4.0 | **Recommended complement** for US occupation adjacency + the ability-vs-skill split that powers Axis B. |
| **Lightcast Open Skills** | ~34,000 skills | Category hierarchy + co-occurrence | No — API-only, gated | ToS, not CC | Avoid as core dep. |
| **SkillsFuture (SG)** | 38 sectors | Role↔skill bipartite | Yes | SG Open Data | Regional add-on only; no skill→skill graph. |

**Recommendation: ESCO backbone + O*NET complement** (both CC BY 4.0, one attribution block). Ship ESCO English-only CSV. Lightest build path: embed each skill label once at build time with a small local model and ship a static `(skill_uri, label, vector)` table (~few MB float16 for ~13k skills); runtime is pure NumPy cosine — no torch, no API at runtime.

## Modeling skill adjacency (Axis A)

Three families, increasing dependency weight:

- **(a) Graph-based (co-occurrence/complementarity):** the validated "Skillscape" recipe — occupation×skill importance matrix → Revealed Comparative Advantage to strip ubiquity bias → complementarity edge weight (min of conditional probabilities). Deps: numpy/pandas/networkx. Interpretable but corpus-biased, transductive (no zero-shot), symmetric unless you add nestedness (prerequisite direction).
- **(b) Embedding-based (cosine of skill vectors):** best pragmatic option — encode each skill string/definition with `all-MiniLM-L6-v2` (384-dim, ~80 MB, CPU, no key), take cosine. Zero-shot on unseen skills. Caveat: captures *linguistic* similarity, not labor-market transferability; best fused with a co-occurrence graph. Pulls torch — gate behind an `[embeddings]` extra.
- **(c) LLM-judgment:** best zero-shot reasoning + human-readable rationale, but non-deterministic, hallucination-prone on niche skills, O(N²) costly, needs a key. Use as a re-ranker/explainer over an embedding-retrieved shortlist — never the primary index; inject the client lazily.

**Recommended layered architecture (respects import-safety):**
1. **Core (light):** ESCO graph + O*NET descriptor vectors → RCA/complementarity adjacency. Pure numpy/pandas/networkx.
2. **`embeddings` extra (heavy):** MiniLM cosine for zero-shot OOV adjacency; blend `α·cosine + (1−α)·graph_proximity`.
3. **`ai` extra (lazy, injected):** LLM re-ranker that explains transfer and judges only a shortlist.

## Transferable-skills frameworks (justifies the "adjacent" bucket)

The Fine→Bolles triad:
- **Functional/transferable skills** (verbs — analyze, coach, audit) expressed in abstract **Data/People/Things** vocabulary → the theoretical home of bucket 2. Fine's D/P/T scales are ordinal & subsuming, giving a built-in directionality rule for strong-match vs adjacent.
- **Self-management/adaptive skills** (adverbs) — dispositional, hard to retrain.
- **Specific-content skills** (nouns) — job-bound, non-portable; when missing, usually a *learnable knowledge* gap.

O*NET operationalizes the same lineage (Cross-Functional Skills = transferable layer vs Occupation-Specific Information = bound layer). **Transferable Skills Analysis (TSA)** from vocational rehab gives a graded "closeness of transfer" ladder that maps ~1:1 onto the four buckets:

| TSA grade | Criterion | Bucket |
|---|---|---|
| Direct-Closest | same Work Fields + same Materials/Products/Subject/Services | 1 strong match |
| Closely/Generally Transferable | shared work field, different content | 2 adjacent |
| Fair/Potential (retraining) | single-field match, content missing | 4 learnable gap |
| Exceeds residual aptitude | gap is an aptitude ceiling | 3 hard-to-learn |

## Learnable vs hard-to-learn (Axis B)

**KSAO is the key.** Trainability gradient: **Knowledge** (declarative, most trainable) → **Skill** (proficiency via practice, trainable) → **Ability** (enduring aptitude, resists training — select, don't teach). O*NET encodes this directly (Skills = "developed capacities", Abilities = "enduring attributes").

Four features predict *how fast* someone clears the **competence** bar (Dreyfus "Competent", not Expert — the interview/ramp target):
1. **Tacit vs explicit (codified)** — the single most discriminating feature. Explicit (specs/courses/tests define correctness — a framework API, SQL) → self-serve fast → learnable. Tacit (judgment, taste, org/domain "feel" — architecture at scale, negotiation) transmits only through experience → hard-to-learn.
2. **Near vs far transfer** — near (shared paradigm/mental models — one OO language → another) → fast; far (new paradigm — OO → functional) → slow.
3. **Prerequisite dependency** — does the candidate already hold the skill's prerequisites?
4. **Feedback-loop tightness** — tight loops (compilers, tests) accelerate; slow/ambiguous (strategy, design taste) don't.

(The 10,000-hour figure is about elite expertise and irrelevant here — Ericsson himself rejected Gladwell's framing.)

## Per-bucket rubric

- **Bucket 1 — Strong match:** high Axis-A proximity. Direct skill match (exact/ESCO synonym/narrower-broader) OR TSA Direct-Closest, with demonstrated Fine D/P/T level ≥ required.
- **Bucket 2 — Adjacent/transferable:** mid-distance A. Shared functional skill (Fine D/P/T) or O*NET cross-functional skill across different content; graph proximity above threshold; embedding cosine mid-band. The asset is the *function*; the delta is the *content*.
- **Bucket 3 — Hard-to-learn gap:** far on A AND gap is an Ability/aptitude or tacit-dominant skill (low trainability), OR role needs expert intuition. Select for it; don't expect to teach it during ramp.
- **Bucket 4 — Learnable gap:** far on A BUT gap is Knowledge/low-complexity Skill that is explicit/codified AND near-transfer from the candidate's expertise, prerequisites largely held, tight feedback loops.

**One-line classifier:** Score transfer distance (A) and trainability (B). Near A → bucket 1; mid A → bucket 2; far A → split by B (low trainability → bucket 3; high trainability → bucket 4).

## REFERENCES

[1] [ESCO — About / Escopedia](https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/esco-v1)
[2] [ESCO — Downloadable datasets structure](https://esco.ec.europa.eu/en/structure-esco-downloadable-datasets) · [Skill reusability level](https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/skill-reusability-level)
[3] [ESCO — Licence notice (CC BY 4.0)](https://esco.ec.europa.eu/en/copyright-notice-esco-skills-competences)
[4] [O*NET Resource Center — Database](https://www.onetcenter.org/database.html)
[5] [O*NET Database License (CC BY 4.0)](https://www.onetcenter.org/license_db.html)
[6] [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) · [TechWolf/Synthetic-ESCO-skill-sentences](https://huggingface.co/datasets/TechWolf/Synthetic-ESCO-skill-sentences)
[7] [Alabdulkareem et al. — "Unpacking the polarization of workplace skills" (Skillscape), Science Advances 2018](https://www.science.org/doi/10.1126/sciadv.aao6030)
[8] [Hidalgo & Balland — The Principle of Relatedness (2018)](https://ideas.repec.org/p/egu/wpaper/1830.html)
[9] [Neffke & Henning — "Skill relatedness and firm diversification," SMJ 2013](https://scholar.harvard.edu/neffke/publications/skill-relatedness-and-firm-diversification)
[10] [Lyu, Frank, Rahwan et al. — "Skill dependencies uncover nested human capital" (arXiv:2303.15629)](https://arxiv.org/pdf/2303.15629)
[11] [Patterns of co-occurrent skills in UK job adverts — PLOS Complex Systems 2024](https://journals.plos.org/complexsystems/article?id=10.1371%2Fjournal.pcsy.0000028)
[12] [Van-Duyet et al. — "Skill2vec" (arXiv:1707.09751)](https://arxiv.org/abs/1707.09751)
[13] [Zhang et al. — "Job2Vec" (arXiv:2009.07429)](https://ar5iv.labs.arxiv.org/html/2009.07429)
[14] [Dawson et al. — "Skill-driven Recommendations for Job Transition Pathways," PLOS ONE 2021](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0254722)
[15] [CareerBERT — resume↔ESCO matching (arXiv:2503.02056)](https://arxiv.org/html/2503.02056)
[17] [Fine & Wiley — "Introduction to Functional Job Analysis" (1971)](https://files.eric.ed.gov/fulltext/ED060221.pdf)
[18] [eParachute — "What's a Skill?" (Bolles triad)](https://eparachute.com/blog/What_is_a_Skill)
[19] [National Academies — Review of O*NET, Ch.2 Content Model](https://www.nationalacademies.org/read/12814/chapter/5) · [O*NET — Cross-Functional Skills](https://www.onetonline.org/find/descriptor/browse/2.B)
[20] [SkillTRAN — Transferable Skills Analysis Defined](https://skilltran.com/index.php/support-area/documentation/support-tsa-defined) · [Wikipedia — TSA](https://en.wikipedia.org/wiki/Transferable_skills_analysis)
[21] [Spector — "What Does KSAO Stand For?"](https://paulspector.com/what-does-ksao-stand-for/) · [APA — KSAOs](https://dictionary.apa.org/knowledge-skills-abilities-and-other-characteristics)
[22] [Dreyfus model — Wikipedia](https://en.wikipedia.org/wiki/Dreyfus_model_of_skill_acquisition)
[23] [Ericsson's critique of the 10,000-hour rule (Salon 2016)](https://www.salon.com/2016/04/10/malcolm_gladwell_got_us_wrong_our_research_was_key_to_the_10000_hour_rule_but_heres_what_got_oversimplified/)
[24] [Polanyi — Tacit Knowledge](https://www.researchgate.net/publication/215439276_Tacit_Knowledge_Revisited_-_We_Can_Still_Learn_from_Polanyi) · [SECI model — Wikipedia](https://en.wikipedia.org/wiki/SECI_model_of_knowledge_dimensions)
[25] [Transfer of learning — Wikipedia](https://en.wikipedia.org/wiki/Transfer_of_learning)
[26] [Programming-paradigm transfer (arXiv:2010.08292)](https://arxiv.org/pdf/2010.08292)
