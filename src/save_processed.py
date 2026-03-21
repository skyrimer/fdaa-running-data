from pathlib import Path
from src.baseline_data import SUSPECT_DATA_2

output = Path("processed")
Path(output).mkdir(parents=True, exist_ok=True)
data = [SUSPECT_DATA_2]

# Write JSON
for suspect_data in data:
    (output / f"{suspect_data.suspect_id}.json").write_text(
        suspect_data.model_dump_json(indent=2)
    )
