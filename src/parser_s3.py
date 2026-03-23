import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

APPLE_WATCH_SOURCE = "Trinity\u2019s Apple\xa0Watch"
WORKOUT_TYPE_RUNNING = "HKWorkoutActivityTypeRunning"


def _parse_records(xml_path: Path):
    """Parse all heart rate, step, and workout records from Apple Health XML,
    filtering to Apple Watch only.

    Args:
        xml_path: Path to the Apple Health export.xml file.

    Returns:
        Tuple of (heart_rates, steps, workouts) lists.
    """
    print("Parsing export.xml... (this may take a moment)")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    heart_rates = []
    steps = []
    workouts = []

    for record in root.iter("Record"):
        if record.get("sourceName") != APPLE_WATCH_SOURCE:
            continue

        t = record.get("type", "")
        if t == "HKQuantityTypeIdentifierHeartRate":
            heart_rates.append({
                "timestamp": datetime.fromisoformat(record.get("startDate")),
                "heart_rate": float(record.get("value")),
            })
        elif t == "HKQuantityTypeIdentifierStepCount":
            steps.append({
                "startDate": datetime.fromisoformat(record.get("startDate")),
                "endDate": datetime.fromisoformat(record.get("endDate")),
                "value": float(record.get("value")),
            })

    for workout in root.iter("Workout"):
        if workout.get("sourceName") != APPLE_WATCH_SOURCE:
            continue
        if workout.get("workoutActivityType") != WORKOUT_TYPE_RUNNING:
            continue
        workouts.append({
            "startDate": datetime.fromisoformat(workout.get("startDate")),
            "endDate": datetime.fromisoformat(workout.get("endDate")),
        })

    heart_rates.sort(key=lambda x: x["timestamp"])
    steps.sort(key=lambda x: x["startDate"])
    workouts.sort(key=lambda x: x["startDate"])

    return heart_rates, steps, workouts


def _get_workout_window(
    workouts: list[dict],
    date_str: str,
    manual_start: str | None,
    manual_end: str | None,
) -> tuple[datetime, datetime]:
    """Resolve the run window for a given date, either from workout records or manual override.

    Args:
        workouts: Parsed workout records from _parse_records().
        date_str: Date string in YYYY-MM-DD format.
        manual_start: Manual start time string in HH:MM:SS format, or None to use workout record.
        manual_end: Manual end time string in HH:MM:SS format, or None to use workout record.

    Returns:
        Tuple of (start_datetime, end_datetime).
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    if manual_start and manual_end:
        tz = workouts[0]["startDate"].tzinfo if workouts else None
        start = datetime.fromisoformat(f"{date_str}T{manual_start}").replace(tzinfo=tz)
        end = datetime.fromisoformat(f"{date_str}T{manual_end}").replace(tzinfo=tz)
        return start, end

    day_workouts = [w for w in workouts if w["startDate"].date() == target_date]

    if not day_workouts:
        raise ValueError(
            f"No running workout found for {date_str}. "
            "Provide a manual_start and manual_end override instead."
        )
    if len(day_workouts) > 1:
        raise ValueError(
            f"Multiple running workouts found for {date_str}. "
            "Provide a manual_start and manual_end override to specify which one."
        )

    return day_workouts[0]["startDate"], day_workouts[0]["endDate"]


def get_exercise_heartbeat(
    heart_rates: list[dict],
    workouts: list[dict],
    date_str: str,
    start_strip: int = 0,
    end_strip: int = 0,
    manual_start: str | None = None,
    manual_end: str | None = None,
) -> list[dict]:
    """Extract per-second heart rate data within the run window for a given date.

    Args:
        heart_rates: Parsed heart rate records from _parse_records().
        workouts: Parsed workout records from _parse_records().
        date_str: Date string in YYYY-MM-DD format.
        start_strip: Seconds to strip from the start of the session.
        end_strip: Seconds to strip from the end of the session.
        manual_start: Manual start time in HH:MM:SS format, overrides workout record.
        manual_end: Manual end time in HH:MM:SS format, overrides workout record.

    Returns:
        List of dicts with 'timestamp' and 'heart_rate' keys.
    """
    window_start, window_end = _get_workout_window(workouts, date_str, manual_start, manual_end)

    if start_strip > 0:
        window_start += timedelta(seconds=start_strip)
    if end_strip > 0:
        window_end -= timedelta(seconds=end_strip)

    records = [
        r for r in heart_rates
        if window_start <= r["timestamp"] <= window_end
    ]

    if not records:
        raise ValueError(f"No heart rate data found within run window for {date_str}.")

    # Forward-fill from window_start to window_end, using the first known
    # HR value to backfill any gap before the first actual sample
    pre_window = [r for r in heart_rates if r["timestamp"] < window_start]
    first_hr = int(pre_window[-1]["heart_rate"]) if pre_window else int(records[0]["heart_rate"])
    # Build a lookup of timestamp -> heart_rate from actual samples
    sample_map = {int(r["timestamp"].timestamp()): int(r["heart_rate"]) for r in records}
    per_second = []
    current_hr = first_hr
    total_seconds = int((window_end - window_start).total_seconds())
    for offset in range(total_seconds):
        ts = window_start + timedelta(seconds=offset)
        ts_key = int(ts.timestamp())
        if ts_key in sample_map:
            current_hr = sample_map[ts_key]
        per_second.append({
            "timestamp": ts.isoformat(),
            "heart_rate": current_hr,
        })
    return per_second

def get_daily_steps(steps: list[dict], date_str: str) -> float:
    """Get total step count for a given calendar day.

    Args:
        steps: Parsed step records from _parse_records().
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        Total step count as a float.
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    return sum(
        r["value"] for r in steps
        if r["startDate"].date() == target_date
    )