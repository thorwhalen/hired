# hired.candidate.workspace

The per-engagement facade: alignment reports, company research, interview prep.

A [`JDWorkspace`](#hired.candidate.workspace.JDWorkspace) is the domain entry point for work on **one engagement** —
one *or a group of* related job descriptions of the same company. It wraps a
[`JDStore`](hired.persistence.base.html.md#hired.persistence.base.JDStore) with validated, intention-revealing
methods and a back-reference to the owning
[`CandidateKnowledgeBase`](hired.candidate.knowledge_base.html.md#hired.candidate.knowledge_base.CandidateKnowledgeBase) (so an alignment
agent has both the candidate’s knowledge and the engagement’s work products at hand).

Obtain one via `kb.jd(jd_id, company=..., label=...)` — never construct directly.

### Classes

| [`JDWorkspace`](#hired.candidate.workspace.JDWorkspace)(kb, jd_id, \*[, store])   | Reports, company research, interview-prep briefings, and parsed jobs for one engagement.   |
|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|

### *class* hired.candidate.workspace.JDWorkspace(kb, jd_id, , store=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Reports, company research, interview-prep briefings, and parsed jobs for one engagement.

```pycon
>>> import tempfile, os
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> from hired.candidate import CandidateKnowledgeBase
>>> kb = CandidateKnowledgeBase()
>>> ws = kb.jd('acme', company='Acme, Inc.', label='Acme roles')
>>> ws.save_report('staff-ds', {'verdict': {'recommendation': 'apply'}})
>>> ws.get_report('staff-ds')['verdict']['recommendation']
'apply'
>>> ws.meta['company']
'Acme, Inc.'
```

#### report_versions(job_id)

Keys of archived prior versions of a job’s report (chronological).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### save_alignment(draft, , job_id=None)

Finalize an analyst-drafted alignment report and save it; return it.

Whatever produced the draft — the `hired-align` skill, the `hired
analyze` command, or an injected-LLM analyzer — this is the one path from
a draft to a persisted report: [`finalize_report()`](hired.alignment.html.md#hired.alignment.finalize_report)
re-derives everything deterministic, then [`save_report()`](#hired.candidate.workspace.JDWorkspace.save_report) archives the
previous version. `job_id` overrides the draft’s own.

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

#### save_briefing(key, data)

Persist an interview-prep research briefing (keyed by subject/job).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### save_company_report(company, data)

Persist a company/people research report (keyed by company name).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### save_report(job_id, data, , archive=True)

Persist the current alignment report, archiving the prior one first.

Archiving (on by default) snapshots any existing report into
`report_history` so the alignment-review agent can diff versions. The
snapshot is keyed by the *archived* report’s `created_at` (else now),
made filename-safe, and never overwrites an earlier snapshot.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
