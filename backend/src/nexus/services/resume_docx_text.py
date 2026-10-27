from html.parser import HTMLParser
import re

class _ResumeTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n• ")
        elif tag == "a":
            href = next((value for name, value in attrs if name == "href"), None)
            if href and href.startswith(("https://", "http://")):
                self.parts.append(f" ({href})")

    def handle_endtag(self, tag: str):
        if tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str):
        self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"[ \t]*\n[ \t]*", "\n", "".join(self.parts)).strip()


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        items = [_text(item) for item in value]
        return " · ".join(text for text in items if text)
    parser = _ResumeTextParser()
    parser.feed(str(value))
    return parser.text()
