from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Iterable

from models import LogEntry, LOG_STATUS_ORDER


def count_statuses(logs: Iterable[LogEntry], habit_id: str) -> dict[str, int]:
    """
    Gibt die Anzahl von success/fail/skip für ein Habit zurück.
    Enthält immer alle 3 Schlüssel in der definierten Reihenfolge.
    """
    counts = Counter(log.status for log in logs if log.habit_id == habit_id)
    return {status: counts.get(status, 0) for status in LOG_STATUS_ORDER}


def current_daily_streak(logs: Iterable[LogEntry], habit_id: str) -> int:
    """
    Berechnet die aktuelle Streak für tägliche (daily) Habits nach einer strikten Regel:

    Definition:
    - Es wird das zuletzt (zeitlich) erfasste Datum für diese Habits genommen.
    - Ab diesem Datum wird Tag für Tag rückwärts gezählt.
    - Nur 'success' zählt zur Streak.
    - 'fail' und 'skip' unterbrechen die Streak.
    - Ein fehlender Tag (ohne Log-Eintrag) unterbricht die Streak ebenfalls.

    Beispiele:
    - success, success, success an Tag 1/2/3 => Streak = 3
    - success, success, fail => Streak = 0, wenn 'fail' der neueste Log ist
    - success an Tag 5, kein Log an Tag 4 => Streak = 1
    """
    habit_logs = [log for log in logs if log.habit_id == habit_id]

    if not habit_logs:
        return 0

    habit_logs.sort(key=lambda log: log.date)

    logs_by_date = {log.date: log for log in habit_logs}

    current_date = habit_logs[-1].date
    streak = 0

    while True:
        log = logs_by_date.get(current_date)
        if log is None:
            break

        if log.status != "success":
            break

        streak += 1
        current_date = current_date - timedelta(days=1)

    return streak