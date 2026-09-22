# hired.search.sources.usajobs

USAJobs source adapter.

Accesses the official US Government jobs API ([https://developer.usajobs.gov/](https://developer.usajobs.gov/)).
Requires a free API key obtained from the USAJobs Developer Portal.

### Functions

| [`get_usajobs_source`](#hired.search.sources.usajobs.get_usajobs_source)()   | Get the default USAJobs source instance.   |
|-------------------------------------------------------------------------|--------------------------------------------|

### Classes

| [`USAJobsSource`](#hired.search.sources.usajobs.USAJobsSource)([api_key, email])   | USAJobs API source implementation.   |
|------------------------------------------------------------------------------------|--------------------------------------|

### *class* hired.search.sources.usajobs.USAJobsSource(api_key=None, email=None)

Bases: [`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)

USAJobs API source implementation.

Searches US Government job postings via the official USAJobs API.
Requires a free API key from [https://developer.usajobs.gov/](https://developer.usajobs.gov/).

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

Search for jobs using USAJobs API.

* **Parameters:**
  **criteria** ([`SearchCriteria`](hired.search.base.html.md#hired.search.base.SearchCriteria)) – Search criteria
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects

### hired.search.sources.usajobs.get_usajobs_source()

Get the default USAJobs source instance.

* **Return type:**
  [`USAJobsSource`](#hired.search.sources.usajobs.USAJobsSource)
