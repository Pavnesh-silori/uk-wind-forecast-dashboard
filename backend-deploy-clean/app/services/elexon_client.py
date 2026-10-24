import httpx
from datetime import date


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"


def fetch_actual_generation(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Fetch actual UK wind generation from Elexon.

    Dates are inclusive for this function.
    """

    url = f"{BASE_URL}/FUELHH/stream"

    params = {
        "settlementDateFrom": start_date.isoformat(),
        "settlementDateTo": end_date.isoformat(),
        "fuelType": "WIND",
    }

    response = httpx.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected actual-generation response format")

    return data


def fetch_forecast_generation(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Fetch wind forecasts published during the requested date range.

    The end date is exclusive: forecasts are requested from midnight
    on start_date up to midnight on end_date.
    """

    url = f"{BASE_URL}/WINDFOR/stream"

    params = {
        "publishDateTimeFrom": f"{start_date.isoformat()}T00:00:00Z",
        "publishDateTimeTo": f"{end_date.isoformat()}T00:00:00Z",
    }

    response = httpx.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected forecast response format")

    return data