"""Run offline deterministic agent evaluation and enforce the quality gate."""

import argparse
import json

from app.evaluation.deterministic import evaluate_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider", default="mock", choices=("mock", "openai", "azure_openai", "anthropic")
    )
    args = parser.parse_args()
    if args.provider != "mock":
        print(
            "Real-provider qualitative judging is opt-in; deterministic checks still run locally."
        )
    report = evaluate_dataset()
    print(json.dumps(report, indent=2))
    if not report["gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
