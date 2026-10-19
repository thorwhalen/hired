# hired.resumejson_pydantic_models

Pydantic models for resume json schema

### Classes

| [`Award`](#hired.resumejson_pydantic_models.Award)(\*[, title, date, awarder, summary])        |    |
|----------------------------------------------------------------------------------------------------|----|
| [`Basics`](#hired.resumejson_pydantic_models.Basics)(\*[, name, label, image, email, ...])      |    |
| [`Certificate`](#hired.resumejson_pydantic_models.Certificate)(\*[, name, date, url, issuer])        |    |
| [`EducationItem`](#hired.resumejson_pydantic_models.EducationItem)(\*[, institution, url, area, ...])  |    |
| [`Interest`](#hired.resumejson_pydantic_models.Interest)(\*[, name, keywords])                    |    |
| [`Iso8601`](#hired.resumejson_pydantic_models.Iso8601)([root])                                   |    |
| [`Language`](#hired.resumejson_pydantic_models.Language)(\*[, language, fluency])                 |    |
| [`Location`](#hired.resumejson_pydantic_models.Location)(\*[, address, postalCode, city, ...])    |    |
| [`Meta`](#hired.resumejson_pydantic_models.Meta)(\*[, canonical, version, lastModified])      |    |
| [`Profile`](#hired.resumejson_pydantic_models.Profile)(\*[, network, username, url])             |    |
| [`Project`](#hired.resumejson_pydantic_models.Project)(\*[, name, description, highlights, ...]) |    |
| [`Publication`](#hired.resumejson_pydantic_models.Publication)(\*[, name, publisher, ...])           |    |
| [`Reference`](#hired.resumejson_pydantic_models.Reference)(\*[, name, reference])                  |    |
| [`ResumeSchema`](#hired.resumejson_pydantic_models.ResumeSchema)(\*[, field_schema, basics, ...])     |    |
| [`Skill`](#hired.resumejson_pydantic_models.Skill)(\*[, name, level, keywords])                |    |
| [`VolunteerItem`](#hired.resumejson_pydantic_models.VolunteerItem)(\*[, organization, position, ...])  |    |
| [`WorkItem`](#hired.resumejson_pydantic_models.WorkItem)(\*[, name, location, description, ...])  |    |

### *class* hired.resumejson_pydantic_models.Award(, title=None, date=None, awarder=None, summary=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Basics(, name=None, label=None, image=None, email=None, phone=None, url=None, summary=None, location=None, profiles=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Certificate(, name=None, date=None, url=None, issuer=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.EducationItem(, institution=None, url=None, area=None, studyType=None, startDate=None, endDate=None, score=None, courses=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Interest(, name=None, keywords=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Iso8601(root=PydanticUndefined)

Bases: `RootModel[Annotated[str, StringConstraints]]`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Language(, language=None, fluency=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Location(, address=None, postalCode=None, city=None, countryCode=None, region=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Meta(, canonical=None, version=None, lastModified=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Profile(, network=None, username=None, url=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Project(, name=None, description=None, highlights=None, keywords=None, startDate=None, endDate=None, url=None, roles=None, entity=None, type=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Publication(, name=None, publisher=None, releaseDate=None, url=None, summary=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Reference(, name=None, reference=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.ResumeSchema(, field_schema=None, basics=None, work=None, volunteer=None, education=None, awards=None, certificates=None, publications=None, skills=None, languages=None, interests=None, references=None, projects=None, meta=None)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'forbid'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Skill(, name=None, level=None, keywords=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.VolunteerItem(, organization=None, position=None, url=None, startDate=None, endDate=None, summary=None, highlights=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.WorkItem(, name=None, location=None, description=None, position=None, url=None, startDate=None, endDate=None, summary=None, highlights=None, \*\*extra_data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].
