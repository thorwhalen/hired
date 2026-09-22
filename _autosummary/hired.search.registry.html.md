# hired.search.registry

Registry system for managing job search sources.

### Functions

| [`get_registry`](#hired.search.registry.get_registry)()                          | Get the global source registry.             |
|------------------------------------------------------------------------------------------|---------------------------------------------|
| [`register_source`](#hired.search.registry.register_source)(source[, source_class]) | Register a source with the global registry. |

### Classes

| [`SourceRegistry`](#hired.search.registry.SourceRegistry)()   | Registry for job search sources.   |
|---------------------------------------------------------------------|------------------------------------|

### *class* hired.search.registry.SourceRegistry

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

### hired.search.registry.get_registry()

Get the global source registry.

* **Return type:**
  [`SourceRegistry`](#hired.search.registry.SourceRegistry)

### hired.search.registry.register_source(source, source_class=None)

Register a source with the global registry.

* **Parameters:**
  * **source** ([`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)) – Instance of a JobSearchSource implementation
  * **source_class** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Type`](https://docs.python.org/3/library/typing.html#typing.Type)[[`JobSearchSource`](hired.search.base.html.md#hired.search.base.JobSearchSource)]]) – Optional class of the source for reference
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
