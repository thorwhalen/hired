"""Pydantic models for resume json schema
"""
from __future__ import annotations

from datetime import date as date_aliased
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, RootModel, constr

# Type alias to avoid strict URL validation
AnyUrl = Optional[str]



class Location(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    address: str | None = Field(
        None,
        description='To add multiple address lines, use \n. For example, 1234 Glücklichkeit Straße\nHinterhaus 5. Etage li.')
    postalCode: str | None = None
    city: str | None = None
    countryCode: str | None = Field(
        None, description='code as per ISO-3166-1 ALPHA-2, e.g. US, AU, IN'
    )
    region: str | None = Field(
        None,
        description='The general region where you live. Can be a US state, or a province, for instance.')


class Profile(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    network: str | None = Field(None, description='e.g. Facebook or Twitter')
    username: str | None = Field(None, description='e.g. neutralthoughts')
    url: AnyUrl | None = Field(
        None, description='e.g. http://twitter.example.com/neutralthoughts'
    )


class Basics(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = None
    label: str | None = Field(None, description='e.g. Web Developer')
    image: str | None = Field(
        None, description='URL (as per RFC 3986) to a image in JPEG or PNG format'
    )
    email: EmailStr | None = Field(None, description='e.g. thomas@gmail.com')
    phone: str | None = Field(
        None,
        description='Phone numbers are stored as strings so use any format you like, e.g. 712-117-2923')
    url: AnyUrl | None = Field(
        None,
        description='URL (as per RFC 3986) to your website, e.g. personal homepage')
    summary: str | None = Field(
        None, description='Write a short 2-3 sentence biography about yourself'
    )
    location: Location | None = None
    profiles: list[Profile] | None = Field(
        None,
        description='Specify any number of social networks that you participate in')


class Certificate(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(
        None, description='e.g. Certified Kubernetes Administrator'
    )
    date: date_aliased | None = Field(None, description='e.g. 1989-06-12')
    url: AnyUrl | None = Field(None, description='e.g. http://example.com')
    issuer: str | None = Field(None, description='e.g. CNCF')


class Skill(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(None, description='e.g. Web Development')
    level: str | None = Field(None, description='e.g. Master')
    keywords: list[str] | None = Field(
        None, description='List some keywords pertaining to this skill'
    )


class Language(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    language: str | None = Field(None, description='e.g. English, Spanish')
    fluency: str | None = Field(None, description='e.g. Fluent, Beginner')


class Interest(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(None, description='e.g. Philosophy')
    keywords: list[str] | None = None


class Reference(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(None, description='e.g. Timothy Cook')
    reference: str | None = Field(
        None,
        description='e.g. Joe blogs was a great employee, who turned up to work at least once a week. He exceeded my expectations when it came to doing nothing.')


class Meta(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    canonical: AnyUrl | None = Field(
        None, description='URL (as per RFC 3986) to latest version of this document'
    )
    version: str | None = Field(
        None, description='A version field which follows semver - e.g. v1.0.0'
    )
    lastModified: str | None = Field(
        None, description='Using ISO 8601 with YYYY-MM-DDThh:mm:ss'
    )


class Iso8601(
    RootModel[
        constr(
            pattern=r'^([1-2][0-9]{3}-[0-1][0-9]-[0-3][0-9]|[1-2][0-9]{3}-[0-1][0-9]|[1-2][0-9]{3})$'
        )
    ]
):
    root: constr(
        pattern=r'^([1-2][0-9]{3}-[0-1][0-9]-[0-3][0-9]|[1-2][0-9]{3}-[0-1][0-9]|[1-2][0-9]{3})$'
    ) = Field(..., description='e.g. 2014-06-29')


class WorkItem(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(None, description='e.g. Facebook')
    location: str | None = Field(None, description='e.g. Menlo Park, CA')
    description: str | None = Field(None, description='e.g. Social Media Company')
    position: str | None = Field(None, description='e.g. Software Engineer')
    url: AnyUrl | None = Field(None, description='e.g. http://facebook.example.com')
    startDate: Iso8601 | None = None
    endDate: Iso8601 | None = None
    summary: str | None = Field(
        None, description='Give an overview of your responsibilities at the company'
    )
    highlights: list[str] | None = Field(
        None, description='Specify multiple accomplishments'
    )


class VolunteerItem(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    organization: str | None = Field(None, description='e.g. Facebook')
    position: str | None = Field(None, description='e.g. Software Engineer')
    url: AnyUrl | None = Field(None, description='e.g. http://facebook.example.com')
    startDate: Iso8601 | None = None
    endDate: Iso8601 | None = None
    summary: str | None = Field(
        None, description='Give an overview of your responsibilities at the company'
    )
    highlights: list[str] | None = Field(
        None, description='Specify accomplishments and achievements'
    )


class EducationItem(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    institution: str | None = Field(
        None, description='e.g. Massachusetts Institute of Technology'
    )
    url: AnyUrl | None = Field(None, description='e.g. http://facebook.example.com')
    area: str | None = Field(None, description='e.g. Arts')
    studyType: str | None = Field(None, description='e.g. Bachelor')
    startDate: Iso8601 | None = None
    endDate: Iso8601 | None = None
    score: str | None = Field(None, description='grade point average, e.g. 3.67/4.0')
    courses: list[str] | None = Field(
        None, description='List notable courses/subjects'
    )


class Award(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    title: str | None = Field(
        None, description='e.g. One of the 100 greatest minds of the century'
    )
    date: Iso8601 | None = None
    awarder: str | None = Field(None, description='e.g. Time Magazine')
    summary: str | None = Field(
        None, description='e.g. Received for my work with Quantum Physics'
    )


class Publication(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(None, description='e.g. The World Wide Web')
    publisher: str | None = Field(None, description='e.g. IEEE, Computer Magazine')
    releaseDate: Iso8601 | None = None
    url: AnyUrl | None = Field(
        None,
        description='e.g. http://www.computer.org.example.com/csdl/mags/co/1996/10/rx069-abs.html')
    summary: str | None = Field(
        None,
        description='Short summary of publication. e.g. Discussion of the World Wide Web, HTTP, HTML.')


class Project(BaseModel):
    model_config = ConfigDict(
        extra='allow')
    name: str | None = Field(None, description='e.g. The World Wide Web')
    description: str | None = Field(
        None, description='Short summary of project. e.g. Collated works of 2017.'
    )
    highlights: list[str] | None = Field(
        None, description='Specify multiple features'
    )
    keywords: list[str] | None = Field(
        None, description='Specify special elements involved'
    )
    startDate: Iso8601 | None = None
    endDate: Iso8601 | None = None
    url: AnyUrl | None = Field(
        None,
        description='e.g. http://www.computer.org/csdl/mags/co/1996/10/rx069-abs.html')
    roles: list[str] | None = Field(
        None, description='Specify your role on this project or in company'
    )
    entity: str | None = Field(
        None,
        description="Specify the relevant company/entity affiliations e.g. 'greenpeace', 'corporationXYZ'")
    type: str | None = Field(
        None,
        description=" e.g. 'volunteering', 'presentation', 'talk', 'application', 'conference'")


class ResumeSchema(BaseModel):
    model_config = ConfigDict(
        extra='forbid')
    field_schema: AnyUrl | None = Field(
        None,
        alias='$schema',
        description='link to the version of the schema that can validate the resume')
    basics: Basics | None = None
    work: list[WorkItem] | None = None
    volunteer: list[VolunteerItem] | None = None
    education: list[EducationItem] | None = None
    awards: list[Award] | None = Field(
        None,
        description='Specify any awards you have received throughout your professional career')
    certificates: list[Certificate] | None = Field(
        None,
        description='Specify any certificates you have received throughout your professional career')
    publications: list[Publication] | None = Field(
        None, description='Specify your publications through your career'
    )
    skills: list[Skill] | None = Field(
        None, description='List out your professional skill-set'
    )
    languages: list[Language] | None = Field(
        None, description='List any other languages you speak'
    )
    interests: list[Interest] | None = None
    references: list[Reference] | None = Field(
        None, description='List references you have received'
    )
    projects: list[Project] | None = Field(
        None, description='Specify career projects'
    )
    meta: Meta | None = Field(
        None,
        description='The schema version and any other tooling configuration lives here')
