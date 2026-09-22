# hired.renderers.rendercv

RenderCV renderer implementation using the RenderCV backend.

### Classes

| [`RenderCVRenderer`](#hired.renderers.rendercv.RenderCVRenderer)([strict_validation])   | Renderer that uses RenderCV for high-quality PDF generation.   |
|------------------------------------------------------------------------------------------|----------------------------------------------------------------|

### *class* hired.renderers.rendercv.RenderCVRenderer(strict_validation=False)

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
