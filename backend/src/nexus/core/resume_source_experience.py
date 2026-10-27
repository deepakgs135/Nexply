import re
from nexus.core.debug import debug_trace

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
