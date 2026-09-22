# hired.search.facade

Main facade for job search functionality.

### Classes

| [`JobSources`](#hired.search.facade.JobSources)([registry])   | Main facade for accessing job search sources.   |
|---------------------------------------------------------------------------|-------------------------------------------------|

### *class* hired.search.facade.JobSources(registry=None)

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
