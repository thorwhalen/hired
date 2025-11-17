
# Complete Job Application Workflow - New Features

This document covers the Phase 1 and Phase 2 features that complete the job application workflow in the `hired` package.

## Table of Contents

1. [Overview](#overview)
2. [Job-to-Resume Integration](#job-to-resume-integration)
3. [Job Matching & Scoring](#job-matching--scoring)
4. [ATS Compatibility Checker](#ats-compatibility-checker)
5. [Cover Letter Generation](#cover-letter-generation)
6. [Application Tracker](#application-tracker)
7. [Complete Workflow Examples](#complete-workflow-examples)

## Overview

The hired package now provides a complete end-to-end workflow for job seekers:

1. **Search** for jobs across multiple sources
2. **Match & Score** jobs against your profile
3. **Tailor** resume to specific job postings
4. **Check** ATS compatibility
5. **Generate** cover letters
6. **Track** applications and follow-ups

## Job-to-Resume Integration

### Direct JobResult to Resume

You can now pass `JobResult` objects directly to `mk_content_for_resume`:

```python
from hired import JobSources, SearchCriteria, mk_content_for_resume, mk_resume

# Search for jobs
sources = JobSources()
jobs = sources.jobspy.search(SearchCriteria(query="python developer", location="SF"))

# Generate resume tailored to specific job
top_job = jobs[0]
resume_content = mk_content_for_resume(
    candidate_info=candidate_dict,
    job_info=top_job  # Pass JobResult directly!
)

# Render to PDF
pdf = mk_resume(resume_content, output_path="resume_tailored.pdf")
```

### Job Analysis

Extract key information from job postings:

```python
from hired import JobAnalyzer, extract_job_keywords, get_job_skills

# Analyze a job posting
analyzer = JobAnalyzer(job_result)

# Get required skills
skills = analyzer.extract_skills()
print(f"Required skills: {skills}")

# Get job requirements
requirements = analyzer.extract_requirements()
for req in requirements:
    print(f"- {req}")

# Get keywords for ATS optimization
keywords = analyzer.extract_keywords(top_n=20)

# Convert to formatted text
job_text = analyzer.to_job_info_text()
```

## Job Matching & Scoring

### Score Jobs Against Your Profile

Match jobs to your skills and experience:

```python
from hired import JobMatcher, quick_match

# Create matcher with your profile
matcher = JobMatcher(
    candidate_skills=['python', 'django', 'postgresql', 'docker', 'aws'],
    candidate_keywords=['backend', 'api', 'microservices'],
    min_salary=100000,
    preferred_locations=['San Francisco', 'Remote'],
    remote_only=False
)

# Score all jobs
matches = matcher.get_top_matches(jobs, n=10, min_score=60.0)

# View results
for match in matches:
    print(f"\n{match.job.title} at {match.job.company}")
    print(f"Overall Score: {match.overall_score:.1f}%")
    print(f"Matched Skills: {', '.join(match.matched_skills)}")
    print(f"Missing Skills: {', '.join(match.missing_skills)}")
```

### Quick Matching

For simple use cases:

```python
from hired import quick_match

# Quick match without creating matcher
matches = quick_match(
    candidate_skills=['python', 'django', 'react'],
    jobs=jobs,
    top_n=5
)

for match in matches:
    print(match.get_summary())
```

### Identify Skill Gaps

See what skills are frequently requested:

```python
# Find skills you're missing
skill_gaps = matcher.identify_skill_gaps(jobs)

print("Skills to consider learning:")
for skill, frequency in list(skill_gaps.items())[:10]:
    pct = (frequency / len(jobs)) * 100
    print(f"- {skill}: appears in {pct:.1f}% of jobs")
```

### Get Recommendations

```python
# Get comprehensive recommendations
recommendations = matcher.get_recommendations(jobs, top_n=5)
print(recommendations)
```

## ATS Compatibility Checker

### Check Resume ATS Compatibility

Ensure your resume passes Applicant Tracking Systems:

```python
from hired import check_resume_ats, ATSChecker

# Quick check
resume_dict = resume_content.model_dump()
report = check_resume_ats(resume_dict, job_result)

print(report.get_summary())
print(f"Overall Score: {report.overall_score}/100")
print(f"Keyword Match: {report.keyword_match_score}%")
```

### Detailed ATS Analysis

```python
# Create checker for multiple checks
checker = ATSChecker()

# Check against specific job
report = checker.check_resume(resume_dict, job=job_result)

# Get critical issues
critical_issues = report.get_critical_issues()
for issue in critical_issues:
    print(f"\n{issue.title}")
    print(f"  {issue.description}")
    print(f"  Suggestion: {issue.suggestion}")

# Get missing keywords
if report.missing_keywords:
    print("\nImportant missing keywords:")
    for keyword in list(report.missing_keywords)[:10]:
        print(f"  - {keyword}")
```

### Report Format

```python
# Export report as dictionary
report_data = report.to_dict()

# Includes:
# - overall_score
# - keyword_match_score
# - matched_keywords
# - missing_keywords
# - issues (with categories: critical, warning, info)
# - critical_count
# - warning_count
```

## Cover Letter Generation

### Generate Cover Letters

Create professional cover letters tailored to job postings:

```python
from hired import mk_cover_letter

# From JobResult
letter_html = mk_cover_letter(
    candidate_info=candidate_dict,
    job_info=job_result,
    tone="professional",  # or "enthusiastic", "formal"
    format="html",
    output_path="cover_letter.html"
)

# From manual job info
letter_text = mk_cover_letter(
    candidate_info={'basics': {
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'phone': '555-1234'
    }},
    job_info={
        'title': 'Senior Software Engineer',
        'company': 'TechCorp'
    },
    format="text"
)
```

### Cover Letter Formats

Supported formats:
- **text**: Plain text (default)
- **html**: HTML with professional styling
- **markdown**: Markdown format

### Custom Tone

Choose the tone that fits the company culture:

- **professional**: Balanced and polished (default)
- **enthusiastic**: Energetic and passionate
- **formal**: Traditional and conservative

### Advanced Usage

```python
from hired import generate_cover_letter_content, render_cover_letter

# Generate content separately
cover_data = generate_cover_letter_content(
    candidate_info=candidate_dict,
    job_info=job_result,
    tone="professional"
)

# Customize the content
cover_data.opening_paragraph = "Custom opening..."
cover_data.body_paragraphs.append("Additional paragraph...")

# Render with custom template
custom_template = """
{{ applicant_name }}
{{ applicant_email }}

Dear {{ hiring_manager_name or 'Hiring Manager' }},

{{ opening_paragraph }}
...
"""

letter = render_cover_letter(cover_data, template=custom_template)
```

## Application Tracker

### Track Your Applications

Manage all your job applications in one place:

```python
from hired import ApplicationTracker

# Create tracker (uses SQLite database)
tracker = ApplicationTracker()  # Default: ~/.hired/applications.db

# Or specify custom location
tracker = ApplicationTracker(db_path="/path/to/my/applications.db")
```

### Add Applications

```python
# From JobResult
app_id = tracker.add_application(
    job=job_result,
    resume_path="resume_techcorp.pdf",
    cover_letter_path="cover_letter_techcorp.pdf",
    status="applied",
    notes="Applied via company website"
)

# Manual entry
app_id = tracker.add_application(
    job_title="Software Engineer",
    company="StartupCo",
    job_url="https://...",
    location="San Francisco, CA",
    salary_range="$120k - $160k",
    status="draft"
)

# With match score from JobMatcher
match = matcher.score_job(job_result)
app_id = tracker.add_application(
    job=job_result,
    match_score=match.overall_score,
    status="interested"
)
```

### Update Applications

```python
# Update status
tracker.update_status(app_id, "interview", notes="Phone screen scheduled for Friday")

# Update any field
tracker.update_application(
    app_id,
    follow_up_date="2025-01-15",
    last_contact_date="2025-01-08",
    notes="Sent thank you email"
)
```

### Query Applications

```python
# Get all applications
all_apps = tracker.get_applications()

# Filter by status
interviews = tracker.get_applications(status="interview")
offers = tracker.get_applications(status="offer")

# Filter by company
techcorp_apps = tracker.get_applications(company="TechCorp")

# Get specific application
app = tracker.get_application(app_id)
print(f"{app.job_title} at {app.company}: {app.status}")
```

### Application Statuses

Built-in statuses:
- `draft`: Still preparing application
- `applied`: Application submitted
- `interview`: Interview stage
- `offer`: Offer received
- `accepted`: Offer accepted
- `rejected`: Application rejected
- `withdrawn`: Application withdrawn

### Follow-ups

```python
# Set follow-up reminder
from datetime import datetime, timedelta

follow_up_date = (datetime.now() + timedelta(days=7)).isoformat()
tracker.update_application(app_id, follow_up_date=follow_up_date)

# Get applications needing follow-up
due_follow_ups = tracker.get_follow_ups_due(days=7)

for app in due_follow_ups:
    print(f"Follow up with {app.company} for {app.job_title}")
    print(f"  Due: {app.follow_up_date}")
```

### Statistics & Analytics

```python
# Get statistics
stats = tracker.get_statistics()

print(f"Total Applications: {stats['total_applications']}")
print(f"Response Rate: {stats['response_rate']}%")
print(f"Avg Days to Response: {stats['avg_days_to_response']}")

print("\nBy Status:")
for status, count in stats['by_status'].items():
    print(f"  {status}: {count}")
```

### Export Data

```python
# Export to CSV
tracker.export_to_csv("my_applications.csv")
```

### Delete Applications

```python
# Delete an application
tracker.delete_application(app_id)
```

## Complete Workflow Examples

### Example 1: Full Application Workflow

```python
from hired import (
    JobSources, SearchCriteria, JobMatcher,
    mk_content_for_resume, mk_resume, check_resume_ats,
    mk_cover_letter, ApplicationTracker
)

# 1. Search for jobs
sources = JobSources()
jobs = sources.search_all(SearchCriteria(
    query="senior python developer",
    location="San Francisco, CA",
    is_remote=True,
    results_wanted=50
))

print(f"Found {len(jobs)} jobs")

# 2. Match jobs to your profile
matcher = JobMatcher(
    candidate_skills=['python', 'django', 'postgresql', 'docker', 'kubernetes'],
    min_salary=120000
)

top_matches = matcher.get_top_matches(jobs, n=10, min_score=70.0)
print(f"Top {len(top_matches)} matches identified")

# 3. Generate tailored resume for top match
candidate_info = {
    'basics': {
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'phone': '555-1234'
    },
    'work': [...],  # Your work experience
    'skills': [...]  # Your skills
}

top_job = top_matches[0].job

resume_content = mk_content_for_resume(
    candidate_info=candidate_info,
    job_info=top_job
)

# 4. Check ATS compatibility
ats_report = check_resume_ats(resume_content.model_dump(), top_job)
print(f"ATS Score: {ats_report.overall_score}/100")

if ats_report.overall_score < 70:
    print("Warning: Low ATS score!")
    for issue in ats_report.get_critical_issues():
        print(f"  - {issue.title}")

# 5. Generate resume PDF
resume_pdf = mk_resume(resume_content, output_path="resume.pdf")

# 6. Generate cover letter
cover_letter = mk_cover_letter(
    candidate_info=candidate_info,
    job_info=top_job,
    format="html",
    output_path="cover_letter.html"
)

# 7. Track the application
tracker = ApplicationTracker()
app_id = tracker.add_application(
    job=top_job,
    resume_path="resume.pdf",
    cover_letter_path="cover_letter.html",
    match_score=top_matches[0].overall_score,
    status="draft",
    notes="High-priority application - great match!"
)

print(f"Application tracked with ID: {app_id}")

# 8. Mark as applied when submitted
tracker.update_status(app_id, "applied", notes="Applied via company website")

# 9. Set follow-up reminder
from datetime import datetime, timedelta
follow_up = (datetime.now() + timedelta(days=7)).isoformat()
tracker.update_application(app_id, follow_up_date=follow_up)

print("✓ Application complete and tracked!")
```

### Example 2: Batch Processing Multiple Applications

```python
from hired import (
    JobSources, SearchCriteria, JobMatcher,
    mk_content_for_resume, mk_resume,
    mk_cover_letter, ApplicationTracker
)

# Search and match
sources = JobSources()
jobs = sources.search_all(SearchCriteria(query="python developer"))

matcher = JobMatcher(candidate_skills=['python', 'django', 'react'])
top_matches = matcher.get_top_matches(jobs, n=5, min_score=70.0)

# Batch process applications
tracker = ApplicationTracker()

for i, match in enumerate(top_matches):
    job = match.job
    print(f"\n{i+1}. Processing: {job.title} at {job.company}")

    # Generate tailored resume
    resume = mk_content_for_resume(candidate_info, job)
    resume_path = f"resume_{job.company.replace(' ', '_')}.pdf"
    mk_resume(resume, output_path=resume_path)

    # Generate cover letter
    letter_path = f"cover_letter_{job.company.replace(' ', '_')}.html"
    mk_cover_letter(candidate_info, job, format="html", output_path=letter_path)

    # Track application
    app_id = tracker.add_application(
        job=job,
        resume_path=resume_path,
        cover_letter_path=letter_path,
        match_score=match.overall_score,
        status="draft"
    )

    print(f"  ✓ Resume: {resume_path}")
    print(f"  ✓ Cover Letter: {letter_path}")
    print(f"  ✓ Tracked: Application #{app_id}")

print("\n✓ Batch processing complete!")
```

### Example 3: Weekly Follow-up Routine

```python
from hired import ApplicationTracker

tracker = ApplicationTracker()

# Check applications needing follow-up
follow_ups = tracker.get_follow_ups_due(days=7)

print(f"You have {len(follow_ups)} applications needing follow-up:\n")

for app in follow_ups:
    print(f"• {app.job_title} at {app.company}")
    print(f"  Status: {app.status}")
    print(f"  Follow-up due: {app.follow_up_date}")
    print(f"  Last contact: {app.last_contact_date or 'Never'}")

    if app.job_url:
        print(f"  URL: {app.job_url}")

    print()

# Get weekly statistics
stats = tracker.get_statistics()
print(f"\nYour job search stats:")
print(f"  Total applications: {stats['total_applications']}")
print(f"  In progress: {stats['by_status'].get('applied', 0) + stats['by_status'].get('interview', 0)}")
print(f"  Response rate: {stats['response_rate']}%")
```

## Integration with Resume Agent

These features integrate seamlessly with the existing resume agent:

```python
from hired.resume_agent import ResumeSession, ResumeExpertAgent, LLMConfig
from hired import JobSources, SearchCriteria, ApplicationTracker

# Search for jobs
sources = JobSources()
jobs = sources.jobspy.search(SearchCriteria(query="ML engineer"))

# Use AI agent to create resume for specific job
job = jobs[0]
llm_config = LLMConfig(model="gpt-4")

session = ResumeSession(
    job_info=job.description,  # Use job description
    candidate_info=candidate_text,
    llm_config=llm_config
)

# Let agent create resume
agent = ResumeExpertAgent(llm_config=llm_config)
final_resume = agent.create_resume(session)

# Track the application
tracker = ApplicationTracker()
tracker.add_application(job=job, status="draft")
```

## Tips and Best Practices

### Resume Tailoring
1. Always use `check_resume_ats()` before submitting
2. Aim for ATS score > 80%
3. Include keywords from job posting
4. Quantify achievements with numbers

### Job Matching
1. Set realistic `min_score` threshold (60-70%)
2. Use `identify_skill_gaps()` to guide learning
3. Update your `candidate_skills` as you learn
4. Consider both technical and soft skills

### Application Tracking
1. Track applications immediately when found
2. Set follow-up reminders (7-10 days)
3. Add detailed notes about contacts and conversations
4. Review statistics weekly to optimize strategy
5. Export data regularly for backup

### Cover Letters
1. Use different tones for different companies
2. Customize the generated content before sending
3. Keep it concise (3-4 paragraphs)
4. Always proofread before sending

## Support

For issues or questions:
- GitHub: https://github.com/thorwhalen/hired
- Documentation: See package documentation

## License

MIT License - See LICENSE file for details
