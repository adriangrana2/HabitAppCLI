from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from models import Habit, LogEntry
from storage import ensure_storage, load_habits, load_logs, upsert_log
from stats import count_statuses


# Wir verwenden einen stabilen Pfad: den Ordner data/ innerhalb des Pakets HabitAppCLI.
DATA_DIR = Path(__file__).resolve().parent / "data"


def normalize_habit_type(raw: str) -> str:
    """
    Normalisiert die Benutzereingabe zu 'good' oder 'bad'.
    Erlaubt Abkürzungen: g/b.
    """
    value = raw.strip().lower()
    mapping = {
        "g": "good",
        "good": "good",
        "b": "bad",
        "bad": "bad",
    }
    if value in mapping:
        return mapping[value]
    raise ValueError("Ungültiger Typ. Verwende: good/bad (oder g/b).")


def normalize_period(raw: str) -> str:
    """
    Normalisiert die Benutzereingabe zu 'daily' oder 'weekly'.
    Erlaubt Abkürzungen: d/w.
    """
    value = raw.strip().lower()
    mapping = {
        "d": "daily",
        "daily": "daily",
        "w": "weekly",
        "weekly": "weekly",
    }
    if value in mapping:
        return mapping[value]
    raise ValueError("Ungültiger Zeitraum. Verwende: daily/weekly (oder d/w).")


def parse_frequency_for_period(period: str, raw: str) -> int:
    """
    Wandelt die Frequenz-Eingabe je nach Zeitraum in einen int um.
    - daily  => immer 0 (auch wenn der Benutzer etwas eingibt)
    - weekly => int >= 1
    """
    if period == "daily":
        return 0

    value = raw.strip()
    if not value:
        raise ValueError("Frequency ist für weekly-Habits erforderlich.")

    freq = int(value)
    if freq < 1:
        raise ValueError("Frequency muss für weekly-Habits >= 1 sein.")
    return freq


def format_habit_line(habit: Habit) -> str:
    """
    Gibt eine gut lesbare Zeile zurück, um ein Habits auf dem Bildschirm anzuzeigen.
    """
    freq_part = ""
    if habit.period == "weekly":
        freq_part = f" | freq={habit.frequency}/week"

    status_part = "active" if habit.active else "inactive"

    return (
        f"{habit.habit_id} | {habit.name} | {habit.type} | {habit.period}"
        f"{freq_part} | start={habit.start_date.isoformat()} | {status_part}"
    )


def print_menu() -> None:
    print("\n=== Habit Tracker (CLI + CSV) ===")
    print("1) Habit anlegen (ausstehend)")
    print("2) Habits anzeigen")
    print("3) Check-in (heute)")
    print("4) Check-in (Datum eingeben) (ausstehend)")
    print("5) Skip (heute) (ausstehend)")
    print("6) Habit deaktivieren (ausstehend)")
    print("7) Statistiken anzeigen (ausstehend)")
    print("0) Beenden")


def choose_habit_by_id(habits: list[Habit]) -> Optional[Habit]:
    """
    Zeigt aktive Habits an und fragt den Benutzer nach einer habit_id.
    Gibt den ausgewählten Habit zurück oder None, falls keine Auswahl möglich war.
    """
    active = [h for h in habits if h.active]

    if not active:
        print("Es gibt keine aktiven Habits. Erstelle zuerst einen (Option 1).")
        return None

    print("\nAktive Habits:")
    for h in active:
        print(" - " + format_habit_line(h))

    chosen = input("\nGib die habit_id ein: ").strip()
    for h in active:
        if h.habit_id == chosen:
            return h

    print("habit_id nicht gefunden (oder nicht aktiv).")
    return None


