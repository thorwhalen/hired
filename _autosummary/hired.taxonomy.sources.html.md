# hired.taxonomy.sources

Fetch the ESCO and O\*NET taxonomies into `SkillNode` / `Occupation`.

Network access is a seam: `get_json(url, params) -> dict` for the ESCO API and
`get_bytes(url) -> bytes` for the O\*NET archive, defaulting to `requests`
(a core dependency) with timeouts and retries. Every page or archive fetched is
written to a `cache` mapping first, so an interrupted build resumes where it
stopped (the ESCO occupation pages are slow — tens of seconds each).

- **ESCO** ([`fetch_esco()`](#hired.taxonomy.sources.fetch_esco)): all skills (labels, alternative labels, skill
  type → KSAO kind, reuse level) and all occupations with their essential and
  optional skills, paged through the public search API (no key needed).
- **O\*NET** ([`fetch_onet()`](#hired.taxonomy.sources.fetch_onet)): the text database archive. Technology examples
  (`Technology Skills.txt`; hot technologies essential, others optional) and the
  Skills / Knowledge / Abilities descriptors an occupation rates at or above
  `min_importance` on the importance scale.

### Functions

| [`esco_occupation`](#hired.taxonomy.sources.esco_occupation)(record, \*[, language])            | An `Occupation` from one ESCO search result (full or brief).                |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`esco_skill_node`](#hired.taxonomy.sources.esco_skill_node)(record, \*[, language])            | A `SkillNode` from one ESCO search result (full or brief).                  |
| [`fetch_esco`](#hired.taxonomy.sources.fetch_esco)(\*[, get_json, cache, page_size, ...])  | All ESCO skills and occupations (with their skill links).                   |
| [`fetch_onet`](#hired.taxonomy.sources.fetch_onet)(\*[, get_bytes, cache, version, ...])   | O\*NET technology and K/S/A nodes, and occupations (downloads ~13 MB once). |
| [`onet_tech_id`](#hired.taxonomy.sources.onet_tech_id)(example)                              | Stable node id for an O\*NET technology example (`C++` → `onet:tech:c++`).  |
| [`parse_onet_archive`](#hired.taxonomy.sources.parse_onet_archive)(data, \*[, min_importance])     | Nodes and occupations from the bytes of an O\*NET text-database archive.    |
| [`requests_get_bytes`](#hired.taxonomy.sources.requests_get_bytes)(url, \*[, timeout, retries])    | Default O\*NET fetcher: the archive's bytes, with retries.                  |
| [`requests_get_json`](#hired.taxonomy.sources.requests_get_json)(url, params, \*[, timeout, ...]) | Default ESCO fetcher: `requests.get(...).json()` with retries.              |

### hired.taxonomy.sources.esco_occupation(record, , language='en')

An `Occupation` from one ESCO search result (full or brief).

* **Return type:**
  [`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)

### hired.taxonomy.sources.esco_skill_node(record, , language='en')

A `SkillNode` from one ESCO search result (full or brief).

* **Return type:**
  [`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)

### hired.taxonomy.sources.fetch_esco(, get_json=None, cache=None, page_size=100, language='en', progress=None)

All ESCO skills and occupations (with their skill links).

Occupation↔skill links are the union of both sides — an occupation’s
`hasEssential/OptionalSkill` and a skill’s `isEssential/OptionalForOccupation`
— so a record that only came back in brief form still gets its links.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)]]

### hired.taxonomy.sources.fetch_onet(, get_bytes=None, cache=None, version='30_0', min_importance=3.5, progress=None)

O\*NET technology and K/S/A nodes, and occupations (downloads ~13 MB once).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)]]

### hired.taxonomy.sources.onet_tech_id(example)

Stable node id for an O\*NET technology example (`C++` → `onet:tech:c++`).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.taxonomy.sources.parse_onet_archive(data, , min_importance=3.5)

Nodes and occupations from the bytes of an O\*NET text-database archive.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`SkillNode`](hired.taxonomy.base.html.md#hired.taxonomy.base.SkillNode)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Occupation`](hired.taxonomy.base.html.md#hired.taxonomy.base.Occupation)]]

### hired.taxonomy.sources.requests_get_bytes(url, , timeout=300, retries=3)

Default O\*NET fetcher: the archive’s bytes, with retries.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

### hired.taxonomy.sources.requests_get_json(url, params, , timeout=180, retries=3)

Default ESCO fetcher: `requests.get(...).json()` with retries.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]
