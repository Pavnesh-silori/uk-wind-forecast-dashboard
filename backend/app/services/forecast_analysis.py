import pandas as pd
def analyse_forecasts(
    actual_records: list[dict],
    forecast_records: list[dict],
    cutoff_hour_utc: int = 10,
) -> dict:
    """
    Compare hourly actual wind generation with the latest eligible forecast.

    Assumption:
    The purchasing cutoff is 10:00 UTC on the day before delivery.
    This is a configurable analytical assumption, not a confirmed market rule.
    """

    if not actual_records:
        return {
            "metrics": {},
            "records": [],
            "message": "No actual-generation records found.",
        }

    if not forecast_records:
        return {
            "metrics": {},
            "records": [],
            "message": "No forecast records found.",
        }

    actual = pd.DataFrame(actual_records)
    forecast = pd.DataFrame(forecast_records)

    required_actual = {"startTime", "generation"}
    required_forecast = {"startTime", "publishTime", "generation"}

    if not required_actual.issubset(actual.columns):
        raise ValueError("Actual data is missing required fields.")

    if not required_forecast.issubset(forecast.columns):
        raise ValueError("Forecast data is missing required fields.")

    # Parse timestamps and generation values.
    actual["startTime"] = pd.to_datetime(
        actual["startTime"], utc=True, errors="coerce"
    )
    actual["generation"] = pd.to_numeric(
        actual["generation"], errors="coerce"
    )

    forecast["startTime"] = pd.to_datetime(
        forecast["startTime"], utc=True, errors="coerce"
    )
    forecast["publishTime"] = pd.to_datetime(
        forecast["publishTime"], utc=True, errors="coerce"
    )
    forecast["generation"] = pd.to_numeric(
        forecast["generation"], errors="coerce"
    )

    actual = actual.dropna(subset=["startTime", "generation"])
    forecast = forecast.dropna(
        subset=["startTime", "publishTime", "generation"]
    )

    # Aggregate half-hourly actual readings into hourly averages.
    # This assumes generation is average power in MW.
    actual["hour"] = actual["startTime"].dt.floor("h")

    actual_hourly = (
        actual.groupby("hour")["generation"]
        .agg(["mean", "count"])
        .reset_index()
    )

    # Keep only hours with both expected half-hourly readings.
    actual_hourly = actual_hourly[actual_hourly["count"] == 2]
    actual_hourly = actual_hourly.rename(
        columns={"hour": "startTime", "mean": "actual_generation"}
    )

    # Calculate the assumed cutoff for each delivery hour.
    forecast["cutoff"] = (
        forecast["startTime"].dt.normalize()
        - pd.Timedelta(days=1)
        + pd.Timedelta(hours=cutoff_hour_utc)
    )

    # Prevent look-ahead bias: exclude forecasts published after cutoff.
    eligible = forecast[
        forecast["publishTime"] <= forecast["cutoff"]
    ].copy()

    # Select the latest eligible publication per delivery hour.
    eligible = eligible.sort_values("publishTime")
    latest_forecast = eligible.drop_duplicates(
        subset=["startTime"], keep="last"
    )

    latest_forecast = latest_forecast[
        ["startTime", "publishTime", "generation"]
    ].rename(columns={"generation": "forecast_generation"})

    # Compare only matching hourly delivery intervals.
    merged = actual_hourly.merge(
        latest_forecast,
        on="startTime",
        how="inner",
    )

    if merged.empty:
        return {
            "metrics": {},
            "records": [],
            "message": (
                "No matching hourly intervals found. "
                "Check the source data and cutoff assumption."
            ),
        }

    # Forecast error: positive means actual generation exceeded forecast.
    merged["error"] = (
        merged["actual_generation"] - merged["forecast_generation"]
    )
    merged["absolute_error"] = merged["error"].abs()
    merged["squared_error"] = merged["error"] ** 2

    # MAPE is undefined when actual generation is zero.
    nonzero_actual = merged["actual_generation"].abs() > 0

    if nonzero_actual.any():
        mape = (
            merged.loc[nonzero_actual, "absolute_error"]
            / merged.loc[nonzero_actual, "actual_generation"].abs()
        ).mean() * 100
    else:
        mape = None

    # Coverage is measured against all 744 expected hourly intervals.
    expected_hours = 31 * 24
    matched_hours = len(merged)

    metrics = {
        "expected_hourly_intervals": expected_hours,
        "matched_intervals": int(matched_hours),
        "missing_intervals": int(expected_hours - matched_hours),
        "coverage_percent": round(
            matched_hours / expected_hours * 100, 2
        ),
        "mae": round(float(merged["absolute_error"].mean()), 2),
        "rmse": round(float(merged["squared_error"].mean() ** 0.5), 2),
        "bias": round(float(merged["error"].mean()), 2),
        "mape_percent": round(float(mape), 2) if mape is not None else None,
        "cutoff_hour_utc": cutoff_hour_utc,
    }

    merged["startTime"] = merged["startTime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    merged["publishTime"] = merged["publishTime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    return {
        "metrics": metrics,
        "records": merged.drop(
            columns=["squared_error"]
        ).to_dict(orient="records"),
        "message": "Analysis completed.",
    }