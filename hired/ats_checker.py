"""
ATS (Applicant Tracking System) compatibility checker.

Analyze resumes to ensure they're compatible with automated screening systems.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from hired.search.base import JobResult
from hired.job_utils import JobAnalyzer


@dataclass
class ATSIssue:
    """Represents an ATS compatibility issue."""

    category: str  # 'critical', 'warning', 'info'
    title: str
    description: str
    suggestion: str

    def to_dict(self) -> Dict[str, str]:
        return {
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'suggestion': self.suggestion,
        }


@dataclass
class ATSReport:
    """Report from ATS compatibility check."""

    overall_score: float  # 0-100
    issues: List[ATSIssue] = field(default_factory=list)
    keyword_match_score: float = 0.0
    matched_keywords: Set[str] = field(default_factory=set)
    missing_keywords: Set[str] = field(default_factory=set)

    def get_issues_by_category(self, category: str) -> List[ATSIssue]:
        """Get issues filtered by category."""
        return [issue for issue in self.issues if issue.category == category]

    def get_critical_issues(self) -> List[ATSIssue]:
        """Get critical issues."""
        return self.get_issues_by_category('critical')

    def get_warnings(self) -> List[ATSIssue]:
        """Get warnings."""
        return self.get_issues_by_category('warning')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'overall_score': round(self.overall_score, 1),
            'keyword_match_score': round(self.keyword_match_score, 1),
            'matched_keywords': list(self.matched_keywords),
            'missing_keywords': list(self.missing_keywords),
            'issues': [issue.to_dict() for issue in self.issues],
            'critical_count': len(self.get_critical_issues()),
            'warning_count': len(self.get_warnings()),
        }

    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            "ATS Compatibility Report",
            "=" * 60,
            f"Overall Score: {self.overall_score:.1f}/100",
            f"Keyword Match: {self.keyword_match_score:.1f}%",
            f"Critical Issues: {len(self.get_critical_issues())}",
            f"Warnings: {len(self.get_warnings())}",
            "",
        ]

        if self.get_critical_issues():
            lines.append("Critical Issues:")
            lines.append("-" * 60)
            for issue in self.get_critical_issues():
                lines.append(f"• {issue.title}")
                lines.append(f"  {issue.description}")
                lines.append(f"  → {issue.suggestion}")
                lines.append("")

        if self.get_warnings():
            lines.append("Warnings:")
            lines.append("-" * 60)
            for issue in self.get_warnings():
                lines.append(f"• {issue.title}")
                lines.append(f"  {issue.description}")
                lines.append(f"  → {issue.suggestion}")
                lines.append("")

        if self.missing_keywords:
            lines.append("Important Missing Keywords:")
            lines.append("-" * 60)
            for keyword in list(self.missing_keywords)[:15]:
                lines.append(f"  - {keyword}")
            lines.append("")

        return "\n".join(lines)


class ATSChecker:
    """
    Check resume for ATS compatibility.

    Examples:
        >>> from hired.ats_checker import ATSChecker
        >>>
        >>> checker = ATSChecker()
        >>> report = checker.check_resume(resume_dict)
        >>> print(report.get_summary())
        >>>
        >>> # Check against specific job
        >>> report = checker.check_resume(resume_dict, job_result)
    """

    # Standard section names that ATS systems recognize
    STANDARD_SECTIONS = {
        'basics', 'summary', 'work', 'work experience', 'experience',
        'education', 'skills', 'projects', 'certifications', 'awards',
        'publications', 'volunteer', 'languages', 'interests', 'references'
    }

    # Common problematic elements
    AVOID_ELEMENTS = {
        'tables': r'<table',
        'text_boxes': r'<textarea',
        'headers_footers': None,  # Checked separately
        'images': r'<img',
        'fancy_fonts': None,  # Checked separately
    }

    def __init__(self):
        """Initialize ATS checker."""
        pass

    def check_resume(
        self,
        resume_content: Dict[str, Any],
        job: Optional[JobResult] = None
    ) -> ATSReport:
        """
        Check resume for ATS compatibility.

        Args:
            resume_content: Resume content as dictionary (JSON Resume format)
            job: Optional JobResult to check keyword matching

        Returns:
            ATSReport with compatibility score and issues
        """
        issues = []
        score = 100.0

        # Check structure
        structure_issues, structure_penalty = self._check_structure(resume_content)
        issues.extend(structure_issues)
        score -= structure_penalty

        # Check contact information
        contact_issues, contact_penalty = self._check_contact_info(resume_content)
        issues.extend(contact_issues)
        score -= contact_penalty

        # Check formatting
        format_issues, format_penalty = self._check_formatting(resume_content)
        issues.extend(format_issues)
        score -= format_penalty

        # Check content
        content_issues, content_penalty = self._check_content(resume_content)
        issues.extend(content_issues)
        score -= content_penalty

        # Check keyword matching if job provided
        keyword_score = 0.0
        matched_keywords = set()
        missing_keywords = set()

        if job:
            keyword_score, matched_keywords, missing_keywords, keyword_issues = \
                self._check_keywords(resume_content, job)
            issues.extend(keyword_issues)

            # Keyword matching affects overall score
            score = (score * 0.7) + (keyword_score * 0.3)

        # Ensure score is in valid range
        score = max(0.0, min(100.0, score))

        return ATSReport(
            overall_score=score,
            issues=issues,
            keyword_match_score=keyword_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
        )

    def _check_structure(self, resume: Dict[str, Any]) -> tuple[List[ATSIssue], float]:
        """Check resume structure."""
        issues = []
        penalty = 0.0

        # Check for basics section
        if 'basics' not in resume or not resume['basics']:
            issues.append(ATSIssue(
                category='critical',
                title='Missing Basics Section',
                description='Resume must have a basics section with contact information.',
                suggestion='Add a basics section with name, email, and phone number.'
            ))
            penalty += 20.0

        # Check for work experience
        if 'work' not in resume or not resume['work']:
            issues.append(ATSIssue(
                category='warning',
                title='Missing Work Experience',
                description='No work experience section found.',
                suggestion='Add work experience entries to demonstrate your background.'
            ))
            penalty += 10.0

        # Check for skills section
        if 'skills' not in resume or not resume['skills']:
            issues.append(ATSIssue(
                category='warning',
                title='Missing Skills Section',
                description='No skills section found. ATS systems often filter by skills.',
                suggestion='Add a skills section with relevant technical and soft skills.'
            ))
            penalty += 10.0

        return issues, penalty

    def _check_contact_info(self, resume: Dict[str, Any]) -> tuple[List[ATSIssue], float]:
        """Check contact information completeness."""
        issues = []
        penalty = 0.0

        basics = resume.get('basics', {})

        # Check email
        if not basics.get('email'):
            issues.append(ATSIssue(
                category='critical',
                title='Missing Email Address',
                description='Email address is required for ATS processing.',
                suggestion='Add your professional email address to the basics section.'
            ))
            penalty += 15.0

        # Check phone
        if not basics.get('phone'):
            issues.append(ATSIssue(
                category='warning',
                title='Missing Phone Number',
                description='Phone number helps ATS systems contact you.',
                suggestion='Add your phone number to the basics section.'
            ))
            penalty += 5.0

        # Check name
        if not basics.get('name'):
            issues.append(ATSIssue(
                category='critical',
                title='Missing Name',
                description='Your name is required.',
                suggestion='Add your full name to the basics section.'
            ))
            penalty += 15.0

        return issues, penalty

    def _check_formatting(self, resume: Dict[str, Any]) -> tuple[List[ATSIssue], float]:
        """Check for formatting that may cause ATS issues."""
        issues = []
        penalty = 0.0

        # In JSON Resume format, we don't have direct access to the rendered format
        # But we can check for potential issues in the data

        # Check for overly long descriptions
        work_entries = resume.get('work', [])
        for i, job in enumerate(work_entries):
            summary = job.get('summary', '')
            if len(summary) > 1000:
                issues.append(ATSIssue(
                    category='info',
                    title=f'Long Job Description (Entry {i+1})',
                    description='Very long descriptions may be truncated by ATS.',
                    suggestion='Keep job descriptions concise (under 500 characters).'
                ))

        return issues, penalty

    def _check_content(self, resume: Dict[str, Any]) -> tuple[List[ATSIssue], float]:
        """Check resume content quality."""
        issues = []
        penalty = 0.0

        # Check for quantifiable achievements
        work_entries = resume.get('work', [])
        has_numbers = False

        for job in work_entries:
            highlights = job.get('highlights', [])
            summary = job.get('summary', '')

            combined_text = summary + ' ' + ' '.join(highlights)

            # Look for numbers, percentages, currency
            if re.search(r'\d+[%$]?|\$\d+', combined_text):
                has_numbers = True
                break

        if not has_numbers:
            issues.append(ATSIssue(
                category='warning',
                title='No Quantifiable Achievements',
                description='Including numbers and metrics makes your resume more compelling.',
                suggestion='Add metrics like "Increased sales by 25%" or "Managed team of 5".'
            ))
            penalty += 5.0

        # Check for action verbs
        if work_entries:
            weak_verbs = {'responsible for', 'worked on', 'helped with', 'did'}
            has_weak_verbs = False

            for job in work_entries:
                highlights = job.get('highlights', [])
                for highlight in highlights:
                    if any(verb in highlight.lower() for verb in weak_verbs):
                        has_weak_verbs = True
                        break

            if has_weak_verbs:
                issues.append(ATSIssue(
                    category='info',
                    title='Weak Action Verbs',
                    description='Using stronger action verbs improves impact.',
                    suggestion='Replace "responsible for" with verbs like "Led", "Developed", "Implemented".'
                ))

        return issues, penalty

    def _check_keywords(
        self,
        resume: Dict[str, Any],
        job: JobResult
    ) -> tuple[float, Set[str], Set[str], List[ATSIssue]]:
        """Check keyword matching against job posting."""
        issues = []

        # Extract keywords from job
        analyzer = JobAnalyzer(job)
        job_keywords = set(analyzer.extract_keywords(30))
        job_skills = analyzer.extract_skills()

        # Combine job keywords and skills
        required_keywords = job_keywords | job_skills

        # Extract text from resume
        resume_text = self._extract_resume_text(resume).lower()

        # Check which keywords are present
        matched = set()
        missing = set()

        for keyword in required_keywords:
            if keyword.lower() in resume_text:
                matched.add(keyword)
            else:
                missing.add(keyword)

        # Calculate score
        if required_keywords:
            score = (len(matched) / len(required_keywords)) * 100
        else:
            score = 100.0

        # Add issues for missing important keywords
        if score < 50:
            issues.append(ATSIssue(
                category='critical',
                title='Low Keyword Match',
                description=f'Only {score:.0f}% of job keywords found in resume.',
                suggestion=f'Include these keywords: {", ".join(list(missing)[:5])}'
            ))
        elif score < 70:
            issues.append(ATSIssue(
                category='warning',
                title='Moderate Keyword Match',
                description=f'{score:.0f}% of job keywords found. Could be improved.',
                suggestion=f'Consider adding: {", ".join(list(missing)[:5])}'
            ))

        return score, matched, missing, issues

    def _extract_resume_text(self, resume: Dict[str, Any]) -> str:
        """Extract all text from resume for keyword matching."""
        parts = []

        # Basics
        basics = resume.get('basics', {})
        if basics.get('name'):
            parts.append(basics['name'])
        if basics.get('label'):
            parts.append(basics['label'])
        if basics.get('summary'):
            parts.append(basics['summary'])

        # Work
        for job in resume.get('work', []):
            parts.append(job.get('position', ''))
            parts.append(job.get('company', ''))
            parts.append(job.get('summary', ''))
            parts.extend(job.get('highlights', []))

        # Skills
        for skill_group in resume.get('skills', []):
            parts.append(skill_group.get('name', ''))
            parts.extend(skill_group.get('keywords', []))

        # Education
        for edu in resume.get('education', []):
            parts.append(edu.get('institution', ''))
            parts.append(edu.get('studyType', ''))
            parts.append(edu.get('area', ''))

        # Projects
        for project in resume.get('projects', []):
            parts.append(project.get('name', ''))
            parts.append(project.get('description', ''))

        return ' '.join(parts)


def check_resume_ats(
    resume_content: Dict[str, Any],
    job: Optional[JobResult] = None
) -> ATSReport:
    """
    Quick utility to check resume ATS compatibility.

    Args:
        resume_content: Resume content as dictionary (JSON Resume format)
        job: Optional JobResult for keyword matching

    Returns:
        ATSReport

    Examples:
        >>> from hired import mk_content_for_resume
        >>> from hired.ats_checker import check_resume_ats
        >>>
        >>> resume = mk_content_for_resume(candidate_info, job_info)
        >>> report = check_resume_ats(resume.model_dump(), job_result)
        >>> print(report.get_summary())
    """
    checker = ATSChecker()
    return checker.check_resume(resume_content, job)
