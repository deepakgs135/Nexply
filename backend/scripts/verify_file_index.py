"""Check that the maintained project file index covers the local project tree."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "PROJECT_FILE_INDEX.md"
IGNORED_DIRECTORIES = {
    ".git", ".venv", "venv", "node_modules", ".pytest_cache",
    "__pycache__", "dist", "build", ".mypy_cache", ".ruff_cache",
}


def project_files() -> set[str]:
    """Return project-relative files, excluding generated dependency/cache trees."""
    found: set[str] = set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        if path.is_file():
            found.add(relative.as_posix())
    return found


def main() -> int:
    """Report index entries that are missing or refer to absent files."""
    if not INDEX.is_file():
        print(f"Missing index: {INDEX}")
        return 1
    indexed_text = INDEX.read_text(encoding="utf-8")
    files = project_files()
    missing = sorted(path for path in files if f"`{path}`" not in indexed_text)
    stale = sorted(
        line.split("`", 2)[1]
        for line in indexed_text.splitlines()
        if line.startswith("| `") and len(line.split("`", 2)) > 1
        and line.split("`", 2)[1] not in files
    )
    if missing or stale:
        for path in missing:
            print(f"Not documented: {path}")
        for path in stale:
            print(f"Stale index entry: {path}")
        return 1
    print(f"Project index covers all {len(files)} project files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
