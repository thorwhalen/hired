# hired.tools

High-level orchestration functions - the main API.

These are the primary user-facing functions that coordinate
the entire pipeline.

### Functions

| [`mk_content_for_resume`](#hired.tools.mk_content_for_resume)(candidate_info_src, ...)    | Generate resume content from candidate and job information.                                                |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`mk_resume`](#hired.tools.mk_resume)(content[, rendering, output_path, ...]) | Render resume content to final format.                                                                     |
| [`render_resume_with_template_and_css`](#hired.tools.render_resume_with_template_and_css)(content, ...) | Render a resume dict (or pydantic model) to PDF using a specific HTML template file and optional CSS file. |

### hired.tools.mk_content_for_resume(candidate_info_src, job_info_src, , agent=None, validate=True, strict=False)

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

### hired.tools.mk_resume(content, rendering=None, , output_path=None, strict=False)

Render resume content to final format.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

### hired.tools.render_resume_with_template_and_css(content, template_path, css_path=None, , format='pdf', strict=False)

Render a resume dict (or pydantic model) to PDF using a specific
HTML template file and optional CSS file.

* **Parameters:**
  * **content** (`Union`[[`ResumeSchemaExtended`](hired.base.html.md#hired.base.ResumeSchemaExtended), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – Resume content as a dict or ResumeSchemaExtended instance.
  * **template_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Path to an HTML/Jinja template file to render from.
  * **css_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Optional path to a CSS file; its contents will be passed to
    the renderer as `custom_css` so PDF rendering picks up the styles.
  * **format** – Output format, ‘pdf’ or ‘html’. Default is ‘pdf’.
  * **strict** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, enable stricter schema validation.
* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)
* **Returns:**
  PDF file bytes.
