import re
from urllib.parse import urlparse
from nexus.core.debug import debug_trace

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
