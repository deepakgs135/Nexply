
import uuid


def _make_memory_id(
    app_id: str,
    memory_type: str,
    text: str,
) -> str:
    """
    Generate a deterministic UUID scoped to a candidate.

    Same candidate + same memory content = same UUID.
    Different candidates = different UUIDs.
    """
    raw = f"{app_id}:{memory_type}:{text}"

    return str(
        uuid.uuid5(uuid.NAMESPACE_URL, raw)
    )


def _clean_value(value) -> str:
    """Convert a profile value into clean readable text."""

    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(
            text for item in value
            if (text := _clean_value(item))
        )

    if isinstance(value, dict):
        return ", ".join(
            f"{key}: {cleaned}"
            for key, item in value.items()
            if (cleaned := _clean_value(item))
        )

    return str(value).strip()


def _build_text(data: dict, fields: list[str]) -> str:
    """Build readable text from selected dictionary fields."""

    parts = []

    for field in fields:
        value = _clean_value(data.get(field))

        if value:
            parts.append(
                f"{field.replace('_', ' ').title()}: {value}"
            )

    return ". ".join(parts)


def build_candidate_memories(profile: dict) -> list[dict]:
    """
    Convert a structured candidate profile into semantic memory chunks.

    Each memory contains:
    - memory_id: deterministic candidate-scoped UUID
    - memory_type: type of information
    - source_section: original profile section
    - source_index: position in the original section
    - text: readable semantic content
    """

    app_id = profile.get("app_id")

    if not app_id:
        raise ValueError(
            "Candidate profile must contain app_id."
        )

    memories = []

    def add_memory(
        memory_type: str,
        source_section: str,
        text: str,
        source_index: int | None = None,
    ):
        text = text.strip()

        if not text:
            return

        memory_id = _make_memory_id(
            app_id,
            memory_type,
            text,
        )

        memories.append({
            "memory_id": memory_id,
            "memory_type": memory_type,
            "source_section": source_section,
            "source_index": source_index,
            "text": text,
        })

    # 1. Professional summary
    add_memory(
        "professional_summary",
        "professional_summary",
        _clean_value(
            profile.get("professional_summary")
        ),
    )

    # 2. Skills
    for index, skill in enumerate(
        profile.get("skills") or []
    ):
        add_memory(
            "technical_skill",
            "skills",
            _clean_value(skill),
            index,
        )

    # 3. Work experience
    experience_fields = [
        "job_title",
        "company",
        "location",
        "employment_type",
        "start_date",
        "end_date",
        "description",
        "responsibilities",
        "achievements",
        "achievements_list",
        "technologies",
    ]

    for index, experience in enumerate(
        profile.get("experience") or []
    ):
        if isinstance(experience, dict):
            add_memory(
                "work_experience",
                "experience",
                _build_text(
                    experience,
                    experience_fields,
                ),
                index,
            )

    # 4. Projects
    project_fields = [
        "name",
        "role",
        "description",
        "responsibilities",
        "technologies",
        "outcomes",
        "achievements_list",
    ]

    for index, project in enumerate(
        profile.get("projects") or []
    ):
        if isinstance(project, dict):
            add_memory(
                "project",
                "projects",
                _build_text(
                    project,
                    project_fields,
                ),
                index,
            )

    # 5. Education
    education_fields = [
        "degree",
        "field_of_study",
        "area_of_study",
        "institution",
        "school_type",
        "location",
        "start_date",
        "end_date",
        "graduation_year",
        "cgpa_or_percentage",
        "honors",
        "coursework",
        "description",
    ]

    for index, education in enumerate(
        profile.get("education") or []
    ):
        if isinstance(education, dict):
            add_memory(
                "education",
                "education",
                _build_text(
                    education,
                    education_fields,
                ),
                index,
            )

    # 6. Certifications
    for index, certification in enumerate(
        profile.get("certifications") or []
    ):
        add_memory(
            "certification",
            "certifications",
            _clean_value(certification),
            index,
        )

    # 7. Awards
    for index, award in enumerate(
        profile.get("awards") or []
    ):
        add_memory(
            "award",
            "awards",
            _clean_value(award),
            index,
        )

    # 8. Publications
    publication_fields = [
        "title",
        "publisher",
        "date_string",
        "publication_date",
        "description",
        "responsibilities",
        "achievements_list",
    ]

    for index, publication in enumerate(
        profile.get("publications") or []
    ):
        if isinstance(publication, dict):
            add_memory(
                "publication",
                "publications",
                _build_text(
                    publication,
                    publication_fields,
                ),
                index,
            )

    # 9. Additional sections
    for index, section in enumerate(
        profile.get("additional_sections") or []
    ):
        if isinstance(section, dict):
            text = _build_text(
                section,
                [
                    "title",
                    "details",
                    "content_list",
                ],
            )

            add_memory(
                "additional_information",
                "additional_sections",
                text,
                index,
            )

    return memories
