from pydantic import BaseModel, ConfigDict, Field


class ResumeSection(BaseModel):
    """A custom resume section that does not fit a standard field."""

    model_config = ConfigDict(extra="allow")

    title: str
    details: list[str] = Field(default_factory=list)


class Education(BaseModel):
    model_config = ConfigDict(extra="allow")

    degree: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    graduation_year: int | None = None
    cgpa_or_percentage: str | None = None
    coursework: list[str] = Field(default_factory=list)
    honors: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    model_config = ConfigDict(extra="allow")

    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class Project(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    role: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    url: str | None = None
    technologies: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)


class Publication(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    publisher: str | None = None
    publication_date: str | None = None
    url: str | None = None
    description: str | None = None


class ResumeData(BaseModel):
    """Broad structured profile; extra source-supported keys are retained."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    professional_title: str | None = None
    professional_summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    websites: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    volunteer_experience: list[Experience] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    additional_sections: list[ResumeSection] = Field(default_factory=list)
