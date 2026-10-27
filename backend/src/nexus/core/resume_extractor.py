
from nexus.core.debug import debug_trace
import json
import re
from html import escape
from collections.abc import Mapping
from urllib.parse import urlparse

import requests
from pydantic import ValidationError

from nexus.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_PATH,
    OLLAMA_MODEL,
    OLLAMA_NUM_PREDICT,
    OLLAMA_TEMPERATURE,
    OLLAMA_THINK,
    OLLAMA_TIMEOUT_SECONDS,
)
from nexus.core.schemas.resume import ResumeData
from nexus.core.prompts.resume_extraction import RESUME_EXTRACTION_PROMPT


OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/{OLLAMA_CHAT_PATH.lstrip('/')}"


def _first(source: Mapping, *keys: str):
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _normalize_items(items, aliases: dict[str, tuple[str, ...]]):
    if not isinstance(items, list):
        return []
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        entry = dict(item)
        for target, keys in aliases.items():
            candidates = [item.get(key) for key in (target, *keys)]
            candidates = [value for value in candidates if value not in (None, "", [], {})]
            list_values = [value for value in candidates if isinstance(value, list)]
            if list_values:
                value = []
                for values in list_values:
                    for part in values:
                        if part not in value:
                            value.append(part)
                if not value:
                    value = None
            else:
                value = candidates[0] if candidates else None
            if value is not None:
                entry[target] = value
            for alias in keys:
                entry.pop(alias, None)
        # Some local models have emitted malformed keys such as
        # "description null, description" and placed the complete bullet list
        # under that key. Recover those source details into the canonical list.
        malformed_bullets = []
        for key in list(entry):
            if key in aliases or key in {target for target in aliases}:
                continue
            normalized_key = re.sub(r"[^a-z]+", " ", str(key).casefold()).strip()
            if "description" in normalized_key and ("null" in normalized_key or normalized_key != "description"):
                value = entry.pop(key)
                malformed_bullets.extend(_detail_strings(value))
        if malformed_bullets:
            entry["responsibilities"] = list(dict.fromkeys([
                *_detail_strings(entry.get("responsibilities")), *malformed_bullets,
            ]))
        # A list under description is a list of work bullets, not prose.
        if isinstance(entry.get("description"), list):
            entry["responsibilities"] = list(dict.fromkeys([
                *_detail_strings(entry.get("responsibilities")),
                *_detail_strings(entry.pop("description")),
            ]))
            entry["description"] = None
        normalized.append(entry)
    return normalized


def _detail_strings(value) -> list[str]:
    """Convert variable LLM detail shapes into the schema's list of strings."""
    if value is None or value == "":
        return []
    values = value if isinstance(value, list) else [value]
    return [
        item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        for item in values
        if item is not None and item != ""
    ]


