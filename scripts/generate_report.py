"""Generate a Markdown evaluation report from deterministic evidence."""

from pathlib import Path

from app.evaluation.deterministic import evaluate_dataset


def main() -> None:
    report = evaluate_dataset()
    lines = ["# Agent Evaluation Report", ""]
    for key, value in report.items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    destination = Path("evaluation-report.md")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
