import json
import re
from collections.abc import Mapping


def first_value(source: Mapping, *keys: str):
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}): return value
    return None


def detail_strings(value) -> list[str]:
    if value is None or value == "": return []
    values = value if isinstance(value, list) else [value]
    return [item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
            for item in values if item is not None and item != ""]


def normalize_items(items, aliases: dict[str, tuple[str, ...]]):
    if not isinstance(items, list): return []
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
                value = list(dict.fromkeys(part for values in list_values for part in values)) or None
            else:
                value = candidates[0] if candidates else None
            if value is not None: entry[target] = value
            for alias in keys: entry.pop(alias, None)
        malformed = []
        for key in list(entry):
            if key in aliases or key in aliases.keys(): continue
            name = re.sub(r"[^a-z]+", " ", str(key).casefold()).strip()
            if "description" in name and ("null" in name or name != "description"):
                malformed.extend(detail_strings(entry.pop(key)))
        if malformed:
            entry["responsibilities"] = list(dict.fromkeys([*detail_strings(entry.get("responsibilities")), *malformed]))
        if isinstance(entry.get("description"), list):
            entry["responsibilities"] = list(dict.fromkeys([*detail_strings(entry.get("responsibilities")), *detail_strings(entry.pop("description"))]))
            entry["description"] = None
        normalized.append(entry)
    return normalized