def prompt_status_for_habit(habit: Habit) -> str:
    """
    Fragt success/fail mit unterschiedlicher Formulierung je nachdem,
    ob es sich um einen good- oder bad-Habit handelt.
    Gibt 'success' oder 'fail' zurück.
    """
    if habit.type == "good":
        question = "Hast du es heute geschafft? (s = ja / n = nein): "
    else:
        question = "Konntest du heute widerstehen? (s = ja / n = nein): "

    while True:
        answer = input(question).strip().lower()
        if answer in {"s", "ja", "j", "y", "yes"}:
            return "success"
        if answer in {"n", "nein", "no"}:
            return "fail"
        print("Ungültige Eingabe. Bitte 's' oder 'n' eingeben.")


def prompt_nonempty(prompt: str) -> str:
    """Fordert Text an und stellt sicher, dass er nicht leer ist."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Darf nicht leer sein.")


def prompt_habit_type() -> str:
    """Fragt den Typ ab und normalisiert ihn mit normalize_habit_type()."""
    while True:
        raw = input("Typ (good/bad) [g/b]: ")
        try:
            return normalize_habit_type(raw)
        except ValueError as e:
            print(str(e))


def prompt_period() -> str:
    """Fragt den Zeitraum ab und normalisiert ihn mit normalize_period()."""
    while True:
        raw = input("Zeitraum (daily/weekly) [d/w]: ")
        try:
            return normalize_period(raw)
        except ValueError as e:
            print(str(e))


def prompt_start_date() -> date:
    """
    Fragt start_date ab. Wenn der Nutzer leer lässt, verwenden wir der Einfachheit halber heute.
    Wenn etwas eingegeben wird, muss es YYYY-MM-DD sein.
    """
    while True:
        raw = input("Startdatum (YYYY-MM-DD) [Enter = heute]: ").strip()
        if not raw:
            return date.today()
        try:
            # Wir verwenden den Parser aus models (Konsistenz mit CSV)
            from models import parse_iso_date
            return parse_iso_date(raw)
        except ValueError:
            print("Ungültiges Datum. Erwartetes Format: YYYY-MM-DD.")


def prompt_frequency(period: str) -> int:
    """Fragt frequency nur ab, wenn period=weekly."""
    if period == "daily":
        return 0

    while True:
        raw = input("Häufigkeit pro Woche (Ganzzahl >= 1): ")
        try:
            return parse_frequency_for_period(period, raw)
        except (ValueError, TypeError) as e:
            print(str(e))


def handle_list_habits(habits_path: Path) -> None:
    habits = load_habits(habits_path)
    active = [h for h in habits if h.active]

    if not active:
        print("Es gibt keine aktiven Habits.")
        return

    print("\nAktive Habits:")
    for h in active:
        print(" - " + format_habit_line(h))


def handle_checkin_today(habits_path: Path, logs_path: Path) -> None:
    habits = load_habits(habits_path)
    habit = choose_habit_by_id(habits)
    if habit is None:
        return

    today = date.today()
    status = prompt_status_for_habit(habit)

    entry = LogEntry.create(habit_id=habit.habit_id, date_value=today, status=status)
    upsert_log(logs_path, entry)

    # Wir zeigen einfache Statistiken als direktes Feedback an
    logs = load_logs(logs_path)
    counts = count_statuses(logs, habit.habit_id)

    print("\n✅ Check-in gespeichert.")
    print(f"Datum: {today.isoformat()} | Status: {status}")
    print("Summen:")
    print(f"  success: {counts['success']}")
    print(f"  fail:    {counts['fail']}")
    print(f"  skip:    {counts['skip']}")


def main() -> None:
    habits_path, logs_path = ensure_storage(DATA_DIR)

    while True:
        print_menu()
        choice = input("\nWähle eine Option: ").strip()

        if choice == "0":
            print("Bis bald!")
            return

        if choice == "2":
            handle_list_habits(habits_path)
            continue

        if choice == "3":
            handle_checkin_today(habits_path, logs_path)
            continue

        print("Option 2 wird implementiert.")


if __name__ == "__main__":
    main()