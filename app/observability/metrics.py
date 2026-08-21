"""Pure metric calculations for dashboards and reports."""

from app.models import ExecutionResult


def pass_rate(results: list[ExecutionResult]) -> float:
    executed = [result for result in results if result.status in {"PASSED", "FAILED"}]
    if not executed:
        return 0.0
    return round(sum(result.status == "PASSED" for result in executed) / len(executed) * 100, 2)
