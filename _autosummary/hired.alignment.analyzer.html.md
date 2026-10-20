# hired.alignment.analyzer

Library-mode autonomous alignment analysis, driven by an injected LLM.

The non-interactive counterpart of the `hired-align` skill: given a job
description’s text and a candidate’s facts, produce a *draft*
[`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport) that
[`save_alignment()`](hired.candidate.workspace.html.md#hired.candidate.workspace.JDWorkspace.save_alignment) finalizes and
persists. The pipeline is a grounded per-requirement judge:

1. **decompose** — the LLM splits the JD into atomic `Requirement` records;
2. **retrieve** — the most relevant facts are pulled from the knowledge base
   (lexical overlap by default, every fact when the KB fits in `k`; inject
   `retrieve=make_embedding_retriever()` for semantic retrieval);
3. **quote-then-answer** — the LLM must quote a verbatim span of a cited fact
   *before* it states a match;
4. **gate** — a quote that is not verbatim in the cited fact, a CONTRADICTED
   judgment not backed by a negation fact, or (with `nli`) a quote that does
   not entail the requirement, drops the judgment to UNKNOWN: it becomes a
   question for the candidate, never an invented match or gap;
5. **aggregate** — the verdict and fit band are computed deterministically from
   the records ([`aggregate_verdict()`](#hired.alignment.analyzer.aggregate_verdict)). The LLM explains; it never sets the score.

Like [`LLMResumeAgent`](hired.content.html.md#hired.content.LLMResumeAgent), the analyzer is lazy and injectable:
`openai` (the `ai` extra) is imported only when no `client` is given, and no
key is read at construction. `client` is anything exposing the OpenAI-style
`chat.completions.create`.

### Functions

| [`aggregate_verdict`](#hired.alignment.analyzer.aggregate_verdict)(records, \*[, apply_at, ...])   | The verdict and fit band, computed from classified records alone.                                                                                                                                                             |
|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`analyze_jd`](#hired.alignment.analyzer.analyze_jd)(workspace, jd_text, \*, job_id[, ...]) | Analyse `jd_text` against the workspace candidate's facts and persist it.                                                                                                                                                     |
| [`coverage`](#hired.alignment.analyzer.coverage)(records, \*[, class_weights, ...])       | `(coverage, resolved_share)`: weighted bucket credit over resolved records, and the weighted share of records that are resolved at all.                                                                                       |
| [`make_embedding_retriever`](#hired.alignment.analyzer.make_embedding_retriever)([embed, min_similarity]) | A semantic `retrieve` for [`LLMAlignmentAnalyzer`](#hired.alignment.analyzer.LLMAlignmentAnalyzer): the `k` facts most cosine-similar to the requirement, so adjacent skills (RabbitMQ for a Kafka requirement) reach the judge. |
| [`openai_embed`](#hired.alignment.analyzer.openai_embed)(\*[, client, model])                 | An `Embed` over OpenAI-style `client.embeddings.create` (`ai` extra).                                                                                                                                                         |
| [`quote_is_grounded`](#hired.alignment.analyzer.quote_is_grounded)(quote, fact, \*[, min_words])   | True when `quote` is a verbatim span (modulo case/whitespace) of `fact`, at least `min_words` long.                                                                                                                           |
| [`retrieve_facts`](#hired.alignment.analyzer.retrieve_facts)(requirement, facts, \*[, k, ...])  | The `k` facts sharing the most words with the requirement.                                                                                                                                                                    |

### Classes

| [`LLMAlignmentAnalyzer`](#hired.alignment.analyzer.LLMAlignmentAnalyzer)(\*[, model, client, ...])   | Draft an alignment report from JD text and facts, with an injected LLM.   |
|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|

### *class* hired.alignment.analyzer.LLMAlignmentAnalyzer(\*, model='gpt-4o-mini', client=None, api_key=None, n_samples=1, temperature=None, calibrator=None, retrieve=<function retrieve_facts>, top_k=5, nli=False, entails=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Draft an alignment report from JD text and facts, with an injected LLM.

`n_samples` > 1 judges each requirement several times and feeds the
agreement into [`apply_calibration()`](hired.alignment.calibration.html.md#hired.alignment.calibration.apply_calibration) (with
`calibrator`, the conformal ask/auto-decide rule). `nli` adds an
entailment check on every confirmed quote; `entails` replaces the default
(an LLM call) with any `(premise, hypothesis) -> bool`. `retrieve`
replaces the lexical [`retrieve_facts()`](#hired.alignment.analyzer.retrieve_facts), e.g. with
[`make_embedding_retriever()`](#hired.alignment.analyzer.make_embedding_retriever) for semantic retrieval.

```pycon
>>> class _Fake:
...     class chat:
...         class completions:
...             @staticmethod
...             def create(**_): ...
>>> LLMAlignmentAnalyzer(client=_Fake()).analyze(jd_text, facts)
```

#### analyze(jd_text, facts, , job_id='job', job_title='', company='', requirements=None)

A draft report: decompose (unless `requirements` given), judge, aggregate.

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

#### decompose(jd_text)

The JD’s atomic requirements, as the LLM extracts them.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Requirement`](hired.alignment.base.html.md#hired.alignment.base.Requirement)]

#### judge(requirement, facts)

One gated, optionally sampled-and-calibrated record for `requirement`.

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

#### llm_entails(premise, hypothesis)

The LLM’s yes/no on whether `premise` establishes `hypothesis`.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.analyzer.aggregate_verdict(records, , apply_at=0.7, stretch_at=0.4, fit_bands=((0.85, FitBand.GREAT), (0.7, FitBand.GOOD), (0.5, FitBand.FAIR), (0.3, FitBand.WEAK), (0.0, FitBand.POOR)), class_weights={RequirementClass.DIFFERENTIATOR: 2.0, RequirementClass.GATE_KEEPER: 3.0, RequirementClass.VALUE_ADD: 1.0}, bucket_credit={Bucket.ADJACENT_TRANSFERABLE: 0.5, Bucket.GAP_HARD: 0.0, Bucket.GAP_LEARNABLE: 0.25, Bucket.STRONG_MATCH: 1.0})

The verdict and fit band, computed from classified records alone.

A blocking gap (a gate-keeper that is a hard gap or contradicted) means
*do not apply*; otherwise the weighted coverage picks the recommendation.
Confidence comes from how much of the JD is resolved, not from the LLM.

```pycon
>>> from hired.alignment.base import MatchType
>>> rec = classify(RequirementRecord(requirement=Requirement(text='Python'),
...     match_state='confirmed', match_type=MatchType.DIRECT, candidate_level=4))
>>> verdict, band = aggregate_verdict([rec])
>>> verdict.recommendation.value, band.value, verdict.confidence.value
('apply', 'great', 'high')
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Verdict`](hired.alignment.base.html.md#hired.alignment.base.Verdict), [`FitBand`](hired.alignment.base.html.md#hired.alignment.base.FitBand)]

### hired.alignment.analyzer.analyze_jd(workspace, jd_text, , job_id, job_title='', analyzer=None, requirements=None)

Analyse `jd_text` against the workspace candidate’s facts and persist it.

The draft goes through `JDWorkspace.save_alignment()` (finalize + archive +
save), the one path from a draft to a stored report. `analyzer` defaults to
an [`LLMAlignmentAnalyzer`](#hired.alignment.analyzer.LLMAlignmentAnalyzer) on the `ai` extra.

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

### hired.alignment.analyzer.coverage(records, , class_weights={RequirementClass.DIFFERENTIATOR: 2.0, RequirementClass.GATE_KEEPER: 3.0, RequirementClass.VALUE_ADD: 1.0}, bucket_credit={Bucket.ADJACENT_TRANSFERABLE: 0.5, Bucket.GAP_HARD: 0.0, Bucket.GAP_LEARNABLE: 0.25, Bucket.STRONG_MATCH: 1.0})

`(coverage, resolved_share)`: weighted bucket credit over resolved records,
and the weighted share of records that are resolved at all.

Records must be classified (see [`classify()`](hired.alignment.rubric.html.md#hired.alignment.rubric.classify)).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### hired.alignment.analyzer.make_embedding_retriever(embed=None, , min_similarity=0.0)

A semantic `retrieve` for [`LLMAlignmentAnalyzer`](#hired.alignment.analyzer.LLMAlignmentAnalyzer): the `k` facts most
cosine-similar to the requirement, so adjacent skills (RabbitMQ for a Kafka
requirement) reach the judge.

`embed` maps texts to vectors (default [`openai_embed()`](#hired.alignment.analyzer.openai_embed), the `ai` extra).
Fact vectors are cached by text, so each fact is embedded once per retriever.

```pycon
>>> vocab = ('kafka', 'rabbitmq', 'queue', 'french')
>>> def embed(texts):  # a fake: 'kafka' and 'rabbitmq' are both message queues
...     return [[t.lower().count(w) + ('queue' == w) * ('kafka' in t.lower() or
...              'rabbitmq' in t.lower()) for w in vocab] for t in texts]
>>> fs = [Fact(statement='Ran RabbitMQ in prod'), Fact(statement='Speaks French')]
>>> retrieve = make_embedding_retriever(embed)
>>> [f.statement for f in retrieve(Requirement(text='Kafka'), fs, k=1)]
['Ran RabbitMQ in prod']
```

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)]]

### hired.alignment.analyzer.openai_embed(, client=None, model='text-embedding-3-small')

An `Embed` over OpenAI-style `client.embeddings.create` (`ai` extra).

`openai` is imported, and the client made, only at the first call.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]], [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

### hired.alignment.analyzer.quote_is_grounded(quote, fact, , min_words=2)

True when `quote` is a verbatim span (modulo case/whitespace) of `fact`,
at least `min_words` long.

```pycon
>>> quote_is_grounded('kafka  CLUSTERS', Fact(statement='Ran Kafka clusters'))
True
>>> quote_is_grounded('Kafka expert', Fact(statement='Ran Kafka clusters'))
False
>>> quote_is_grounded('Kafka', Fact(statement='Ran Kafka clusters'))
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.analyzer.retrieve_facts(requirement, facts, , k=5, small_kb_passes_all=True)

The `k` facts sharing the most words with the requirement.

Lexical, so it misses an adjacent skill named in different words (RabbitMQ
for Kafka). When the whole knowledge base fits in `k` (and
`small_kb_passes_all`), every fact is passed, best overlap first, so the judge
sees the adjacent skill anyway; a negation fact sharing no word is still dropped,
so an unrelated “does not …” cannot back a contradiction. Otherwise facts
sharing no word are dropped (none if none do). For large KBs, inject [`make_embedding_retriever()`](#hired.alignment.analyzer.make_embedding_retriever).

```pycon
>>> from hired.candidate.base import Fact
>>> fs = [Fact(statement='Ran Kafka clusters'), Fact(statement='Speaks French')]
>>> [f.statement for f in retrieve_facts(Requirement(text='Kafka streaming'), fs)]
['Ran Kafka clusters', 'Speaks French']
>>> [f.statement for f in retrieve_facts(Requirement(text='Kafka streaming'), fs, k=1)]
['Ran Kafka clusters']
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)]
