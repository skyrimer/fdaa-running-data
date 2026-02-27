import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def parse_heart_rate_data(xml_path: str | Path = "data/export.xml") -> pd.DataFrame:
    """Parse heart rate records from Apple Health export XML.

    Args:
        xml_path: Path to the Apple Health export.xml file.

    Returns:
        DataFrame with columns: value, start_date, end_date, creation_date,
        source_name, unit.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    records = []
    for record in root.findall(".//Record[@type='HKQuantityTypeIdentifierHeartRate']"):
        records.append({
            "value": float(record.get("value")),
            "start_date": record.get("startDate"),
            "end_date": record.get("endDate"),
            "creation_date": record.get("creationDate"),
            "source_name": record.get("sourceName"),
            "unit": record.get("unit"),
        })

    df = pd.DataFrame(records)

    # Convert date columns to datetime
    for col in ["start_date", "end_date", "creation_date"]:
        df[col] = pd.to_datetime(df[col])

    return df


def parse_samsung_health_heartbeat(data_dir: str | Path) -> pd.DataFrame:
    """Parse second-by-second heart rate data from Samsung Health exercise JSON files.

    Args:
        data_dir: Path to the Samsung Health export directory containing jsons folder.

    Returns:
        DataFrame with columns: heart_rate, timestamp, exercise_id.
    """
    data_dir = Path(data_dir)
    exercise_jsons_dir = data_dir / "jsons" / "com.samsung.shealth.exercise"

    if not exercise_jsons_dir.exists():
        raise FileNotFoundError(f"Exercise JSON directory not found: {exercise_jsons_dir}")

    records = []

    # Iterate through all live_data JSON files
    for json_file in exercise_jsons_dir.rglob("*.com.samsung.health.exercise.live_data.json"):
        exercise_id = json_file.stem.split(".")[0]  # Extract UUID from filename

        with open(json_file, "r") as f:
            data = json.load(f)

        # Extract heart rate measurements
        for entry in data:
            if "heart_rate" in entry:
                records.append({
                    "heart_rate": entry["heart_rate"],
                    "timestamp": pd.to_datetime(entry["start_time"], unit="ms"),
                    "exercise_id": exercise_id,
                })

    df = pd.DataFrame(records)

    # Sort by timestamp
    if not df.empty:
        df = df.sort_values("timestamp").reset_index(drop=True)

    return df


if __name__ == "__main__":
    # Example for Apple Health
    # df = parse_heart_rate_data()
    # print(f"Loaded {len(df)} heart rate records")
    # print(df.head())
    # print(df.info())

    # Example for Samsung Health
    df_samsung = parse_samsung_health_heartbeat("data/suspect_2/samsunghealth_chekmenev2004_20260227224960")
    print(f"Loaded {len(df_samsung)} heart rate records")
    print(df_samsung.head(10))
    print(df_samsung.info())
