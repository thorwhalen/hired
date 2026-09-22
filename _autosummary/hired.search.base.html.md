# hired.search.base

Base classes and interfaces for job search functionality.

### Classes

| [`CompensationInfo`](#hired.search.base.CompensationInfo)([min_amount, max_amount, ...])   | Compensation information for a job.              |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------|
| [`JobResult`](#hired.search.base.JobResult)(title, source[, company, ...])          | Standardized job result across all sources.      |
| [`JobSearchSource`](#hired.search.base.JobSearchSource)()                                 | Abstract base class for job search sources.      |
| [`JobType`](#hired.search.base.JobType)(\*values)                                 | Standardized job types across all sources.       |
| [`LocationInfo`](#hired.search.base.LocationInfo)([city, state, country, ...])         | Location information for a job.                  |
| [`SearchCriteria`](#hired.search.base.SearchCriteria)(query[, location, country, ...])   | Standardized search criteria across all sources. |

### Exceptions

| [`SourceConfigError`](#hired.search.base.SourceConfigError)   | Raised when a source is not properly configured.   |
|----------------------------------------------------------------------|----------------------------------------------------|

### *class* hired.search.base.CompensationInfo(min_amount=None, max_amount=None, currency=None, interval=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Compensation information for a job.

### *class* hired.search.base.JobResult(title, source, company=None, company_url=None, job_url=None, location=None, is_remote=None, description=None, job_type=None, compensation=None, date_posted=None, date_updated=None, application_deadline=None, skills=<factory>, benefits=<factory>, emails=<factory>, raw_data=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Standardized job result across all sources.

This provides a unified interface regardless of which source
the job was retrieved from.

#### to_dict()

Convert JobResult to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.search.base.JobSearchSource

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
  **criteria** ([`SearchCriteria`](#hired.search.base.SearchCriteria)) – SearchCriteria object with search parameters
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`JobResult`](#hired.search.base.JobResult)]
* **Returns:**
  List of JobResult objects
* **Raises:**
  * [**SourceConfigError**](#hired.search.base.SourceConfigError) – If the source is not properly configured
  * [**Exception**](https://docs.python.org/3/builtins/exceptions.html#Exception) – For other errors during search

#### validate_configured()

Validate that the source is configured, raise error if not.

* **Raises:**
  [**SourceConfigError**](#hired.search.base.SourceConfigError) – If the source is not properly configured
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.search.base.JobType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Standardized job types across all sources.

### *class* hired.search.base.LocationInfo(city=None, state=None, country=None, postal_code=None, raw=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Location information for a job.

### *class* hired.search.base.SearchCriteria(query, location=None, country=None, city=None, state=None, postal_code=None, distance_miles=None, job_type=None, is_remote=None, posted_within_days=None, results_wanted=20, offset=0, min_salary=None, max_salary=None, keywords=<factory>, exclude_keywords=<factory>, source_params=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Standardized search criteria across all sources.

Different sources may not support all criteria, but this provides
a consistent interface for users.

### *exception* hired.search.base.SourceConfigError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Raised when a source is not properly configured.
