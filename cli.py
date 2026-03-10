from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from models import Habit, LogEntry, parse_iso_date
from storage import (
    ensure_storage,
    load_habits,
    load_logs,
    upsert_log,
    add_habit,
    set_habit_active
)
from stats import count_statuses, current_daily_streak


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

def parse_date_or_today(raw: str, today_value: date | None = None) -> date:
    """
    Wenn raw leer ist, gib das heutige Datum zurück.
    Wenn raw Text enthält, muss er im Format YYYY-MM-DD sein.
    """
    if today_value is None:
        today_value = date.today()

    value = raw.strip()
    if not value:
        return today_value

    return parse_iso_date(value)


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
    print("1) Habit anlegen")
    print("2) Habits anzeigen")
    print("3) Check-in (heute)")
    print("4) Check-in (Datum eingeben)")
    print("5) Skip (heute)")
    print("6) Habit deaktivieren")
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
    Wenn etwas eingegeben wird, muss es JJJJ-MM-TT sein.
    """
    while True:
        raw = input("Startdatum (JJJJ-MM-TT) [Enter = heute]: ").strip()
        try:
            return parse_date_or_today(raw)
        except ValueError:
            print("Ungültiges Datum. Erwartetes Format: JJJJ-MM-TT.")


def prompt_log_date() -> date:
    """
    Fragt das Datum für einen Log-Eintrag ab.
    Leere Eingabe = heute.
    """
    while True:
        raw = input("Log-Datum (JJJJ-MM-TT) [Enter = heute]: ").strip()
        try:
            return parse_date_or_today(raw)
        except ValueError:
            print("Ungültiges Datum. Erwartetes Format: JJJJ-MM-TT.")


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


def handle_create_habit(habits_path: Path) -> None:
    print("\n=== Habit erstellen ===")

    name = prompt_nonempty("Name: ")
    habit_type = prompt_habit_type()
    period = prompt_period()
    freq = prompt_frequency(period)
    start = prompt_start_date()

    habit = Habit.create(
        name=name,
        type=habit_type,
        period=period,
        frequency=freq,
        start_date=start,
        active=True,
    )

    add_habit(habits_path, habit)

    print("\n✅ Habit erstellt:")
    print(" - " + format_habit_line(habit))


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


def handle_checkin_for_date(habits_path: Path, logs_path: Path) -> None:
    habits = load_habits(habits_path)
    habit = choose_habit_by_id(habits)
    if habit is None:
        return

    try:
        chosen_date = prompt_log_date()
    except ValueError:
        print("Ungültiges Datum. Erwartetes Format: JJJJ-MM-TT.")
        return

    status = prompt_status_for_habit(habit)

    entry = LogEntry.create(habit_id=habit.habit_id, date_value=chosen_date, status=status)
    upsert_log(logs_path, entry)

    logs = load_logs(logs_path)
    counts = count_statuses(logs, habit.habit_id)

    print("\n✅ Check-in gespeichert.")
    print(f"Datum: {chosen_date.isoformat()} | Status: {status}")
    print("Gesamt:")
    print(f"  Erfolg:        {counts['success']}")
    print(f"  Fehlgeschlagen:{counts['fail']}")
    print(f"  Übersprungen:  {counts['skip']}")


def handle_show_stats(habits_path: Path, logs_path: Path) -> None:
    habits = load_habits(habits_path)
    habit = choose_habit_by_id(habits)
    if habit is None:
        return

    logs = load_logs(logs_path)
    counts = count_statuses(logs, habit.habit_id)

    print("\n=== Statistiken ===")
    print("Gewohnheit:")
    print(" - " + format_habit_line(habit))
    print("Gesamt:")
    print(f"  Erfolg: {counts['success']}")
    print(f"  Fehl:   {counts['fail']}")
    print(f"  Übersprungen: {counts['skip']}")

    if habit.period == "daily":
        streak = current_daily_streak(logs, habit.habit_id)
        print(f"Aktueller täglicher Streak: {streak}")
    else:
        print("Aktueller wöchentlicher Streak: noch zu implementieren.")


def handle_skip_today(habits_path: Path, logs_path: Path) -> None:
    habits = load_habits(habits_path)
    habit = choose_habit_by_id(habits)
    if habit is None:
        return

    today = date.today()

    entry = LogEntry.create(habit_id=habit.habit_id, date_value=today, status="skip")
    upsert_log(logs_path, entry)

    logs = load_logs(logs_path)
    counts = count_statuses(logs, habit.habit_id)

    print("\n⏭️  Überspringen gespeichert.")
    print(f"Datum: {today.isoformat()} | Status: skip")
    print("Gesamtzahlen:")
    print(f"  success: {counts['success']}")
    print(f"  fail:    {counts['fail']}")
    print(f"  skip:    {counts['skip']}")


def handle_deactivate_habit(habits_path: Path) -> None:
    habits = load_habits(habits_path)
    habit = choose_habit_by_id(habits)  # nur aktive
    if habit is None:
        return

    updated = set_habit_active(habits_path, habit.habit_id, False)

    print("\n🚫 Habit deaktiviert:")
    print(" - " + format_habit_line(updated))


def main() -> None:
    habits_path, logs_path = ensure_storage(DATA_DIR)

    while True:
        print_menu()
        choice = input("\nWähle eine Option: ").strip()

        if choice == "0":
            print("Bis bald!")
            return

        if choice == "1":
            handle_create_habit(habits_path)
            continue

        if choice == "2":
            handle_list_habits(habits_path)
            continue

        if choice == "3":
            handle_checkin_today(habits_path, logs_path)
            continue

        if choice == "4":
            handle_checkin_for_date(habits_path, logs_path)
            continue

        if choice == "5":
            handle_skip_today(habits_path, logs_path)
            continue

        if choice == "6":
            handle_deactivate_habit(habits_path)
            continue

        if choice == "7":
            handle_show_stats(habits_path, logs_path)
            continue

        print("Option wird implementiert.")


if __name__ == "__main__":
    main()