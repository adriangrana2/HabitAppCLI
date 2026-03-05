from __future__ import annotations

from collections import Counter
from typing import Iterable

from models import LogEntry, LOG_STATUS_ORDER


def count_statuses(logs: Iterable[LogEntry], habit_id: str) -> dict[str, int]:
    """
    Gibt die Anzahl von success/fail/skip für ein Habit zurück.
    Enthält immer alle 3 Schlüssel in der definierten Reihenfolge.
    """
    counts = Counter(log.status for log in logs if log.habit_id == habit_id)
    return {status: counts.get(status, 0) for status in LOG_STATUS_ORDER}