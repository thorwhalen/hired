# hired.search.sources.jobspy

JobSpy source adapter.

Wraps the python-jobspy package to search across multiple job boards
(LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google) concurrently.

### Functions

| [`get_jobspy_source`](#hired.search.sources.jobspy.get_jobspy_source)()   | Get the default JobSpy source instance.   |
|------------------------------------------------------------------------|-------------------------------------------|

### Classes

| [`JobSpySource`](#hired.search.sources.jobspy.JobSpySource)([sites, proxies])   | JobSpy source implementation.   |
|-----------------------------------------------------------------------------------|---------------------------------|

### *class* hired.search.sources.jobspy.JobSpySource(sites=None, proxies=None)

Bases: [`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)

JobSpy source implementation.

Uses python-jobspy to scrape jobs from multiple sources simultaneously.
Does not require API keys, but may be subject to rate limiting.

#### *property* display_name *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Return the display name of this source (e.g., ‘Indeed’, ‘USAJobs’).

#### get_setup_instructions()

Return setup instructions for this source.

Should include:

- Where to get API keys if needed
- Environment variables or config file settings
- URLs for documentation

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Multi-line string with setup instructions.

#### is_configured()

Check if this source is properly configured.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if the source is ready to use, False otherwise.

#### *property* name *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

Return the name of this source (e.g., ‘indeed’, ‘usajobs’).

#### *property* requires_auth *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Return True if this source requires authentication/API keys.

#### search(criteria)

Search for jobs using JobSpy.

* **Parameters:**
  **criteria** ([`SearchCriteria`](hired.search.base.html.md#hired.search.base.SearchCriteria)) – Search criteria
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects

### hired.search.sources.jobspy.get_jobspy_source()

Get the default JobSpy source instance.

* **Return type:**
  [`JobSpySource`](#hired.search.sources.jobspy.JobSpySource)
