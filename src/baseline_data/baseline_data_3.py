from pathlib import Path

from src.data_models import (
    RunMetadata,
    RunSecondData,
    SuspectExperiment,
    SuspectMetadata,
    SuspectRun,
)
from src.parser_s3 import _parse_records, get_exercise_heartbeat, get_daily_steps
from src.weather import get_weather_for_dates, EINDHOVEN_ALTITUDE_M

XML_PATH = Path("src/baseline_data/export.xml")

# (start_strip_seconds, end_strip_seconds, manual_start, manual_end)
DATE_ID_MAPPER = {
    "2026-03-02": (0, 0, "19:04:25", "19:24:25"),
    "2026-03-04": (0, 0, "19:45:05", "20:05:05"),
    "2026-03-06": (0, 0, "19:34:50", "19:54:50"),
    "2026-03-09": (0, 0, "17:54:45", "18:14:45"),
    "2026-03-11": (0, 0, "09:15:55", "09:35:55"),
    "2026-03-13": (0, 0, "20:31:38", "20:51:38"),
    "2026-03-16": (0, 0, "17:57:30", "18:17:30"),
    "2026-03-18": (0, 0, "19:27:00", "19:47:00"),
    "2026-03-20": (0, 0, "16:51:40", "17:11:40"),
}


def _build_suspect_data_3() -> SuspectExperiment:
    metadata = SuspectMetadata(
        age=20,
        sex="F",
        height=1.59,
        weight=47.0,
        lifetime_sports_activity=10,
        target_speed=12,
        watch_type="Apple Watch",
    )

    heart_rates, steps, workouts = _parse_records(XML_PATH)

    weather = get_weather_for_dates(list(DATE_ID_MAPPER.keys()))

    runs = []
    for date_str, (start_strip, end_strip, manual_start, manual_end) in DATE_ID_MAPPER.items():
        hr_data = get_exercise_heartbeat(
            heart_rates, workouts, date_str,
            start_strip, end_strip,
            manual_start, manual_end,
        )

        per_second_data = [
            RunSecondData(
                timestamp=row["timestamp"],
                heart_rate=row["heart_rate"],
            )
            for row in hr_data
        ]

        temperature, atm_pressure = weather[date_str]
        run_metadata = RunMetadata(
            atm_pressure=atm_pressure,
            temperature=temperature,
            altitude=EINDHOVEN_ALTITUDE_M,
            sleep_duration=420,
            daily_activity=30.0,
            steps_count=get_daily_steps(steps, date_str),
        )

        runs.append(SuspectRun(
            run_id=f"P3_run_{date_str}",
            metadata=run_metadata,
            per_second_data=per_second_data,
        ))

    return SuspectExperiment(
        suspect_id="P3",
        metadata=metadata,
        runs=runs,
    )


SUSPECT_DATA_3 = _build_suspect_data_3()


if __name__ == "__main__":
    output = Path("processed")
    output.mkdir(parents=True, exist_ok=True)
    (output / f"JBM170_HR_Day1-21_{SUSPECT_DATA_3.suspect_id}.json").write_text(
        SUSPECT_DATA_3.model_dump_json(indent=2)
    )
    print(f"Saved to processed/JBM170_HR_Day1-21_{SUSPECT_DATA_3.suspect_id}.json")