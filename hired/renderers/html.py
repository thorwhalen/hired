"""HTML renderer implementation using Jinja2 templates."""

from typing import Mapping, Any, Iterable
import re, os, importlib
import html as html_mod
from collections.abc import Mapping as ABCMapping
from hired.base import Renderer, RenderingConfig

try:  # Optional dependency
    import weasyprint  # type: ignore
except Exception:  # pragma: no cover - absence path
    weasyprint = None

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except (
    ImportError
) as e:  # pragma: no cover - jinja2 should be present or this errors clearly
    raise RuntimeError("Jinja2 is required for rendering; please install jinja2") from e


# Minimal theme registry
class ThemeRegistry(ABCMapping):
    """Registry for available themes.

    Each theme is a mapping with keys:
        name: str
        template: str (filename relative to themes directory)
        css: str (raw CSS text, optional)
    """

    def __init__(self, *, themes_path: str | None = None):
        if themes_path is None:
            # Derive path relative to hired package
            import hired

            themes_path = os.path.join(os.path.dirname(hired.__file__), 'themes')
        self._themes_path = themes_path
        self._themes = {
            'default': {'template': 'default.html', 'css': ''},
            'minimal': {'template': 'minimal.html', 'css': ''},
        }

    def __getitem__(self, theme_name: str) -> dict:
        return self._themes[theme_name]

    def __iter__(self):
        return iter(self._themes)

    def __len__(self) -> int:
        return len(self._themes)

    @property
    def themes_path(self) -> str:
        return self._themes_path


class HTMLRenderer:
    """Renders resume to HTML or PDF.

    Process:
        * Build a sanitized context (omit empty sections).
        * Render via Jinja2 template.
        * If PDF: use WeasyPrint if available, else fallback minimal PDF builder.
    """

    def __init__(self, *, theme_registry: ThemeRegistry | None = None):
        self._themes = theme_registry or ThemeRegistry()
        self._env = Environment(
            loader=FileSystemLoader(self._themes.themes_path),
            autoescape=select_autoescape(['html', 'xml']),
        )

    # ------------------ Public API ------------------ #
    def render(
        self, content: Any, config: RenderingConfig
    ) -> bytes:  # content is ResumeSchema
        theme = self._themes[config.theme]
        html = self._render_to_html(content, theme)
        if config.format == 'pdf':
            return self._html_to_pdf(html, theme.get('css', ''))
        return html.encode('utf-8')

    # ------------------ HTML rendering ------------------ #
    def _render_to_html(
        self, content: Any, theme: dict
    ) -> str:  # content is ResumeSchema
        ctx = self._build_context(content)
        template = self._env.get_template(theme['template'])
        return template.render(**ctx)

    def _build_context(self, content: Any) -> dict:  # content is ResumeSchema
        # Convert pydantic model to dict, handling the new schema structure
        content_dict = (
            content.model_dump(exclude_none=True)
            if hasattr(content, 'model_dump')
            else content
        )

        basics = content_dict.get('basics', {})
        work = content_dict.get('work', [])
        education = content_dict.get('education', [])

        # Filter out empty work and education entries
        work = [w for w in work if not _is_empty_section(w)]
        education = [e for e in education if not _is_empty_section(e)]

        # Handle extra sections (anything not in the core schema)
        core_sections = {
            'basics',
            'work',
            'education',
            'volunteer',
            'awards',
            'certificates',
            'publications',
            'skills',
            'languages',
            'interests',
            'references',
            'projects',
            'meta',
            'field_schema',
        }
        extra_sections = list(
            _iter_extra_sections(
                {k: v for k, v in content_dict.items() if k not in core_sections}
            )
        )

        return {
            'basics': basics,
            'work': work,
            'education': education,
            'extra_sections': extra_sections,
        }

    # ------------------ PDF conversion ------------------ #
    def _html_to_pdf(self, html: str, css: str) -> bytes:
        if weasyprint is not None:
            try:  # pragma: no cover (WeasyPrint path typically optional in tests)
                return weasyprint.HTML(string=html).write_pdf(
                    stylesheets=[weasyprint.CSS(string=css)] if css else None
                )
            except Exception:
                # Fallback to minimal builder if WeasyPrint fails for some reason
                pass
        text = _extract_text_from_html(html)
        return _build_minimal_pdf(text)


