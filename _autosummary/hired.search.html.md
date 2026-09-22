# hired.search

Job search functionality for the hired package.

This module provides a unified interface for searching jobs across
multiple sources (Indeed, LinkedIn, USAJobs, Adzuna, etc.).

Example usage:

```pycon
>>> from hired.search import JobSources, SearchCriteria
>>>
>>> # Create job sources facade
>>> sources = JobSources()
>>>
>>> # List available sources
>>> print(sources.list_available())
>>>
>>> # Search using a specific source
>>> criteria = SearchCriteria(
...     query="python developer",
...     location="San Francisco, CA",
...     results_wanted=20
... )
>>> results = sources.jobspy.search(criteria)
>>>
>>> # Or search across all sources
>>> all_results = sources.search_all(criteria)
```

### Functions

| [`get_registry`](#hired.search.get_registry)()                          | Get the global source registry.             |
|------------------------------------------------------------------------------------------|---------------------------------------------|
| [`register_source`](#hired.search.register_source)(source[, source_class]) | Register a source with the global registry. |

### Classes

| [`JobSources`](#hired.search.JobSources)([registry])                          | Main facade for accessing job search sources.    |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------|
| [`SearchCriteria`](#hired.search.SearchCriteria)(query[, location, country, ...]) | Standardized search criteria across all sources. |
| [`JobResult`](#hired.search.JobResult)(title, source[, company, ...])        | Standardized job result across all sources.      |
| [`JobSearchSource`](#hired.search.JobSearchSource)()                               | Abstract base class for job search sources.      |
| [`JobType`](#hired.search.JobType)(\*values)                               | Standardized job types across all sources.       |
| [`LocationInfo`](#hired.search.LocationInfo)([city, state, country, ...])       | Location information for a job.                  |
| [`CompensationInfo`](#hired.search.CompensationInfo)([min_amount, max_amount, ...]) | Compensation information for a job.              |
| [`SourceRegistry`](#hired.search.SourceRegistry)()                                | Registry for job search sources.                 |
| [`JobSpySource`](#hired.search.JobSpySource)([sites, proxies])                  | JobSpy source implementation.                    |
| [`USAJobsSource`](#hired.search.USAJobsSource)([api_key, email])                 | USAJobs API source implementation.               |
| [`AdzunaSource`](#hired.search.AdzunaSource)([app_id, app_key, country])        | Adzuna API source implementation.                |

### Exceptions

| [`SourceConfigError`](#hired.search.SourceConfigError)   | Raised when a source is not properly configured.   |
|----------------------------------------------------------------------|----------------------------------------------------|

### *class* hired.search.AdzunaSource(app_id=None, app_key=None, country='us')

Bases: [`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)

Adzuna API source implementation.

Searches international job postings via the Adzuna Jobs API.
Requires a free API key from [https://developer.adzuna.com/](https://developer.adzuna.com/).

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

Search for jobs using Adzuna API.

* **Parameters:**
  **criteria** ([`SearchCriteria`](hired.search.base.html.md#hired.search.base.SearchCriteria)) – Search criteria
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects

### *class* hired.search.CompensationInfo(min_amount=None, max_amount=None, currency=None, interval=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Compensation information for a job.

### *class* hired.search.JobResult(title, source, company=None, company_url=None, job_url=None, location=None, is_remote=None, description=None, job_type=None, compensation=None, date_posted=None, date_updated=None, application_deadline=None, skills=<factory>, benefits=<factory>, emails=<factory>, raw_data=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Standardized job result across all sources.

This provides a unified interface regardless of which source
the job was retrieved from.

#### to_dict()

Convert JobResult to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.search.JobSearchSource

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
  * [**SourceConfigError**](#hired.search.SourceConfigError) – If the source is not properly configured
  * [**Exception**](https://docs.python.org/3/builtins/exceptions.html#Exception) – For other errors during search

#### validate_configured()

Validate that the source is configured, raise error if not.

* **Raises:**
  [**SourceConfigError**](#hired.search.SourceConfigError) – If the source is not properly configured
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.search.JobSources(registry=None)

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

### *class* hired.search.JobSpySource(sites=None, proxies=None)

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

### *class* hired.search.JobType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Standardized job types across all sources.

### *class* hired.search.LocationInfo(city=None, state=None, country=None, postal_code=None, raw=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Location information for a job.

### *class* hired.search.SearchCriteria(query, location=None, country=None, city=None, state=None, postal_code=None, distance_miles=None, job_type=None, is_remote=None, posted_within_days=None, results_wanted=20, offset=0, min_salary=None, max_salary=None, keywords=<factory>, exclude_keywords=<factory>, source_params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Standardized search criteria across all sources.

Different sources may not support all criteria, but this provides
a consistent interface for users.

### *exception* hired.search.SourceConfigError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Raised when a source is not properly configured.

### *class* hired.search.SourceRegistry

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Registry for job search sources.

Provides a plugin system where sources can be registered
and retrieved by name.

#### get(name)

Get a source by name.

* **Parameters:**
  **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name of the source
* **Return type:**
  [`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)
* **Returns:**
  JobSearchSource instance
* **Raises:**
  [**KeyError**](https://docs.python.org/3/builtins/exceptions.html#KeyError) – If source not found

#### get_source_info(name)

Get information about a source.

* **Parameters:**
  **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name of the source
* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), `any`]
* **Returns:**
  Dictionary with source information

#### list_available_sources()

List sources that are properly configured and ready to use.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of source names that are configured

#### list_sources()

List all registered source names.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of source names

#### list_unconfigured_sources()

List sources that are registered but not configured.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of source names that need configuration

#### register(source, source_class=None)

Register a job search source.

* **Parameters:**
  * **source** ([`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)) – Instance of a JobSearchSource implementation
  * **source_class** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Type`](https://docs.python.org/3/library/typing.html#typing.Type)[[`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)]]) – Optional class of the source for reference
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### unregister(name)

Unregister a source by name.

* **Parameters:**
  **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name of the source to unregister
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.search.USAJobsSource(api_key=None, email=None)

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

### hired.search.get_registry()

Get the global source registry.

* **Return type:**
  [`SourceRegistry`](hired.search.registry.html.md#hired.search.registry.SourceRegistry)

### hired.search.register_source(source, source_class=None)

Register a source with the global registry.

* **Parameters:**
  * **source** ([`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)) – Instance of a JobSearchSource implementation
  * **source_class** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Type`](https://docs.python.org/3/library/typing.html#typing.Type)[[`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)]]) – Optional class of the source for reference
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Modules

| [`base`](hired.search.base.html.md#module-hired.search.base)         | Base classes and interfaces for job search functionality.   |
|----------------------------------------------------------------------------------------|-------------------------------------------------------------|
| [`facade`](hired.search.facade.html.md#module-hired.search.facade)     | Main facade for job search functionality.                   |
| [`registry`](hired.search.registry.html.md#module-hired.search.registry) | Registry system for managing job search sources.            |
| [`sources`](hired.search.sources.html.md#module-hired.search.sources)   | Job search source implementations.                          |
