"""
Tests for job search functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from hired.search import (
    JobSources,
    SearchCriteria,
    JobResult,
    JobSearchSource,
    JobType,
    LocationInfo,
    CompensationInfo,
    SourceConfigError,
    get_registry,
    register_source,
)


class MockJobSource(JobSearchSource):
    """Mock job source for testing."""

    def __init__(self, name="mock", configured=True, results=None):
        self._name = name
        self._configured = configured
        self._results = results or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return f"Mock {self._name.capitalize()}"

    @property
    def requires_auth(self) -> bool:
        return not self._configured

    def is_configured(self) -> bool:
        return self._configured

    def get_setup_instructions(self) -> str:
        return f"Setup instructions for {self._name}"

    def search(self, criteria: SearchCriteria) -> list:
        self.validate_configured()
        return self._results


class TestSearchCriteria:
    """Tests for SearchCriteria class."""

    def test_create_basic_criteria(self):
        """Test creating basic search criteria."""
        criteria = SearchCriteria(query="python developer")

        assert criteria.query == "python developer"
        assert criteria.results_wanted == 20
        assert criteria.offset == 0
        assert criteria.location is None

    def test_create_full_criteria(self):
        """Test creating criteria with all options."""
        criteria = SearchCriteria(
            query="data scientist",
            location="New York, NY",
            city="New York",
            state="NY",
            country="US",
            job_type=JobType.FULL_TIME,
            is_remote=True,
            posted_within_days=7,
            results_wanted=50,
            min_salary=100000,
            keywords=["python", "ml"],
        )

        assert criteria.query == "data scientist"
        assert criteria.location == "New York, NY"
        assert criteria.city == "New York"
        assert criteria.job_type == JobType.FULL_TIME
        assert criteria.is_remote is True
        assert criteria.posted_within_days == 7
        assert criteria.results_wanted == 50
        assert criteria.min_salary == 100000
        assert "python" in criteria.keywords


class TestJobResult:
    """Tests for JobResult class."""

    def test_create_basic_result(self):
        """Test creating basic job result."""
        result = JobResult(
            title="Software Engineer",
            source="test"
        )

        assert result.title == "Software Engineer"
        assert result.source == "test"
        assert result.company is None

    def test_create_full_result(self):
        """Test creating result with all fields."""
        location = LocationInfo(
            city="San Francisco",
            state="CA",
            country="US"
        )
        compensation = CompensationInfo(
            min_amount=120000,
            max_amount=180000,
            currency="USD",
            interval="yearly"
        )

        result = JobResult(
            title="Senior Developer",
            source="test",
            company="TechCorp",
            company_url="https://techcorp.com",
            job_url="https://jobs.com/123",
            location=location,
            is_remote=True,
            description="Great job",
            job_type=JobType.FULL_TIME,
            compensation=compensation,
            date_posted=datetime(2025, 1, 1),
            skills=["Python", "Docker"],
        )

        assert result.title == "Senior Developer"
        assert result.company == "TechCorp"
        assert result.location.city == "San Francisco"
        assert result.compensation.min_amount == 120000
        assert result.is_remote is True
        assert "Python" in result.skills

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = JobResult(
            title="Test Job",
            source="test",
            company="Test Co",
            job_type=JobType.FULL_TIME,
        )

        data = result.to_dict()

        assert data['title'] == "Test Job"
        assert data['source'] == "test"
        assert data['company'] == "Test Co"
        assert data['job_type'] == "fulltime"


class TestSourceRegistry:
    """Tests for SourceRegistry."""

    def test_register_and_get_source(self):
        """Test registering and retrieving a source."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        source = MockJobSource(name="test1")

        registry.register(source)

        retrieved = registry.get("test1")
        assert retrieved.name == "test1"

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate source raises error."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        source1 = MockJobSource(name="test2")
        source2 = MockJobSource(name="test2")

        registry.register(source1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(source2)

    def test_get_nonexistent_source_raises_error(self):
        """Test that getting nonexistent source raises error."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_list_sources(self):
        """Test listing all sources."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        registry.register(MockJobSource(name="source1"))
        registry.register(MockJobSource(name="source2"))

        sources = registry.list_sources()

        assert "source1" in sources
        assert "source2" in sources
        assert len(sources) == 2

    def test_list_available_sources(self):
        """Test listing only configured sources."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        registry.register(MockJobSource(name="configured", configured=True))
        registry.register(MockJobSource(name="unconfigured", configured=False))

        available = registry.list_available_sources()

        assert "configured" in available
        assert "unconfigured" not in available

    def test_unregister_source(self):
        """Test unregistering a source."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        source = MockJobSource(name="test3")
        registry.register(source)

        assert "test3" in registry
        registry.unregister("test3")
        assert "test3" not in registry


class TestJobSources:
    """Tests for JobSources facade."""

    def test_create_job_sources(self):
        """Test creating JobSources instance."""
        sources = JobSources()
        assert sources is not None

    def test_list_sources(self):
        """Test listing sources."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        registry.register(MockJobSource(name="test4"))

        sources = JobSources(registry=registry)
        source_list = sources.list()

        assert "test4" in source_list

    def test_get_source_by_name(self):
        """Test getting source by name."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        mock_source = MockJobSource(name="test5")
        registry.register(mock_source)

        sources = JobSources(registry=registry)
        retrieved = sources.get_source("test5")

        assert retrieved.name == "test5"

    def test_get_source_by_attribute(self):
        """Test getting source via attribute access."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        mock_source = MockJobSource(name="test6")
        registry.register(mock_source)

        sources = JobSources(registry=registry)
        retrieved = sources.test6

        assert retrieved.name == "test6"

    def test_get_source_by_mapping(self):
        """Test getting source via mapping interface."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        mock_source = MockJobSource(name="test7")
        registry.register(mock_source)

        sources = JobSources(registry=registry)
        retrieved = sources['test7']

        assert retrieved.name == "test7"

    def test_search_specific_source(self):
        """Test searching with a specific source."""
        from hired.search.registry import SourceRegistry

        mock_results = [
            JobResult(title="Job 1", source="test8"),
            JobResult(title="Job 2", source="test8"),
        ]
        mock_source = MockJobSource(name="test8", results=mock_results)

        registry = SourceRegistry()
        registry.register(mock_source)

        sources = JobSources(registry=registry)
        criteria = SearchCriteria(query="developer")

        results = sources.search("test8", criteria)

        assert len(results) == 2
        assert results[0].title == "Job 1"

    def test_search_all_sources(self):
        """Test searching across all sources."""
        from hired.search.registry import SourceRegistry

        results1 = [JobResult(title="Job 1", source="source1")]
        results2 = [JobResult(title="Job 2", source="source2")]

        source1 = MockJobSource(name="source1", results=results1)
        source2 = MockJobSource(name="source2", results=results2)

        registry = SourceRegistry()
        registry.register(source1)
        registry.register(source2)

        sources = JobSources(registry=registry)
        criteria = SearchCriteria(query="developer")

        all_results = sources.search_all(criteria)

        assert len(all_results) == 2
        assert any(r.title == "Job 1" for r in all_results)
        assert any(r.title == "Job 2" for r in all_results)

    def test_search_all_skips_unconfigured(self):
        """Test that search_all skips unconfigured sources by default."""
        from hired.search.registry import SourceRegistry

        results1 = [JobResult(title="Job 1", source="configured")]

        configured = MockJobSource(name="configured", configured=True, results=results1)
        unconfigured = MockJobSource(name="unconfigured", configured=False)

        registry = SourceRegistry()
        registry.register(configured)
        registry.register(unconfigured)

        sources = JobSources(registry=registry)
        criteria = SearchCriteria(query="developer")

        # Should only get results from configured source
        all_results = sources.search_all(criteria, skip_unconfigured=True)

        assert len(all_results) == 1
        assert all_results[0].source == "configured"

    def test_contains_check(self):
        """Test checking if source exists."""
        from hired.search.registry import SourceRegistry

        registry = SourceRegistry()
        registry.register(MockJobSource(name="test9"))

        sources = JobSources(registry=registry)

        assert "test9" in sources
        assert "nonexistent" not in sources


class TestJobSearchSource:
    """Tests for JobSearchSource base class."""

    def test_validate_configured_success(self):
        """Test validation passes for configured source."""
        source = MockJobSource(configured=True)
        # Should not raise
        source.validate_configured()

    def test_validate_configured_failure(self):
        """Test validation fails for unconfigured source."""
        source = MockJobSource(configured=False)

        with pytest.raises(SourceConfigError, match="not properly configured"):
            source.validate_configured()


class TestJobSpySource:
    """Tests for JobSpy source."""

    def test_jobspy_not_available(self):
        """Test behavior when jobspy is not installed."""
        from hired.search.sources.jobspy import JobSpySource

        with patch('hired.search.sources.jobspy.JobSpySource._check_jobspy_available', return_value=False):
            source = JobSpySource()
            assert not source.is_configured()
            assert "python-jobspy" in source.get_setup_instructions()

    def test_jobspy_properties(self):
        """Test JobSpy source properties."""
        from hired.search.sources.jobspy import JobSpySource

        source = JobSpySource()

        assert source.name == "jobspy"
        assert "JobSpy" in source.display_name
        assert source.requires_auth is False

    def test_jobspy_map_job_type(self):
        """Test job type mapping."""
        from hired.search.sources.jobspy import JobSpySource

        source = JobSpySource()

        assert source._map_job_type("fulltime") == JobType.FULL_TIME
        assert source._map_job_type("parttime") == JobType.PART_TIME
        assert source._map_job_type("contract") == JobType.CONTRACT
        assert source._map_job_type("other") == JobType.OTHER


class TestUSAJobsSource:
    """Tests for USAJobs source."""

    def test_usajobs_not_configured(self):
        """Test USAJobs when not configured."""
        from hired.search.sources.usajobs import USAJobsSource

        source = USAJobsSource()
        assert not source.is_configured()

    def test_usajobs_configured(self):
        """Test USAJobs when configured."""
        from hired.search.sources.usajobs import USAJobsSource

        source = USAJobsSource(api_key="test_key", email="test@example.com")
        assert source.is_configured()

    def test_usajobs_properties(self):
        """Test USAJobs source properties."""
        from hired.search.sources.usajobs import USAJobsSource

        source = USAJobsSource()

        assert source.name == "usajobs"
        assert "USAJobs" in source.display_name
        assert source.requires_auth is True
        assert "developer.usajobs.gov" in source.get_setup_instructions()


class TestAdzunaSource:
    """Tests for Adzuna source."""

    def test_adzuna_not_configured(self):
        """Test Adzuna when not configured."""
        from hired.search.sources.adzuna import AdzunaSource

        source = AdzunaSource()
        assert not source.is_configured()

    def test_adzuna_configured(self):
        """Test Adzuna when configured."""
        from hired.search.sources.adzuna import AdzunaSource

        source = AdzunaSource(app_id="test_id", app_key="test_key")
        assert source.is_configured()

    def test_adzuna_properties(self):
        """Test Adzuna source properties."""
        from hired.search.sources.adzuna import AdzunaSource

        source = AdzunaSource()

        assert source.name == "adzuna"
        assert "Adzuna" in source.display_name
        assert source.requires_auth is True
        assert "developer.adzuna.com" in source.get_setup_instructions()

    def test_adzuna_map_job_type(self):
        """Test Adzuna job type mapping."""
        from hired.search.sources.adzuna import AdzunaSource

        source = AdzunaSource()

        assert source._map_job_type("permanent") == JobType.FULL_TIME
        assert source._map_job_type("part_time") == JobType.PART_TIME
        assert source._map_job_type("contract") == JobType.CONTRACT


class TestIntegration:
    """Integration tests."""

    def test_default_sources_registered(self):
        """Test that default sources are registered on import."""
        from hired.search import get_registry

        registry = get_registry()
        sources = registry.list_sources()

        # All three default sources should be registered
        assert "jobspy" in sources
        assert "usajobs" in sources
        assert "adzuna" in sources

    def test_job_sources_facade_works(self):
        """Test that JobSources facade works with default sources."""
        from hired import JobSources

        sources = JobSources()

        # Should have all three sources
        all_sources = sources.list()
        assert len(all_sources) >= 3

        # Should be able to access by attribute
        assert hasattr(sources, 'jobspy')
        assert hasattr(sources, 'usajobs')
        assert hasattr(sources, 'adzuna')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
