"""
Job matching and scoring utilities.

Match candidate profiles against job postings to identify the best opportunities.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Any, Optional
from hired.search.base import JobResult
from hired.job_utils import JobAnalyzer


@dataclass
class MatchScore:
    """Score for a job match."""

    job: JobResult
    overall_score: float  # 0-100
    skill_match_score: float  # 0-100
    keyword_match_score: float  # 0-100

    matched_skills: Set[str] = field(default_factory=set)
    missing_skills: Set[str] = field(default_factory=set)
    matched_keywords: Set[str] = field(default_factory=set)

    # Additional metadata
    compensation_match: Optional[bool] = None
    location_match: Optional[bool] = None

    def __lt__(self, other):
        """Enable sorting by overall score."""
        return self.overall_score < other.overall_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'job_title': self.job.title,
            'company': self.job.company,
            'overall_score': round(self.overall_score, 1),
            'skill_match_score': round(self.skill_match_score, 1),
            'keyword_match_score': round(self.keyword_match_score, 1),
            'matched_skills': list(self.matched_skills),
            'missing_skills': list(self.missing_skills),
            'matched_keywords': list(self.matched_keywords),
            'job_url': self.job.job_url,
        }

    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            f"Job: {self.job.title} at {self.job.company}",
            f"Overall Match: {self.overall_score:.1f}%",
            f"Skills Match: {self.skill_match_score:.1f}%",
            f"Keywords Match: {self.keyword_match_score:.1f}%",
        ]

        if self.matched_skills:
            lines.append(f"Matched Skills: {', '.join(sorted(self.matched_skills)[:5])}")

        if self.missing_skills:
            lines.append(f"Missing Skills: {', '.join(sorted(self.missing_skills)[:5])}")

        return "\n".join(lines)


class JobMatcher:
    """
    Match candidate profiles against job postings.

    Examples:
        >>> matcher = JobMatcher(candidate_skills=['python', 'django', 'aws'])
        >>> scores = matcher.score_jobs(job_results)
        >>> top_jobs = matcher.get_top_matches(job_results, n=10)
    """

    def __init__(
        self,
        candidate_skills: Optional[List[str]] = None,
        candidate_keywords: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        preferred_locations: Optional[List[str]] = None,
        remote_only: bool = False,
    ):
        """
        Initialize job matcher with candidate profile.

        Args:
            candidate_skills: List of candidate's skills
            candidate_keywords: List of keywords from candidate's experience
            required_skills: Skills that must be present in job
            min_salary: Minimum acceptable salary
            max_salary: Maximum acceptable salary
            preferred_locations: List of preferred location strings
            remote_only: Only match remote jobs
        """
        self.candidate_skills = set(s.lower() for s in (candidate_skills or []))
        self.candidate_keywords = set(k.lower() for k in (candidate_keywords or []))
        self.required_skills = set(s.lower() for s in (required_skills or []))
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.preferred_locations = [loc.lower() for loc in (preferred_locations or [])]
        self.remote_only = remote_only

    def score_job(self, job: JobResult) -> MatchScore:
        """
        Score a single job against candidate profile.

        Args:
            job: JobResult to score

        Returns:
            MatchScore object
        """
        analyzer = JobAnalyzer(job)

        # Extract job requirements
        job_skills = analyzer.extract_skills()
        job_keywords = set(analyzer.extract_keywords())

        # Calculate skill match
        matched_skills = self.candidate_skills & job_skills
        missing_skills = job_skills - self.candidate_skills

        if job_skills:
            skill_match_score = (len(matched_skills) / len(job_skills)) * 100
        else:
            skill_match_score = 50.0  # Neutral if no skills specified

        # Calculate keyword match
        matched_keywords = self.candidate_keywords & job_keywords

        if job_keywords:
            keyword_match_score = (len(matched_keywords) / len(job_keywords)) * 100
        else:
            keyword_match_score = 50.0

        # Check compensation match
        compensation_match = None
        if job.compensation and (self.min_salary or self.max_salary):
            job_min = job.compensation.min_amount
            job_max = job.compensation.max_amount

            if job_max and self.min_salary:
                compensation_match = job_max >= self.min_salary
            if job_min and self.max_salary:
                compensation_match = (compensation_match is not False) and (job_min <= self.max_salary)

        # Check location match
        location_match = None
        if self.remote_only:
            location_match = job.is_remote == True
        elif self.preferred_locations and job.location:
            job_loc_str = (job.location.raw or '').lower()
            location_match = any(pref in job_loc_str for pref in self.preferred_locations)

        # Calculate overall score
        # Weight: 60% skills, 30% keywords, 10% other factors
        overall_score = skill_match_score * 0.6 + keyword_match_score * 0.3

        # Bonus points for matching preferences
        if compensation_match:
            overall_score += 5
        if location_match:
            overall_score += 5

        # Penalty for missing required skills
        if self.required_skills:
            missing_required = self.required_skills - matched_skills
            if missing_required:
                # Severe penalty for missing required skills
                overall_score *= (1 - len(missing_required) / max(len(self.required_skills), 1))

        # Cap at 100
        overall_score = min(overall_score, 100.0)

        return MatchScore(
            job=job,
            overall_score=overall_score,
            skill_match_score=skill_match_score,
            keyword_match_score=keyword_match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            compensation_match=compensation_match,
            location_match=location_match,
        )

    def score_jobs(self, jobs: List[JobResult]) -> List[MatchScore]:
        """
        Score multiple jobs.

        Args:
            jobs: List of JobResult objects

        Returns:
            List of MatchScore objects
        """
        return [self.score_job(job) for job in jobs]

    def get_top_matches(
        self,
        jobs: List[JobResult],
        n: int = 10,
        min_score: float = 0.0
    ) -> List[MatchScore]:
        """
        Get top N job matches sorted by score.

        Args:
            jobs: List of JobResult objects
            n: Number of top matches to return
            min_score: Minimum score threshold (0-100)

        Returns:
            List of MatchScore objects sorted by overall_score descending
        """
        scores = self.score_jobs(jobs)
        filtered = [s for s in scores if s.overall_score >= min_score]
        sorted_scores = sorted(filtered, key=lambda x: x.overall_score, reverse=True)
        return sorted_scores[:n]

    def filter_jobs(
        self,
        jobs: List[JobResult],
        min_score: float = 50.0
    ) -> List[JobResult]:
        """
        Filter jobs that meet minimum score threshold.

        Args:
            jobs: List of JobResult objects
            min_score: Minimum score threshold (0-100)

        Returns:
            List of JobResult objects that meet threshold
        """
        scores = self.score_jobs(jobs)
        return [s.job for s in scores if s.overall_score >= min_score]

    def identify_skill_gaps(self, jobs: List[JobResult]) -> Dict[str, int]:
        """
        Identify skills frequently requested but not possessed by candidate.

        Args:
            jobs: List of JobResult objects to analyze

        Returns:
            Dictionary of {skill: frequency} for missing skills
        """
        skill_frequency = {}

        for job in jobs:
            analyzer = JobAnalyzer(job)
            job_skills = analyzer.extract_skills()
            missing = job_skills - self.candidate_skills

            for skill in missing:
                skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

        # Sort by frequency
        return dict(sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True))

    def get_recommendations(self, jobs: List[JobResult], top_n: int = 5) -> str:
        """
        Get human-readable recommendations based on job matches.

        Args:
            jobs: List of JobResult objects
            top_n: Number of top jobs to include in recommendations

        Returns:
            Formatted recommendation string
        """
        if not jobs:
            return "No jobs to analyze."

        top_matches = self.get_top_matches(jobs, n=top_n)
        skill_gaps = self.identify_skill_gaps(jobs)

        lines = [
            "Job Match Recommendations",
            "=" * 50,
            "",
            f"Analyzed {len(jobs)} jobs",
            f"Average match score: {sum(s.overall_score for s in self.score_jobs(jobs)) / len(jobs):.1f}%",
            "",
            f"Top {len(top_matches)} Matches:",
            "-" * 50,
        ]

        for i, match in enumerate(top_matches, 1):
            lines.append(f"\n{i}. {match.job.title} at {match.job.company}")
            lines.append(f"   Score: {match.overall_score:.1f}%")
            if match.job.job_url:
                lines.append(f"   URL: {match.job.job_url}")

        if skill_gaps:
            lines.extend([
                "",
                "",
                "Skills to Consider Learning:",
                "-" * 50,
            ])

            for skill, freq in list(skill_gaps.items())[:10]:
                pct = (freq / len(jobs)) * 100
                lines.append(f"- {skill}: appears in {freq} jobs ({pct:.1f}%)")

        return "\n".join(lines)


def quick_match(
    candidate_skills: List[str],
    jobs: List[JobResult],
    top_n: int = 10
) -> List[MatchScore]:
    """
    Quick utility function to match jobs against candidate skills.

    Args:
        candidate_skills: List of candidate's skills
        jobs: List of JobResult objects
        top_n: Number of top matches to return

    Returns:
        List of top MatchScore objects

    Examples:
        >>> from hired import JobSources, SearchCriteria
        >>> from hired.matching import quick_match
        >>>
        >>> sources = JobSources()
        >>> jobs = sources.jobspy.search(SearchCriteria(query="python developer"))
        >>>
        >>> matches = quick_match(
        ...     candidate_skills=['python', 'django', 'postgresql'],
        ...     jobs=jobs,
        ...     top_n=5
        ... )
        >>>
        >>> for match in matches:
        ...     print(match.get_summary())
    """
    matcher = JobMatcher(candidate_skills=candidate_skills)
    return matcher.get_top_matches(jobs, n=top_n)
