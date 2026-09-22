# hired.search.sources.adzuna

Adzuna source adapter.

Accesses the Adzuna Jobs API ([https://developer.adzuna.com/](https://developer.adzuna.com/)).
Requires a free API key (app_id and app_key) from the Adzuna Developer Portal.

### Functions

| [`get_adzuna_source`](#hired.search.sources.adzuna.get_adzuna_source)()   | Get the default Adzuna source instance.   |
|------------------------------------------------------------------------|-------------------------------------------|

### Classes

| [`AdzunaSource`](#hired.search.sources.adzuna.AdzunaSource)([app_id, app_key, country])   | Adzuna API source implementation.   |
|---------------------------------------------------------------------------------------------|-------------------------------------|

### *class* hired.search.sources.adzuna.AdzunaSource(app_id=None, app_key=None, country='us')

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

### hired.search.sources.adzuna.get_adzuna_source()

Get the default Adzuna source instance.

* **Return type:**
  [`AdzunaSource`](#hired.search.sources.adzuna.AdzunaSource)
