from pathlib import Path

from src.data_models import (
    RunMetadata,
    RunSecondData,
    SuspectExperiment,
    SuspectMetadata,
    SuspectRun,
)
from src.parser_s3 import _parse_records, get_exercise_heartbeat, get_daily_steps

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

        run_metadata = RunMetadata(
            steps_count=get_daily_steps(steps, date_str),
        )

        runs.append(SuspectRun(
            run_id=f"s3_run_{date_str}",
            metadata=run_metadata,
            per_second_data=per_second_data,
        ))

    return SuspectExperiment(
        suspect_id="suspect_3",
        metadata=metadata,
        runs=runs,
    )


SUSPECT_DATA_3 = _build_suspect_data_3()


if __name__ == "__main__":
    output = Path("processed")
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{SUSPECT_DATA_3.suspect_id}.json").write_text(
        SUSPECT_DATA_3.model_dump_json(indent=2)
    )
    print(f"Saved to processed/{SUSPECT_DATA_3.suspect_id}.json")