from app.evaluation.deterministic import detect_unsupported_references, evaluate_dataset


def test_evaluation_dataset_has_expected_size_and_passes() -> None:
    report = evaluate_dataset()
    assert 30 <= report["case_count"] <= 50
    assert report["gate_passed"]


def test_hallucination_check_detects_unknown_ids() -> None:
    assert detect_unsupported_references(["REQ-1", "API-MADE-UP"], {"REQ-1"}) == ["API-MADE-UP"]
