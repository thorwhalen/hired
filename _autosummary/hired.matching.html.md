# hired.matching

Job matching and scoring utilities.

Match candidate profiles against job postings to identify the best opportunities.

### Functions

| [`quick_match`](#hired.matching.quick_match)(candidate_skills, jobs[, top_n])   | Quick utility function to match jobs against candidate skills.   |
|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------|

### Classes

| [`JobMatcher`](#hired.matching.JobMatcher)([candidate_skills, ...])        | Match candidate profiles against job postings.   |
|---------------------------------------------------------------------------------------------|--------------------------------------------------|
| [`MatchScore`](#hired.matching.MatchScore)(job, overall_score, ...[, ...]) | Score for a job match.                           |

### *class* hired.matching.JobMatcher(candidate_skills=None, candidate_keywords=None, required_skills=None, min_salary=None, max_salary=None, preferred_locations=None, remote_only=False)

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
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`MatchScore`](#hired.matching.MatchScore)]
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
  [`MatchScore`](#hired.matching.MatchScore)
* **Returns:**
  MatchScore object

#### score_jobs(jobs)

Score multiple jobs.

* **Parameters:**
  **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`MatchScore`](#hired.matching.MatchScore)]
* **Returns:**
  List of MatchScore objects

### *class* hired.matching.MatchScore(job, overall_score, skill_match_score, keyword_match_score, matched_skills=<factory>, missing_skills=<factory>, matched_keywords=<factory>, compensation_match=None, location_match=None)

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

### hired.matching.quick_match(candidate_skills, jobs, top_n=10)

Quick utility function to match jobs against candidate skills.

* **Parameters:**
  * **candidate_skills** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – List of candidate’s skills
  * **jobs** ([`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – List of JobResult objects
  * **top_n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of top matches to return
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`MatchScore`](#hired.matching.MatchScore)]
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
