# hired.taxonomy.base

Schemas and on-disk layout for the skills taxonomy (ESCO + O\*NET).

A taxonomy is two things:

- **nodes** — skills (and, for O\*NET, technologies, knowledge areas, abilities),
  each a [`SkillNode`](#hired.taxonomy.base.SkillNode) with a stable id (`esco:<uuid>`,
  `onet:tech:<slug>`, `onet:<element-id>`), a preferred label, alternative
  labels, and a KSAO `kind`;
- **occupations** — each an [`Occupation`](#hired.taxonomy.base.Occupation) listing the nodes it requires
  (`essential`) or may use (`optional`). Skill *adjacency* is learned from
  which skills occupations require together (see [`hired.taxonomy.graph`](hired.taxonomy.graph.html.md#module-hired.taxonomy.graph)).

The built taxonomy is shared reference data, not candidate data, so it lives at
`<data root>/taxonomy/` (not under `users/`). It is built on demand by
[`hired.taxonomy.build_skill_index()`](hired.taxonomy.html.md#hired.taxonomy.build_skill_index) — nothing is vendored into the package.

Attribution (both sources are CC BY 4.0) is in `ATTRIBUTION` and is written
next to the data as `NOTICE.md`.

### Functions

| [`attribution`](#hired.taxonomy.base.attribution)([sources, onet_version])   | The CC BY 4.0 notice for the sources a build used (written as `NOTICE.md`).   |
|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`dump_models`](#hired.taxonomy.base.dump_models)(models)                    | JSON-able dicts for a list of models, without empty/default noise.            |
| [`normalize_label`](#hired.taxonomy.base.normalize_label)(text)                  | Case-, accent- and punctuation-insensitive form of a label, for matching.     |
| [`taxonomy_dir`](#hired.taxonomy.base.taxonomy_dir)(\*subpaths[, root, make]) | Directory of the built taxonomy: `root` or `<data root>/taxonomy`.            |

### Classes

| [`Occupation`](#hired.taxonomy.base.Occupation)(\*, id, label, source[, ...])          | An occupation and the skill nodes it requires or may use.   |
|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| [`SkillNode`](#hired.taxonomy.base.SkillNode)(\*, id, label[, alt_labels, kind, ...]) | One skill-like concept from a source taxonomy.              |

### *class* hired.taxonomy.base.Occupation(\*, id, label, source, essential=<factory>, optional=<factory>)

Bases: `BaseModel`

An occupation and the skill nodes it requires or may use.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.taxonomy.base.SkillNode(\*, id, label, alt_labels=<factory>, source, kind='skill', reuse_level=None, uri=None)

Bases: `BaseModel`

One skill-like concept from a source taxonomy.

#### kind *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

“skill”, “knowledge”, “ability”, “technology”, “competence”, …

* **Type:**
  KSAO kind

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

#### reuse_level *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

ESCO skill-reuse level (“transversal”, “cross-sector”, “sector-specific”,
“occupation-specific”), when known — a transferability hint.

### hired.taxonomy.base.attribution(sources=('esco', 'onet'), , onet_version='30.0')

The CC BY 4.0 notice for the sources a build used (written as `NOTICE.md`).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.taxonomy.base.dump_models(models)

JSON-able dicts for a list of models, without empty/default noise.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### hired.taxonomy.base.normalize_label(text)

Case-, accent- and punctuation-insensitive form of a label, for matching.

```pycon
>>> normalize_label('  Machine-Learning (ML)! ')
'machine learning ml'
>>> normalize_label('Café')
'cafe'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.taxonomy.base.taxonomy_dir(\*subpaths, root=None, make=True)

Directory of the built taxonomy: `root` or `<data root>/taxonomy`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
