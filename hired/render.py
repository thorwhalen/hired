"""Rendering pipeline and theme management.

Current features:
* Pluggable renderer system supporting multiple backends.
* HTML and PDF rendering via HTMLRenderer
* Optional RenderCV integration for high-quality PDF generation
"""

from hired.base import (
    Renderer,
    RenderingConfig,
    register_renderer,
    get_renderer_registry,
)
from hired.renderers.html import HTMLRenderer

# Optional RenderCV renderer
try:
    from hired.renderers.rendercv import RenderCVRenderer

    RENDERCV_AVAILABLE = True
except ImportError:
    RENDERCV_AVAILABLE = False


# Initialize and register default renderers
def _initialize_default_renderers():
    """Register built-in renderers with the global registry."""
    registry = get_renderer_registry()

    # Register HTML renderer for html and pdf formats
    registry.register('html', HTMLRenderer)
    registry.register('pdf', HTMLRenderer)

    # Register RenderCV renderer if available
    if RENDERCV_AVAILABLE:
        registry.register('pdf-rendercv', RenderCVRenderer)
        registry.register('rendercv', RenderCVRenderer)


def _get_renderer_for_format(format: str) -> Renderer:
    """Get renderer for specified format from the registry."""
    registry = get_renderer_registry()

    # Initialize default renderers if registry is empty
    if not registry._renderers:
        _initialize_default_renderers()

    try:
        return registry.get_renderer(format)
    except KeyError:
        # Fallback for backwards compatibility
        if format in ('pdf', 'html'):
            return HTMLRenderer()
        raise NotImplementedError(f'Format {format} not supported')


# Initialize renderers when module is imported
_initialize_default_renderers()
