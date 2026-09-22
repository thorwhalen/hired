# hired

Public API for the hired package.
Import the main user-facing functions and classes.

### *class* hired.ATSChecker

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Check resume for ATS compatibility.

### Examples

```pycon
>>> from hired.ats_checker import ATSChecker
>>>
>>> checker = ATSChecker()
>>> report = checker.check_resume(resume_dict)
>>> print(report.get_summary())
>>>
>>> # Check against specific job
>>> report = checker.check_resume(resume_dict, job_result)
```

#### check_resume(resume_content, job=None)

Check resume for ATS compatibility.

* **Parameters:**
  * **resume_content** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Resume content as dictionary (JSON Resume format)
  * **job** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Optional JobResult to check keyword matching
* **Return type:**
  [`ATSReport`](hired.ats_checker.html.md#hired.ats_checker.ATSReport)
* **Returns:**
  ATSReport with compatibility score and issues

### *class* hired.ATSReport(overall_score, issues=<factory>, keyword_match_score=0.0, matched_keywords=<factory>, missing_keywords=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Report from ATS compatibility check.

#### get_critical_issues()

Get critical issues.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`ATSIssue`](hired.ats_checker.html.md#hired.ats_checker.ATSIssue)]

#### get_issues_by_category(category)

Get issues filtered by category.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`ATSIssue`](hired.ats_checker.html.md#hired.ats_checker.ATSIssue)]

#### get_summary()

Get human-readable summary.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### get_warnings()

Get warnings.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`ATSIssue`](hired.ats_checker.html.md#hired.ats_checker.ATSIssue)]

#### to_dict()

Convert to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.AlignmentReport(\*\*data)

Bases: `BaseModel`

A complete, verdict-first alignment analysis for one JD.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.Application(job_title, company, id=None, job_url=None, location=None, salary_range=None, resume_path=None, cover_letter_path=None, status='draft', applied_date=None, created_at=None, updated_at=None, follow_up_date=None, last_contact_date=None, notes='', contacts='', interview_dates='', match_score=None, source=None, source_data='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Represents a job application.

#### *classmethod* from_job_result(job, \*\*kwargs)

Create an Application from a JobResult.

* **Parameters:**
  * **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
  * **\*\*kwargs** – Additional fields to set
* **Return type:**
  [`Application`](hired.tracking.html.md#hired.tracking.Application)
* **Returns:**
  Application object

#### to_dict()

Convert to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.ApplicationTracker(db_path=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Track job applications in a SQLite database.

### Examples

```pycon
>>> tracker = ApplicationTracker()
>>>
>>> # Add application from job search
>>> app_id = tracker.add_application(
...     job=job_result,
...     resume_path="resume.pdf",
...     status="applied"
... )
>>>
>>> # Update status
>>> tracker.update_status(app_id, "interview")
>>>
>>> # Get all applications in interview stage
>>> interviews = tracker.get_applications(status="interview")
>>>
>>> # Get statistics
>>> stats = tracker.get_statistics()
```

#### add_application(job=None, \*\*kwargs)

Add a new application.

* **Parameters:**
  * **job** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Optional JobResult to create application from
  * **\*\*kwargs** – Additional fields (or all fields if job not provided)
* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
* **Returns:**
  ID of created application

### Examples

```pycon
>>> # From JobResult
>>> app_id = tracker.add_application(
...     job=job_result,
...     resume_path="resume.pdf",
...     status="applied"
... )
>>>
>>> # Manual entry
>>> app_id = tracker.add_application(
...     job_title="Software Engineer",
...     company="TechCorp",
...     status="applied"
... )
```

#### delete_application(app_id)

Delete an application.

* **Parameters:**
  **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if deleted, False if not found

#### export_to_csv(output_path)

Export applications to CSV file.

* **Parameters:**
  **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to output CSV file

#### get_application(app_id)

Get application by ID.

* **Parameters:**
  **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Application`](hired.tracking.html.md#hired.tracking.Application)]
* **Returns:**
  Application object or None if not found

#### get_applications(status=None, company=None, limit=None)

Get applications with optional filtering.

* **Parameters:**
  * **status** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Filter by status
  * **company** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Filter by company name
  * **limit** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Maximum number of results
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Application`](hired.tracking.html.md#hired.tracking.Application)]
* **Returns:**
  List of Application objects

#### get_follow_ups_due(days=7)

Get applications that need follow-up.

* **Parameters:**
  **days** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of days to look ahead
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Application`](hired.tracking.html.md#hired.tracking.Application)]
* **Returns:**
  List of Application objects needing follow-up

#### get_statistics()

Get application statistics.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]
* **Returns:**
  Dictionary with statistics

#### update_application(app_id, \*\*kwargs)

Update application fields.

* **Parameters:**
  * **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
  * **\*\*kwargs** – Fields to update
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if updated, False if not found

#### update_status(app_id, status, notes=None)

Update application status.

* **Parameters:**
  * **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
  * **status** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – New status
  * **notes** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional notes to append
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if updated, False if not found

### *class* hired.CandidateKnowledgeBase(user='me', , store=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Accumulated, open-world knowledge about a single candidate (user-level).

```pycon
>>> import tempfile, os
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> kb = CandidateKnowledgeBase()                 # default candidate "me"
>>> from hired.candidate.base import Fact, FactCategory
>>> _ = kb.add_fact(Fact(statement='Built ML pipelines in Python',
...                       category=FactCategory.SKILL, tags=['python', 'ml']))
>>> [f.statement for f in kb.facts(category=FactCategory.SKILL)]
['Built ML pipelines in Python']
>>> [f.statement for f in kb.facts(tags=['ml'])]
['Built ML pipelines in Python']
```

#### add_fact(fact)

Persist a fact, returning its id.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### add_note(subject, text=None, , files=None)

Record volunteered info about a subject into its dossier.

`text` is appended to the dossier’s `overview.md`; `files` (a
`{name: bytes}` mapping) are attached as detail/media. Returns the
dossier. This is the “by the way, I also did X” entry point — a single
sentence or a whole folder both land here.

* **Return type:**
  [`TopicDossier`](hired.candidate.topics.html.md#hired.candidate.topics.TopicDossier)

#### add_source(src, , name=None)

Store a raw source (file path or bytes) and record its content digest.

Returns the source key (its name in the raw store). The digest (in
`state.json`) lets a later refresh detect new/changed sources without
re-reading everything. Facts extracted from a source cite it by this key.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### facts(, category=None, tags=None, status=FactStatus.ASSERTED, include_negations=True)

Iterate facts, optionally filtered by category/tags/status.

By default only `ASSERTED` facts are returned (superseded ones are
hidden). `tags` matches facts containing *any* of the given tags.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)]

#### jd(jd_id, , company=None, label=None)

Get-or-create the workspace for an engagement (1+ JDs of one company).

`company` / `label` are recorded in the engagement’s `meta` when given.

* **Return type:**
  [`JDWorkspace`](hired.candidate.workspace.html.md#hired.candidate.workspace.JDWorkspace)

#### jds()

Ids of all engagements for this candidate.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### needs_refresh()

True when uningested source/Q&A material exists (refresh warranted).

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### pending_qa()

Q&A entries not yet distilled into facts.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`QAEntry`](hired.candidate.base.html.md#hired.candidate.base.QAEntry)]

#### pending_sources()

Raw sources new, changed, or not yet distilled into facts.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### record_qa(entry, , derived_facts=None)

Append a clarifying Q&A exchange; optionally distill it into facts.

When `derived_facts` (atomic fact records extracted from the answer) are
given, they are ingested with `SourceKind.QA` provenance (`source_id`
= the Q&A id, quotes verified against the answer) and back-linked via the
entry’s `derived_fact_ids` — so a Q&A answer becomes reusable,
discoverable knowledge rather than being buried in the history.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### refresh(mode='soft', , ingest_fn=None, apply=True)

Refresh `info` from changed sources + undistilled Q&A.

`ingest_fn(item)` supplies extraction (intelligence is external); with
`apply=False` the result is a non-destructive preview. See
[`hired.candidate.refresh`](hired.candidate.html.md#hired.candidate.refresh).

* **Return type:**
  [`RefreshReport`](hired.candidate.html.md#hired.candidate.RefreshReport)

#### regenerate_synopsis()

Rebuild and persist a human-readable synopsis from current facts.

This is a *projection* — always derived from the fact store, never
hand-edited — so it can be regenerated at any time without loss.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### save_upload(name, data)

Store a raw uploaded document by filename (see [`add_source()`](#hired.CandidateKnowledgeBase.add_source)).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### sources()

Keys of all raw sources the candidate has provided.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### supersede(old_fact_id, new_fact)

Replace `old_fact_id` with `new_fact` (invalidate, don’t delete).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### *property* synopsis *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

The last persisted synopsis, regenerating it if absent.

#### topic(name)

Get-or-create the dossier for a subject (overview + optional files).

* **Return type:**
  [`TopicDossier`](hired.candidate.topics.html.md#hired.candidate.topics.TopicDossier)

#### topics()

Slugs of all topic dossiers.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### *class* hired.CoverLetterData(applicant_name, applicant_email, company_name, position_title, applicant_phone=None, applicant_address=None, hiring_manager_name=None, opening_paragraph='', body_paragraphs=None, closing_paragraph='', date=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Data structure for cover letter generation.

#### to_dict()

Convert to dictionary for template rendering.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.DefaultAIAgent(, model='default', api_key=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Default AI agent implementation (mock).

### *class* hired.JDWorkspace(kb, jd_id, , store=None)

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

### *class* hired.JobAnalyzer(job)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Analyze job postings to extract key information for resume tailoring.

#### extract_keywords(top_n=20)

Extract most important keywords from job posting.

* **Parameters:**
  **top_n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of top keywords to return
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of keywords sorted by relevance

#### extract_requirements()

Extract job requirements from description.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of requirement strings

#### extract_skills(include_soft_skills=True)

Extract mentioned skills from job posting.

* **Parameters:**
  **include_soft_skills** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether to include soft skills
* **Return type:**
  [`Set`](https://docs.python.org/3/library/typing.html#typing.Set)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  Set of identified skills

#### get_summary()

Get a summary of the job posting.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]
* **Returns:**
  Dictionary with job summary

#### to_job_info_text()

Convert job posting to a formatted text suitable for resume generation.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Formatted job description text

### *class* hired.JobMatcher(candidate_skills=None, candidate_keywords=None, required_skills=None, min_salary=None, max_salary=None, preferred_locations=None, remote_only=False)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Match candidate profiles against job postings.

### Examples

```pycon
>>> matcher = JobMatcher(candidate_skills=['python', 'django', 'aws'])
>>> scores = matcher.score_jobs(job_results)
>>> top_jobs = matcher.get_top_matches(job_results, n=10)
```

#### filter_jobs(jobs, min_score=50.0)

Filter jobs that meet minimum score threshold.

* **Parameters:**
  * **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
  * **min_score** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Minimum score threshold (0-100)
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects that meet threshold

#### get_recommendations(jobs, top_n=5)

Get human-readable recommendations based on job matches.

* **Parameters:**
  * **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
  * **top_n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of top jobs to include in recommendations
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Formatted recommendation string

#### get_top_matches(jobs, n=10, min_score=0.0)

Get top N job matches sorted by score.

* **Parameters:**
  * **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
  * **n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of top matches to return
  * **min_score** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Minimum score threshold (0-100)
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`MatchScore`](hired.matching.html.md#hired.matching.MatchScore)]
* **Returns:**
  List of MatchScore objects sorted by overall_score descending

#### identify_skill_gaps(jobs)

Identify skills frequently requested but not possessed by candidate.

* **Parameters:**
  **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects to analyze
* **Returns:**
  frequency} for missing skills
* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

#### score_job(job)

Score a single job against candidate profile.

* **Parameters:**
  **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult to score
* **Return type:**
  [`MatchScore`](hired.matching.html.md#hired.matching.MatchScore)
* **Returns:**
  MatchScore object

#### score_jobs(jobs)

Score multiple jobs.

* **Parameters:**
  **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`MatchScore`](hired.matching.html.md#hired.matching.MatchScore)]
* **Returns:**
  List of MatchScore objects

### *class* hired.JobResult(title, source, company=None, company_url=None, job_url=None, location=None, is_remote=None, description=None, job_type=None, compensation=None, date_posted=None, date_updated=None, application_deadline=None, skills=<factory>, benefits=<factory>, emails=<factory>, raw_data=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Standardized job result across all sources.

This provides a unified interface regardless of which source
the job was retrieved from.

#### to_dict()

Convert JobResult to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.JobSearchSource

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Abstract base class for job search sources.

All job search sources must implement this interface to be
registered in the system.

#### *abstract property* display_name *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Return the display name of this source (e.g., ‘Indeed’, ‘USAJobs’).

#### *abstractmethod* get_setup_instructions()

Return setup instructions for this source.

Should include:

- Where to get API keys if needed
- Environment variables or config file settings
- URLs for documentation

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Multi-line string with setup instructions.

#### *abstractmethod* is_configured()

Check if this source is properly configured.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if the source is ready to use, False otherwise.

#### *abstract property* name *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Return the name of this source (e.g., ‘indeed’, ‘usajobs’).

#### *abstract property* requires_auth *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Return True if this source requires authentication/API keys.

#### *abstractmethod* search(criteria)

Search for jobs using the given criteria.

* **Parameters:**
  **criteria** ([`SearchCriteria`](hired.search.base.html.md#hired.search.base.SearchCriteria)) – SearchCriteria object with search parameters
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects
* **Raises:**
  * [**SourceConfigError**](hired.search.html.md#hired.search.SourceConfigError) – If the source is not properly configured
  * [**Exception**](https://docs.python.org/3/builtins/exceptions.html#Exception) – For other errors during search

#### validate_configured()

Validate that the source is configured, raise error if not.

* **Raises:**
  [**SourceConfigError**](hired.search.html.md#hired.search.SourceConfigError) – If the source is not properly configured
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.JobSources(registry=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Main facade for accessing job search sources.

Provides both mapping interface (dict-like access) and attribute access
to registered job sources.

### Examples

```pycon
>>> sources = JobSources()
>>> # List all available sources
>>> sources.list()
['jobspy', 'usajobs', 'adzuna']
```

```pycon
>>> # Access via attribute
>>> results = sources.jobspy.search(SearchCriteria(query="python developer"))
```

```pycon
>>> # Access via mapping
>>> results = sources['indeed'].search(SearchCriteria(query="data scientist"))
```

```pycon
>>> # Search across multiple sources
>>> results = sources.search_all(
...     SearchCriteria(query="software engineer", location="San Francisco")
... )
```

#### get_info(name)

Get information about a source.

* **Parameters:**
  **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name of the source
* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), `any`]
* **Returns:**
  Dictionary with source information including setup instructions

#### get_source(name)

Get a source by name.

* **Parameters:**
  **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name of the source
* **Return type:**
  [`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)
* **Returns:**
  JobSearchSource instance
* **Raises:**
  [**KeyError**](https://docs.python.org/3/builtins/exceptions.html#KeyError) – If source not found

#### keys()

Get list of source names (dict-like interface).

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### list()

List all registered sources.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of source names

#### list_available()

List sources that are configured and ready to use.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of configured source names

#### list_unconfigured()

List sources that need configuration.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of unconfigured source names

#### print_status()

Print the status of all registered sources.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### search(source_name, criteria)

Search using a specific source.

* **Parameters:**
  * **source_name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name of the source to use
  * **criteria** ([`SearchCriteria`](hired.search.base.html.md#hired.search.base.SearchCriteria)) – Search criteria
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects

#### search_all(criteria, sources=None, skip_unconfigured=True)

Search across multiple sources.

* **Parameters:**
  * **criteria** ([`SearchCriteria`](hired.search.base.html.md#hired.search.base.SearchCriteria)) – Search criteria
  * **sources** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]) – Optional list of source names. If None, uses all available sources.
  * **skip_unconfigured** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, skip sources that are not configured
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  Combined list of JobResult objects from all sources

### *class* hired.JobType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Standardized job types across all sources.

### *class* hired.LLMConfig(model, temperature=0.7, max_tokens=None, top_p=1.0, provider='openai', api_key=None, base_url=None, extra_params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Configuration for LLM model selection and parameters.

```pycon
>>> config = LLMConfig(model="gpt-4", temperature=0.7)
>>> config.model
'gpt-4'
```

#### to_dspy_lm()

Convert to DSPy LM instance.

#### to_langchain_kwargs()

Convert to LangChain model kwargs.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *class* hired.LLMResumeAgent(, model='gpt-4o-mini', client=None, api_key=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

AI agent that tailors a candidate’s profile to a job via an LLM.

Opt-in alternative to [`DefaultAIAgent`](#hired.DefaultAIAgent) (which is a pass-through). It
is **dependency-injected and lazy**: `openai` is imported only when an agent
is used *without* an injected `client`, so importing `hired` never
requires `openai`, and no API key is read at construction time. Inject a
`client` (anything exposing the OpenAI-style
`chat.completions.create`) to test without network or secrets.

```pycon
>>> class _FakeClient:
...     class chat:
...         class completions:
...             @staticmethod
...             def create(**_):
...                 ...
```

### *class* hired.MatchScore(job, overall_score, skill_match_score, keyword_match_score, matched_skills=<factory>, missing_skills=<factory>, matched_keywords=<factory>, compensation_match=None, location_match=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Score for a job match.

#### get_summary()

Get human-readable summary.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### to_dict()

Convert to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.RenderingConfig(format='pdf', theme='default', custom_css=None, custom_template=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Configuration for resume rendering.

### *class* hired.Requirement(\*\*data)

Bases: `BaseModel`

One atomic requirement extracted verbatim from a job description.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.RequirementRecord(\*\*data)

Bases: `BaseModel`

The analysis of one requirement against the candidate’s knowledge.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### hired.ResumeContent

alias of [`ResumeSchemaExtended`](hired.base.html.md#hired.base.ResumeSchemaExtended)

### *class* hired.ResumeExpertAgent(, llm_config=None, model_registry=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Autonomous agent that uses ResumeSession as a tool.

Operates in auto mode, making decisions about expansion, distillation,
search, and generation operations to produce complete resumes.

```pycon
>>> config = LLMConfig(model="gpt-4")
>>> agent = ResumeExpertAgent(llm_config=config)
>>> agent.llm_config.model
'gpt-4'
```

#### create_resume(session, , mode='standard', max_iterations=5)

Autonomously create resume using session as tool.

Operates in plan-and-execute pattern:

1. Analyze job and candidate info
2. Plan resume creation strategy
3. Execute operations (expand, distill, match)
4. Generate resume
5. Critique and refine

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### execute_plan(session, plan, , interactive=False, approval_callback=None)

Execute a plan step by step.

* **Parameters:**
  * **session** ([`ResumeSession`](hired.resume_agent.html.md#hired.resume_agent.ResumeSession)) – Resume session to operate on
  * **plan** ([`Plan`](hired.resume_agent.html.md#hired.resume_agent.Plan)) – Plan to execute
  * **interactive** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, pause after each step for approval
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  Dict with execution results and final outputs

#### propose_plan(session, , mode='standard')

Generate execution plan for resume creation.

Returns structured Plan object that can be edited before execution.

* **Return type:**
  [`Plan`](hired.resume_agent.html.md#hired.resume_agent.Plan)

#### revise_plan(plan, instruction)

Revise plan based on natural language instruction.

Uses LLM to interpret instruction and modify plan accordingly.

* **Return type:**
  [`Plan`](hired.resume_agent.html.md#hired.resume_agent.Plan)

### *class* hired.ResumeSchema(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'forbid'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.ResumeSchemaExtended(\*\*data)

Bases: [`ResumeSchema`](hired.resumejson_pydantic_models.html.md#hired.resumejson_pydantic_models.ResumeSchema)

Extended version of ResumeSchema that allows extra fields for custom sections.

This class inherits all the validation and structure from ResumeSchema
but allows additional fields to be stored for custom sections.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.ResumeSession(job_info, candidate_info, , mode=OperationMode.MANUAL, system_prompt=None, max_recent_turns=10, llm_config=None, model_registry=None, auto_persist=True, data_dir=None, name=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Stateful conversation session for resume creation.

Provides manual chat interface where users give natural language
instructions to perform expansion, distillation, search, and generation
operations. Maintains conversation history and structured state.

```pycon
>>> config = LLMConfig("gpt-4")
>>> session = ResumeSession(
...     job_info="Senior ML Engineer at TechCo",
...     candidate_info="5 years Python, ML experience",
...     llm_config=config
... )
>>> session.llm_config.model
'gpt-4'
```

#### chat(user_message)

Process user instruction and return assistant response.

This is the main interface for manual mode operation.
Automatically persists session after each turn if auto_persist enabled.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### *property* history *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[Turn](hired.resume_agent.html.md#hired.resume_agent.Turn)]*

Get all conversation turns.

#### *classmethod* list_persisted(data_dir=None)

List all persisted sessions.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

```pycon
>>> for session_info in ResumeSession.list_persisted():
...     print(session_info['session_id'])
```

#### *classmethod* load(session_id, , data_dir=None, llm_config=None)

Load session from persistent storage.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ResumeSession`](hired.resume_agent.html.md#hired.resume_agent.ResumeSession)]

```pycon
>>> session = ResumeSession.load("abc123def456")
>>> session.session_id if session else None
'abc123def456'
```

#### *property* metadata *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)*

Return a small metadata dict for quick inspection.

Includes: session_id, name, created_at (iso), n_turns, mode, model

#### save(data_dir=None)

Manually save session to persistent storage.

Returns path to saved session file.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

#### *property* snapshots *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[SessionSnapshot](hired.resume_agent.html.md#hired.resume_agent.SessionSnapshot)]*

Get all session snapshots.

#### *property* state *: [SessionState](hired.resume_agent.html.md#hired.resume_agent.SessionState)*

Get current session state.

#### switch_mode(mode)

Switch between manual and auto operation modes.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.SearchCriteria(query, location=None, country=None, city=None, state=None, postal_code=None, distance_miles=None, job_type=None, is_remote=None, posted_within_days=None, results_wanted=20, offset=0, min_salary=None, max_salary=None, keywords=<factory>, exclude_keywords=<factory>, source_params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Standardized search criteria across all sources.

Different sources may not support all criteria, but this provides
a consistent interface for users.

### hired.check_resume_ats(resume_content, job=None)

Quick utility to check resume ATS compatibility.

* **Parameters:**
  * **resume_content** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Resume content as dictionary (JSON Resume format)
  * **job** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Optional JobResult for keyword matching
* **Return type:**
  [`ATSReport`](hired.ats_checker.html.md#hired.ats_checker.ATSReport)
* **Returns:**
  ATSReport

### Examples

```pycon
>>> from hired import mk_content_for_resume
>>> from hired.ats_checker import check_resume_ats
>>>
>>> resume = mk_content_for_resume(candidate_info, job_info)
>>> report = check_resume_ats(resume.model_dump(), job_result)
>>> print(report.get_summary())
```

### hired.classify(record)

Fill `gap_size` and `bucket` (and `needs_clarification`) in place.

Returns the same record for convenience.

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

### hired.extract_job_keywords(job, top_n=20)

Extract top keywords from a job posting.

* **Parameters:**
  * **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
  * **top_n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of keywords to return
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of top keywords

### hired.generate_cover_letter_content(candidate_info, job_info, tone='professional')

Generate cover letter content from candidate and job information.

* **Parameters:**
  * **candidate_info** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Candidate information (resume dict or basics)
  * **job_info** (`Union`[[`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Job information (dict, text, or JobResult)
  * **tone** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Tone of the letter (‘professional’, ‘enthusiastic’, ‘formal’)
* **Return type:**
  [`CoverLetterData`](hired.cover_letter.html.md#hired.cover_letter.CoverLetterData)
* **Returns:**
  CoverLetterData object with generated content

### Examples

```pycon
>>> data = generate_cover_letter_content(
...     candidate_info={'basics': {'name': 'Jane Doe', 'email': 'jane@example.com'}},
...     job_info={'title': 'Software Engineer', 'company': 'TechCorp'},
... )
```

### hired.get_job_skills(job)

Extract skills mentioned in job posting.

* **Parameters:**
  **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
* **Return type:**
  [`Set`](https://docs.python.org/3/library/typing.html#typing.Set)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  Set of skills

### hired.job_to_text(job)

Convert a JobResult to formatted text for resume generation.

* **Parameters:**
  **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Formatted text description

### hired.mk_content_for_resume(candidate_info_src, job_info_src, , agent=None, validate=True, strict=False)

Generate resume content from candidate and job information.

* **Parameters:**
  * **candidate_info_src** (`Union`[[`ContentSource`](hired.base.html.md#hired.base.ContentSource), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – Candidate information as ContentSource, file path, or dict
  * **job_info_src** (`Union`[[`ContentSource`](hired.base.html.md#hired.base.ContentSource), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict), [`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Job information as ContentSource, file path, dict, or JobResult
  * **agent** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Optional AI agent for content generation
  * **validate** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether to validate the generated content
  * **strict** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether to use strict validation
* **Return type:**
  [`ResumeSchemaExtended`](hired.base.html.md#hired.base.ResumeSchemaExtended)
* **Returns:**
  ResumeSchemaExtended object with generated content

### Examples

```pycon
>>> # Using file paths
>>> content = mk_content_for_resume("candidate.json", "job.txt")
>>>
>>> # Using JobResult from job search
>>> from hired import JobSources, SearchCriteria
>>> sources = JobSources()
>>> jobs = sources.jobspy.search(SearchCriteria(query="python developer"))
>>> content = mk_content_for_resume(candidate_dict, jobs[0])
```

### hired.mk_cover_letter(candidate_info, job_info, , tone='professional', format='text', output_path=None)

Generate and render a cover letter.

* **Parameters:**
  * **candidate_info** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Candidate information (resume dict or basics)
  * **job_info** (`Union`[[`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Job information (dict, text, or JobResult)
  * **tone** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Tone of the letter (‘professional’, ‘enthusiastic’, ‘formal’)
  * **format** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Output format (‘text’, ‘html’, ‘markdown’)
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to save the cover letter
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Rendered cover letter as string

### Examples

```pycon
>>> from hired import mk_cover_letter, JobSources, SearchCriteria
>>>
>>> # From job search result
>>> sources = JobSources()
>>> jobs = sources.jobspy.search(SearchCriteria(query="software engineer"))
>>>
>>> letter = mk_cover_letter(
...     candidate_info={'basics': {'name': 'Jane Doe', 'email': 'jane@example.com'}},
...     job_info=jobs[0],
...     format='html'
... )
```

### hired.mk_resume(content, rendering=None, , output_path=None, strict=False)

Render resume content to final format.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

### hired.quick_match(candidate_skills, jobs, top_n=10)

Quick utility function to match jobs against candidate skills.

* **Parameters:**
  * **candidate_skills** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – List of candidate’s skills
  * **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
  * **top_n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of top matches to return
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`MatchScore`](hired.matching.html.md#hired.matching.MatchScore)]
* **Returns:**
  List of top MatchScore objects

### Examples

```pycon
>>> from hired import JobSources, SearchCriteria
>>> from hired.matching import quick_match
>>>
>>> sources = JobSources()
>>> jobs = sources.jobspy.search(SearchCriteria(query="python developer"))
>>>
>>> matches = quick_match(
...     candidate_skills=['python', 'django', 'postgresql'],
...     jobs=jobs,
...     top_n=5
... )
>>>
>>> for match in matches:
...     print(match.get_summary())
```

### hired.render_report_markdown(report)

Render the report as a Markdown string.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Modules

| [`alignment`](hired.alignment.html.md#module-hired.alignment)                                   | JD-vs-candidate alignment: classify each requirement honestly into four buckets.   |
|---------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| [`ats_checker`](hired.ats_checker.html.md#module-hired.ats_checker)                               | ATS (Applicant Tracking System) compatibility checker.                             |
| [`base`](hired.base.html.md#module-hired.base)                                             | Core data models and protocols for the hired package.                              |
| [`candidate`](hired.candidate.html.md#module-hired.candidate)                                   | Candidate knowledge domain: accumulate open-world facts about a candidate.         |
| [`config`](hired.config.html.md#module-hired.config)                                         | Configuration management using Mapping interfaces.                                 |
| [`content`](hired.content.html.md#module-hired.content)                                       | Content generation logic and AI agent implementations.                             |
| [`cover_letter`](hired.cover_letter.html.md#module-hired.cover_letter)                             | Cover letter generation functionality.                                             |
| [`job_utils`](hired.job_utils.html.md#module-hired.job_utils)                                   | Utilities for working with job postings and matching them to resumes.              |
| [`matching`](hired.matching.html.md#module-hired.matching)                                     | Job matching and scoring utilities.                                                |
| [`persistence`](hired.persistence.html.md#module-hired.persistence)                               | dol-based persistence foundation for hired (Storage v2).                           |
| [`render`](hired.render.html.md#module-hired.render)                                         | Rendering pipeline and theme management.                                           |
| [`renderers`](hired.renderers.html.md#module-hired.renderers)                                   | Renderer implementations package.                                                  |
| [`resume_agent`](hired.resume_agent.html.md#module-hired.resume_agent)                             | Resume Generation System - Core Architecture                                       |
| [`resumejson_pydantic_models`](hired.resumejson_pydantic_models.html.md#module-hired.resumejson_pydantic_models) | Pydantic models for resume json schema                                             |
| [`search`](hired.search.html.md#module-hired.search)                                         | Job search functionality for the hired package.                                    |
| [`tools`](hired.tools.html.md#module-hired.tools)                                           | High-level orchestration functions - the main API.                                 |
| [`tracking`](hired.tracking.html.md#module-hired.tracking)                                     | Application tracking system for managing job applications.                         |
| [`util`](hired.util.html.md#module-hired.util)                                             | Utilities for external dependencies and general helpers.                           |
