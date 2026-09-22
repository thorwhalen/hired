# hired.job_utils

Utilities for working with job postings and matching them to resumes.

### Functions

| [`extract_job_keywords`](#hired.job_utils.extract_job_keywords)(job[, top_n])   | Extract top keywords from a job posting.                     |
|---------------------------------------------------------------------------------------|--------------------------------------------------------------|
| [`get_job_skills`](#hired.job_utils.get_job_skills)(job)                  | Extract skills mentioned in job posting.                     |
| [`job_to_text`](#hired.job_utils.job_to_text)(job)                     | Convert a JobResult to formatted text for resume generation. |

### Classes

| [`JobAnalyzer`](#hired.job_utils.JobAnalyzer)(job)   | Analyze job postings to extract key information for resume tailoring.   |
|---------------------------------------------------------------------|-------------------------------------------------------------------------|

### *class* hired.job_utils.JobAnalyzer(job)

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

### hired.job_utils.extract_job_keywords(job, top_n=20)

Extract top keywords from a job posting.

* **Parameters:**
  * **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
  * **top_n** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of keywords to return
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of top keywords

### hired.job_utils.get_job_skills(job)

Extract skills mentioned in job posting.

* **Parameters:**
  **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
* **Return type:**
  [`Set`](https://docs.python.org/3/library/typing.html#typing.Set)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  Set of skills

### hired.job_utils.job_to_text(job)

Convert a JobResult to formatted text for resume generation.

* **Parameters:**
  **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Formatted text description
