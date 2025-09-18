from hired.base import ResumeContent, ResumeBasics, ResumeWork, RenderingConfig
from hired.render import HTMLRenderer


def test_empty_sections_omitted():
    content = ResumeContent(
        basics=ResumeBasics(name="Alice", email="alice@example.com"),
        work=[ResumeWork(company="Acme", position="Engineer")],
        education=[],
        extra_sections={
            'awards': [],  # should be omitted
            'certificates': {},  # omitted
            'volunteer': None,  # omitted
            'references': [""],  # omitted
            'summary': "Seasoned engineer",  # kept
        },
    )
    renderer = HTMLRenderer()
    html = renderer.render(content, RenderingConfig(format='html')).decode('utf-8')
    assert '<h2>Awards</h2>' not in html
    assert '<h2>Certificates</h2>' not in html
    assert '<h2>Volunteer</h2>' not in html
    assert '<h2>References</h2>' not in html
    assert '<h2>Summary</h2>' in html


def test_minimal_theme():
    content = ResumeContent(
        basics=ResumeBasics(name="Bob", email="bob@example.com"),
        work=[ResumeWork(company="Org", position="Dev")],
        education=[],
        extra_sections={},
    )
    renderer = HTMLRenderer()
    html = renderer.render(content, RenderingConfig(format='html', theme='minimal'))
    assert b'Experience' in html
    assert b'Bob' in html
