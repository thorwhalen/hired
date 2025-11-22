"""
Utilities for working with job postings and matching them to resumes.
"""

import re
from typing import List, Set, Dict, Any, Optional
from hired.search.base import JobResult


class JobAnalyzer:
    """
    Analyze job postings to extract key information for resume tailoring.
    """

    # Common skill keywords (can be extended)
    TECH_SKILLS = {
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
        'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'express',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'git', 'ci/cd', 'agile', 'scrum', 'jira', 'linux', 'bash',
        'ml', 'ai', 'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'data science', 'analytics', 'tableau', 'power bi', 'spark', 'hadoop',
        'rest', 'graphql', 'microservices', 'api', 'backend', 'frontend',
    }

    SOFT_SKILLS = {
        'leadership', 'communication', 'collaboration', 'teamwork', 'problem-solving',
        'critical thinking', 'project management', 'mentoring', 'coaching',
        'strategic thinking', 'analytical', 'creative', 'adaptable', 'organized',
    }

    def __init__(self, job: JobResult):
        """
        Initialize analyzer with a job posting.

        Args:
            job: JobResult object
        """
        self.job = job
        self._text = self._extract_text()
        self._text_lower = self._text.lower()

    def _extract_text(self) -> str:
        """Extract all searchable text from job posting."""
        parts = []

        if self.job.title:
            parts.append(self.job.title)
        if self.job.company:
            parts.append(self.job.company)
        if self.job.description:
            parts.append(self.job.description)

        # Add skills if present
        if self.job.skills:
            parts.extend(self.job.skills)

        return ' '.join(parts)

    def extract_skills(self, include_soft_skills: bool = True) -> Set[str]:
        """
        Extract mentioned skills from job posting.

        Args:
            include_soft_skills: Whether to include soft skills

        Returns:
            Set of identified skills
        """
        found_skills = set()

        # Check technical skills
        for skill in self.TECH_SKILLS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, self._text_lower):
                found_skills.add(skill)

        # Check soft skills if requested
        if include_soft_skills:
            for skill in self.SOFT_SKILLS:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, self._text_lower):
                    found_skills.add(skill)

        # Add explicitly listed skills
        if self.job.skills:
            found_skills.update(s.lower() for s in self.job.skills)

        return found_skills

    def extract_requirements(self) -> List[str]:
        """
        Extract job requirements from description.

        Returns:
            List of requirement strings
        """
        if not self.job.description:
            return []

        requirements = []

        # Look for common requirement section headers
        desc_lower = self.job.description.lower()

        # Find requirements sections
        patterns = [
            r'(?:requirements?|qualifications?|what we\'re looking for):?\s*\n+((?:[-•*]\s*.+\n?)+)',
            r'(?:required|must have):?\s*\n+((?:[-•*]\s*.+\n?)+)',
            r'(?:responsibilities|you will):?\s*\n+((?:[-•*]\s*.+\n?)+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, self.job.description, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                bullet_text = match.group(1)
                # Split by bullets and clean
                bullets = re.split(r'\n[-•*]\s*', bullet_text)
                requirements.extend(b.strip() for b in bullets if b.strip())

        # If no structured requirements found, look for years of experience
        if not requirements:
            exp_pattern = r'(\d+\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience)'
            exp_matches = re.findall(exp_pattern, desc_lower)
            requirements.extend(exp_matches)

        return requirements

    def extract_keywords(self, top_n: int = 20) -> List[str]:
        """
        Extract most important keywords from job posting.

        Args:
            top_n: Number of top keywords to return

        Returns:
            List of keywords sorted by relevance
        """
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'we', 'you', 'they', 'our', 'your', 'their',
        }

        # Tokenize and count
        words = re.findall(r'\b[a-z]{3,}\b', self._text_lower)
        word_freq = {}

        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]

    def to_job_info_text(self) -> str:
        """
        Convert job posting to a formatted text suitable for resume generation.

        Returns:
            Formatted job description text
        """
        lines = []

        if self.job.title:
            lines.append(f"Position: {self.job.title}")

        if self.job.company:
            lines.append(f"Company: {self.job.company}")

        if self.job.location and self.job.location.raw:
            lines.append(f"Location: {self.job.location.raw}")

        if self.job.is_remote:
            lines.append("Work Mode: Remote")

        if self.job.job_type:
            lines.append(f"Job Type: {self.job.job_type.value}")

        if self.job.compensation:
            comp = self.job.compensation
            if comp.min_amount and comp.max_amount:
                currency = comp.currency or "USD"
                interval = comp.interval or "yearly"
                lines.append(
                    f"Compensation: ${comp.min_amount:,.0f} - ${comp.max_amount:,.0f} "
                    f"{currency} ({interval})"
                )

        lines.append("")  # Blank line

        # Add description
        if self.job.description:
            lines.append("Job Description:")
            lines.append(self.job.description)

        # Add extracted requirements
        requirements = self.extract_requirements()
        if requirements:
            lines.append("")
            lines.append("Key Requirements:")
            for req in requirements[:10]:  # Top 10 requirements
                lines.append(f"- {req}")

        # Add skills
        skills = self.extract_skills()
        if skills:
            lines.append("")
            lines.append("Required Skills:")
            lines.append(", ".join(sorted(skills)))

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the job posting.

        Returns:
            Dictionary with job summary
        """
        return {
            'title': self.job.title,
            'company': self.job.company,
            'location': self.job.location.raw if self.job.location else None,
            'is_remote': self.job.is_remote,
            'skills': list(self.extract_skills()),
            'requirements': self.extract_requirements(),
            'keywords': self.extract_keywords(),
            'job_url': self.job.job_url,
        }


def job_to_text(job: JobResult) -> str:
    """
    Convert a JobResult to formatted text for resume generation.

    Args:
        job: JobResult object

    Returns:
        Formatted text description
    """
    analyzer = JobAnalyzer(job)
    return analyzer.to_job_info_text()


def extract_job_keywords(job: JobResult, top_n: int = 20) -> List[str]:
    """
    Extract top keywords from a job posting.

    Args:
        job: JobResult object
        top_n: Number of keywords to return

    Returns:
        List of top keywords
    """
    analyzer = JobAnalyzer(job)
    return analyzer.extract_keywords(top_n)


def get_job_skills(job: JobResult) -> Set[str]:
    """
    Extract skills mentioned in job posting.

    Args:
        job: JobResult object

    Returns:
        Set of skills
    """
    analyzer = JobAnalyzer(job)
    return analyzer.extract_skills()
