# hired.base

Core data models and protocols for the hired package.

Define:

- RenderingConfig: Configuration for rendering pipeline
- ContentSource: Protocol for data sources (candidate/job info)
- AIAgent: Protocol for content generation agents
- Renderer: Protocol for resume renderers
- ResumeSchemaExtended: Extended version of ResumeSchema that allows extra fields

### Functions

| [`get_renderer_registry`](#hired.base.get_renderer_registry)()        | Get the global renderer registry.           |
|---------------------------------------------------------------------------------|---------------------------------------------|
| [`register_renderer`](#hired.base.register_renderer)(format_name) | Decorator for registering renderer classes. |

### Classes

| [`AIAgent`](#hired.base.AIAgent)(\*args, \*\*kwargs)                       | Protocol for AI agents that generate resume content.                           |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`ContentSource`](#hired.base.ContentSource)(\*args, \*\*kwargs)                 | Protocol for sources that provide candidate or job information.                |
| [`Renderer`](#hired.base.Renderer)(\*args, \*\*kwargs)                      | Protocol for resume renderers.                                                 |
| [`RendererRegistry`](#hired.base.RendererRegistry)()                                | Registry for managing multiple renderer implementations.                       |
| [`RenderingConfig`](#hired.base.RenderingConfig)([format, theme, custom_css, ...]) | Configuration for resume rendering.                                            |
| [`ResumeSchemaExtended`](#hired.base.ResumeSchemaExtended)(\*\*data)                    | Extended version of ResumeSchema that allows extra fields for custom sections. |

### *class* hired.base.AIAgent(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Protocol for AI agents that generate resume content.

### *class* hired.base.ContentSource(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Protocol for sources that provide candidate or job information.

### *class* hired.base.Renderer(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Protocol for resume renderers.

### *class* hired.base.RendererRegistry

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Registry for managing multiple renderer implementations.

#### get_renderer(format_name)

Get a renderer instance for the specified format.

* **Return type:**
  [`Renderer`](#hired.base.Renderer)

#### is_registered(format_name)

Check if a format is registered.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### list_formats()

List all registered format names.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### register(format_name, renderer_class)

Register a renderer class for a specific format.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.base.RenderingConfig(format='pdf', theme='default', custom_css=None, custom_template=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Configuration for resume rendering.

### *class* hired.base.ResumeSchemaExtended(\*\*data)

Bases: [`ResumeSchema`](hired.resumejson_pydantic_models.html.md#hired.resumejson_pydantic_models.ResumeSchema)

Extended version of ResumeSchema that allows extra fields for custom sections.

This class inherits all the validation and structure from ResumeSchema
but allows additional fields to be stored for custom sections.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### hired.base.get_renderer_registry()

Get the global renderer registry.

* **Return type:**
  [`RendererRegistry`](#hired.base.RendererRegistry)

### hired.base.register_renderer(format_name)

Decorator for registering renderer classes.
