# import xml.etree.ElementTree as ET
# from datetime import datetime, timedelta
# from pathlib import Path
#
# APPLE_WATCH_SOURCE = "Trinity\u2019s Apple\xa0Watch"
# WORKOUT_TYPE_RUNNING = "HKWorkoutActivityTypeRunning"
#
#
# def _parse_records(xml_path: Path):
#     """Parse all heart rate, step, and workout records from Apple Health XML,
#     filtering to Apple Watch only.
#
#     Args:
#         xml_path: Path to the Apple Health export.xml file.
#
#     Returns:
#         Tuple of (heart_rates, steps, workouts) lists.
#     """
#     print("Parsing export.xml... (this may take a moment)")
#     tree = ET.parse(xml_path)
#     root = tree.getroot()
#
#     heart_rates = []
#     steps = []
#     workouts = []
#
#     for record in root.iter("Record"):
#         if record.get("sourceName") != APPLE_WATCH_SOURCE:
#             continue
#
#         t = record.get("type", "")
#         if t == "HKQuantityTypeIdentifierHeartRate":
#             heart_rates.append({
#                 "timestamp": datetime.fromisoformat(record.get("startDate")),
#                 "heart_rate": float(record.get("value")),
#             })
#         elif t == "HKQuantityTypeIdentifierStepCount":
#             steps.append({
#                 "startDate": datetime.fromisoformat(record.get("startDate")),
#                 "endDate": datetime.fromisoformat(record.get("endDate")),
#                 "value": float(record.get("value")),
#             })
#
#     for workout in root.iter("Workout"):
#         if workout.get("sourceName") != APPLE_WATCH_SOURCE:
#             continue
#         if workout.get("workoutActivityType") != WORKOUT_TYPE_RUNNING:
#             continue
#         workouts.append({
#             "startDate": datetime.fromisoformat(workout.get("startDate")),
#             "endDate": datetime.fromisoformat(workout.get("endDate")),
#         })
#
#     heart_rates.sort(key=lambda x: x["timestamp"])
#     steps.sort(key=lambda x: x["startDate"])
#     workouts.sort(key=lambda x: x["startDate"])
#
#     return heart_rates, steps, workouts
#
#
# def _get_workout_window(
#     workouts: list[dict],
#     date_str: str,
#     manual_start: str | None,
#     manual_end: str | None,
# ) -> tuple[datetime, datetime]:
#     """Resolve the run window for a given date, either from workout records or manual override.
#
#     Args:
#         workouts: Parsed workout records from _parse_records().
#         date_str: Date string in YYYY-MM-DD format.
#         manual_start: Manual start time string in HH:MM:SS format, or None to use workout record.
#         manual_end: Manual end time string in HH:MM:SS format, or None to use workout record.
#
#     Returns:
#         Tuple of (start_datetime, end_datetime).
#     """
#     target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#
#     if manual_start and manual_end:
#         tz = workouts[0]["startDate"].tzinfo if workouts else None
#         start = datetime.fromisoformat(f"{date_str}T{manual_start}").replace(tzinfo=tz)
#         end = datetime.fromisoformat(f"{date_str}T{manual_end}").replace(tzinfo=tz)
#         return start, end
#
#     day_workouts = [w for w in workouts if w["startDate"].date() == target_date]
#
#     if not day_workouts:
#         raise ValueError(
#             f"No running workout found for {date_str}. "
#             "Provide a manual_start and manual_end override instead."
#         )
#     if len(day_workouts) > 1:
#         raise ValueError(
#             f"Multiple running workouts found for {date_str}. "
#             "Provide a manual_start and manual_end override to specify which one."
#         )
#
#     return day_workouts[0]["startDate"], day_workouts[0]["endDate"]
#
#
# def get_exercise_heartbeat(
#     heart_rates: list[dict],
#     workouts: list[dict],
#     date_str: str,
#     start_strip: int = 0,
#     end_strip: int = 0,
#     manual_start: str | None = None,
#     manual_end: str | None = None,
# ) -> list[dict]:
#     """Extract per-second heart rate data within the run window for a given date.
#
#     Args:
#         heart_rates: Parsed heart rate records from _parse_records().
#         workouts: Parsed workout records from _parse_records().
#         date_str: Date string in YYYY-MM-DD format.
#         start_strip: Seconds to strip from the start of the session.
#         end_strip: Seconds to strip from the end of the session.
#         manual_start: Manual start time in HH:MM:SS format, overrides workout record.
#         manual_end: Manual end time in HH:MM:SS format, overrides workout record.
#
#     Returns:
#         List of dicts with 'timestamp' and 'heart_rate' keys.
#     """
#     window_start, window_end = _get_workout_window(workouts, date_str, manual_start, manual_end)
#
#     if start_strip > 0:
#         window_start += timedelta(seconds=start_strip)
#     if end_strip > 0:
#         window_end -= timedelta(seconds=end_strip)
#
#     records = [
#         r for r in heart_rates
#         if window_start <= r["timestamp"] <= window_end
#     ]
#
#     if not records:
#         raise ValueError(f"No heart rate data found within run window for {date_str}.")
#
#     # Forward-fill from window_start to window_end, using the first known
#     # HR value to backfill any gap before the first actual sample
#     pre_window = [r for r in heart_rates if r["timestamp"] < window_start]
#     first_hr = int(pre_window[-1]["heart_rate"]) if pre_window else int(records[0]["heart_rate"])
#     # Build a lookup of timestamp -> heart_rate from actual samples
#     sample_map = {int(r["timestamp"].timestamp()): int(r["heart_rate"]) for r in records}
#     per_second = []
#     current_hr = first_hr
#     total_seconds = int((window_end - window_start).total_seconds())
#     for offset in range(total_seconds):
#         ts = window_start + timedelta(seconds=offset)
#         ts_key = int(ts.timestamp())
#         if ts_key in sample_map:
#             current_hr = sample_map[ts_key]
#         per_second.append({
#             "timestamp": ts.isoformat(),
#             "heart_rate": current_hr,
#         })
#     return per_second
#
# def get_daily_steps(steps: list[dict], date_str: str) -> float:
#     """Get total step count for a given calendar day.
#
#     Args:
#         steps: Parsed step records from _parse_records().
#         date_str: Date string in YYYY-MM-DD format.
#
#     Returns:
#         Total step count as a float.
#     """
#     target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#
#     return sum(
#         r["value"] for r in steps
#         if r["startDate"].date() == target_date
#     )

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

    Gaps between raw watch samples are filled using linear interpolation rather
    than forward-fill. Rationale: this function commits to a regular per-second
    grid, so every second must have a value. Forward-fill populates that grid
    with stale readings — identical repeated values that artificially suppress
    variance during transitions and inflate it at sample boundaries. Linear
    interpolation instead estimates the most physically plausible HR for each
    gap second, consistent with the fact that heart rate is a smoothly varying
    continuous signal that cannot jump instantaneously. For the typical gap
    sizes seen in Apple Watch data (<5s, occasionally up to ~30s), the
    interpolated values introduce negligible bias in session mean HR and produce
    a more honest estimate of within-session HR variance than forward-fill.

    The session boundary (before the first sample, after the last) is handled
    by anchoring to the nearest known value outside the window where available,
    falling back to the first/last in-window sample otherwise.

    Args:
        heart_rates: Parsed heart rate records from _parse_records().
        workouts: Parsed workout records from _parse_records().
        date_str: Date string in YYYY-MM-DD format.
        start_strip: Seconds to strip from the start of the session.
        end_strip: Seconds to strip from the end of the session.
        manual_start: Manual start time in HH:MM:SS format, overrides workout record.
        manual_end: Manual end time in HH:MM:SS format, overrides workout record.

    Returns:
        List of dicts with 'timestamp' (ISO 8601 string) and 'heart_rate' (int) keys,
        one entry per second for the full session window.
    """
    window_start, window_end = _get_workout_window(workouts, date_str, manual_start, manual_end)

    if start_strip > 0:
        window_start += timedelta(seconds=start_strip)
    if end_strip > 0:
        window_end -= timedelta(seconds=end_strip)

    # Collect in-window samples
    in_window = [
        r for r in heart_rates
        if window_start <= r["timestamp"] <= window_end
    ]

    if not in_window:
        raise ValueError(f"No heart rate data found within run window for {date_str}.")

    total_seconds = int((window_end - window_start).total_seconds())

    # Build anchor points for interpolation.
    # We include one sample before and one after the window (if available) so
    # that the interpolation has a gradient to work with at the boundaries,
    # rather than flat-filling the leading/trailing edge.
    pre_window  = [r for r in heart_rates if r["timestamp"] < window_start]
    post_window = [r for r in heart_rates if r["timestamp"] > window_end]

    anchor_before = pre_window[-1]  if pre_window  else None
    anchor_after  = post_window[0]  if post_window else None

    # Assemble all anchor points as (elapsed_seconds, hr) pairs.
    # elapsed_seconds is relative to window_start; anchors outside the window
    # get negative or >total_seconds offsets, which is fine for interpolation.
    def to_elapsed(ts: datetime) -> float:
        return (ts - window_start).total_seconds()

    anchors: list[tuple[float, float]] = []
    if anchor_before:
        anchors.append((to_elapsed(anchor_before["timestamp"]), anchor_before["heart_rate"]))
    for r in in_window:
        anchors.append((to_elapsed(r["timestamp"]), r["heart_rate"]))
    if anchor_after:
        anchors.append((to_elapsed(anchor_after["timestamp"]), anchor_after["heart_rate"]))

    anchors.sort(key=lambda x: x[0])
    elapsed_known = [a[0] for a in anchors]
    hr_known      = [a[1] for a in anchors]

    # Linear interpolation over the per-second grid.
    # numpy is not imported to keep dependencies minimal; we implement piecewise
    # linear interpolation manually using the sorted anchor list.
    def lerp(t: float) -> int:
        """Return linearly interpolated HR at elapsed time t (seconds)."""
        # Clamp to boundary values if t is outside anchor range
        if t <= elapsed_known[0]:
            return int(round(hr_known[0]))
        if t >= elapsed_known[-1]:
            return int(round(hr_known[-1]))
        # Find surrounding anchors
        for i in range(len(elapsed_known) - 1):
            t0, t1 = elapsed_known[i], elapsed_known[i + 1]
            if t0 <= t <= t1:
                if t1 == t0:
                    return int(round(hr_known[i]))
                frac = (t - t0) / (t1 - t0)
                return int(round(hr_known[i] + frac * (hr_known[i + 1] - hr_known[i])))
        return int(round(hr_known[-1]))  # fallback (should not be reached)

    per_second = []
    for offset in range(total_seconds):
        ts = window_start + timedelta(seconds=offset)
        per_second.append({
            "timestamp": ts.isoformat(),
            "heart_rate": lerp(float(offset)),
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