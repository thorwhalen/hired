# hired.resumejson_pydantic_models

Pydantic models for resume json schema

### Classes

| [`Award`](#hired.resumejson_pydantic_models.Award)(\*\*data)         |    |
|--------------------------------------------------------------------------|----|
| [`Basics`](#hired.resumejson_pydantic_models.Basics)(\*\*data)        |    |
| [`Certificate`](#hired.resumejson_pydantic_models.Certificate)(\*\*data)   |    |
| [`EducationItem`](#hired.resumejson_pydantic_models.EducationItem)(\*\*data) |    |
| [`Interest`](#hired.resumejson_pydantic_models.Interest)(\*\*data)      |    |
| [`Iso8601`](#hired.resumejson_pydantic_models.Iso8601)([root])         |    |
| [`Language`](#hired.resumejson_pydantic_models.Language)(\*\*data)      |    |
| [`Location`](#hired.resumejson_pydantic_models.Location)(\*\*data)      |    |
| [`Meta`](#hired.resumejson_pydantic_models.Meta)(\*\*data)          |    |
| [`Profile`](#hired.resumejson_pydantic_models.Profile)(\*\*data)       |    |
| [`Project`](#hired.resumejson_pydantic_models.Project)(\*\*data)       |    |
| [`Publication`](#hired.resumejson_pydantic_models.Publication)(\*\*data)   |    |
| [`Reference`](#hired.resumejson_pydantic_models.Reference)(\*\*data)     |    |
| [`ResumeSchema`](#hired.resumejson_pydantic_models.ResumeSchema)(\*\*data)  |    |
| [`Skill`](#hired.resumejson_pydantic_models.Skill)(\*\*data)         |    |
| [`VolunteerItem`](#hired.resumejson_pydantic_models.VolunteerItem)(\*\*data) |    |
| [`WorkItem`](#hired.resumejson_pydantic_models.WorkItem)(\*\*data)      |    |

### *class* hired.resumejson_pydantic_models.Award(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Basics(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Certificate(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.EducationItem(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Interest(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Iso8601(root=PydanticUndefined, \*\*data)

Bases: `RootModel[Annotated[str, StringConstraints]]`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Language(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Location(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Meta(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Profile(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Project(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Publication(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Reference(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.ResumeSchema(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'forbid'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.Skill(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.VolunteerItem(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.resumejson_pydantic_models.WorkItem(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {'extra': 'allow'}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].
