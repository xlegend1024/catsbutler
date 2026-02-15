from services.metrics_service import measure


def test_measure_reports_elapsed_ms():
    result = measure(lambda: "ok")
    assert result.value == "ok"
    assert result.elapsed_ms >= 0
