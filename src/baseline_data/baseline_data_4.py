from pathlib import Path

from src.data_models import (
    RunMetadata,
    RunSecondData,
    SuspectExperiment,
    SuspectMetadata,
    SuspectRun,
)
from src.parser_s2 import get_exercise_heartbeat, get_sleep_duration_minutes, get_daily_activity_minutes, get_daily_step_count
from src.weather import get_weather_for_dates, EINDHOVEN_ALTITUDE_M

DATA_DIR = Path("/data/suspect_4")

# (exercise_index, start_strip_seconds, end_strip_seconds)
DATE_ID_MAPPER = {
    "2026-03-03": (2, 0, 0),
    "2026-03-05": (3, 0, 0),
    "2026-03-07": (3, 0, 0),
    "2026-03-10": (1, 0, 0),
    "2026-03-12": (1, 0, 60),
    "2026-03-14": (1, 0, 30),
    "2026-03-17": (2, 0, 0),
    "2026-03-19": (0, 0, 0),
    "2026-03-21": (0, 0, 0),
}


def _build_suspect_data_4() -> SuspectExperiment:
    metadata = SuspectMetadata(
        age=24,
        sex="F",
        height=1.60,
        weight=62.0,
        lifetime_sports_activity=144,
        target_speed=9,
        watch_type="Samsung Galaxy Fit 3",
    )

    weather = get_weather_for_dates(list(DATE_ID_MAPPER.keys()))

    runs = []
    for date_str, (exercise_index, start_strip, end_strip) in DATE_ID_MAPPER.items():
        hr_df = get_exercise_heartbeat(
            DATA_DIR, date_str,
            exercise_index=exercise_index,
            start_strip=start_strip,
            end_strip=end_strip,
        )

        per_second_data = [
            RunSecondData(
                timestamp=row["timestamp"].to_pydatetime(),
                heart_rate=int(row["heart_rate"]),
            )
            for _, row in hr_df.iterrows()
        ]

        temperature, atm_pressure = weather[date_str]
        run_metadata = RunMetadata(
            atm_pressure=atm_pressure,
            temperature=temperature,
            altitude=EINDHOVEN_ALTITUDE_M,
            sleep_duration=get_sleep_duration_minutes(DATA_DIR, date_str),
            daily_activity=get_daily_activity_minutes(DATA_DIR, date_str) - (len(per_second_data) // 60),
            steps_count=get_daily_step_count(DATA_DIR, date_str, exercise_index),
        )

        runs.append(SuspectRun(
            run_id=f"P4_run_{date_str}",
            metadata=run_metadata,
            per_second_data=per_second_data,
        ))

    return SuspectExperiment(
        suspect_id="P4",
        metadata=metadata,
        runs=runs,
    )


SUSPECT_DATA_4 = _build_suspect_data_4()

if __name__ == "__main__":
    output = Path("processed")
    output.mkdir(parents=True, exist_ok=True)
    (output / f"JBM170_HR_Day1-21_{SUSPECT_DATA_4.suspect_id}.json").write_text(
        SUSPECT_DATA_4.model_dump_json(indent=2)
    )
    print(f"Saved to processed/JBM170_HR_Day1-21_{SUSPECT_DATA_4.suspect_id}.json")