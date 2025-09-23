"""
Generated Pydantic models for JSON Resume Schema
Can be imported and used in other projects.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class Location(BaseModel):
    address: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    countryCode: Optional[str] = None
    region: Optional[str] = None

class Profile(BaseModel):
    network: Optional[str] = None
    username: Optional[str] = None
    url: Optional[str] = None

class Basics(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[Location] = None
    profiles: Optional[List[Profile]] = None

class Work(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    position: Optional[str] = None
    url: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None

class Volunteer(BaseModel):
    organization: Optional[str] = None
    position: Optional[str] = None
    url: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None

class Education(BaseModel):
    institution: Optional[str] = None
    url: Optional[str] = None
    area: Optional[str] = None
    studyType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    score: Optional[str] = None
    courses: Optional[List[str]] = None

class Award(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    awarder: Optional[str] = None
    summary: Optional[str] = None

class Certificate(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    issuer: Optional[str] = None

class Publication(BaseModel):
    name: Optional[str] = None
    publisher: Optional[str] = None
    releaseDate: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None

class Skill(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    keywords: Optional[List[str]] = None

class Language(BaseModel):
    language: Optional[str] = None
    fluency: Optional[str] = None

class Interest(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None

class Reference(BaseModel):
    name: Optional[str] = None
    reference: Optional[str] = None

class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    url: Optional[str] = None
    roles: Optional[List[str]] = None
    entity: Optional[str] = None
    type: Optional[str] = None

class Meta(BaseModel):
    canonical: Optional[str] = None
    version: Optional[str] = None
    lastModified: Optional[str] = None

class Resume(BaseModel):
    """JSON Resume Schema - Complete Resume Model"""
    schema_: Optional[str] = Field(None, alias='$schema')
    basics: Optional[Basics] = None
    work: Optional[List[Work]] = None
    volunteer: Optional[List[Volunteer]] = None
    education: Optional[List[Education]] = None
    awards: Optional[List[Award]] = None
    certificates: Optional[List[Certificate]] = None
    publications: Optional[List[Publication]] = None
    skills: Optional[List[Skill]] = None
    languages: Optional[List[Language]] = None
    interests: Optional[List[Interest]] = None
    references: Optional[List[Reference]] = None
    projects: Optional[List[Project]] = None
    meta: Optional[Meta] = None
    
    class Config:
        allow_population_by_field_name = True
        extra = 'allow'
