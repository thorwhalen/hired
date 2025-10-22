"""RenderCV renderer implementation using the RenderCV backend."""

import tempfile
import os
import warnings
from pathlib import Path
from typing import Any, Dict, List
from hired.base import Renderer, RenderingConfig

try:
    from jsonresume_to_rendercv.converter import convert
    from rendercv import api as rendercv_api

    RENDERCV_AVAILABLE = True
except ImportError:
    RENDERCV_AVAILABLE = False


class RenderCVRenderer(Renderer):
    """Renderer that uses RenderCV for high-quality PDF generation.

    This renderer:
    1. Converts JSON Resume format to RenderCV YAML format
    2. Uses RenderCV to generate PDF with LaTeX/Typst backend
    3. Returns the rendered PDF bytes

    Features robust data handling:
    - Fills in missing required fields with sensible defaults
    - Issues warnings about missing or incomplete data
    - Gracefully handles schema validation issues
    """

    def __init__(self, strict_validation: bool = False):
        """Initialize RenderCV renderer.

        Args:
            strict_validation: If True, fail on missing data. If False (default),
                            fill missing data with defaults and warn.
        """
        if not RENDERCV_AVAILABLE:
            raise ImportError(
                "RenderCV renderer requires 'rendercv' and 'jsonresume-to-rendercv' packages. "
                "Install with: pip install hired[rendercv]"
            )
        self.strict_validation = strict_validation
        self.warnings = []

    def render(
        self, content: Any, config: RenderingConfig
    ) -> bytes:  # content is ResumeSchemaExtended
        """Render resume content using RenderCV backend."""
        self.warnings = []  # Reset warnings for each render

        # Convert ResumeSchemaExtended to JSON Resume dict with robust handling
        json_resume = self._content_to_json_resume_robust(content)

        # Print warnings if any
        if self.warnings:
            print("⚠️  RenderCV Data Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()

        # Convert JSON Resume to RenderCV format
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create temporary JSON file for input
            json_resume_path = temp_path / "resume.json"
            with open(json_resume_path, 'w') as f:
                import json

                json.dump(json_resume, f, indent=2)

            # Create temporary YAML file for RenderCV
            rendercv_yaml_path = temp_path / "resume.yaml"

            try:
                # Convert using jsonresume-to-rendercv
                convert(str(json_resume_path), str(rendercv_yaml_path))
            except Exception as e:
                if self.strict_validation:
                    raise RuntimeError(
                        f"JSON Resume to RenderCV conversion failed: {e}"
                    )
                else:
                    # Try to fix common issues and retry
                    json_resume = self._fix_common_conversion_issues(json_resume)
                    with open(json_resume_path, 'w') as f:
                        import json

                        json.dump(json_resume, f, indent=2)
                    convert(str(json_resume_path), str(rendercv_yaml_path))

            # Generate PDF using RenderCV
            pdf_path = temp_path / "resume.pdf"

            # Use RenderCV API to create PDF
            with open(rendercv_yaml_path) as f:
                yaml_content = f.read()

            try:
                rendercv_api.create_a_pdf_from_a_yaml_string(
                    yaml_file_as_string=yaml_content, output_file_path=pdf_path
                )
            except Exception as e:
                # Debug: show YAML content and detailed error
                print(f"RenderCV PDF generation failed: {e}")
                print(f"YAML content preview:")
                print(
                    yaml_content[:500] + "..."
                    if len(yaml_content) > 500
                    else yaml_content
                )
                raise RuntimeError(f"RenderCV PDF generation failed: {e}")

            # Read and return PDF bytes
            if pdf_path.exists():
                return pdf_path.read_bytes()
            else:
                raise RuntimeError(
                    "RenderCV failed to generate PDF - no output file created"
                )

    def _content_to_json_resume_robust(
        self, content: Any
    ) -> dict:  # content is ResumeSchemaExtended
        """Convert ResumeSchemaExtended to JSON Resume dictionary format with robust error handling."""

        # Convert Pydantic model to dict
        content_dict = (
            content.model_dump(exclude_none=True)
            if hasattr(content, 'model_dump')
            else content
        )

        # Extract basics section
        basics = content_dict.get('basics', {})
        basics = self._ensure_basics_complete(basics)

        # Build JSON Resume structure
        json_resume = {
            "basics": basics,
            "work": self._ensure_work_complete(content_dict.get('work', [])),
            "education": self._ensure_education_complete(
                content_dict.get('education', [])
            ),
        }

        # Add optional sections if present
        optional_sections = [
            'volunteer',
            'awards',
            'certificates',
            'publications',
            'skills',
            'languages',
            'interests',
            'references',
            'projects',
        ]

        for section_name in optional_sections:
            if section_name in content_dict:
                section_data = content_dict[section_name]
                if section_name == 'publications':
                    json_resume[section_name] = self._ensure_publications_complete(
                        section_data or []
                    )
                elif section_name == 'projects':
                    json_resume[section_name] = self._ensure_projects_complete(
                        section_data or []
                    )
                elif section_name == 'skills':
                    json_resume[section_name] = self._ensure_skills_complete(
                        section_data or []
                    )
                elif section_name == 'awards':
                    json_resume[section_name] = self._ensure_awards_complete(
                        section_data or []
                    )
                else:
                    json_resume[section_name] = section_data or []

        # Handle any extra sections (not in standard JSON Resume schema)
        for section_name, section_data in content_dict.items():
            if section_name not in [
                'basics',
                'work',
                'education',
            ] + optional_sections + ['field_schema', 'meta']:
                json_resume[section_name] = section_data
                self.warnings.append(
                    f"Unknown section '{section_name}' may not render correctly"
                )

        # Ensure all required top-level sections exist (even if empty)
        for section in optional_sections:
            if section not in json_resume:
                json_resume[section] = []

        return json_resume

    def _ensure_basics_complete(self, basics: dict) -> dict:
        """Ensure basics section has all required fields."""

        # Required fields with defaults
        required_fields = {
            'name': 'Professional Name',
            'email': 'professional@email.com',
            'phone': '+1-555-000-0000',
            'summary': 'Professional summary to be filled in.',
            'url': 'https://example.com',
        }

        for field, default_value in required_fields.items():
            if field not in basics or not basics[field]:
                if self.strict_validation:
                    raise ValueError(f"Missing required field in basics: {field}")
                else:
                    basics[field] = default_value
                    self.warnings.append(
                        f"Missing '{field}' in basics section, using default: '{default_value}'"
                    )

        # Ensure location exists
        if 'location' not in basics:
            basics['location'] = {
                'city': 'City',
                'countryCode': 'US',
                'region': 'State',
            }
            self.warnings.append("Missing location in basics, using default location")

        return basics

    def _ensure_work_complete(self, work_entries: list[dict]) -> list[dict]:
        """Ensure work entries have required fields."""

        for i, work in enumerate(work_entries):
            # Required fields for work entries
            if 'name' not in work and 'company' not in work:
                if self.strict_validation:
                    raise ValueError(f"Work entry {i} missing company/name field")
                else:
                    work['name'] = work.get('company', 'Company Name')
                    self.warnings.append(
                        f"Work entry {i} missing company name, using default"
                    )

            if 'position' not in work:
                if self.strict_validation:
                    raise ValueError(f"Work entry {i} missing position field")
                else:
                    work['position'] = 'Position Title'
                    self.warnings.append(
                        f"Work entry {i} missing position, using default"
                    )

            if 'startDate' not in work:
                if self.strict_validation:
                    raise ValueError(f"Work entry {i} missing startDate field")
                else:
                    work['startDate'] = '2020-01-01'
                    self.warnings.append(
                        f"Work entry {i} missing startDate, using default"
                    )

        return work_entries

    def _ensure_education_complete(self, education_entries: list[dict]) -> list[dict]:
        """Ensure education entries have required fields."""

        for i, edu in enumerate(education_entries):
            # Required fields for education entries
            required_fields = {
                'institution': 'Educational Institution',
                'area': 'Field of Study',
                'studyType': 'Degree Type',
                'startDate': '2020-01-01',
                'endDate': '2024-12-31',
            }

            for field, default_value in required_fields.items():
                if field not in edu:
                    if self.strict_validation:
                        raise ValueError(f"Education entry {i} missing {field} field")
                    else:
                        edu[field] = default_value
                        self.warnings.append(
                            f"Education entry {i} missing '{field}', using default: '{default_value}'"
                        )

        return education_entries

    def _fix_common_conversion_issues(self, json_resume: dict) -> dict:
        """Fix common issues that cause conversion failures."""

        # Make a copy to avoid modifying original
        import copy

        fixed_resume = copy.deepcopy(json_resume)

        # Fix empty arrays that cause issues
        for section in ['work', 'education', 'skills', 'projects']:
            if section in fixed_resume and not fixed_resume[section]:
                # Add a minimal entry to prevent conversion errors
                if section == 'work':
                    fixed_resume[section] = [
                        {
                            'name': 'Example Company',
                            'position': 'Position Title',
                            'startDate': '2020-01-01',
                            'endDate': '2023-12-31',
                            'summary': 'Professional experience to be filled in.',
                        }
                    ]
                    self.warnings.append(
                        "Added example work entry to prevent conversion errors"
                    )
                elif section == 'education':
                    fixed_resume[section] = [
                        {
                            'institution': 'Educational Institution',
                            'area': 'Field of Study',
                            'studyType': 'Degree',
                            'startDate': '2020-01-01',
                            'endDate': '2024-12-31',
                        }
                    ]
                    self.warnings.append(
                        "Added example education entry to prevent conversion errors"
                    )

        return fixed_resume

    def _ensure_publications_complete(self, publications: list[dict]) -> list[dict]:
        """Ensure publications entries have required fields."""

        for i, pub in enumerate(publications):
            # Required fields for publications
            required_fields = {
                'name': 'Publication Title',
                'publisher': 'Publisher Name',
                'releaseDate': '2023-01-01',  # This is what was missing!
                'url': 'https://example.com',
            }

            for field, default_value in required_fields.items():
                if field not in pub:
                    if self.strict_validation:
                        raise ValueError(f"Publication entry {i} missing {field} field")
                    else:
                        pub[field] = default_value
                        self.warnings.append(
                            f"Publication entry {i} missing '{field}', using default: '{default_value}'"
                        )

        return publications

    def _ensure_projects_complete(self, projects: list[dict]) -> list[dict]:
        """Ensure projects entries have required fields."""

        for i, proj in enumerate(projects):
            # Required fields for projects
            required_fields = {
                'name': 'Project Name',
                'description': 'Project description to be filled in.',
                'startDate': '2023-01-01',
                'endDate': '2023-12-31',
            }

            for field, default_value in required_fields.items():
                if field not in proj:
                    if self.strict_validation:
                        raise ValueError(f"Project entry {i} missing {field} field")
                    else:
                        proj[field] = default_value
                        self.warnings.append(
                            f"Project entry {i} missing '{field}', using default: '{default_value}'"
                        )

        return projects

    def _ensure_skills_complete(self, skills: list[dict]) -> list[dict]:
        """Ensure skills entries have required fields."""

        for i, skill in enumerate(skills):
            # Required fields for skills
            if 'name' not in skill:
                if self.strict_validation:
                    raise ValueError(f"Skill entry {i} missing name field")
                else:
                    skill['name'] = 'Skill Category'
                    self.warnings.append(
                        f"Skill entry {i} missing 'name', using default: 'Skill Category'"
                    )

            if 'keywords' not in skill:
                skill['keywords'] = []  # Empty list is acceptable for keywords

        return skills

    def _ensure_awards_complete(self, awards: list[dict]) -> list[dict]:
        """Ensure awards entries have required fields."""

        for i, award in enumerate(awards):
            # Required fields for awards
            required_fields = {
                'title': 'Award Title',
                'date': '2023-01-01',
                'awarder': 'Awarding Organization',
            }

            for field, default_value in required_fields.items():
                if field not in award:
                    if self.strict_validation:
                        raise ValueError(f"Award entry {i} missing {field} field")
                    else:
                        award[field] = default_value
                        self.warnings.append(
                            f"Award entry {i} missing '{field}', using default: '{default_value}'"
                        )

        return awards

    def _content_to_json_resume(
        self, content: Any
    ) -> dict:  # content is ResumeSchemaExtended
        """Legacy method - kept for backward compatibility."""
        return self._content_to_json_resume_robust(content)
