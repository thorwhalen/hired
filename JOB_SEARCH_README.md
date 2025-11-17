# Job Search Integration

The `hired` package now includes comprehensive job search functionality, allowing you to search for jobs across multiple sources using a unified interface.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Available Sources](#available-sources)
- [Search Criteria](#search-criteria)
- [Usage Examples](#usage-examples)
- [Setting Up API Sources](#setting-up-api-sources)
- [Advanced Usage](#advanced-usage)
- [Extending with Custom Sources](#extending-with-custom-sources)

## Installation

### Basic Installation

```bash
pip install hired
```

This installs the core search functionality with support for USAJobs and Adzuna APIs.

### Full Installation (with JobSpy)

To include the JobSpy scraper for multi-source job searching:

```bash
pip install hired[search]
# or
pip install hired[all]
```

This adds support for scraping jobs from LinkedIn, Indeed, Glassdoor, ZipRecruiter, and Google.

## Quick Start

```python
from hired import JobSources, SearchCriteria

# Create the job sources interface
sources = JobSources()

# Check which sources are available
print(sources.list_available())

# Search for jobs
criteria = SearchCriteria(
    query="python developer",
    location="San Francisco, CA",
    results_wanted=20
)

# Search using JobSpy (if installed)
results = sources.jobspy.search(criteria)

# Or search across all configured sources
all_results = sources.search_all(criteria)

# Display results
for job in results:
    print(f"{job.title} at {job.company}")
    print(f"  Location: {job.location.raw if job.location else 'N/A'}")
    print(f"  URL: {job.job_url}")
    print()
```

## Available Sources

### 1. JobSpy (Multi-Source Scraper)

**Requires:** `pip install python-jobspy`

**Sources:** LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google

**Authentication:** None required

**Features:**
- Scrapes multiple job boards concurrently
- No API keys needed
- Free to use

**Limitations:**
- LinkedIn has rate limiting (~10 pages per IP)
- May be affected by site changes

### 2. USAJobs (US Government Jobs)

**Requires:** Free API key from [developer.usajobs.gov](https://developer.usajobs.gov/)

**Authentication:** API key + email

**Features:**
- Official US Government job postings
- Comprehensive federal job listings
- Reliable and well-documented API

**Setup:** See [USAJobs Setup](#usajobs-setup)

### 3. Adzuna (International Jobs)

**Requires:** Free API key from [developer.adzuna.com](https://developer.adzuna.com/)

**Authentication:** App ID + App Key

**Features:**
- International coverage (US, UK, CA, AU, DE, FR, etc.)
- Rich salary and company data
- Free tier with generous limits

**Setup:** See [Adzuna Setup](#adzuna-setup)

## Search Criteria

The `SearchCriteria` class provides a unified interface for searching across all sources:

```python
from hired import SearchCriteria, JobType

criteria = SearchCriteria(
    # Required
    query="software engineer",           # Free-form text query

    # Location (optional)
    location="New York, NY",              # General location string
    city="New York",                      # Specific city
    state="NY",                           # State/province
    country="US",                         # Country code
    distance_miles=25,                    # Search radius

    # Job type (optional)
    job_type=JobType.FULL_TIME,          # FULL_TIME, PART_TIME, CONTRACT, etc.
    is_remote=True,                       # Remote jobs only

    # Time filters (optional)
    posted_within_days=7,                 # Jobs posted in last N days

    # Pagination (optional)
    results_wanted=50,                    # Number of results
    offset=0,                             # Starting offset

    # Salary (optional)
    min_salary=80000,
    max_salary=150000,

    # Keywords (optional)
    keywords=["python", "docker"],        # Must include these
    exclude_keywords=["java"],            # Must not include these

    # Source-specific parameters (optional)
    source_params={
        "country": "uk",                  # For Adzuna
        "sites": ["indeed", "linkedin"]   # For JobSpy
    }
)
```

## Usage Examples

### Example 1: Search a Specific Source

```python
from hired import JobSources, SearchCriteria

sources = JobSources()

# Search Indeed via JobSpy
criteria = SearchCriteria(
    query="data scientist",
    location="Boston, MA",
    results_wanted=30,
    source_params={"sites": ["indeed"]}
)

results = sources.jobspy.search(criteria)
```

### Example 2: Search Multiple Sources

```python
from hired import JobSources, SearchCriteria

sources = JobSources()

criteria = SearchCriteria(
    query="machine learning engineer",
    location="Seattle, WA",
    posted_within_days=14,
    results_wanted=25
)

# Search all available sources
all_results = sources.search_all(criteria)

# Group by source
from collections import defaultdict
by_source = defaultdict(list)
for job in all_results:
    by_source[job.source].append(job)

for source, jobs in by_source.items():
    print(f"\n{source}: {len(jobs)} jobs")
```

### Example 3: Filter Remote Jobs

```python
from hired import JobSources, SearchCriteria, JobType

sources = JobSources()

criteria = SearchCriteria(
    query="frontend developer",
    is_remote=True,
    job_type=JobType.FULL_TIME,
    posted_within_days=7,
    results_wanted=50
)

results = sources.search_all(criteria)
remote_jobs = [job for job in results if job.is_remote]

print(f"Found {len(remote_jobs)} remote jobs")
```

### Example 4: Export to CSV

```python
from hired import JobSources, SearchCriteria
import csv

sources = JobSources()

criteria = SearchCriteria(
    query="product manager",
    location="San Francisco, CA",
    results_wanted=100
)

results = sources.search_all(criteria)

# Export to CSV
with open('jobs.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Company', 'Location', 'Salary', 'URL', 'Source'])

    for job in results:
        salary = ""
        if job.compensation:
            if job.compensation.min_amount and job.compensation.max_amount:
                salary = f"${job.compensation.min_amount:,.0f} - ${job.compensation.max_amount:,.0f}"

        location = job.location.raw if job.location else ""

        writer.writerow([
            job.title,
            job.company or "",
            location,
            salary,
            job.job_url or "",
            job.source
        ])

print(f"Exported {len(results)} jobs to jobs.csv")
```

### Example 5: Check Source Status

```python
from hired import JobSources

sources = JobSources()

# Print detailed status of all sources
sources.print_status()

# Output:
# Job Search Sources Status:
# ============================================================
#
# JobSpy (Multi-Source Scraper) (jobspy): ✓ Ready
#
# USAJobs (US Government) (usajobs): ✗ Needs Setup (requires auth)
#
# Setup instructions:
#   USAJobs Setup Instructions:
#   ...
```

## Setting Up API Sources

### USAJobs Setup

1. Visit [developer.usajobs.gov](https://developer.usajobs.gov/)
2. Click "Request API Key" and complete the form
3. You'll receive an API key via email
4. Set environment variables:

```bash
export USAJOBS_API_KEY="your-api-key"
export USAJOBS_EMAIL="your-email@example.com"
```

Or configure programmatically:

```python
from hired.search.sources.usajobs import USAJobsSource
from hired.search import register_source

# Create custom instance with credentials
usajobs = USAJobsSource(
    api_key="your-api-key",
    email="your-email@example.com"
)

# Register it (replaces default instance)
register_source(usajobs, USAJobsSource)
```

### Adzuna Setup

1. Visit [developer.adzuna.com](https://developer.adzuna.com/)
2. Sign up for a free account
3. You'll receive an `app_id` and `app_key`
4. Set environment variables:

```bash
export ADZUNA_APP_ID="your-app-id"
export ADZUNA_APP_KEY="your-app-key"
```

Or configure programmatically:

```python
from hired.search.sources.adzuna import AdzunaSource
from hired.search import register_source

# Create custom instance with credentials
adzuna = AdzunaSource(
    app_id="your-app-id",
    app_key="your-app-key",
    country="us"  # or "uk", "ca", "au", etc.
)

# Register it
register_source(adzuna, AdzunaSource)
```

## Advanced Usage

### Using Multiple JobSpy Sites

```python
from hired import JobSources, SearchCriteria

sources = JobSources()

criteria = SearchCriteria(
    query="devops engineer",
    location="Austin, TX",
    results_wanted=20,
    source_params={
        "sites": ["indeed", "linkedin", "glassdoor"]
    }
)

results = sources.jobspy.search(criteria)
```

### Using Proxies with JobSpy

For large-scale scraping, especially LinkedIn:

```python
from hired.search.sources.jobspy import JobSpySource
from hired.search import register_source

# Create instance with proxies
jobspy = JobSpySource(
    proxies=["user:pass@proxy1.com:8080", "user:pass@proxy2.com:8080"]
)

# Register it
register_source(jobspy, JobSpySource)
```

### Searching International Jobs with Adzuna

```python
from hired import JobSources, SearchCriteria

sources = JobSources()

# Search UK jobs
criteria = SearchCriteria(
    query="software developer",
    location="London",
    source_params={"country": "uk"}
)

uk_jobs = sources.adzuna.search(criteria)
```

### Accessing Individual Sources via Mapping Interface

```python
from hired import JobSources, SearchCriteria

sources = JobSources()

criteria = SearchCriteria(query="python developer")

# Access via attribute
results1 = sources.jobspy.search(criteria)

# Access via mapping (dict-like)
results2 = sources['jobspy'].search(criteria)

# Check if source exists
if 'usajobs' in sources:
    results3 = sources['usajobs'].search(criteria)

# Iterate over source names
for source_name in sources.keys():
    print(f"Available: {source_name}")
```

## Extending with Custom Sources

You can add your own job search sources by implementing the `JobSearchSource` interface:

```python
from typing import List
from hired.search import (
    JobSearchSource,
    JobResult,
    SearchCriteria,
    register_source,
    LocationInfo
)

class MyCustomSource(JobSearchSource):
    """Custom job search source."""

    @property
    def name(self) -> str:
        return "mycustom"

    @property
    def display_name(self) -> str:
        return "My Custom Job Board"

    @property
    def requires_auth(self) -> bool:
        return False

    def is_configured(self) -> bool:
        return True

    def get_setup_instructions(self) -> str:
        return "No setup required for My Custom Source."

    def search(self, criteria: SearchCriteria) -> List[JobResult]:
        # Implement your search logic here
        results = []

        # Example: fetch from your API
        # data = my_api.search(criteria.query, criteria.location)

        # Convert to JobResult objects
        # for item in data:
        #     results.append(JobResult(
        #         title=item['title'],
        #         source=self.name,
        #         company=item['company'],
        #         job_url=item['url'],
        #         location=LocationInfo(city=item['city'], state=item['state']),
        #         ...
        #     ))

        return results

# Register your custom source
custom_source = MyCustomSource()
register_source(custom_source, MyCustomSource)

# Now you can use it
from hired import JobSources, SearchCriteria

sources = JobSources()
results = sources.mycustom.search(SearchCriteria(query="developer"))
```

## API Reference

### JobSources

Main facade for accessing job sources.

**Methods:**
- `list()` - List all registered sources
- `list_available()` - List configured/ready sources
- `list_unconfigured()` - List sources needing setup
- `get_source(name)` - Get a specific source
- `search(source_name, criteria)` - Search using a specific source
- `search_all(criteria, sources=None, skip_unconfigured=True)` - Search across multiple sources
- `print_status()` - Print status of all sources

### SearchCriteria

Search parameters.

**Key Fields:**
- `query` (str, required) - Free-form search query
- `location` (str, optional) - Location string
- `job_type` (JobType, optional) - Type of job
- `is_remote` (bool, optional) - Remote jobs only
- `posted_within_days` (int, optional) - Recency filter
- `results_wanted` (int) - Number of results (default: 20)
- `min_salary` / `max_salary` (float, optional) - Salary range
- `source_params` (dict, optional) - Source-specific parameters

### JobResult

Standardized job result.

**Key Fields:**
- `title` (str) - Job title
- `source` (str) - Source name
- `company` (str) - Company name
- `job_url` (str) - Application URL
- `location` (LocationInfo) - Location details
- `is_remote` (bool) - Remote position flag
- `description` (str) - Job description
- `job_type` (JobType) - Job type
- `compensation` (CompensationInfo) - Salary info
- `date_posted` (datetime) - Posted date
- `application_deadline` (datetime) - Application deadline

**Methods:**
- `to_dict()` - Convert to dictionary

## Troubleshooting

### JobSpy Not Available

If you get an error about JobSpy not being installed:

```bash
pip install python-jobspy
```

### Rate Limiting (LinkedIn)

LinkedIn rate limits around the 10th page. Solutions:
- Use proxies
- Reduce `results_wanted`
- Focus on other sources (Indeed, Glassdoor)

### API Authentication Failures

If USAJobs or Adzuna fail to authenticate:
1. Verify your API keys are correct
2. Check environment variables are set
3. Try explicitly passing credentials
4. Review setup instructions: `sources.print_status()`

### No Results Returned

If searches return no results:
- Broaden your search query
- Remove location restrictions
- Increase `results_wanted`
- Try different sources
- Check if the source is configured: `sources.list_available()`

## Best Practices

1. **Start with JobSpy** - It's the easiest to set up (no API keys)
2. **Set up API sources** - For more reliable and comprehensive results
3. **Use `search_all()`** - Get maximum coverage
4. **Filter results** - Apply your own post-processing for best matches
5. **Respect rate limits** - Don't hammer APIs with rapid requests
6. **Cache results** - Save API calls by caching search results
7. **Verify links** - Job URLs may expire, check before applying

## Support

For issues, questions, or contributions:
- GitHub: [https://github.com/thorwhalen/hired](https://github.com/thorwhalen/hired)
- Documentation: See package documentation

## License

MIT License - See LICENSE file for details
