"""Validate externally versioned prompt metadata."""

from pathlib import Path

REQUIRED = ("name:", "version:", "agent:")


def main() -> None:
    paths = sorted(Path("prompts").glob("*/v*.md"))
    if not paths:
        raise SystemExit("No prompt files found")
    failures: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or any(field not in text[:200] for field in REQUIRED):
            failures.append(str(path))
    if failures:
        raise SystemExit("Invalid prompt metadata: " + ", ".join(failures))
    print(f"Validated {len(paths)} versioned prompts")


if __name__ == "__main__":
    main()
