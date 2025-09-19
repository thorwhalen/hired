"""
Resume Facade Library

A clean Python facade over third-party resume tools:
- Uses jsonresume-to-rendercv for JSON Resume <-> renderCV conversion
- Uses rendercv API for rendering resumes to various formats

Installation:
    pip install jsonresume-to-rendercv rendercv[full] pydantic

Usage:
    from resume_facade import resumejson_to_rendercv, rendercv_to_resumejson, render_resume_w_rendercv

    # Convert between formats
    rendercv_dict = resumejson_to_rendercv(resumejson_dict)
    resumejson_dict = rendercv_to_resumejson(rendercv_dict)

    # Render resume to various formats
    pdf_bytes = render_resume_w_rendercv(rendercv_dict, 'pdf', theme='classic')
    html_bytes = render_resume_w_rendercv(rendercv_dict, 'html')
"""

import io
import json
import tempfile
import subprocess
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, Literal

try:
    # Try to import the third-party packages
    import rendercv.api
    import rendercv.data

    RENDERCV_AVAILABLE = True
except ImportError:
    RENDERCV_AVAILABLE = False
    rendercv = None

# For the conversion tool, we'll use subprocess since it's primarily a CLI tool
JSONRESUME_TO_RENDERCV_AVAILABLE = True  # We'll check this at runtime


def _check_dependencies():
    """Check if required dependencies are available."""
    missing = []

    if not RENDERCV_AVAILABLE:
        missing.append("rendercv[full] - pip install 'rendercv[full]'")

    # Check if jsonresume-to-rendercv CLI is available
    try:
        # This tool doesn't support --help, so we just check if it runs without args
        result = subprocess.run(
            ['jsonresume_to_rendercv'], capture_output=True, check=False
        )
        # If it runs (even with error code 1 for missing args), it's available
        # FileNotFoundError would be raised if the command doesn't exist
    except FileNotFoundError:
        missing.append("jsonresume-to-rendercv - pip install jsonresume-to-rendercv")

    if missing:
        raise ImportError(f"Missing dependencies: {', '.join(missing)}")


