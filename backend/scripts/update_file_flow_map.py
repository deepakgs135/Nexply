"""Refresh the import-level file connection map in PROJECT_FILE_INDEX.md."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "PROJECT_FILE_INDEX.md"
START = "<!-- BEGIN GENERATED FILE FLOW MAP -->"
END = "<!-- END GENERATED FILE FLOW MAP -->"
CODE_ROOTS = (ROOT / "src", ROOT / "frontend/src", ROOT / "tests", ROOT / "scripts")
EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".css")


def module_name(path: Path) -> str:
    relative = path.relative_to(ROOT / "src").with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_ts_import(source: Path, specifier: str, known: set[Path]) -> Path | None:
    candidate = (source.parent / specifier).resolve()
    options = [candidate, *(Path(str(candidate) + ext) for ext in EXTENSIONS)]
    options.extend(candidate / f"index{ext}" for ext in EXTENSIONS)
    return next((item for item in options if item in known), None)


def python_connections(source: Path, known_modules: dict[str, Path]) -> set[Path]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    targets: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in known_modules:
                    targets.add(known_modules[alias.name])
        if not isinstance(node, ast.ImportFrom):
            continue
        base = node.module or ""
        if node.level:
            package = module_name(source).split(".")
            base = ".".join(package[: len(package) - node.level + 1] + ([base] if base else []))
        if base in known_modules:
            targets.add(known_modules[base])
        for alias in node.names:
            child = f"{base}.{alias.name}".strip(".")
            if child in known_modules:
                targets.add(known_modules[child])
    targets.discard(source)
    return targets


def connections(source: Path, known: set[Path], known_modules: dict[str, Path]) -> set[Path]:
    if source.suffix == ".py":
        return python_connections(source, known_modules)
    content = source.read_text(encoding="utf-8")
    pattern = r"@import\s+[\"']([^\"']+)|(?:from\s*|import\s*)[\"']([^\"']+)"
    specs = (left or right for left, right in re.findall(pattern, content))
    return {target for spec in specs if spec.startswith(".")
            if (target := resolve_ts_import(source, spec, known)) is not None}


def render_flow_map() -> str:
    files = sorted(path for folder in CODE_ROOTS for path in folder.rglob("*")
                   if path.is_file() and path.suffix in EXTENSIONS)
    known = {path.resolve() for path in files}
    modules = {module_name(path): path.resolve() for path in files
               if path.is_relative_to(ROOT / "src") and path.suffix == ".py"}
    rows = ["| File | Direct project file connections |", "|---|---|"]
    for source in files:
        targets = sorted(connections(source, known, modules))
        names = ", ".join(f"`{path.relative_to(ROOT).as_posix()}`" for path in targets)
        rows.append(f"| `{source.relative_to(ROOT).as_posix()}` | {names or 'No direct local imports; see its role above.'} |")
    return "\n".join(rows)


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("Add the generated-flow-map markers to PROJECT_FILE_INDEX.md first.")
    begin = text.index(START) + len(START)
    finish = text.index(END, begin)
    updated = text[:begin] + "\n\n" + render_flow_map() + "\n\n" + text[finish:]
    INDEX.write_text(updated, encoding="utf-8")
    print("Updated the file-level connection map in PROJECT_FILE_INDEX.md.")


if __name__ == "__main__":
    main()
