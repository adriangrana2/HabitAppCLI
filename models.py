from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from uuid import uuid4

# Zulässige Werte (zur Validierung von Eingaben)
HABIT_TYPES = {"good", "bad"}
PERIODS = {"daily", "weekly"}
LOG_STATUSES = {"success", "fail", "skip"}

# Reihenfolge für Berichte
LOG_STATUS_ORDER = ["success", "fail", "skip"]


@dataclass(frozen=True)
class Habit:
    habit_id: str
    name: str
    type: str         #  'good' | 'bad'
    period: str       # 'daily' | 'weekly'
    frequency: int    # weekly: >=1, daily: 0
    start_date: date
    active: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Habit.name darf nicht leer sein.")

        if self.type not in HABIT_TYPES:
            raise ValueError(f"Ungültige Habit.type: {self.type!r}. Muss 'daily' oder 'weekly' sein.")

        if self.period not in PERIODS:
            raise ValueError(f"Ungültige Habit.period: {self.period!r}. Muss 'daily' oder 'weekly' sein.")

        if self.period == "daily" and self.frequency != 0:
            raise ValueError("Bei daily-Gewohnheiten muss frequency 0 sein.")

        if self.period == "weekly" and self.frequency < 1:
            raise ValueError("Bei weekly-Gewohnheiten muss frequency >= 1 sein.")

    @classmethod
    def create(
            cls,
            name: str,
            type: str,
            period: str,
            start_date: date,
            frequency: int,
            active: bool = True
        ) -> Habit:
        """Factory, um Gewohnheiten zu erstellen, ohne um die habit_id kümmern zu müssen."""
        return cls(
            habit_id=new_id(),
            name=name,
            type=type,
            period=period,
            frequency=frequency,
            start_date=start_date,
            active=active,
        )

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Habit:
        """Erstellt ein Habit aus einer CSV-Zeile (alles kommt als String an)."""
        return cls(
            habit_id=row["habit_id"],
            name=row["name"],
            type=row["type"],
            period=row["period"],
            frequency=int(row["frequency"]) if row["frequency"] else 0,
            start_date=parse_iso_date(row["start_date"]),
            active=parse_bool(row["active"]),
        )

    def to_row(self) -> dict[str, str]:
        """Wandelt das Habit in ein Dict aus Strings um, bereit für DictWriter."""
        return {
            "habit_id": self.habit_id,
            "name": self.name,
            "type": self.type,
            "period": self.period,
            "frequency": str(self.frequency),
            "start_date": format_iso_date(self.start_date),
            "active": format_bool(self.active),
        }


@dataclass(frozen=True)
class LogEntry:
    log_id: str
    habit_id: str
    date: date
    status: str        # 'success' | 'fail' | 'skip'

    def __post_init__(self) -> None:
        if self.status not in LOG_STATUSES:
            raise ValueError(f"Ungültiger Wert für LogEntry.status: {self.status!r}.")

    @classmethod
    def create(cls, habit_id: str, date_value: date, status: str) -> "LogEntry":
        """Factory-Methode zum Erstellen eines Logs mit automatisch generierter ID."""
        return cls(
            log_id=new_id(),
            habit_id=habit_id,
            date=date_value,
            status=status,
        )

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "LogEntry":
        """Erstellt einen LogEntry aus einer CSV-Zeile."""
        return cls(
            log_id=row["log_id"],
            habit_id=row["habit_id"],
            date=parse_iso_date(row["date"]),
            status=row["status"],
        )

    def to_row(self) -> dict[str, str]:
        """Konvertiert in ein String-Dict, bereit für CSV."""
        return {
            "log_id": self.log_id,
            "habit_id": self.habit_id,
            "date": format_iso_date(self.date),
            "status": self.status,
        }