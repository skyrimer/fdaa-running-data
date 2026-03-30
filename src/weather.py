import json
import urllib.request
from urllib.parse import urlencode

_EINDHOVEN_LAT = 51.4416
_EINDHOVEN_LON = 5.4697
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

EINDHOVEN_ALTITUDE_M = 17.0


def get_weather_for_date(date_str: str) -> tuple[float, float]:
    """Return (temperature_celsius, pressure_hpa) for Eindhoven on the given date.

    Fetches hourly data from the Open-Meteo archive API (free, no key required)
    and returns the daily mean temperature and surface pressure.

    Args:
        date_str: Date in 'YYYY-MM-DD' format.

    Returns:
        Tuple of (mean temperature in °C, mean surface pressure in hPa).
    """
    params = urlencode({
        "latitude": _EINDHOVEN_LAT,
        "longitude": _EINDHOVEN_LON,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": "temperature_2m,surface_pressure",
        "timezone": "Europe/Amsterdam",
    })
    url = f"{_ARCHIVE_URL}?{params}"

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read())

    hourly = data["hourly"]
    temps = [v for v in hourly["temperature_2m"] if v is not None]
    pressures = [v for v in hourly["surface_pressure"] if v is not None]

    if not temps or not pressures:
        raise ValueError(f"No weather data returned for {date_str}")

    return round(sum(temps) / len(temps), 2), round(sum(pressures) / len(pressures), 2)


def get_weather_for_dates(date_strs: list[str]) -> dict[str, tuple[float, float]]:
    """Batch fetch weather for multiple dates, returning one API call per date range.

    Args:
        date_strs: List of dates in 'YYYY-MM-DD' format.

    Returns:
        Dict mapping each date string to (temperature_celsius, pressure_hpa).
    """
    if not date_strs:
        return {}

    sorted_dates = sorted(date_strs)
    params = urlencode({
        "latitude": _EINDHOVEN_LAT,
        "longitude": _EINDHOVEN_LON,
        "start_date": sorted_dates[0],
        "end_date": sorted_dates[-1],
        "hourly": "temperature_2m,surface_pressure",
        "timezone": "Europe/Amsterdam",
    })
    url = f"{_ARCHIVE_URL}?{params}"

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read())

    hourly = data["hourly"]
    timestamps = hourly["time"]
    temps = hourly["temperature_2m"]
    pressures = hourly["surface_pressure"]

    date_temps: dict[str, list[float]] = {d: [] for d in date_strs}
    date_pressures: dict[str, list[float]] = {d: [] for d in date_strs}

    for ts, temp, pressure in zip(timestamps, temps, pressures):
        day = ts[:10]
        if day in date_temps:
            if temp is not None:
                date_temps[day].append(temp)
            if pressure is not None:
                date_pressures[day].append(pressure)

    result = {}
    for date_str in date_strs:
        t_vals = date_temps[date_str]
        p_vals = date_pressures[date_str]
        if not t_vals or not p_vals:
            raise ValueError(f"No weather data returned for {date_str}")
        result[date_str] = (
            round(sum(t_vals) / len(t_vals), 2),
            round(sum(p_vals) / len(p_vals), 2),
        )
    return result
