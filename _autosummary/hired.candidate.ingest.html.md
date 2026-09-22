# hired.candidate.ingest

Turn extracted atomic-fact records into persisted, provenance-bearing facts.

The *intelligence* of extraction (reading a CV/bio/publication and proposing
atomic claims) is supplied externally — by the `hired-profile-ingest` subagent
in interactive use, or an injected LLM in autonomous use. This module is the
deterministic glue: it validates those proposals into `Fact` objects,
enforces the provenance-quote invariant, and persists them.

A *record* is a lightweight dict:

```text
{"statement": "...", "category": "skill", "tags": ["python"],
 "confidence": "high", "quote": "...", "locator": "experience[1]",
 "is_negation": false}
```

### Functions

| [`fact_from_record`](#hired.candidate.ingest.fact_from_record)(record, \*, source_kind[, ...])   | Build a (not-yet-persisted) `Fact` from a record dict.                 |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`ingest_facts`](#hired.candidate.ingest.ingest_facts)(kb, records, \*, source_kind[, ...])  | Validate, quote-check, and persist fact records; return persisted ids. |
| [`verify_quote`](#hired.candidate.ingest.verify_quote)(quote, source_text)                   | True if `quote` is a verbatim substring of `source_text`.              |

### hired.candidate.ingest.fact_from_record(record, , source_kind, source_id='', subject='me')

Build a (not-yet-persisted) `Fact` from a record dict.

* **Return type:**
  [`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)

### hired.candidate.ingest.ingest_facts(kb, records, , source_kind, source_id='', source_text=None, drop_unverified_quotes=True)

Validate, quote-check, and persist fact records; return persisted ids.

When `source_text` is given, each record’s `quote` is checked to be a
verbatim substring. Unverified quotes are dropped (the fact is still kept,
but without the spurious quote) unless `drop_unverified_quotes` is False,
in which case a `ValueError` is raised — useful for strict pipelines.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.candidate.ingest.verify_quote(quote, source_text)

True if `quote` is a verbatim substring of `source_text`.

A `None` quote (no quote claimed) always verifies. When no source text is
available to check against, we cannot disprove it, so it verifies too — the
invariant only bites when we *can* check.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