def normalize_resume_payload(data: dict) -> dict:
    """Map common model naming variants into the stable resume schema."""
    normalized = dict(data)
    name = data.get("name")
    if isinstance(name, dict):
        full_name = " ".join(
            str(part).strip()
            for part in (name.get("first_name"), name.get("middle_name"), name.get("last_name"))
            if part and str(part).strip()
        )
        normalized["full_name"] = _first(data, "full_name") or full_name or None
    elif isinstance(name, str):
        normalized["full_name"] = _first(data, "full_name") or name
    normalized.pop("name", None)

    contact = data.get("contact_info") or data.get("contact_details")
    if isinstance(contact, dict):
        for field, aliases in {
            "email": ("email", "email_address"),
            "phone": ("phone", "phone_number", "mobile"),
            "location": ("location", "address", "city"),
        }.items():
            normalized[field] = _first(data, field) or _first(contact, *aliases)
    normalized.pop("contact_info", None)
    normalized.pop("contact_details", None)

    field_aliases = {
        "professional_title": ("title", "current_title", "headline"),
        "professional_summary": ("professional_summary_text", "summary", "profile_summary", "objective"),
        "skills": ("skills_list", "technical_skills", "key_skills"),
        "education": ("education_list", "academic_history", "qualifications"),
        "experience": ("experience_list", "work_experience", "employment_history", "job_history"),
        "projects": ("projects_list", "key_projects"),
        "certifications": ("certifications_list", "licenses", "licenses_and_certifications"),
        "languages": ("languages_list",),
        "websites": ("links", "profile_links", "social_links"),
        "awards": ("awards_list", "honors"),
        "publications": ("publications_list",),
        "volunteer_experience": ("volunteering", "volunteer_work"),
        "interests": ("interests_list",),
        "references": ("references_list",),
        "additional_sections": ("additional_sections_list", "other_sections"),
    }
    known_aliases = {alias for aliases in field_aliases.values() for alias in aliases}
    for field, aliases in field_aliases.items():
        current = normalized.get(field)
        source = _first(data, *aliases)
        if current in (None, "", [], {}) and source is not None:
            normalized[field] = source
        for alias in aliases:
            normalized.pop(alias, None)

    website_values = normalized.get("websites")
    if isinstance(website_values, str):
        normalized["websites"] = [website_values]
    elif isinstance(website_values, dict):
        normalized["websites"] = [
            f"{key.replace('_', ' ').title()}: {value}" if isinstance(value, str) else json.dumps({key: value}, ensure_ascii=False)
            for key, value in website_values.items()
        ]

    normalized["education"] = _normalize_items(normalized.get("education"), {
        "degree": ("degree_name", "qualification", "program"),
        "field_of_study": ("major", "field", "specialization"),
        "institution": ("university", "college", "school"),
        "graduation_year": ("year", "completion_year"),
    })
    normalized["experience"] = _normalize_items(normalized.get("experience"), {
        "company": ("company_name", "employer", "organization"),
        "job_title": ("title", "position", "role", "position_title"),
        "start_date": ("from", "start", "startDate", "start_date_string"),
        "end_date": ("to", "end", "endDate", "end_date_string"),
        "responsibilities": ("duties", "key_responsibilities", "job_description", "responsibilities_and_results", "responsibilities_and_achievements"),
        "location": ("location_string", "location_text", "work_location"),
        "achievements": ("key_achievements", "results", "accomplishments"),
        "technologies": ("tools", "tech_stack"),
    })
    # The profile editor's Description field is a rich-text block. Keep the
    # source's role bullets there as a real unordered list instead of exposing
    # model-generated alias keys as stray editable fields.
    for item in normalized["experience"]:
        if not isinstance(item, dict):
            continue
        bullets = list(dict.fromkeys([
            *_detail_strings(item.get("responsibilities")),
            *_detail_strings(item.get("achievements")),
        ]))
        if bullets:
            bullet_html = "<ul>" + "".join(f"<li>{escape(bullet)}</li>" for bullet in bullets) + "</ul>"
            current_description = item.get("description")
            item["description"] = f"{current_description}<p></p>{bullet_html}" if current_description else bullet_html
            item["responsibilities"] = []
            item["achievements"] = []
    normalized["projects"] = _normalize_items(normalized.get("projects"), {
        "name": ("project_name", "title"),
        "description": ("overview", "summary"),
        "technologies": ("tools", "tech_stack", "technology_stack"),
        "responsibilities": ("contributions", "key_contributions"),
        "outcomes": ("results", "achievements"),
    })
    normalized["publications"] = _normalize_items(normalized.get("publications"), {
        "title": ("name", "paper_title"),
        "publisher": ("journal", "organization", "venue"),
        "publication_date": ("date", "published_at"),
        "url": ("link",),
    })
    normalized["volunteer_experience"] = _normalize_items(normalized.get("volunteer_experience"), {
        "company": ("organization", "company_name"),
        "job_title": ("title", "role", "position"),
        "start_date": ("from", "start"),
        "end_date": ("to", "end"),
        "responsibilities": ("duties", "contributions"),
    })
    custom_sections = normalized.get("additional_sections")
    if isinstance(custom_sections, str):
        custom_sections = [{"title": "Additional information", "details": custom_sections}]
    elif isinstance(custom_sections, dict):
        if any(key in custom_sections for key in ("title", "section_name", "name", "heading")):
            custom_sections = [custom_sections]
        else:
            custom_sections = [
                {"title": key.replace("_", " ").title(), "details": value}
                for key, value in custom_sections.items()
            ]
    elif not isinstance(custom_sections, list):
        custom_sections = []

    converted_sections = []
    for section in custom_sections:
        if isinstance(section, str):
            converted_sections.append({"title": "Additional information", "details": _detail_strings(section)})
        elif isinstance(section, dict):
            converted = dict(section)
            converted["title"] = str(
                _first(section, "title", "section_name", "name", "heading")
                or "Additional information"
            )
            detail_value = _first(section, "details", "content", "items", "bullets", "description")
            converted["details"] = _detail_strings(detail_value)
            for alias in ("section_name", "heading", "content", "items", "bullets", "description"):
                converted.pop(alias, None)
            normalized_section = converted
            converted_sections.append(normalized_section)
        else:
            converted_sections.append({
                "title": "Additional information",
                "details": _detail_strings(section),
            })
    normalized["additional_sections"] = converted_sections

    for field in ("certifications", "languages", "skills", "websites", "awards", "interests", "references"):
        values = normalized.get(field)
        if not isinstance(values, list):
            continue
        normalized[field] = [
            " · ".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in entry.items() if value not in (None, "", [], {}))
            if isinstance(entry, dict) else entry
            for entry in values
        ]

    # Unexpected root-level fields are retained in the typed custom-section list.
    schema_fields = set(ResumeData.model_fields)
    custom = list(normalized.get("additional_sections") or [])
    for key in list(normalized):
        if key not in schema_fields and key not in known_aliases:
            value = normalized.pop(key)
            if value not in (None, "", [], {}):
                details = value if isinstance(value, list) else [value]
                custom.append({"title": key.replace("_", " ").title(), "details": [
                    detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
                    for detail in details
                ]})
    normalized["additional_sections"] = custom
    return normalized


