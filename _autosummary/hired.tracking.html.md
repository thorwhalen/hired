# hired.tracking

Application tracking system for managing job applications.

Track applications, statuses, follow-ups, and outcomes.

### Classes

| [`Application`](#hired.tracking.Application)(job_title, company[, id, ...])   | Represents a job application.                |
|-----------------------------------------------------------------------------------------------|----------------------------------------------|
| [`ApplicationTracker`](#hired.tracking.ApplicationTracker)([db_path])                | Track job applications in a SQLite database. |

### *class* hired.tracking.Application(job_title, company, id=None, job_url=None, location=None, salary_range=None, resume_path=None, cover_letter_path=None, status='draft', applied_date=None, created_at=None, updated_at=None, follow_up_date=None, last_contact_date=None, notes='', contacts='', interview_dates='', match_score=None, source=None, source_data='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Represents a job application.

#### *classmethod* from_job_result(job, \*\*kwargs)

Create an Application from a JobResult.

* **Parameters:**
  * **job** ([`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)) – JobResult object
  * **\*\*kwargs** – Additional fields to set
* **Return type:**
  [`Application`](#hired.tracking.Application)
* **Returns:**
  Application object

#### to_dict()

Convert to dictionary.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.tracking.ApplicationTracker(db_path=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Track job applications in a SQLite database.

### Examples

```pycon
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
```

#### add_application(job=None, \*\*kwargs)

Add a new application.

* **Parameters:**
  * **job** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`JobResult`](hired.search.base.html.md#hired.search.base.JobResult)]) – Optional JobResult to create application from
  * **\*\*kwargs** – Additional fields (or all fields if job not provided)
* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
* **Returns:**
  ID of created application

### Examples

```pycon
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
```

#### delete_application(app_id)

Delete an application.

* **Parameters:**
  **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if deleted, False if not found

#### export_to_csv(output_path)

Export applications to CSV file.

* **Parameters:**
  **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to output CSV file

#### get_application(app_id)

Get application by ID.

* **Parameters:**
  **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Application`](#hired.tracking.Application)]
* **Returns:**
  Application object or None if not found

#### get_applications(status=None, company=None, limit=None)

Get applications with optional filtering.

* **Parameters:**
  * **status** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Filter by status
  * **company** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Filter by company name
  * **limit** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Maximum number of results
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Application`](#hired.tracking.Application)]
* **Returns:**
  List of Application objects

#### get_follow_ups_due(days=7)

Get applications that need follow-up.

* **Parameters:**
  **days** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of days to look ahead
* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Application`](#hired.tracking.Application)]
* **Returns:**
  List of Application objects needing follow-up

#### get_statistics()

Get application statistics.

* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]
* **Returns:**
  Dictionary with statistics

#### update_application(app_id, \*\*kwargs)

Update application fields.

* **Parameters:**
  * **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
  * **\*\*kwargs** – Fields to update
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if updated, False if not found

#### update_status(app_id, status, notes=None)

Update application status.

* **Parameters:**
  * **app_id** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Application ID
  * **status** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – New status
  * **notes** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional notes to append
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if updated, False if not found