def _normalize_resumejson(resumejson_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize JSON Resume data to ensure all required fields are present.
    
    The jsonresume-to-rendercv tool is strict about required fields, so we'll
    add missing fields with appropriate defaults to make the conversion robust.
    
    Args:
        resumejson_dict: Original resume data
        
    Returns:
        Normalized resume data with all required fields
    """
    import copy
    from collections import defaultdict
    
    # Create a deep copy to avoid modifying the original
    normalized = copy.deepcopy(resumejson_dict)
    
    # Define required fields for each section with their default values
    SECTION_DEFAULTS = {
        'basics': {
            'name': '',
            'label': '',
            'email': '',
            'phone': '',
            'url': '',
            'summary': '',
            'location': {
                'address': '',
                'postalCode': '',
                'city': '',
                'countryCode': '',
                'region': ''
            },
            'profiles': []
        },
        'work': {
            '_item_defaults': {
                'name': '',
                'position': '',
                'url': '',
                'startDate': '2000-01',  # Default to a valid date format
                # 'endDate' intentionally omitted - empty string fails validation
                'summary': '',
                'highlights': [],
                'location': ''
            }
        },
        'volunteer': {
            '_item_defaults': {
                'organization': '',
                'position': '',
                'url': '',
                'startDate': '2000-01',
                # 'endDate' intentionally omitted - empty string fails validation
                'summary': '',
                'highlights': []
            }
        },
        'education': {
            '_item_defaults': {
                'institution': '',
                'url': '',
                'area': '',
                'studyType': '',
                'startDate': '2000-01',  # Required by jsonresume-to-rendercv
                # 'endDate' intentionally omitted - empty string fails validation
                'score': '',
                'courses': []
            }
        },
        'awards': {
            '_item_defaults': {
                'title': '',
                'date': '2000-01',
                'awarder': '',
                'summary': ''
            }
        },
        'certificates': {
            '_item_defaults': {
                'name': '',
                'date': '2000-01',
                'issuer': '',
                'url': ''
            }
        },
        'publications': {
            '_item_defaults': {
                'name': '',
                'publisher': '',
                'releaseDate': '2000-01',  # Required by jsonresume-to-rendercv
                'url': '',
                'summary': ''
            }
        },
        'skills': {
            '_item_defaults': {
                'name': '',
                'level': '',
                'keywords': []
            }
        },
        'languages': {
            '_item_defaults': {
                'language': '',
                'fluency': ''
            }
        },
        'interests': {
            '_item_defaults': {
                'name': '',
                'keywords': []
            }
        },
        'references': {
            '_item_defaults': {
                'name': '',
                'reference': ''
            }
        },
        'projects': {
            '_item_defaults': {
                'name': '',
                'description': '',
                'highlights': [],
                'keywords': [],
                'startDate': '2000-01',
                # 'endDate' intentionally omitted - empty string fails validation
                'url': '',
                'roles': [],
                'entity': '',
                'type': ''
            }
        }
    }
    
    # Normalize top-level sections
    for section_name, defaults in SECTION_DEFAULTS.items():
        if section_name not in normalized:
            if '_item_defaults' in defaults:
                normalized[section_name] = []
            else:
                normalized[section_name] = {}
        
        section_data = normalized[section_name]
        
        if '_item_defaults' in defaults:
            # This is an array section (work, education, etc.)
            item_defaults = defaults['_item_defaults']
            if isinstance(section_data, list):
                for item in section_data:
                    if isinstance(item, dict):
                        # First, remove empty date fields that would fail validation
                        date_fields = ['endDate', 'date']
                        for date_field in date_fields:
                            if date_field in item and item[date_field] == '':
                                del item[date_field]
                        
                        # Then add missing required fields
                        for key, default_value in item_defaults.items():
                            if key not in item:
                                item[key] = default_value
        else:
            # This is an object section (basics)
            if isinstance(section_data, dict):
                for key, default_value in defaults.items():
                    if key not in section_data:
                        section_data[key] = default_value
    
    return normalized


def resumejson_to_rendercv(resumejson_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert JSON Resume format to renderCV format using jsonresume-to-rendercv.

    Args:
        resumejson_dict: Resume data in JSON Resume format

    Returns:
        Resume data in renderCV format

    Raises:
        ImportError: If required dependencies are not available
        ValueError: If conversion fails
    """
    _check_dependencies()
    
    # Normalize the input data to ensure all required fields are present
    normalized_data = _normalize_resumejson(resumejson_dict)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write JSON Resume to temp file
        json_file = temp_path / "input.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, indent=2, ensure_ascii=False)

        # Convert using jsonresume-to-rendercv CLI
        yaml_file = temp_path / "output.yaml"
        result = subprocess.run(
            ['jsonresume_to_rendercv', str(json_file), str(yaml_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise ValueError(f"Conversion failed: {result.stderr}")

        # Read the converted YAML
        with open(yaml_file, 'r', encoding='utf-8') as f:
            rendercv_dict = yaml.safe_load(f)

        return rendercv_dict


def rendercv_to_resumejson(rendercv_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert renderCV format to JSON Resume format.

    Note: This is a reverse conversion. Since jsonresume-to-rendercv only goes
    one direction, this implements the reverse mapping.

    Args:
        rendercv_dict: Resume data in renderCV format

    Returns:
        Resume data in JSON Resume format
    """
    # Extract CV data
    cv_data = rendercv_dict.get('cv', {})

    # Build JSON Resume structure
    resumejson = {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json"
    }

    # Convert basics
    basics = {}
    if cv_data.get('name'):
        basics['name'] = cv_data['name']
    if cv_data.get('label'):
        basics['label'] = cv_data['label']
    if cv_data.get('email'):
        basics['email'] = cv_data['email']
    if cv_data.get('phone'):
        basics['phone'] = cv_data['phone']
    if cv_data.get('website'):
        basics['url'] = cv_data['website']
    if cv_data.get('summary'):
        basics['summary'] = cv_data['summary']

    # Convert location
    if cv_data.get('location'):
        location_str = cv_data['location']
        parts = [part.strip() for part in location_str.split(',')]
        if len(parts) >= 3:
            basics['location'] = {
                'city': parts[0],
                'region': parts[1],
                'countryCode': parts[2],
            }
        elif len(parts) == 2:
            basics['location'] = {'city': parts[0], 'region': parts[1]}
        elif len(parts) == 1:
            basics['location'] = {'city': parts[0]}

    # Convert social networks
    social_networks = cv_data.get('social_networks', [])
    if social_networks:
        basics['profiles'] = []
        for social in social_networks:
            profile = {
                'network': social.get('network', ''),
                'username': social.get('username', ''),
            }
            if social.get('url'):
                profile['url'] = social['url']
            basics['profiles'].append(profile)

    if basics:
        resumejson['basics'] = basics

    # Convert sections
    sections = cv_data.get('sections', {})

    # Convert work experience
    for section_name, entries in sections.items():
        section_lower = section_name.lower()

        if any(
            keyword in section_lower for keyword in ['work', 'experience', 'employment']
        ):
            work_entries = []
            for entry in entries:
                if isinstance(entry, dict):
                    work_entry = {
                        'name': entry.get('company', ''),
                        'position': entry.get('position', ''),
                        'location': entry.get('location', ''),
                        'startDate': entry.get('start_date', ''),
                        'endDate': entry.get('end_date', ''),
                        'summary': entry.get('summary', ''),
                        'highlights': entry.get('highlights', []),
                    }
                    if entry.get('url'):
                        work_entry['url'] = entry['url']
                    # Remove empty values
                    work_entry = {k: v for k, v in work_entry.items() if v}
                    work_entries.append(work_entry)

            if work_entries:
                resumejson['work'] = work_entries

        elif 'education' in section_lower:
            education_entries = []
            for entry in entries:
                if isinstance(entry, dict):
                    edu_entry = {
                        'institution': entry.get('institution', ''),
                        'area': entry.get('area', ''),
                        'studyType': entry.get('degree', ''),
                        'startDate': entry.get('start_date', ''),
                        'endDate': entry.get('end_date', ''),
                    }
                    if entry.get('url'):
                        edu_entry['url'] = entry['url']
                    if entry.get('gpa'):
                        edu_entry['score'] = entry['gpa']
                    # Remove empty values
                    edu_entry = {k: v for k, v in edu_entry.items() if v}
                    education_entries.append(edu_entry)

            if education_entries:
                resumejson['education'] = education_entries

        elif 'skill' in section_lower:
            skills = []
            for entry in entries:
                if isinstance(entry, str):
                    # Parse skill strings like "**Name**: keyword1, keyword2"
                    if '**' in entry and ':' in entry:
                        parts = entry.split(':', 1)
                        name = parts[0].replace('**', '').strip()
                        keywords = [kw.strip() for kw in parts[1].split(',')]
                        skills.append({'name': name, 'keywords': keywords})
                    else:
                        skills.append({'name': entry, 'keywords': []})

            if skills:
                resumejson['skills'] = skills

        elif any(keyword in section_lower for keyword in ['project', 'portfolio']):
            projects = []
            for entry in entries:
                if isinstance(entry, dict):
                    project = {
                        'name': entry.get('name', ''),
                        'description': entry.get('summary', ''),
                        'highlights': entry.get('highlights', []),
                        'startDate': entry.get('start_date', entry.get('date', '')),
                        'endDate': entry.get('end_date', ''),
                    }
                    if entry.get('url'):
                        project['url'] = entry['url']
                    # Remove empty values
                    project = {k: v for k, v in project.items() if v}
                    projects.append(project)

            if projects:
                resumejson['projects'] = projects

        elif 'publication' in section_lower:
            publications = []
            for entry in entries:
                if isinstance(entry, dict):
                    pub = {
                        'name': entry.get('title', ''),
                        'releaseDate': entry.get('date', ''),
                        'summary': entry.get('summary', ''),
                    }
                    if entry.get('journal'):
                        pub['publisher'] = entry['journal']
                    elif entry.get('authors'):
                        if isinstance(entry['authors'], list):
                            pub['publisher'] = ', '.join(entry['authors'])
                        else:
                            pub['publisher'] = entry['authors']
                    if entry.get('url'):
                        pub['url'] = entry['url']
                    # Remove empty values
                    pub = {k: v for k, v in pub.items() if v}
                    publications.append(pub)

            if publications:
                resumejson['publications'] = publications

    return resumejson


def render_resume_w_rendercv(
    rendercv_dict: Dict[str, Any],
    format_spec: Literal['pdf', 'html', 'markdown', 'typst', 'png'] = 'pdf',
    theme: str = 'classic',
    font_size: str = '10pt',
    page_size: str = 'letterpaper',
    **kwargs,
) -> bytes:
    """
    Render resume using renderCV to the specified format.

    Args:
        rendercv_dict: Resume data in renderCV format
        format_spec: Output format ('pdf', 'html', 'markdown', 'typst', 'png')
        theme: renderCV theme ('classic', 'sb2nov', 'engineeringresumes', 'moderncv')
        font_size: Font size (e.g., '10pt', '11pt', '12pt')
        page_size: Page size ('letterpaper', 'a4paper', etc.)
        **kwargs: Additional options passed to renderCV

    Returns:
        Rendered resume as bytes

    Raises:
        ImportError: If renderCV is not available
        ValueError: If rendering fails
        NotImplementedError: If format is not supported
    """
    _check_dependencies()

    # Ensure we have design settings
    if 'design' not in rendercv_dict:
        rendercv_dict = dict(rendercv_dict)  # Don't modify original
        rendercv_dict['design'] = {}

    # Update design settings
    design = rendercv_dict['design']
    design.update(
        {
            'theme': theme,
            'font_size': font_size,
            'page_size': page_size,
            **{
                k: v
                for k, v in kwargs.items()
                if k in ['color', 'disable_page_numbering', 'header_separator']
            },
        }
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_file = None

        try:
            if format_spec == 'pdf':
                output_file = temp_path / "resume.pdf"
                try:
                    rendercv.api.create_a_pdf_from_a_python_dictionary(rendercv_dict, str(output_file))
                except Exception as pdf_error:
                    raise ValueError(f"PDF generation failed: {pdf_error}")

            elif format_spec == 'html':
                output_file = temp_path / "resume.html"
                try:
                    rendercv.api.create_an_html_file_from_a_python_dictionary(rendercv_dict, str(output_file))
                except Exception as html_error:
                    raise ValueError(f"HTML generation failed: {html_error}")

            elif format_spec == 'markdown':
                output_file = temp_path / "resume.md"
                try:
                    rendercv.api.create_a_markdown_file_from_a_python_dictionary(rendercv_dict, str(output_file))
                except Exception as md_error:
                    raise ValueError(f"Markdown generation failed: {md_error}")

            elif format_spec == 'typst':
                output_file = temp_path / "resume.typ"
                try:
                    rendercv.api.create_a_typst_file_from_a_python_dictionary(rendercv_dict, str(output_file))
                except Exception as typst_error:
                    raise ValueError(f"Typst generation failed: {typst_error}")

            elif format_spec == 'png':
                # Generate PDF first, then PNG via renderCV CLI
                yaml_file = temp_path / "resume.yaml"
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(rendercv_dict, f, default_flow_style=False)

                result = subprocess.run(
                    [
                        'rendercv',
                        'render',
                        '--output-folder-name',
                        str(temp_path),
                        '--dont-generate-html',
                        '--dont-generate-markdown',
                        str(yaml_file),
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    raise ValueError(f"PNG generation failed: {result.stderr}")

                # Find the first PNG file
                png_files = list(temp_path.glob("*.png"))
                if png_files:
                    output_file = png_files[0]
                else:
                    raise ValueError("PNG file was not generated")

            else:
                raise NotImplementedError(f"Format '{format_spec}' not supported")

            # Read the generated file
            if output_file and output_file.exists():
                with open(output_file, 'rb') as f:
                    return f.read()
            else:
                raise ValueError(f"Output file was not created: {output_file}")

        except Exception as e:
            if "not found" in str(e).lower():
                raise ImportError(
                    f"renderCV command not found. Install with: pip install 'rendercv[full]'"
                )
            raise


# Convenience functions for common use cases
def render_pdf(rendercv_dict: Dict[str, Any], **kwargs) -> bytes:
    """Render resume as PDF."""
    return render_resume_w_rendercv(rendercv_dict, 'pdf', **kwargs)


def render_html(rendercv_dict: Dict[str, Any], **kwargs) -> bytes:
    """Render resume as HTML."""
    return render_resume_w_rendercv(rendercv_dict, 'html', **kwargs)


def render_markdown(rendercv_dict: Dict[str, Any], **kwargs) -> bytes:
    """Render resume as Markdown."""
    return render_resume_w_rendercv(rendercv_dict, 'markdown', **kwargs)


# Example usage
if __name__ == "__main__":
    # Example JSON Resume data
    sample_resumejson = {
        "basics": {
            "name": "John Doe",
            "label": "Software Engineer",
            "email": "john@example.com",
            "phone": "+1-555-123-4567",
            "url": "https://johndoe.dev",
            "summary": "Experienced software engineer with expertise in Python and web development.",
            "location": {
                "city": "San Francisco",
                "region": "California",
                "countryCode": "US",
            },
            "profiles": [
                {
                    "network": "LinkedIn",
                    "username": "johndoe",
                    "url": "https://linkedin.com/in/johndoe",
                },
                {
                    "network": "GitHub",
                    "username": "johndoe",
                    "url": "https://github.com/johndoe",
                },
            ],
        },
        "work": [
            {
                "name": "Tech Corp",
                "position": "Senior Software Engineer",
                "location": "San Francisco, CA",
                "startDate": "2020-01",
                "summary": "Lead backend development for web applications.",
                "highlights": [
                    "Built scalable APIs serving 1M+ requests/day",
                    "Mentored junior developers",
                    "Improved system performance by 40%",
                ],
            }
        ],
    }

    try:
        print("Converting JSON Resume to renderCV...")
        rendercv_dict = resumejson_to_rendercv(sample_resumejson)
        print("✅ Conversion successful!")

        print("Rendering PDF...")
        pdf_bytes = render_pdf(rendercv_dict)
        print(f"✅ PDF rendered: {len(pdf_bytes)} bytes")

        print("Converting back to JSON Resume...")
        resumejson_restored = rendercv_to_resumejson(rendercv_dict)
        print("✅ Reverse conversion successful!")

        # Save files for inspection
        with open('sample_resume.pdf', 'wb') as f:
            f.write(pdf_bytes)

        with open('rendercv_format.yaml', 'w') as f:
            yaml.dump(rendercv_dict, f, default_flow_style=False)

        with open('restored_jsonresume.json', 'w') as f:
            json.dump(resumejson_restored, f, indent=2)

        print("✅ All operations completed successfully!")
        print(
            "Files saved: sample_resume.pdf, rendercv_format.yaml, restored_jsonresume.json"
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        print(
            "Make sure to install: pip install jsonresume-to-rendercv 'rendercv[full]'"
        )
