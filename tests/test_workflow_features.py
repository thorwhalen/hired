"""
Tests for workflow features: matching, ATS checking, cover letters, and tracking.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from hired.search.base import JobResult, LocationInfo, CompensationInfo
from hired.job_utils import JobAnalyzer, job_to_text, extract_job_keywords
from hired.matching import JobMatcher, MatchScore, quick_match
from hired.ats_checker import ATSChecker, check_resume_ats
from hired.cover_letter import mk_cover_letter, generate_cover_letter_content
from hired.tracking import ApplicationTracker, Application


# Test fixtures

@pytest.fixture
def sample_job():
    """Create a sample JobResult for testing."""
    return JobResult(
        title="Senior Python Developer",
        source="test",
        company="TechCorp",
        job_url="https://example.com/job",
        description="We are looking for an experienced Python developer with Django and PostgreSQL experience. "
                   "Must have 5+ years of experience. Knowledge of Docker and AWS is a plus.",
        location=LocationInfo(city="San Francisco", state="CA", country="US"),
        is_remote=True,
        compensation=CompensationInfo(min_amount=120000, max_amount=160000, currency="USD", interval="yearly"),
        skills=["Python", "Django", "PostgreSQL", "Docker"],
    )


@pytest.fixture
def sample_resume():
    """Create a sample resume dict for testing."""
    return {
        'basics': {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '555-1234',
            'summary': 'Experienced software engineer',
        },
        'work': [
            {
                'company': 'Previous Corp',
                'position': 'Software Engineer',
                'startDate': '2020-01-01',
                'endDate': '2024-01-01',
                'summary': 'Developed backend systems',
                'highlights': [
                    'Built API serving 1M requests/day',
                    'Improved performance by 40%'
                ]
            }
        ],
        'skills': [
            {'name': 'Python', 'keywords': ['Django', 'Flask']},
            {'name': 'Databases', 'keywords': ['PostgreSQL', 'MySQL']},
        ],
        'education': [
            {
                'institution': 'University',
                'area': 'Computer Science',
                'studyType': 'Bachelor'
            }
        ]
    }


# JobAnalyzer Tests

class TestJobAnalyzer:
    def test_extract_skills(self, sample_job):
        analyzer = JobAnalyzer(sample_job)
        skills = analyzer.extract_skills()

        assert 'python' in skills
        assert 'django' in skills
        assert 'postgresql' in skills
        assert 'docker' in skills

    def test_extract_requirements(self, sample_job):
        analyzer = JobAnalyzer(sample_job)
        requirements = analyzer.extract_requirements()

        # Should find years of experience
        assert any('5' in req and 'years' in req.lower() for req in requirements)

    def test_extract_keywords(self, sample_job):
        analyzer = JobAnalyzer(sample_job)
        keywords = analyzer.extract_keywords(top_n=10)

        assert isinstance(keywords, list)
        assert len(keywords) <= 10
        assert 'developer' in keywords or 'python' in keywords

    def test_to_job_info_text(self, sample_job):
        analyzer = JobAnalyzer(sample_job)
        text = analyzer.to_job_info_text()

        assert "Senior Python Developer" in text
        assert "TechCorp" in text
        assert "San Francisco" in text

    def test_job_to_text_function(self, sample_job):
        text = job_to_text(sample_job)
        assert "Senior Python Developer" in text
        assert "TechCorp" in text


# JobMatcher Tests

class TestJobMatcher:
    def test_score_job(self, sample_job):
        matcher = JobMatcher(
            candidate_skills=['python', 'django', 'postgresql'],
        )

        score = matcher.score_job(sample_job)

        assert isinstance(score, MatchScore)
        assert 0 <= score.overall_score <= 100
        assert 'python' in score.matched_skills
        assert 'django' in score.matched_skills

    def test_get_top_matches(self, sample_job):
        jobs = [sample_job]
        matcher = JobMatcher(candidate_skills=['python', 'django'])

        matches = matcher.get_top_matches(jobs, n=5)

        assert len(matches) <= 5
        assert all(isinstance(m, MatchScore) for m in matches)

    def test_filter_jobs(self, sample_job):
        jobs = [sample_job]
        matcher = JobMatcher(candidate_skills=['python'])

        filtered = matcher.filter_jobs(jobs, min_score=50.0)

        assert isinstance(filtered, list)

    def test_identify_skill_gaps(self, sample_job):
        jobs = [sample_job]
        matcher = JobMatcher(candidate_skills=['python'])

        gaps = matcher.identify_skill_gaps(jobs)

        assert isinstance(gaps, dict)
        # Should identify missing skills
        assert 'docker' in gaps or 'postgresql' in gaps

    def test_quick_match(self, sample_job):
        jobs = [sample_job]
        matches = quick_match(['python', 'django'], jobs, top_n=5)

        assert isinstance(matches, list)
        assert all(isinstance(m, MatchScore) for m in matches)


# ATSChecker Tests

class TestATSChecker:
    def test_check_resume(self, sample_resume):
        checker = ATSChecker()
        report = checker.check_resume(sample_resume)

        assert 0 <= report.overall_score <= 100
        assert isinstance(report.issues, list)

    def test_check_resume_with_job(self, sample_resume, sample_job):
        checker = ATSChecker()
        report = checker.check_resume(sample_resume, job=sample_job)

        assert 0 <= report.overall_score <= 100
        assert 0 <= report.keyword_match_score <= 100
        assert isinstance(report.matched_keywords, set)
        assert isinstance(report.missing_keywords, set)

    def test_check_resume_ats_function(self, sample_resume, sample_job):
        report = check_resume_ats(sample_resume, sample_job)

        assert isinstance(report.overall_score, float)
        assert hasattr(report, 'issues')

    def test_report_summary(self, sample_resume):
        checker = ATSChecker()
        report = checker.check_resume(sample_resume)

        summary = report.get_summary()
        assert isinstance(summary, str)
        assert "ATS Compatibility Report" in summary

    def test_report_to_dict(self, sample_resume):
        checker = ATSChecker()
        report = checker.check_resume(sample_resume)

        data = report.to_dict()
        assert 'overall_score' in data
        assert 'issues' in data
        assert 'critical_count' in data


# CoverLetter Tests

class TestCoverLetter:
    def test_generate_cover_letter_content(self, sample_resume, sample_job):
        data = generate_cover_letter_content(sample_resume, sample_job)

        assert data.applicant_name == 'Jane Doe'
        assert data.applicant_email == 'jane@example.com'
        assert data.company_name == 'TechCorp'
        assert data.position_title == 'Senior Python Developer'
        assert len(data.opening_paragraph) > 0
        assert len(data.body_paragraphs) > 0
        assert len(data.closing_paragraph) > 0

    def test_mk_cover_letter_text(self, sample_resume, sample_job):
        letter = mk_cover_letter(
            sample_resume,
            sample_job,
            format='text'
        )

        assert isinstance(letter, str)
        assert 'Jane Doe' in letter
        assert 'TechCorp' in letter
        assert 'Senior Python Developer' in letter

    def test_mk_cover_letter_html(self, sample_resume, sample_job):
        letter = mk_cover_letter(
            sample_resume,
            sample_job,
            format='html'
        )

        assert isinstance(letter, str)
        assert '<html>' in letter.lower()
        assert 'Jane Doe' in letter

    def test_mk_cover_letter_markdown(self, sample_resume, sample_job):
        letter = mk_cover_letter(
            sample_resume,
            sample_job,
            format='markdown'
        )

        assert isinstance(letter, str)
        assert '#' in letter
        assert 'Jane Doe' in letter

    def test_cover_letter_tones(self, sample_resume, sample_job):
        for tone in ['professional', 'enthusiastic', 'formal']:
            letter = mk_cover_letter(
                sample_resume,
                sample_job,
                tone=tone,
                format='text'
            )
            assert isinstance(letter, str)
            assert len(letter) > 100


# ApplicationTracker Tests

class TestApplicationTracker:
    @pytest.fixture
    def tracker(self):
        """Create a temporary tracker for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield ApplicationTracker(db_path=db_path)

    def test_add_application(self, tracker, sample_job):
        app_id = tracker.add_application(
            job=sample_job,
            resume_path="resume.pdf",
            status="applied"
        )

        assert isinstance(app_id, int)
        assert app_id > 0

    def test_add_application_manual(self, tracker):
        app_id = tracker.add_application(
            job_title="Software Engineer",
            company="TestCorp",
            status="draft"
        )

        assert isinstance(app_id, int)

    def test_get_application(self, tracker, sample_job):
        app_id = tracker.add_application(job=sample_job)
        app = tracker.get_application(app_id)

        assert app is not None
        assert app.job_title == sample_job.title
        assert app.company == sample_job.company

    def test_get_applications(self, tracker, sample_job):
        tracker.add_application(job=sample_job, status="applied")
        tracker.add_application(
            job_title="Another Job",
            company="Another Corp",
            status="interview"
        )

        all_apps = tracker.get_applications()
        assert len(all_apps) == 2

        applied = tracker.get_applications(status="applied")
        assert len(applied) == 1
        assert applied[0].status == "applied"

    def test_update_status(self, tracker, sample_job):
        app_id = tracker.add_application(job=sample_job, status="draft")

        success = tracker.update_status(app_id, "applied", notes="Submitted via website")
        assert success

        app = tracker.get_application(app_id)
        assert app.status == "applied"
        assert "Submitted via website" in app.notes

    def test_update_application(self, tracker, sample_job):
        app_id = tracker.add_application(job=sample_job)

        success = tracker.update_application(
            app_id,
            follow_up_date="2025-01-15",
            notes="Need to follow up"
        )
        assert success

        app = tracker.get_application(app_id)
        assert app.follow_up_date == "2025-01-15"

    def test_delete_application(self, tracker, sample_job):
        app_id = tracker.add_application(job=sample_job)

        success = tracker.delete_application(app_id)
        assert success

        app = tracker.get_application(app_id)
        assert app is None

    def test_get_statistics(self, tracker, sample_job):
        tracker.add_application(job=sample_job, status="applied")
        tracker.add_application(
            job_title="Job 2",
            company="Corp 2",
            status="interview"
        )

        stats = tracker.get_statistics()

        assert stats['total_applications'] == 2
        assert 'by_status' in stats
        assert 'applied' in stats['by_status']
        assert stats['by_status']['applied'] == 1

    def test_application_from_job_result(self, sample_job):
        app = Application.from_job_result(sample_job, status="applied")

        assert app.job_title == sample_job.title
        assert app.company == sample_job.company
        assert app.status == "applied"
        assert app.source == sample_job.source


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
