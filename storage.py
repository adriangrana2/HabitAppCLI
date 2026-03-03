from __future__ import annotations

import csv
from typing import Tuple, List
from pathlib import Path # um Dateisystempfade in Python zu verwalten

# ============ CSV (headers) ============
HABITS_HEADER = ["habit_id", "name", "type", "period", "frequency", "start_date", "active"]
LOGS_HEADER = ["log_id", "habit_id", "date", "status"]

# ============ CSV Dateienüberprüfung and Pfade ============

def ensure_storage(data_dir: str | Path = "data" ) -> Tuple[Path, Path]:

    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    habits_path = data_path / "habits.csv"
    logs_path = data_path / "logs.csv"

    _ensure_csv_headers(habits_path, HABITS_HEADER)
    _ensure_csv_headers(logs_path, LOGS_HEADER)
    return habits_path, logs_path


def _ensure_csv_headers(path: Path, headers: List[str]) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
    elif path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
