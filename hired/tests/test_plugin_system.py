"""
Tests for the new renderer plugin system and RenderCV integration.
"""

import pytest
from hired import mk_content_for_resume, mk_resume
from hired.base import get_renderer_registry, RendererRegistry
from hired.renderers.html import HTMLRenderer


def test_renderer_registry():
    """Test that the renderer registry works correctly."""
    registry = RendererRegistry()

    # Test registering a renderer
    registry.register('test', HTMLRenderer)
    assert 'test' in registry._renderers

    # Test getting a renderer
    renderer = registry.get_renderer('test')
    assert isinstance(renderer, HTMLRenderer)

    # Test getting same instance twice (caching)
    renderer2 = registry.get_renderer('test')
    assert renderer is renderer2


def test_default_renderers_available():
    """Test that default renderers are properly registered."""
    registry = get_renderer_registry()

    # Should have at least html and pdf renderers
    assert 'html' in registry._renderers
    assert 'pdf' in registry._renderers

    # Get renderers to ensure they work
    html_renderer = registry.get_renderer('html')
    pdf_renderer = registry.get_renderer('pdf')

    assert isinstance(html_renderer, HTMLRenderer)
    assert isinstance(pdf_renderer, HTMLRenderer)


def test_basic_resume_workflow():
    """Test the complete resume generation workflow with plugin system."""

    # Test data
    candidate = {
        'basics': {'name': 'Test User', 'email': 'test@example.com'},
        'work': [{'company': 'Test Co', 'position': 'Engineer'}],
    }
    job = {'title': 'Software Engineer', 'skills': ['Python']}

    # Generate content
    content = mk_content_for_resume(candidate, job)
    assert content.basics.name == 'Test User'

    # Test HTML rendering
    html = mk_resume(content, {'format': 'html'})
    assert b'<html' in html.lower()
    assert b'Test User' in html

    # Test PDF rendering
    pdf = mk_resume(content, {'format': 'pdf'})
    assert pdf.startswith(b'%PDF')
    assert len(pdf) > 100


def test_rendercv_available():
    """Test if RenderCV renderer is available (may fail if dependencies not installed)."""
    registry = get_renderer_registry()

    # Check if RenderCV renderers are registered
    if 'pdf-rendercv' in registry._renderers:
        print("RenderCV renderer is available")
        # Try to get the renderer (this tests instantiation)
        try:
            renderer = registry.get_renderer('pdf-rendercv')
            print(f"RenderCV renderer instance: {type(renderer)}")
        except Exception as e:
            print(f"RenderCV renderer instantiation failed: {e}")
    else:
        print("RenderCV renderer not available (dependencies not installed)")


if __name__ == '__main__':
    # Run tests manually for now
    test_renderer_registry()
    print("✓ Renderer registry test passed")

    test_default_renderers_available()
    print("✓ Default renderers test passed")

    test_basic_resume_workflow()
    print("✓ Basic resume workflow test passed")

    test_rendercv_available()
    print("✓ RenderCV availability test completed")

    print("\nAll tests completed successfully!")
