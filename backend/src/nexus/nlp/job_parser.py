
from nexus.core.debug import debug_trace
import re

from pydantic import BaseModel, ConfigDict, Field


class JobInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=20, max_length=100_000)


class JobProfile(BaseModel):
    title: str
    company: str
    skills: list[str]
    description: str


# Initial baseline: deliberately small skill dictionary.
# We will expand and improve it based on measured errors.
SKILL_ALIASES = {
    "python": "Python",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "mongodb": "MongoDB",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "computer vision": "Computer Vision",
    "sql": "SQL",
    "pandas": "pandas",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
}


@debug_trace
def extract_skills(description: str) -> list[str]:
    """Extract known skills using case-insensitive whole-word matching."""
    text = description.casefold()
    found = set()

    for alias, canonical_name in SKILL_ALIASES.items():
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

        if re.search(pattern, text):
            found.add(canonical_name)

    return sorted(found)


@debug_trace
def parse_job(job: JobInput) -> JobProfile:
    return JobProfile(
        title=job.title.strip(),
        company=job.company.strip(),
        skills=extract_skills(job.description),
        description=job.description.strip(),
    )
