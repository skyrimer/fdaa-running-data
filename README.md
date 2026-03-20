# fdaa-running-data

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

This creates a `.venv` virtual environment and installs all dependencies from `uv.lock`.

### 3. Add data

Place the Samsung Health export directory under `data/suspect_2/`:

```
data/
└── suspect_2/
    ├── com.samsung.shealth.exercise.*.csv
    ├── com.samsung.shealth.sleep_combined.*.csv
    ├── com.samsung.shealth.activity.day_summary.*.csv
    ├── ...
    └── jsons/
```

## Usage

### Running scripts

Prefix any Python command with `uv run` to use the project environment:

```bash
uv run python src/baseline_data/baseline_data_2.py
```

### Jupyter notebooks

```bash
uv run jupyter notebook notebooks/
```

### Importing baseline data

```python
from src.baseline_data import SUSPECT_DATA_2

for run in SUSPECT_DATA_2.runs:
    print(run.run_id, len(run.per_second_data), "seconds of HR data")
```

## Project structure

```
src/
├── data_models.py          # Pydantic models (SuspectExperiment, SuspectRun, ...)
├── parser_s2.py            # Samsung Health parser (suspect_2 data)
└── baseline_data/
    ├── __init__.py         # Exports SUSPECT_DATA_2
    └── baseline_data_2.py  # Builds the suspect_2 experiment object
notebooks/
└── test.ipynb              # HR visualisation across all sessions
data/
└── suspect_2/              # Samsung Health export (not committed)
```
