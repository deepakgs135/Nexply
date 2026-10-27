import re

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
