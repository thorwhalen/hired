"""
Application tracking system for managing job applications.

Track applications, statuses, follow-ups, and outcomes.
"""

import sqlite3
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from pathlib import Path
import json

if TYPE_CHECKING:
    from hired.search.base import JobResult


# Default database location
DEFAULT_DB_PATH = Path.home() / ".hired" / "applications.db"


@dataclass
class Application:
    """Represents a job application."""

    # Required fields
    job_title: str
    company: str

    # Identification
    id: Optional[int] = None

    # Job details
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None

    # Application materials
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None

    # Status tracking
    status: str = "draft"  # draft, applied, interview, offer, rejected, accepted, withdrawn
    applied_date: Optional[str] = None

    # Timeline
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Follow-up
    follow_up_date: Optional[str] = None
    last_contact_date: Optional[str] = None

    # Notes and metadata
    notes: str = ""
    contacts: str = ""  # JSON string of contact information
    interview_dates: str = ""  # JSON string of interview dates

    # Matching score (from JobMatcher)
    match_score: Optional[float] = None

    # Source tracking
    source: Optional[str] = None  # e.g., "linkedin", "indeed", "usajobs"
    source_data: str = ""  # JSON string for additional source data

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Parse JSON fields
        if self.contacts:
            try:
                data['contacts'] = json.loads(self.contacts)
            except json.JSONDecodeError:
                data['contacts'] = []

        if self.interview_dates:
            try:
                data['interview_dates'] = json.loads(self.interview_dates)
            except json.JSONDecodeError:
                data['interview_dates'] = []

        if self.source_data:
            try:
                data['source_data'] = json.loads(self.source_data)
            except json.JSONDecodeError:
                data['source_data'] = {}

        return data

    @classmethod
    def from_job_result(cls, job: 'JobResult', **kwargs) -> 'Application':
        """
        Create an Application from a JobResult.

        Args:
            job: JobResult object
            **kwargs: Additional fields to set

        Returns:
            Application object
        """
        salary_range = None
        if job.compensation:
            if job.compensation.min_amount and job.compensation.max_amount:
                currency = job.compensation.currency or "USD"
                salary_range = f"${job.compensation.min_amount:,.0f} - ${job.compensation.max_amount:,.0f} {currency}"

        location = job.location.raw if job.location else None

        return cls(
            job_title=job.title,
            company=job.company or "Unknown",
            job_url=job.job_url,
            location=location,
            salary_range=salary_range,
            source=job.source,
            source_data=json.dumps(job.raw_data) if job.raw_data else "",
            **kwargs
        )