# ---------------------------- helpers ---------------------------- #


def _is_empty_section(value: Any) -> bool:
    """Heuristic to determine if a section value is 'empty'."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    if isinstance(value, (list, tuple, set)):
        return all(_is_empty_section(v) for v in value)
    if isinstance(value, dict):
        return all(_is_empty_section(v) for v in value.values())
    return False


def _iter_extra_sections(extra: Mapping[str, Any]) -> Iterable[dict]:
    for name, value in extra.items():
        if _is_empty_section(value):
            continue
        section_id = name
        title = name.replace('_', ' ').title()
        # Normalize to HTML snippet
        if isinstance(value, str):
            html_fragment = f"<p>{value}</p>"
        elif isinstance(value, list):
            items = [v for v in value if not _is_empty_section(v)]
            if not items:
                continue
            html_fragment = '<ul>' + ''.join(f'<li>{v}</li>' for v in items) + '</ul>'
        elif isinstance(value, dict):
            kv_pairs = {k: v for k, v in value.items() if not _is_empty_section(v)}
            if not kv_pairs:
                continue
            html_fragment = (
                '<dl>'
                + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in kv_pairs.items())
                + '</dl>'
            )
        else:
            html_fragment = f"<pre>{html_mod.escape(repr(value))}</pre>"
        yield {'id': section_id, 'title': title, 'html': html_fragment}


def _extract_text_from_html(html: str) -> str:
    # Remove tags
    txt = re.sub(r'<[^>]+>', ' ', html)
    # Unescape entities
    txt = html_mod.unescape(txt)
    # Collapse whitespace
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt[:4000]  # keep it bounded


def _build_minimal_pdf(text: str) -> bytes:
    """Build a minimal, valid single-page PDF containing the given text.

    Not layout-aware; wraps at ~90 chars manually.
    """
    # Escape parentheses and backslashes
    safe = text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')
    # Wrap lines
    width = 90
    lines = [safe[i : i + width] for i in range(0, len(safe), width)] or ['']
    # PDF content stream commands: start text, move for each line
    y = 720
    line_gap = 14
    parts = ["BT /F1 12 Tf 72 {} Td ({} ) Tj".format(y, lines[0])]  # first line
    for line in lines[1:]:
        y -= line_gap
        if y < 50:  # simple overflow guard
            parts.append("(… truncated …) Tj")
            break
        parts.append("T* ({} ) Tj".format(line))
    parts.append("ET")
    stream_text = ' '.join(parts)
    stream_bytes = stream_text.encode('utf-8')

    objects = []  # (number, bytes)

    def obj(n: int, body: str | bytes) -> bytes:
        if isinstance(body, str):
            body = body.encode('utf-8')
        return f"{n} 0 obj\n".encode() + body + b"\nendobj\n"

    # 1 Catalog, 2 Pages, 3 Page, 4 Font, 5 Contents
    objects.append(obj(1, "<< /Type /Catalog /Pages 2 0 R >>"))
    objects.append(obj(2, "<< /Type /Pages /Count 1 /Kids [3 0 R] >>"))
    objects.append(
        obj(
            3,
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        )
    )
    objects.append(obj(4, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))
    objects.append(
        obj(
            5,
            f"<< /Length {len(stream_bytes)} >>\nstream\n{stream_text}\nendstream",
        )
    )

    pdf = b"%PDF-1.4\n"
    offsets = [0]  # object 0
    for ob in objects:
        offsets.append(len(pdf))
        pdf += ob
    # xref
    xref_offset = len(pdf)
    count = len(objects) + 1
    xref_lines = ["xref", f"0 {count}", "0000000000 65535 f "]
    for off in offsets[1:]:
        xref_lines.append(f"{off:010d} 00000 n ")
    pdf += ("\n".join(xref_lines) + "\n").encode()
    pdf += "trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF".format(
        size=count, start=xref_offset
    ).encode()
    return pdf
