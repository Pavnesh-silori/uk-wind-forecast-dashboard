from app.services.forecast_analysis import analyse_forecasts


def test_analysis_calculates_forecast_errors():
    actual_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "generation": 1000,
        },
        {
            "startTime": "2026-01-02T10:30:00Z",
            "generation": 1200,
        },
    ]

    forecast_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 1500,
        },
    ]

    result = analyse_forecasts(
        actual_records,
        forecast_records,
        cutoff_hour_utc=10,
    )

    assert result["message"] == "Analysis completed."

    metrics = result["metrics"]

    assert metrics["matched_intervals"] == 1
    assert metrics["mae"] == 400.0
    assert metrics["bias"] == -400.0
    assert metrics["rmse"] == 400.0
    assert metrics["mape_percent"] == 36.36


def test_analysis_selects_latest_eligible_forecast():
    actual_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "generation": 1000,
        },
        {
            "startTime": "2026-01-02T10:30:00Z",
            "generation": 1200,
        },
    ]

    forecast_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T08:00:00Z",
            "generation": 800,
        },
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T09:30:00Z",
            "generation": 900,
        },
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T10:30:00Z",
            "generation": 1100,
        },
    ]

    result = analyse_forecasts(
        actual_records,
        forecast_records,
        cutoff_hour_utc=10,
    )

    assert result["message"] == "Analysis completed."
    assert len(result["records"]) == 1

    record = result["records"][0]

    # Select the latest forecast published before the 10:00 UTC cutoff.
    assert record["forecast_generation"] == 900
    assert record["publishTime"] == "2026-01-01T09:30:00Z"


def test_analysis_handles_empty_actual_data():
    forecast_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 1000,
        }
    ]

    result = analyse_forecasts([], forecast_records)

    assert result["metrics"] == {}
    assert result["records"] == []
    assert result["message"] == "No actual-generation records found."



def test_analysis_handles_empty_forecast_data():
    actual_records = [
        {"startTime": "2026-01-02T10:00:00Z", "generation": 1000},
        {"startTime": "2026-01-02T10:30:00Z", "generation": 1200},
    ]

    result = analyse_forecasts(actual_records, [])

    assert result["metrics"] == {}
    assert result["records"] == []
    assert result["message"] == "No forecast records found."


def test_analysis_ignores_incomplete_hour_of_actual_data():
    # Only one half-hour reading exists, so the hour is incomplete.
    actual_records = [
        {"startTime": "2026-01-02T10:00:00Z", "generation": 1000},
    ]
    forecast_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 900,
        },
    ]

    result = analyse_forecasts(
        actual_records, forecast_records, cutoff_hour_utc=10
    )

    assert result["metrics"] == {}
    assert result["records"] == []
    assert "No matching hourly intervals" in result["message"]


def test_analysis_handles_zero_actual_generation():
    actual_records = [
        {"startTime": "2026-01-02T10:00:00Z", "generation": 0},
        {"startTime": "2026-01-02T10:30:00Z", "generation": 0},
    ]
    forecast_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 100,
        },
    ]

    result = analyse_forecasts(
        actual_records, forecast_records, cutoff_hour_utc=10
    )

    assert result["message"] == "Analysis completed."
    assert result["metrics"]["matched_intervals"] == 1
    assert result["metrics"]["mae"] == 100.0
    assert result["metrics"]["bias"] == -100.0
    assert result["metrics"]["mape_percent"] is None


def test_analysis_ignores_invalid_records():
    actual_records = [
        {"startTime": "2026-01-02T10:00:00Z", "generation": 1000},
        {"startTime": "2026-01-02T10:30:00Z", "generation": 1200},
        {"startTime": "invalid-timestamp", "generation": 500},
        {"startTime": "2026-01-02T11:00:00Z", "generation": "not-a-number"},
    ]
    forecast_records = [
        {
            "startTime": "2026-01-02T10:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 900,
        },
        {
            "startTime": "invalid-timestamp",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 800,
        },
    ]

    result = analyse_forecasts(
        actual_records, forecast_records, cutoff_hour_utc=10
    )

    assert result["message"] == "Analysis completed."
    assert result["metrics"]["matched_intervals"] == 1
    assert len(result["records"]) == 1


def test_analysis_returns_message_when_no_intervals_match():
    actual_records = [
        {"startTime": "2026-01-02T10:00:00Z", "generation": 1000},
        {"startTime": "2026-01-02T10:30:00Z", "generation": 1200},
    ]
    forecast_records = [
        {
            # Forecast delivery time does not match the actual hour.
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 900,
        },
    ]

    result = analyse_forecasts(
        actual_records, forecast_records, cutoff_hour_utc=10
    )

    assert result["metrics"] == {}
    assert result["records"] == []
    assert "No matching hourly intervals" in result["message"]