# hired.alignment.rubric

Deterministic bucket assignment — the two-axis rubric in code.

The *judgment* (transfer distance, trainability, evidence) is supplied by the
analyst (Claude or an injected LLM). This module turns those judgments into a
[`Bucket`](hired.alignment.base.html.md#hired.alignment.base.Bucket) deterministically, so the classification is
auditable and reproducible. It also applies the **AI-leverage modifier**: a
candidate who works with armies of AI agents closes *codified / knowledge-breadth*
gaps faster — but not *tacit-judgment* or *enduring-aptitude* gaps.

See `misc/docs/DESIGN.md` §7.

### Functions

| [`apply_ai_leverage`](#hired.alignment.rubric.apply_ai_leverage)(closeability, ai_leverage, ...)   | Soften a *codified* gap's closeability by the candidate's AI leverage.                             |
|------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| [`assign_bucket`](#hired.alignment.rubric.assign_bucket)(record)                               | Assign the alignment bucket for a record, or `None` if it should be a clarifying question instead. |
| [`classify`](#hired.alignment.rubric.classify)(record)                                    | Fill `gap_size` and `bucket` (and `needs_clarification`) in place.                                 |
| [`compute_gap_size`](#hired.alignment.rubric.compute_gap_size)(required_level, candidate_level)   | Residual gap, floored at zero.                                                                     |

### hired.alignment.rubric.apply_ai_leverage(closeability, ai_leverage, , skill_type, is_tacit=False)

Soften a *codified* gap’s closeability by the candidate’s AI leverage.

Tacit/soft gaps and structurally-hard gaps are never softened — AI agents
extend *breadth of codified knowledge*, not judgment or enduring aptitude.

* **Return type:**
  [`Closeability`](hired.alignment.base.html.md#hired.alignment.base.Closeability)

```pycon
>>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
...                    skill_type=SkillType.TECHNICAL)
<Closeability.LEARNABLE: 'learnable'>
>>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
...                    skill_type=SkillType.SOFT_SKILL)
<Closeability.REQUIRES_EXPERIENCE: 'requires_experience'>
```

### hired.alignment.rubric.assign_bucket(record)

Assign the alignment bucket for a record, or `None` if it should be a
clarifying question instead.

Returns `None` when the requirement is `UNKNOWN` on an OPEN field — that
routes to elicitation rather than being scored as a gap (the “don’t assume
absence” rule). `UNKNOWN` on a CLOSED field is treated as a real gap.

* **Return type:**
  [`Bucket`](hired.alignment.base.html.md#hired.alignment.base.Bucket) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### hired.alignment.rubric.classify(record)

Fill `gap_size` and `bucket` (and `needs_clarification`) in place.

Returns the same record for convenience.

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

### hired.alignment.rubric.compute_gap_size(required_level, candidate_level)

Residual gap, floored at zero.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
