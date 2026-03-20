"""
Samsung Health Data Parser for Suspect_2 Dataset.

Public API
==========
    get_exercise_heartbeat()      Per-second HR for a specific exercise on a given day
    get_sleep_duration_minutes()  Total sleep duration in minutes for a given night
    get_daily_activity_minutes()  Total active time in minutes for a given day
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import pandas as pd


DATA_DIR = Path("data/suspect_2")

_EXERCISE_TYPES = {
    0: "Other/Custom",
    1001: "Walking",
    1002: "Running",
    1003: "Hiking",
    2001: "Treadmill",
    2002: "Elliptical",
    10001: "Indoor Cycling",
    11007: "Outdoor Cycling",
    13001: "Pilates",
    13002: "Yoga",
    14001: "Swimming",
    15001: "Circuit Training",
    15002: "Strength Training",
    15003: "Stretching",
    15005: "Functional Training",
}


# =============================================================================
# Internal helpers
# =============================================================================

def _find_csv(data_dir: Path, pattern: str) -> Optional[Path]:
    files = list(data_dir.glob(pattern))
    return files[0] if files else None


def _load_csv(file_path: Path) -> pd.DataFrame:
    """Load a Samsung Health CSV, stripping the metadata row and trailing commas."""
    import io
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()[1:]  # skip metadata row
    cleaned = [line.rstrip().rstrip(",") + "\n" for line in lines]
    return pd.read_csv(io.StringIO("".join(cleaned)), on_bad_lines="skip")


def _ms_to_dt(ms: Union[int, float]) -> datetime:
    return datetime.fromtimestamp(ms / 1000)


def _json_path(data_dir: Path, data_type: str, filename: str) -> Optional[Path]:
    if not filename:
        return None
    return data_dir / "jsons" / data_type / filename[0].lower() / filename


# =============================================================================
# Exercise helpers
# =============================================================================

def _load_exercises(data_dir: Path) -> pd.DataFrame:
    csv_file = _find_csv(data_dir, "com.samsung.shealth.exercise.[0-9]*.csv")
    if not csv_file:
        raise FileNotFoundError(f"Exercise CSV not found in {data_dir}")

    df = _load_csv(csv_file)
    records = []
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row.get("com.samsung.health.exercise.start_time"))
            if pd.isna(start):
                continue
            ex_type = row.get("com.samsung.health.exercise.exercise_type")
            records.append({
                "exercise_id": row.get("com.samsung.health.exercise.datauuid"),
                "start_time": start,
                "exercise_type_label": _EXERCISE_TYPES.get(int(ex_type) if pd.notna(ex_type) else 0, "Unknown"),
            })
        except (ValueError, TypeError):
            continue

    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("start_time").reset_index(drop=True)
    return result


def _get_exercises_for_date(data_dir: Path, date) -> pd.DataFrame:
    df = _load_exercises(data_dir)
    df["date"] = df["start_time"].dt.date
    return df[df["date"] == date].drop(columns=["date"])


def _load_exercise_hr(data_dir: Path, exercise_id: str) -> pd.DataFrame:
    filename = f"{exercise_id}.com.samsung.health.exercise.live_data.json"
    path = _json_path(data_dir, "com.samsung.shealth.exercise", filename)
    if not path or not path.exists():
        return pd.DataFrame()

    with open(path) as f:
        data = json.load(f)

    records = [
        {"timestamp": _ms_to_dt(e["start_time"]), "heart_rate": e["heart_rate"], "exercise_id": exercise_id}
        for e in data if "heart_rate" in e
    ]
    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("timestamp").reset_index(drop=True)
    return result


# =============================================================================
# Sleep helpers
# =============================================================================

def _load_sleep_combined(data_dir: Path) -> pd.DataFrame:
    csv_file = _find_csv(data_dir, "com.samsung.shealth.sleep_combined.*.csv")
    if not csv_file:
        raise FileNotFoundError(f"Sleep combined CSV not found in {data_dir}")

    df = _load_csv(csv_file)
    records = []
    for _, row in df.iterrows():
        try:
            end = pd.to_datetime(row.get("end_time"))
            duration = int(row.get("sleep_duration", 0))
            if pd.isna(end):
                continue
            records.append({"end_time": end, "sleep_duration_min": duration})
        except (ValueError, TypeError):
            continue

    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("end_time").reset_index(drop=True)
    return result


def _load_sleep_sessions(data_dir: Path) -> pd.DataFrame:
    csv_file = _find_csv(data_dir, "com.samsung.shealth.sleep.*.csv")
    if not csv_file:
        raise FileNotFoundError(f"Sleep CSV not found in {data_dir}")

    df = _load_csv(csv_file)
    records = []
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row.get("com.samsung.health.sleep.start_time"))
            end = pd.to_datetime(row.get("com.samsung.health.sleep.end_time"))
            if pd.isna(start) or pd.isna(end):
                continue
            records.append({"end_time": end, "duration_hours": (end - start).total_seconds() / 3600})
        except (ValueError, TypeError):
            continue

    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("end_time").reset_index(drop=True)
    return result


# =============================================================================
# Activity helpers
# =============================================================================

def _load_activity_day_summary(data_dir: Path) -> pd.DataFrame:
    csv_file = _find_csv(data_dir, "com.samsung.shealth.activity.day_summary.*.csv")
    if not csv_file:
        raise FileNotFoundError(f"Activity day summary CSV not found in {data_dir}")

    df = _load_csv(csv_file)
    df["day_time"] = pd.to_datetime(df["day_time"])
    records = []
    for _, row in df.iterrows():
        try:
            day = row.get("day_time")
            if pd.isna(day):
                continue
            records.append({
                "date": day.date(),
                "active_time_min": int(row.get("active_time", 0)) / 60000,
            })
        except (ValueError, TypeError):
            continue

    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("date").reset_index(drop=True)
    return result


# =============================================================================
# Public API
# =============================================================================

def get_exercise_heartbeat(
    data_dir: Union[str, Path],
    date: Union[str, datetime],
    exercise_index: int = 0,
    start_strip: int = 0,
    end_strip: int = 0,
) -> pd.DataFrame:
    """Per-second heart rate for a specific exercise on a given day.

    Args:
        data_dir: Path to the Samsung Health export directory.
        date: Target date as "YYYY-MM-DD" string or datetime.
        exercise_index: Zero-based index of the exercise on that day (by start time).
        start_strip: Seconds to remove from the beginning of the recording.
        end_strip: Seconds to remove from the end of the recording.

    Returns:
        DataFrame with columns: timestamp, heart_rate, exercise_id.
        Empty DataFrame if no data is available.
    """
    if exercise_index < 0:
        raise IndexError(f"exercise_index must be >= 0, got {exercise_index}")

    data_dir = Path(data_dir)

    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()
    elif isinstance(date, datetime):
        date = date.date()

    exercises = _get_exercises_for_date(data_dir, date)
    if exercises.empty or exercise_index >= len(exercises):
        return pd.DataFrame(columns=["timestamp", "heart_rate", "exercise_id"])

    df = _load_exercise_hr(data_dir, exercises.iloc[exercise_index]["exercise_id"])

    if df.empty or (start_strip == 0 and end_strip == 0):
        return df

    start_time = df["timestamp"].iloc[0] + pd.Timedelta(seconds=start_strip)
    end_time = df["timestamp"].iloc[-1] - pd.Timedelta(seconds=end_strip)
    return df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)].reset_index(drop=True)


def get_sleep_duration_minutes(
    data_dir: Union[str, Path],
    date: Union[str, datetime],
) -> int:
    """Total sleep duration in minutes for the night ending on the given date.

    Uses sleep_combined (Samsung Watch detailed data) as primary source,
    falling back to raw sleep sessions if unavailable.

    Args:
        data_dir: Path to data directory.
        date: Wake-up date (the morning the sleep session ends).

    Returns:
        Total sleep duration in minutes, or 0 if no data is available.
    """
    data_dir = Path(data_dir)

    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()
    elif isinstance(date, datetime):
        date = date.date()

    try:
        df = _load_sleep_combined(data_dir)
        df["end_date"] = df["end_time"].dt.date
        night = df[df["end_date"] == date]
        if not night.empty:
            return int(night.iloc[0]["sleep_duration_min"])
    except Exception:
        pass

    try:
        df = _load_sleep_sessions(data_dir)
        df["end_date"] = df["end_time"].dt.date
        night = df[df["end_date"] == date]
        if not night.empty:
            return int(round(night.iloc[0]["duration_hours"] * 60))
    except Exception:
        pass

    return 0


def get_daily_activity_minutes(
    data_dir: Union[str, Path],
    date: Union[str, datetime],
) -> float:
    """Total active time in minutes for a specific date.

    Counts all movement (walking, running, other activity) throughout the day.

    Args:
        data_dir: Path to data directory.
        date: Target date as "YYYY-MM-DD" string or datetime.

    Returns:
        Total active time in minutes, or 0.0 if no data is available.
    """
    data_dir = Path(data_dir)

    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()
    elif isinstance(date, datetime):
        date = date.date()

    try:
        df = _load_activity_day_summary(data_dir)
        row = df[df["date"] == date]
        if not row.empty:
            return round(row.iloc[0]["active_time_min"], 1)
    except Exception:
        pass

    return 0.0