def fill_contact_from_source(data: dict, parsed_text: str) -> dict:
    """Recover literal contact values from labels and a clear name heading."""
    lines = [re.sub(r"^---\s*Page\s+\d+\s*---\s*$", "", line, flags=re.I).strip()
             for line in parsed_text.splitlines()]
    lines = [line for line in lines if line]
    searchable_text = "\n".join(lines)
    if not data.get("email"):
        match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", searchable_text, re.I)
        if match:
            data["email"] = match.group(0)
    if not data.get("phone"):
        labeled = re.search(r"(?im)^\s*(?:phone|mobile|tel(?:ephone)?)\s*[:|\-]\s*(\+?[\d().\-\s]{7,})", searchable_text)
        match = labeled or re.search(r"(?<!\w)(\+?\d[\d().\-\s]{7,}\d)(?!\w)", searchable_text)
        if match:
            data["phone"] = (match.group(1) if labeled else match.group(1)).strip()
    if not data.get("location"):
        match = re.search(r"(?im)^\s*(?:location|address|based in)\s*[:|\-]\s*(.+?)\s*$", searchable_text)
        if match:
            data["location"] = match.group(1).strip()
    if not data.get("full_name"):
        labeled = re.search(r"(?im)^\s*(?:candidate\s+)?name\s*[:|\-]\s*(.+?)\s*$", searchable_text)
        if labeled:
            data["full_name"] = labeled.group(1).strip()
        elif lines:
            heading = lines[0].strip("|•· ")
            if (2 <= len(heading.split()) <= 5
                    and re.fullmatch(r"[\w.'’\-]+(?:\s+[\w.'’\-]+){1,4}", heading)
                    and "@" not in heading and not re.search(r"\d", heading)):
                data["full_name"] = heading
    return data


@debug_trace
def fill_profile_links_from_source(data: dict, parsed_text: str) -> dict:
    """Keep clickable professional profile URLs found in PDF annotations or text."""
    url_pattern = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.I)
    label_pattern = re.compile(r"(?i)(linkedin|github|leetcode|gitlab|kaggle|behance|dribbble|medium|portfolio|personal website|website)\s*[:|—-]\s*(https?://[^\s<>\"']+|www\.[^\s<>\"']+)")

    def tidy(url: str) -> str:
        return url.rstrip(".,;:!?)»]")

    def platform_for(url: str, explicit: str = "") -> str | None:
        parsed_url = urlparse(url if "://" in url else f"https://{url}")
        host = (parsed_url.hostname or "").lower().removeprefix("www.")
        for domain, title in {
            "linkedin.com": "LinkedIn", "github.com": "GitHub", "leetcode.com": "LeetCode",
            "gitlab.com": "GitLab", "kaggle.com": "Kaggle", "behance.net": "Behance",
            "dribbble.com": "Dribbble", "medium.com": "Medium", "scholar.google.com": "Google Scholar",
        }.items():
            if host == domain or host.endswith(f".{domain}"):
                if title == "GitHub" and len([part for part in parsed_url.path.split("/") if part]) > 1:
                    return None
                return title
        if "portfolio" in host or explicit.casefold() == "portfolio":
            return "Portfolio"
        if explicit.casefold() in {"personal website", "website"}:
            return "Website"
        return None

    found: list[str] = []
    source_lines = parsed_text.splitlines()
    for line in source_lines:
        for match in label_pattern.finditer(line):
            url = tidy(match.group(2))
            title = platform_for(url, match.group(1))
            if title:
                found.append(f"{title}: {url}")
        for match in url_pattern.finditer(line):
            url = tidy(match.group(0))
            title = platform_for(url)
            if title:
                found.append(f"{title}: {url}")

    for value in data.get("websites", []):
        if not isinstance(value, str):
            continue
        match = url_pattern.search(value)
        if not match:
            continue
        url = tidy(match.group(0))
        explicit = value[:match.start()].strip(" :|—-")
        title = platform_for(url, explicit)
        if title:
            found.append(f"{title}: {url}")

    data["websites"] = list(dict.fromkeys(found))
    return data


