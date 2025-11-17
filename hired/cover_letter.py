"""
Cover letter generation functionality.

Generate professional cover letters tailored to specific job applications.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
import jinja2

if TYPE_CHECKING:
    from hired.search.base import JobResult


@dataclass
class CoverLetterData:
    """
    Data structure for cover letter generation.
    """

    # Required fields
    applicant_name: str
    applicant_email: str
    company_name: str
    position_title: str

    # Optional applicant information
    applicant_phone: Optional[str] = None
    applicant_address: Optional[str] = None

    # Optional target information
    hiring_manager_name: Optional[str] = None

    # Content
    opening_paragraph: str = ""
    body_paragraphs: Optional[list] = None
    closing_paragraph: str = ""

    # Metadata
    date: Optional[str] = None

    def __post_init__(self):
        if self.body_paragraphs is None:
            self.body_paragraphs = []
        if self.date is None:
            self.date = datetime.now().strftime("%B %d, %Y")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            'applicant_name': self.applicant_name,
            'applicant_email': self.applicant_email,
            'applicant_phone': self.applicant_phone,
            'applicant_address': self.applicant_address,
            'company_name': self.company_name,
            'position_title': self.position_title,
            'hiring_manager_name': self.hiring_manager_name,
            'opening_paragraph': self.opening_paragraph,
            'body_paragraphs': self.body_paragraphs,
            'closing_paragraph': self.closing_paragraph,
            'date': self.date,
        }


def generate_cover_letter_content(
    candidate_info: Dict[str, Any],
    job_info: Dict[str, Any] | 'JobResult',
    tone: str = "professional"
) -> CoverLetterData:
    """
    Generate cover letter content from candidate and job information.

    Args:
        candidate_info: Candidate information (resume dict or basics)
        job_info: Job information (dict, text, or JobResult)
        tone: Tone of the letter ('professional', 'enthusiastic', 'formal')

    Returns:
        CoverLetterData object with generated content

    Examples:
        >>> data = generate_cover_letter_content(
        ...     candidate_info={'basics': {'name': 'Jane Doe', 'email': 'jane@example.com'}},
        ...     job_info={'title': 'Software Engineer', 'company': 'TechCorp'},
        ... )
    """
    # Extract applicant info
    basics = candidate_info.get('basics', candidate_info)
    applicant_name = basics.get('name', 'Applicant')
    applicant_email = basics.get('email', '')
    applicant_phone = basics.get('phone')

    # Build address if available
    location = basics.get('location', {})
    applicant_address = None
    if location:
        address_parts = []
        if location.get('address'):
            address_parts.append(location['address'])
        if location.get('city'):
            city_state = location['city']
            if location.get('region'):
                city_state += f", {location['region']}"
            address_parts.append(city_state)
        if location.get('postalCode'):
            address_parts.append(location['postalCode'])
        if address_parts:
            applicant_address = ', '.join(address_parts)

    # Extract job info
    if hasattr(job_info, 'title'):  # JobResult
        company_name = job_info.company or "the company"
        position_title = job_info.title
    else:  # dict
        company_name = job_info.get('company', job_info.get('company_name', 'the company'))
        position_title = job_info.get('title', job_info.get('position', 'the position'))

    # Generate content based on tone
    opening = _generate_opening(applicant_name, position_title, company_name, tone)
    body = _generate_body(candidate_info, job_info, tone)
    closing = _generate_closing(tone)

    return CoverLetterData(
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        applicant_phone=applicant_phone,
        applicant_address=applicant_address,
        company_name=company_name,
        position_title=position_title,
        opening_paragraph=opening,
        body_paragraphs=body,
        closing_paragraph=closing,
    )


def _generate_opening(
    applicant_name: str,
    position_title: str,
    company_name: str,
    tone: str
) -> str:
    """Generate opening paragraph."""
    if tone == "enthusiastic":
        return (
            f"I am thrilled to apply for the {position_title} position at {company_name}. "
            f"With my background and passion for the field, I am excited about the opportunity "
            f"to contribute to your team's success."
        )
    elif tone == "formal":
        return (
            f"I am writing to express my interest in the {position_title} position at {company_name}. "
            f"I believe my qualifications and experience make me a strong candidate for this role."
        )
    else:  # professional
        return (
            f"I am writing to apply for the {position_title} position at {company_name}. "
            f"I am confident that my skills and experience align well with the requirements "
            f"of this role and would allow me to make valuable contributions to your team."
        )


def _generate_body(
    candidate_info: Dict[str, Any],
    job_info: Any,
    tone: str
) -> list[str]:
    """Generate body paragraphs."""
    paragraphs = []

    # Paragraph 1: Relevant experience
    work = candidate_info.get('work', [])
    if work:
        recent_job = work[0]
        position = recent_job.get('position', 'my previous role')
        company = recent_job.get('company', 'my previous employer')

        para1 = (
            f"In my current role as {position} at {company}, I have developed strong skills "
            f"in relevant areas that directly apply to this position. My experience has "
            f"prepared me well for the challenges and opportunities of this role."
        )
        paragraphs.append(para1)

    # Paragraph 2: Skills and achievements
    skills = candidate_info.get('skills', [])
    if skills:
        skill_names = [s.get('name') for s in skills if s.get('name')]
        if skill_names:
            skill_list = ', '.join(skill_names[:3])
            para2 = (
                f"My technical expertise includes {skill_list}, among other skills. "
                f"I have successfully applied these skills to deliver impactful results "
                f"and am eager to bring this experience to your organization."
            )
            paragraphs.append(para2)

    # Paragraph 3: Why this company
    para3 = (
        f"I am particularly drawn to this opportunity because of your company's reputation "
        f"and the exciting work you are doing. I am enthusiastic about the possibility of "
        f"contributing to your team and growing professionally in this role."
    )
    paragraphs.append(para3)

    return paragraphs


def _generate_closing(tone: str) -> str:
    """Generate closing paragraph."""
    if tone == "enthusiastic":
        return (
            "I would love the opportunity to discuss how my background, skills, and "
            "enthusiasm can contribute to your team. Thank you for considering my application, "
            "and I look forward to speaking with you soon!"
        )
    elif tone == "formal":
        return (
            "I would welcome the opportunity to discuss my qualifications in more detail. "
            "Thank you for your time and consideration. I look forward to hearing from you."
        )
    else:  # professional
        return (
            "I would appreciate the opportunity to discuss how my experience and skills "
            "can benefit your team. Thank you for considering my application. "
            "I look forward to the possibility of speaking with you."
        )


def render_cover_letter(
    cover_letter_data: CoverLetterData,
    format: str = 'text',
    template: Optional[str] = None
) -> str:
    """
    Render cover letter to specified format.

    Args:
        cover_letter_data: CoverLetterData object
        format: Output format ('text', 'html', 'markdown')
        template: Optional custom Jinja2 template string

    Returns:
        Rendered cover letter as string
    """
    if template:
        jinja_template = jinja2.Template(template)
    elif format == 'html':
        jinja_template = jinja2.Template(_HTML_TEMPLATE)
    elif format == 'markdown':
        jinja_template = jinja2.Template(_MARKDOWN_TEMPLATE)
    else:  # text
        jinja_template = jinja2.Template(_TEXT_TEMPLATE)

    return jinja_template.render(**cover_letter_data.to_dict())


def mk_cover_letter(
    candidate_info: Dict[str, Any],
    job_info: Dict[str, Any] | 'JobResult',
    *,
    tone: str = "professional",
    format: str = 'text',
    output_path: Optional[str] = None
) -> str:
    """
    Generate and render a cover letter.

    Args:
        candidate_info: Candidate information (resume dict or basics)
        job_info: Job information (dict, text, or JobResult)
        tone: Tone of the letter ('professional', 'enthusiastic', 'formal')
        format: Output format ('text', 'html', 'markdown')
        output_path: Optional path to save the cover letter

    Returns:
        Rendered cover letter as string

    Examples:
        >>> from hired import mk_cover_letter, JobSources, SearchCriteria
        >>>
        >>> # From job search result
        >>> sources = JobSources()
        >>> jobs = sources.jobspy.search(SearchCriteria(query="software engineer"))
        >>>
        >>> letter = mk_cover_letter(
        ...     candidate_info={'basics': {'name': 'Jane Doe', 'email': 'jane@example.com'}},
        ...     job_info=jobs[0],
        ...     format='html'
        ... )
    """
    # Handle JobResult conversion
    if hasattr(job_info, 'title') and hasattr(job_info, 'source'):
        from hired.job_utils import job_to_text
        # Create a dict with the job info for easier processing
        job_dict = {
            'title': job_info.title,
            'company': job_info.company,
            'description': job_info.description,
        }
        cover_letter_data = generate_cover_letter_content(candidate_info, job_info, tone)
    else:
        cover_letter_data = generate_cover_letter_content(candidate_info, job_info, tone)

    result = render_cover_letter(cover_letter_data, format=format)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)

    return result


# Templates

_TEXT_TEMPLATE = """{{ date }}

