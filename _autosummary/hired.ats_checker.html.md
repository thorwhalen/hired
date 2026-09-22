# hired.ats_checker

ATS (Applicant Tracking System) compatibility checker.

Analyze resumes to ensure they’re compatible with automated screening systems.

### Functions

| [`check_resume_ats`](#hired.ats_checker.check_resume_ats)(resume_content[, job])   | Quick utility to check resume ATS compatibility.   |
|--------------------------------------------------------------------------------------------|----------------------------------------------------|

### Classes

| [`ATSChecker`](#hired.ats_checker.ATSChecker)()                                | Check resume for ATS compatibility.    |
|----------------------------------------------------------------------------------------------|----------------------------------------|
| [`ATSIssue`](#hired.ats_checker.ATSIssue)(category, title, description, ...) | Represents an ATS compatibility issue. |
| [`ATSReport`](#hired.ats_checker.ATSReport)(overall_score[, issues, ...])     | Report from ATS compatibility check.   |

### *class* hired.ats_checker.ATSChecker

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
  [`ATSReport`](#hired.ats_checker.ATSReport)
* **Returns:**
  ATSReport with compatibility score and issues

### *class* hired.ats_checker.ATSIssue(category, title, description, suggestion)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Represents an ATS compatibility issue.

### *class* hired.ats_checker.ATSReport(overall_score, issues=<factory>, keyword_match_score=0.0, matched_keywords=<factory>, missing_keywords=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Report from ATS compatibility check.

#### get_critical_issues()

Get critical issues.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`ATSIssue`](#hired.ats_checker.ATSIssue)]

#### get_issues_by_category(category)

Get issues filtered by category.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`ATSIssue`](#hired.ats_checker.ATSIssue)]

#### get_summary()

Get human-readable summary.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### get_warnings()

Get warnings.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`ATSIssue`](#hired.ats_checker.ATSIssue)]

#### to_dict()

Convert to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.ats_checker.check_resume_ats(resume_content, job=None)

Quick utility to check resume ATS compatibility.

* **Parameters:**
  * **resume_content** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Resume content as dictionary (JSON Resume format)
  * **job** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Optional JobResult for keyword matching
* **Return type:**
  [`ATSReport`](#hired.ats_checker.ATSReport)
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
