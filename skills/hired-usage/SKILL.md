---
name: hired-usage
description: Use when helping a job seeker with `hired` — tailor/generate a resume and render it to PDF/HTML, search jobs across boards, score/match a resume to a job, run an ATS-compatibility check, draft a cover letter, or track applications. Triggers on "tailor/build a resume", "render resume to PDF", "search for jobs", "match resume to job", "ATS check", "cover letter", "track applications". Core install `pip install hired`; features need extras (`hired[pdf]`, `hired[search]`, `hired[ai]`, `hired[all]`).
---

# Using `hired`

A job-application suite. `import hired` works with core deps alone; specific
features need extras.

## Core: tailor → render a resume

```python
from hired import mk_content_for_resume, mk_resume

content = mk_content_for_resume(candidate, job)          # candidate/job: dict | file path | JobResult
pdf = mk_resume(content, {"format": "pdf", "theme": "default"})   # bytes
```

- `candidate`/`job` may be dicts, file paths (json/yaml), or a `JobResult`.
- Rendering: HTML always; **PDF needs `hired[pdf]`** (WeasyPrint + system libs
  cairo/pango), or `hired[rendercv]` for LaTeX/Typst-quality PDFs.

### Real AI tailoring (opt-in)

By default `mk_content_for_resume` uses a pass-through agent. For real LLM
tailoring, install `hired[ai]` and inject `LLMResumeAgent` (needs `OPENAI_API_KEY`):

```python
from hired import LLMResumeAgent
content = mk_content_for_resume(candidate, job, agent=LLMResumeAgent())
```

## Search jobs (`hired[search]`)

```python
from hired import JobSources, SearchCriteria
sources = JobSources()
jobs = sources.search_all(SearchCriteria(query="python developer", location="SF"))
```

Sources: `jobspy` (no key), `adzuna`/`usajobs` (need `ADZUNA_*` / `USAJOBS_*`).

## Support the application (core deps)

```python
from hired import quick_match, check_resume_ats, mk_cover_letter, ApplicationTracker
quick_match(resume, jobs)              # score/rank jobs vs the resume
check_resume_ats(resume_dict, job)     # ATS-compatibility report
mk_cover_letter(resume, job)           # draft a cover letter
ApplicationTracker().add_application(...)   # track applications (SQLite)
```

## Pick the install

`pip install hired[all]` for everything, or compose: `hired[pdf]`, `hired[search]`,
`hired[ai]`, `hired[rendercv]`.
