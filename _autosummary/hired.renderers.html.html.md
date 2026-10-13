# hired.renderers.html

HTML renderer implementation using Jinja2 templates.

### Functions

| [`html_to_pdf`](#hired.renderers.html.html_to_pdf)(html, css)   | Convert HTML to PDF using WeasyPrint if available, else minimal builder.   |
|---------------------------------------------------------------------------|----------------------------------------------------------------------------|

### Classes

| [`ThemeRegistry`](#hired.renderers.html.ThemeRegistry)(\*[, themes_path])   | Registry for available themes.   |
|-------------------------------------------------------------------------------------|----------------------------------|
| [`HTMLRenderer`](#hired.renderers.html.HTMLRenderer)(\*[, theme_registry]) | Renders resume to HTML or PDF.   |

### *class* hired.renderers.html.HTMLRenderer(, theme_registry=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Renders resume to HTML or PDF.

Process:

> * Build a sanitized context (omit empty sections).
> * Render via Jinja2 template.
> * If PDF: use WeasyPrint if available, else fallback minimal PDF builder.

### *class* hired.renderers.html.ThemeRegistry(, themes_path=None)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

Registry for available themes.

Each theme is a mapping with keys:
: name: str
  template: str (filename relative to themes directory)
  css: str (raw CSS text, optional)

### hired.renderers.html.html_to_pdf(html, css)

Convert HTML to PDF using WeasyPrint if available, else minimal builder.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)
