# hired.renderers

Renderer implementations package.
Contains various renderer backends for different output formats.

### Classes

| [`HTMLRenderer`](#hired.renderers.HTMLRenderer)(\*[, theme_registry])    | Renders resume to HTML or PDF.                               |
|----------------------------------------------------------------------------------------|--------------------------------------------------------------|
| [`RenderCVRenderer`](#hired.renderers.RenderCVRenderer)([strict_validation]) | Renderer that uses RenderCV for high-quality PDF generation. |

### *class* hired.renderers.HTMLRenderer(, theme_registry=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Renders resume to HTML or PDF.

Process:

> * Build a sanitized context (omit empty sections).
> * Render via Jinja2 template.
> * If PDF: use WeasyPrint if available, else fallback minimal PDF builder.

### *class* hired.renderers.RenderCVRenderer(strict_validation=False)

Bases: [`Renderer`](hired.base.html.md#hired.base.Renderer)

Renderer that uses RenderCV for high-quality PDF generation.

This renderer:

1. Converts JSON Resume format to RenderCV YAML format
2. Uses RenderCV to generate PDF with LaTeX/Typst backend
3. Returns the rendered PDF bytes

Features robust data handling:

- Fills in missing required fields with sensible defaults
- Issues warnings about missing or incomplete data
- Gracefully handles schema validation issues

#### render(content, config)

Render resume content using RenderCV backend.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

### Modules

| [`html`](hired.renderers.html.html.md#module-hired.renderers.html)         | HTML renderer implementation using Jinja2 templates.         |
|-------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| [`rendercv`](hired.renderers.rendercv.html.md#module-hired.renderers.rendercv) | RenderCV renderer implementation using the RenderCV backend. |
