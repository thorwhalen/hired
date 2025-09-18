# hired

Streamline the job application process for job seekers

## Overview

The `hired` package is a Python library designed to simplify the process of creating professional resumes tailored to specific job applications. It leverages AI-driven content generation, schema validation, and customizable rendering pipelines to produce high-quality resumes in various formats.

## Features

### 1. Content Generation
- **AI-Driven Content**: Automatically generate resume content by analyzing candidate profiles and job descriptions.
- **Flexible Sources**: Supports JSON, YAML, and Python dictionaries as input sources.

### 2. Validation
- **JSON Resume Schema**: Ensures compliance with the [JSON Resume schema](https://jsonresume.org/schema/).
- **Strict and Permissive Modes**: Validate content strictly or allow flexibility for missing fields.
- **Pruning**: Automatically removes `None` values to ensure schema compliance.

### 3. Rendering
- **HTML and PDF**: Render resumes as HTML or PDF.
- **Template-Based Themes**: Use Jinja2 templates for customizable themes (e.g., `default`, `minimal`).
- **Optional WeasyPrint Integration**: Generate professional PDFs with WeasyPrint if installed.
- **Fallback PDF Builder**: Minimal PDF generation without external dependencies.
- **Empty Section Omission**: Automatically skips rendering empty sections.

## Installation

Install the package using pip:

```bash
pip install hired
```

To enable PDF generation with WeasyPrint, install the optional dependency:

```bash
pip install weasyprint
```

## Usage

### Generating Resume Content

```python
from hired.tools import mk_content_for_resume

candidate_info = {
    "basics": {"name": "Alice", "email": "alice@example.com"},
    "work": [{"company": "Acme Corp", "position": "Engineer"}]
}
job_info = {"title": "Software Engineer", "skills": ["Python", "Django"]}

content = mk_content_for_resume(candidate_info, job_info)
```

### Rendering a Resume

```python
from hired.tools import mk_resume

# Render to HTML
html = mk_resume(content, {"format": "html"})

# Render to PDF
pdf = mk_resume(content, {"format": "pdf"}, output_path="resume.pdf")
```

### Validating Resume Content

```python
from hired.validators import validate_resume_content

is_valid = validate_resume_content(content.model_dump(), strict=True)
print("Valid Resume" if is_valid else "Invalid Resume")
```

## Themes

Themes are stored in the `hired/themes` directory. You can customize or add new themes by modifying the Jinja2 templates.

### Default Theme
- A structured layout with sections for work, education, and extra content.

### Minimal Theme
- A concise layout with essential details.

## Tests

Run the test suite to ensure everything is working:

```bash
pytest
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License.

