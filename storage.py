from __future__ import annotations

import csv
from typing import Tuple, List, Iterable
from pathlib import Path # um Dateisystempfade in Python zu verwalten
from models import Habit, LogEntry

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

def _read_dict_rows(path: Path) -> List[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def _write_dict_rows(path: Path, headers: List[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_habits(habits_path: Path) -> List[Habit]:
    rows = _read_dict_rows(habits_path)
    return [Habit.from_row(r) for r in rows]


def save_habits(habits_path: Path, habits: Iterable[Habit]) -> None:
    _write_dict_rows(habits_path, HABITS_HEADER, (h.to_row() for h in habits))


def load_logs(logs_path: Path) -> List[LogEntry]:
    rows = _read_dict_rows(logs_path)
    return [LogEntry.from_row(r) for r in rows]


def save_logs(logs_path: Path, logs: Iterable[LogEntry]) -> None:
    _write_dict_rows(logs_path, LOGS_HEADER, (l.to_row() for l in logs))