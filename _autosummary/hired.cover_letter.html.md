# hired.cover_letter

Cover letter generation functionality.

Generate professional cover letters tailored to specific job applications.

### Functions

| [`generate_cover_letter_content`](#hired.cover_letter.generate_cover_letter_content)(...[, tone])    | Generate cover letter content from candidate and job information.   |
|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`mk_cover_letter`](#hired.cover_letter.mk_cover_letter)(candidate_info, job_info, \*) | Generate and render a cover letter.                                 |
| [`render_cover_letter`](#hired.cover_letter.render_cover_letter)(cover_letter_data[, ...]) | Render cover letter to specified format.                            |

### Classes

| [`CoverLetterData`](#hired.cover_letter.CoverLetterData)(applicant_name, ...[, ...])   | Data structure for cover letter generation.   |
|------------------------------------------------------------------------------------------------|-----------------------------------------------|

### *class* hired.cover_letter.CoverLetterData(applicant_name, applicant_email, company_name, position_title, applicant_phone=None, applicant_address=None, hiring_manager_name=None, opening_paragraph='', body_paragraphs=None, closing_paragraph='', date=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Data structure for cover letter generation.

#### to_dict()

Convert to dictionary for template rendering.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.cover_letter.generate_cover_letter_content(candidate_info, job_info, tone='professional')

Generate cover letter content from candidate and job information.

* **Parameters:**
  * **candidate_info** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Candidate information (resume dict or basics)
  * **job_info** (`Union`[[`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Job information (dict, text, or JobResult)
  * **tone** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Tone of the letter (‘professional’, ‘enthusiastic’, ‘formal’)
* **Return type:**
  [`CoverLetterData`](#hired.cover_letter.CoverLetterData)
* **Returns:**
  CoverLetterData object with generated content

### Examples

```pycon
>>> data = generate_cover_letter_content(
...     candidate_info={'basics': {'name': 'Jane Doe', 'email': 'jane@example.com'}},
...     job_info={'title': 'Software Engineer', 'company': 'TechCorp'},
... )
```

### hired.cover_letter.mk_cover_letter(candidate_info, job_info, , tone='professional', format='text', output_path=None)

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

### hired.cover_letter.render_cover_letter(cover_letter_data, format='text', template=None)

Render cover letter to specified format.

* **Parameters:**
  * **cover_letter_data** ([`CoverLetterData`](#hired.cover_letter.CoverLetterData)) – CoverLetterData object
  * **format** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Output format (‘text’, ‘html’, ‘markdown’)
  * **template** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional custom Jinja2 template string
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Rendered cover letter as string
