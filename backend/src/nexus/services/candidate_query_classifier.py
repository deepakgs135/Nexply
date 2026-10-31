
"""Rule-based query intent classifier for NEXPLY."""

import re


INTENT_SECTION_MAP = {
    "SKILL_SEARCH": "skills",
    "PROJECT_SEARCH": "projects",
    "EXPERIENCE_SEARCH": "experience",
    "EDUCATION_SEARCH": "education",
    "CERTIFICATION_SEARCH": "certifications",
    "SUMMARY_SEARCH": "professional_summary",
    "AWARD_SEARCH": "awards",
    "PUBLICATION_SEARCH": "publications",
}


INTENT_PATTERNS = {
    "PROJECT_SEARCH": [
        r"\bprojects?\b",
        r"\bportfolio\b",
        r"\bthings\s+(?:they|he|she)\s+built\b",
    ],
    "SKILL_SEARCH": [
        r"\bskills?\b",
        r"\btechnologies\b",
        r"\bprogramming\s+languages?\b",
        r"\btools?\b",
        r"\bproficien(?:cy|t)\b",
    ],
    "EXPERIENCE_SEARCH": [
        r"\bwork\s+experience\b",
        r"\bprofessional\s+experience\b",
        r"\bemployment\s+history\b",
        r"\bjob\s+history\b",
        r"\bworked\b",
        r"\bexperience\b",
    ],
    "EDUCATION_SEARCH": [
        r"\beducation\b",
        r"\bdegrees?\b",
        r"\bqualifications?\b",
        r"\bacademic\b",
        r"\bacademic\s+background\b",
        r"\bcollege\b",
        r"\buniversity\b",
        r"\bgraduation\b",
        r"\bstudy\b",
        r"\bstudies\b",
    ],
    "CERTIFICATION_SEARCH": [
        r"\bcertifications?\b",
        r"\bcertificates?\b",
        r"\blicenses?\b",
    ],
    "SUMMARY_SEARCH": [
        r"\bprofessional\s+summary\b",
        r"\bprofile\s+summary\b",
        r"\bcandidate\s+summary\b",
    ],
    "AWARD_SEARCH": [
        r"\bawards?\b",
        r"\bachievements?\b",
        r"\brecognitions?\b",
    ],
    "PUBLICATION_SEARCH": [
        r"\bpublications?\b",
        r"\bresearch\s+papers?\b",
    ],
}


def classify_candidate_query(query: str) -> dict:
    """Identify the intended candidate information category."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    normalized_query = re.sub(
        r"\s+",
        " ",
        query.strip().lower(),
    )

    matched_intents = []

    for intent, patterns in INTENT_PATTERNS.items():
        if any(
            re.search(pattern, normalized_query)
            for pattern in patterns
        ):
            matched_intents.append(intent)

    if len(matched_intents) == 1:
        intent = matched_intents[0]
        source_section = INTENT_SECTION_MAP[intent]

    else:
        intent = "GENERAL_SEARCH"
        source_section = None

    return {
        "intent": intent,
        "source_section": source_section,
        "query": query.strip(),
    }