def fill_experience_dates_from_source(data: dict, parsed_text: str) -> dict:
    """Restore date ranges from a matching role/company line if the model omits one."""
    date_range = re.compile(
        r"(?P<start>(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\.?\s+)?(?:19|20)\d{2}|"
        r"(?:0?[1-9]|1[0-2])[/.-](?:19|20)?\d{2})\s*"
        r"(?:-|–|—|\bto\b|\bthrough\b)\s*"
        r"(?P<end>present|current|now|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
        r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(?:19|20)\d{2}|"
        r"(?:0?[1-9]|1[0-2])[/.-](?:19|20)?\d{2}|(?:19|20)\d{2})",
        re.I,
    )
    lines = [line.strip() for line in parsed_text.splitlines() if line.strip()]
    for role in data.get("experience", []):
        if not isinstance(role, dict) or (role.get("start_date") and role.get("end_date")):
            continue
        identifiers = [role.get(key) for key in ("company", "job_title") if role.get(key)]
        if not identifiers:
            continue
        for line in lines:
            if not all(str(value).casefold() in line.casefold() for value in identifiers):
                continue
            match = date_range.search(line)
            if match:
                role["start_date"] = role.get("start_date") or match.group("start").strip()
                role["end_date"] = role.get("end_date") or match.group("end").strip()
                break
    return data


@debug_trace
def fill_experience_locations_from_source(data: dict, parsed_text: str) -> dict:
    """Recover short location lines adjacent to each role's printed date range."""
    lines = [line.strip() for line in parsed_text.splitlines()]
    for role in data.get("experience", []):
        if not isinstance(role, dict) or role.get("location"):
            continue
        start, end = role.get("start_date"), role.get("end_date")
        if not start or not end:
            continue
        for index, line in enumerate(lines):
            folded = line.casefold()
            if str(start).casefold() not in folded or str(end).casefold() not in folded:
                continue
            for candidate in lines[index + 1:index + 4]:
                candidate = candidate.strip(" •\t")
                if not candidate or re.match(r"^---\s*Page\s+\d+\s*---$", candidate, re.I):
                    continue
                if candidate.startswith(("•", "-", "▪")) or len(candidate) > 100:
                    break
                if re.search(r"@|https?://|\b(experience|education|skills|projects)\b", candidate, re.I):
                    break
                role["location"] = candidate
                break
            if role.get("location"):
                break
    return data


@debug_trace
def extract_resume_data(parsed_text: str) -> dict:
    """Extract structured resume data using local Ollama."""
    if not parsed_text or not parsed_text.strip():
        raise ValueError("Resume text cannot be empty.")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "think": OLLAMA_THINK,
            "format": ResumeData.model_json_schema(),
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_NUM_PREDICT,
            },
            "messages": [
                {
                    "role": "system",
                    "content": RESUME_EXTRACTION_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Use exactly these standard property names: full_name, email, "
                        "phone, location, professional_title, professional_summary, "
                        "skills, education, experience, projects, certifications, "
                        "languages, websites, awards, publications, volunteer_experience, "
                        "interests, references, additional_sections. Put the person's "
                        "full name into full_name, contact values into their matching "
                        "top-level properties, job title into experience.job_title, "
                        "dates into start_date/end_date, and every job bullet into "
                        "responsibilities or achievements. Extract every supported "
                        "resume detail and do not omit items to shorten the response. "
                        "Source text follows:\n\n"
                        f"<resume_text>\n{parsed_text}\n</resume_text>"
                    ),
                },
            ],
        },
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    result = response.json()

    message = result.get("message")
    if not isinstance(message, dict):
        raise ValueError("Ollama response is missing its message object.")

    raw_json = message.get("content")
    if not isinstance(raw_json, str) or not raw_json.strip():
        done_reason = result.get("done_reason", "unknown")
        raise ValueError(
            f"Ollama returned empty content (done_reason={done_reason})."
        )

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Ollama returned invalid JSON.") from exc

    data = normalize_resume_payload(data)
    data = fill_contact_from_source(data, parsed_text)
    data = fill_profile_links_from_source(data, parsed_text)
    data = fill_experience_dates_from_source(data, parsed_text)
    data = fill_experience_locations_from_source(data, parsed_text)

    try:
        validated = ResumeData.model_validate(data)
    except ValidationError as exc:
        issues = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['type']}"
            for issue in exc.errors(include_input=False)
        )
        raise ValueError(
            f"Ollama response does not match ResumeData: {issues}"
        ) from exc

    return validated.model_dump()
