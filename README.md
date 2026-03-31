# fdaa-running-data — JBM170 Heart Rate Dataset

Pseudonymized heart-rate and contextual metadata collected during a structured running protocol (JBM170) at Eindhoven University of Technology. Five participants (P2–P6) each completed up to nine sessions over three weeks (March 2026), wearing consumer-grade fitness watches at a fixed target pace.

The dataset, schema, and complete analysis codebase are made available under the MIT License to support reproducible sports-science research.

---

## Dataset overview

| Field | Description |
|---|---|
| **Participants** | 5 pseudonymized participants (P2, P3, P4, P5, P6) |
| **Sessions** | Up to 9 running sessions per participant, March 2026 |
| **Protocol** | Alternating run/walk intervals at participant-specific target speeds |
| **Location** | Eindhoven, Netherlands (altitude ≈ 17 m a.s.l.) |
| **Sampling** | Heart rate at 10-second intervals (Samsung/Xiaomi) or per-second (Apple Watch), aligned to a common 10-second grid in processed files |

### Devices used

| Participant | Device | Export format |
|---|---|---|
| P2 | Samsung Galaxy Watch 7 | Samsung Health CSV + JSON export |
| P3 | Apple Watch | Apple Health XML export (`export.xml`) |
| P4 | Samsung Galaxy Fit 3 | Samsung Health CSV + JSON export |
| P5 | Xiaomi Mi Fitness Band 9 | Mi Fitness app export |
| P6 | Xiaomi Mi Fitness 9 | Mi Fitness app export |

---

## File naming convention

All processed files follow the persistent identifier pattern:

```
JBM170_HR_Day1-21_P<ID>.json
```

where `<ID>` is the pseudonymized participant number (e.g., `P2`, `P3`, …, `P6`).

---

## Data schema

Each file conforms to the schema defined in `src/data_models.py` and `schema/schema.json`.

### Participant-level metadata

| Field | Type | Unit | Description |
|---|---|---|---|
| `suspect_id` | string | — | Pseudonymized participant identifier (e.g., `P2`) |
| `age` | integer | years | Age at time of experiment |
| `sex` | `"M"` / `"F"` / `"U"` | — | Biological sex |
| `height` | float | metres | Standing height |
| `weight` | float | kg | Body mass |
| `lifetime_sports_activity` | integer | months | Cumulative months of sports participation |
| `target_speed` | integer | km/h | Prescribed running pace for the protocol |
| `watch_type` | string | — | Wearable device model |

### Run-level metadata

| Field | Type | Unit | Description |
|---|---|---|---|
| `atm_pressure` | float | hPa | Atmospheric pressure at session time (Open-Meteo API) |
| `temperature` | float | °C | Ambient temperature at session time (Open-Meteo API) |
| `altitude` | float | m | Altitude above sea level |
| `sleep_duration` | integer | minutes | Total sleep duration on the night preceding the session |
| `daily_activity` | float | minutes | Non-running physical activity on the session day (walking, cycling, gym, etc.) |
| `steps_count` | float | steps | Total step count for the session day |

### Per-sample data (`per_second_data`)

| Field | Type | Unit | Description |
|---|---|---|---|
| `timestamp` | ISO 8601 datetime | — | Absolute timestamp of the measurement |
| `heart_rate` | integer | bpm | Heart Rate (BPM) measured by the wearable sensor |

---

## Data extraction and provenance

Raw exports were obtained from each vendor's official health app. The following steps transform them into the unified schema:

1. **Samsung Health (P2, P4)** — `src/parser_s2.py` reads exercise CSVs, sleep CSVs, and activity day-summary CSVs. Weather is fetched from the Open-Meteo historical API via `src/weather.py` using the session date and Eindhoven coordinates.
2. **Apple Health (P3)** — `src/parser_s3.py` parses the `export.xml` file, extracts `HKQuantityTypeIdentifierHeartRate` samples, and clips the window to the protocol start/end times.
3. **Mi Fitness (P5, P6)** — Data was manually exported from the Mi Fitness app and entered into the schema directly, without an automated parser.

All parser scripts can be re-run to regenerate the processed files:

```bash
uv run python src/baseline_data/baseline_data_2.py   # regenerates P2
uv run python src/baseline_data/baseline_data_3.py   # regenerates P3
uv run python src/baseline_data/baseline_data_4.py   # regenerates P4
```

---

## Repository structure

```
processed/
├── JBM170_HR_Day1-21_P2.json   # Participant P2 (Samsung Galaxy Watch 7)
├── JBM170_HR_Day1-21_P3.json   # Participant P3 (Apple Watch)
├── JBM170_HR_Day1-21_P4.json   # Participant P4 (Samsung Galaxy Fit 3)
├── JBM170_HR_Day1-21_P5.json   # Participant P5 (Xiaomi Mi Fitness Band 9)
└── JBM170_HR_Day1-21_P6.json   # Participant P6 (Xiaomi Mi Fitness 9)
schema/
└── schema.json                  # JSON Schema for all processed files
src/
├── data_models.py               # Pydantic models defining the schema
├── parser_s2.py                 # Samsung Health parser (P2, P4)
├── parser_s3.py                 # Apple Health XML parser (P3)
├── weather.py                   # Open-Meteo weather fetcher
└── baseline_data/
    ├── baseline_data_2.py       # Builds and serialises P2 experiment object
    ├── baseline_data_3.py       # Builds and serialises P3 experiment object
    └── baseline_data_4.py       # Builds and serialises P4 experiment object
notebooks/
├── eda.ipynb                    # Exploratory HR visualisations across all sessions
└── stats_analysis.ipynb         # Linear mixed-effects models (H1–H3)
data/
└── suspect_2/                   # Raw Samsung Health export for P2 (not committed)
```

---

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and install dependencies

```bash
git clone <repo-url>
cd fdaa-running-data
uv sync
```

### 3. (Optional) Add raw data to regenerate processed files

Place the Samsung Health export directory under `data/suspect_2/` (for P2):

```
data/
└── suspect_2/
    ├── com.samsung.shealth.exercise.*.csv
    ├── com.samsung.shealth.sleep_combined.*.csv
    ├── com.samsung.shealth.activity.day_summary.*.csv
    └── jsons/
```

### 4. Run analysis notebooks

```bash
uv run jupyter notebook notebooks/
```

---

## Usage

### Load a processed dataset

```python
import json

with open("processed/JBM170_HR_Day1-21_P2.json") as f:
    data = json.load(f)

for run in data["runs"]:
    print(run["run_id"], len(run["per_second_data"]), "HR samples")
```

### Load via the Python package

```python
from src.baseline_data import SUSPECT_DATA_2

for run in SUSPECT_DATA_2.runs:
    print(run.run_id, run.metadata.temperature, "°C")
```

---

## License

This project and its data are released under the [MIT License](LICENSE).
