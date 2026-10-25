import pytest
from pydantic import ValidationError

from nexus.nlp.job_parser import JobInput, extract_skills, parse_job


def test_extract_skills_is_case_insensitive_deduplicated_and_sorted():
    result = extract_skills("PYTHON, Python; NLP and natural language processing; SQL")

    assert result == ["NLP", "Python", "SQL"]


def test_extract_skills_uses_whole_word_matches():
    result = extract_skills("pythonista and SQLAlchemy are not Python or SQL mentions")

    assert result == ["Python", "SQL"]


def test_parse_job_trims_fields_and_extracts_skills():
    job = JobInput(
        title="  Backend Engineer  ",
        company=" Sample Labs ",
        description="  Build Python APIs and use MongoDB for persistent storage.  ",
    )

    result = parse_job(job)

    assert result.title == "Backend Engineer"
    assert result.company == "Sample Labs"
    assert result.description.startswith("Build Python APIs")
    assert result.skills == ["MongoDB", "Python"]


def test_job_input_rejects_whitespace_only_fields():
    with pytest.raises(ValidationError):
        JobInput(title="  ", company=" ", description=" " * 20)