{{ applicant_name }}
{% if applicant_address %}{{ applicant_address }}{% endif %}
{{ applicant_email }}
{% if applicant_phone %}{{ applicant_phone }}{% endif %}

{% if hiring_manager_name %}{{ hiring_manager_name }}{% else %}Hiring Manager{% endif %}
{{ company_name }}

Dear {% if hiring_manager_name %}{{ hiring_manager_name }}{% else %}Hiring Manager{% endif %},

{{ opening_paragraph }}

{% for paragraph in body_paragraphs %}
{{ paragraph }}

{% endfor %}
{{ closing_paragraph }}

Sincerely,
{{ applicant_name }}
"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Times New Roman', serif;
            max-width: 800px;
            margin: 40px auto;
            line-height: 1.6;
            color: #333;
        }
        .header {
            margin-bottom: 20px;
        }
        .date {
            margin-bottom: 30px;
        }
        .recipient {
            margin-bottom: 30px;
        }
        .salutation {
            margin-bottom: 20px;
        }
        p {
            margin-bottom: 15px;
            text-align: justify;
        }
        .closing {
            margin-top: 30px;
        }
        .signature {
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="header">
        <strong>{{ applicant_name }}</strong><br>
        {% if applicant_address %}{{ applicant_address }}<br>{% endif %}
        {{ applicant_email }}<br>
        {% if applicant_phone %}{{ applicant_phone }}<br>{% endif %}
    </div>

    <div class="date">{{ date }}</div>

    <div class="recipient">
        <strong>{% if hiring_manager_name %}{{ hiring_manager_name }}{% else %}Hiring Manager{% endif %}</strong><br>
        {{ company_name }}
    </div>

    <div class="salutation">
        Dear {% if hiring_manager_name %}{{ hiring_manager_name }}{% else %}Hiring Manager{% endif %},
    </div>

    <p>{{ opening_paragraph }}</p>

    {% for paragraph in body_paragraphs %}
    <p>{{ paragraph }}</p>
    {% endfor %}

    <p class="closing">{{ closing_paragraph }}</p>

    <div class="signature">
        Sincerely,<br><br>
        {{ applicant_name }}
    </div>
</body>
</html>
"""

_MARKDOWN_TEMPLATE = """# Cover Letter

**{{ applicant_name }}**
{% if applicant_address %}{{ applicant_address }}  {% endif %}
{{ applicant_email }}
{% if applicant_phone %}{{ applicant_phone }}  {% endif %}

---

{{ date }}

**{% if hiring_manager_name %}{{ hiring_manager_name }}{% else %}Hiring Manager{% endif %}**
{{ company_name }}

---

Dear {% if hiring_manager_name %}{{ hiring_manager_name }}{% else %}Hiring Manager{% endif %},

{{ opening_paragraph }}

{% for paragraph in body_paragraphs %}
{{ paragraph }}

{% endfor %}

{{ closing_paragraph }}

Sincerely,

{{ applicant_name }}
"""
