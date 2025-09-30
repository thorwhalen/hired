from hired.base import RenderingConfig, ResumeSchemaExtended
from hired.resumejson_pydantic_models import Basics, WorkItem

# For backward compatibility
ResumeContent = ResumeSchemaExtended
from hired.render import HTMLRenderer


def test_empty_sections_omitted():
    """Test that empty sections are omitted from rendering."""
    from hired.renderers.html import HTMLRenderer

    content = ResumeSchemaExtended(
        basics=Basics(name='Test User', email='test@example.com'),
        work=None,  # empty section
        education=None,  # empty section
    )
    renderer = HTMLRenderer()
    config = RenderingConfig(format='html', theme='default')
    html = renderer.render(content, config)

    # Basics should be present
    assert b'Test User' in html
    assert b'test@example.com' in html


def test_minimal_theme():
    content = ResumeSchemaExtended(
        basics=Basics(name="Bob", email="bob@example.com"),
        work=[WorkItem(name="Org", position="Dev")],
    )
    renderer = HTMLRenderer()
    html = renderer.render(content, RenderingConfig(format='html', theme='minimal'))
    assert b'Experience' in html
    assert b'Bob' in html


def test_minimal_theme():
    """Test rendering with minimal theme."""
    from hired.renderers.html import HTMLRenderer

    content = ResumeSchema(
        basics=Basics(name='Minimal User', email='minimal@example.com'),
        work=[
            WorkItem(
                name='Company A',
                position='Engineer',
                startDate='2022-01-01',
                endDate='2023-12-31',
            )
        ],
    )
    renderer = HTMLRenderer()
    config = RenderingConfig(format='html', theme='minimal')
    html = renderer.render(content, config)

    # Check basic content is present
    assert b'Minimal User' in html
    assert b'Company A' in html
    assert b'Engineer' in html


def test_minimal_theme():
    content = ResumeSchemaExtended(
        basics=Basics(name="Bob", email="bob@example.com"),
        work=[WorkItem(name="Org", position="Dev")],
    )
    renderer = HTMLRenderer()
    html = renderer.render(content, RenderingConfig(format='html', theme='minimal'))
    assert b'Experience' in html
    assert b'Bob' in html
