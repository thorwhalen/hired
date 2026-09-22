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
`report_history` so the alignment-review agent can diff versions.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
