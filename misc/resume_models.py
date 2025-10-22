"""
Generated Pydantic models for JSON Resume Schema
Can be imported and used in other projects.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class Location(BaseModel):
    address: str | None = None
    postalCode: str | None = None
    city: str | None = None
    countryCode: str | None = None
    region: str | None = None

class Profile(BaseModel):
    network: str | None = None
    username: str | None = None
    url: str | None = None

class Basics(BaseModel):
    name: str | None = None
    label: str | None = None
    image: str | None = None
    email: str | None = None
    phone: str | None = None
    url: str | None = None
    summary: str | None = None
    location: Location | None = None
    profiles: list[Profile] | None = None

class Work(BaseModel):
    name: str | None = None
    location: str | None = None
    description: str | None = None
    position: str | None = None
    url: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None

class Volunteer(BaseModel):
    organization: str | None = None
    position: str | None = None
    url: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None

class Education(BaseModel):
    institution: str | None = None
    url: str | None = None
    area: str | None = None
    studyType: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    score: str | None = None
    courses: list[str] | None = None

class Award(BaseModel):
    title: str | None = None
    date: str | None = None
    awarder: str | None = None
    summary: str | None = None

class Certificate(BaseModel):
    name: str | None = None
    date: str | None = None
    url: str | None = None
    issuer: str | None = None

class Publication(BaseModel):
    name: str | None = None
    publisher: str | None = None
    releaseDate: str | None = None
    url: str | None = None
    summary: str | None = None

class Skill(BaseModel):
    name: str | None = None
    level: str | None = None
    keywords: list[str] | None = None

class Language(BaseModel):
    language: str | None = None
    fluency: str | None = None

class Interest(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None

class Reference(BaseModel):
    name: str | None = None
    reference: str | None = None

class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    highlights: list[str] | None = None
    keywords: list[str] | None = None
    startDate: str | None = None
    endDate: str | None = None
    url: str | None = None
    roles: list[str] | None = None
    entity: str | None = None
    type: str | None = None

class Meta(BaseModel):
    canonical: str | None = None
    version: str | None = None
    lastModified: str | None = None

class Resume(BaseModel):
    """JSON Resume Schema - Complete Resume Model"""
    schema_: str | None = Field(None, alias='$schema')
    basics: Basics | None = None
    work: list[Work] | None = None
    volunteer: list[Volunteer] | None = None
    education: list[Education] | None = None
    awards: list[Award] | None = None
    certificates: list[Certificate] | None = None
    publications: list[Publication] | None = None
    skills: list[Skill] | None = None
    languages: list[Language] | None = None
    interests: list[Interest] | None = None
    references: list[Reference] | None = None
    projects: list[Project] | None = None
    meta: Meta | None = None
    
    class Config:
        allow_population_by_field_name = True
        extra = 'allow'