class ApplicationTracker:
    """
    Track job applications in a SQLite database.

    Examples:
        >>> tracker = ApplicationTracker()
        >>>
        >>> # Add application from job search
        >>> app_id = tracker.add_application(
        ...     job=job_result,
        ...     resume_path="resume.pdf",
        ...     status="applied"
        ... )
        >>>
        >>> # Update status
        >>> tracker.update_status(app_id, "interview")
        >>>
        >>> # Get all applications in interview stage
        >>> interviews = tracker.get_applications(status="interview")
        >>>
        >>> # Get statistics
        >>> stats = tracker.get_statistics()
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize application tracker.

        Args:
            db_path: Path to SQLite database. If None, uses default location.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                job_url TEXT,
                location TEXT,
                salary_range TEXT,
                resume_path TEXT,
                cover_letter_path TEXT,
                status TEXT DEFAULT 'draft',
                applied_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                follow_up_date TEXT,
                last_contact_date TEXT,
                notes TEXT,
                contacts TEXT,
                interview_dates TEXT,
                match_score REAL,
                source TEXT,
                source_data TEXT
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON applications(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_company ON applications(company)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_applied_date ON applications(applied_date)
        """)

        conn.commit()
        conn.close()

    def add_application(
        self,
        job: Optional['JobResult'] = None,
        **kwargs
    ) -> int:
        """
        Add a new application.

        Args:
            job: Optional JobResult to create application from
            **kwargs: Additional fields (or all fields if job not provided)

        Returns:
            ID of created application

        Examples:
            >>> # From JobResult
            >>> app_id = tracker.add_application(
            ...     job=job_result,
            ...     resume_path="resume.pdf",
            ...     status="applied"
            ... )
            >>>
            >>> # Manual entry
            >>> app_id = tracker.add_application(
            ...     job_title="Software Engineer",
            ...     company="TechCorp",
            ...     status="applied"
            ... )
        """
        if job:
            app = Application.from_job_result(job, **kwargs)
        else:
            app = Application(**kwargs)

        app.updated_at = datetime.now().isoformat()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO applications (
                job_title, company, job_url, location, salary_range,
                resume_path, cover_letter_path, status, applied_date,
                created_at, updated_at, follow_up_date, last_contact_date,
                notes, contacts, interview_dates, match_score, source, source_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app.job_title, app.company, app.job_url, app.location, app.salary_range,
            app.resume_path, app.cover_letter_path, app.status, app.applied_date,
            app.created_at, app.updated_at, app.follow_up_date, app.last_contact_date,
            app.notes, app.contacts, app.interview_dates, app.match_score,
            app.source, app.source_data
        ))

        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return app_id

    def get_application(self, app_id: int) -> Optional[Application]:
        """
        Get application by ID.

        Args:
            app_id: Application ID

        Returns:
            Application object or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Application(**dict(row))
        return None

    def get_applications(
        self,
        status: Optional[str] = None,
        company: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Application]:
        """
        Get applications with optional filtering.

        Args:
            status: Filter by status
            company: Filter by company name
            limit: Maximum number of results

        Returns:
            List of Application objects
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM applications WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")

        query += " ORDER BY updated_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [Application(**dict(row)) for row in rows]

    def update_status(
        self,
        app_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update application status.

        Args:
            app_id: Application ID
            status: New status
            notes: Optional notes to append

        Returns:
            True if updated, False if not found
        """
        updates = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }

        if status == "applied" and not self.get_application(app_id).applied_date:
            updates['applied_date'] = datetime.now().isoformat()

        if notes:
            app = self.get_application(app_id)
            if app:
                existing_notes = app.notes or ""
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                updates['notes'] = f"{existing_notes}\n[{timestamp}] {notes}".strip()

        return self.update_application(app_id, **updates)

    def update_application(self, app_id: int, **kwargs) -> bool:
        """
        Update application fields.

        Args:
            app_id: Application ID
            **kwargs: Fields to update

        Returns:
            True if updated, False if not found
        """
        if not kwargs:
            return False

        kwargs['updated_at'] = datetime.now().isoformat()

        set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
        values = list(kwargs.values())
        values.append(app_id)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            f"UPDATE applications SET {set_clause} WHERE id = ?",
            values
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def delete_application(self, app_id: int) -> bool:
        """
        Delete an application.

        Args:
            app_id: Application ID

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get application statistics.

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Total applications
        cursor.execute("SELECT COUNT(*) FROM applications")
        total = cursor.fetchone()[0]

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) FROM applications GROUP BY status
        """)
        by_status = dict(cursor.fetchall())

        # Response rate (if applied, how many got responses)
        applied = by_status.get('applied', 0) + by_status.get('interview', 0) + \
                  by_status.get('offer', 0) + by_status.get('accepted', 0) + \
                  by_status.get('rejected', 0)

        responses = by_status.get('interview', 0) + by_status.get('offer', 0) + \
                   by_status.get('accepted', 0) + by_status.get('rejected', 0)

        response_rate = (responses / applied * 100) if applied > 0 else 0

        # Average time to response
        cursor.execute("""
            SELECT AVG(julianday(last_contact_date) - julianday(applied_date))
            FROM applications
            WHERE applied_date IS NOT NULL AND last_contact_date IS NOT NULL
        """)
        avg_days = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'total_applications': total,
            'by_status': by_status,
            'response_rate': round(response_rate, 1),
            'avg_days_to_response': round(avg_days, 1),
        }

    def get_follow_ups_due(self, days: int = 7) -> List[Application]:
        """
        Get applications that need follow-up.

        Args:
            days: Number of days to look ahead

        Returns:
            List of Application objects needing follow-up
        """
        cutoff_date = (datetime.now() + timedelta(days=days)).isoformat()

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM applications
            WHERE follow_up_date IS NOT NULL
            AND follow_up_date <= ?
            AND status NOT IN ('rejected', 'accepted', 'withdrawn')
            ORDER BY follow_up_date
        """, (cutoff_date,))

        rows = cursor.fetchall()
        conn.close()

        return [Application(**dict(row)) for row in rows]

    def export_to_csv(self, output_path: str):
        """
        Export applications to CSV file.

        Args:
            output_path: Path to output CSV file
        """
        import csv

        applications = self.get_applications()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not applications:
                return

            fieldnames = [
                'id', 'job_title', 'company', 'location', 'salary_range',
                'status', 'applied_date', 'job_url', 'match_score', 'notes'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for app in applications:
                row = {field: getattr(app, field, '') for field in fieldnames}
                writer.writerow(row)
