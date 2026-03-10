import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path
from models import Habit, LogEntry
from storage import (
    ensure_storage,
    HABITS_HEADER,
    LOGS_HEADER,
    load_habits,
    save_habits,
    load_logs,
    upsert_log,
    add_habit,
    set_habit_active,
)

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)
        self.habits_path, self.logs_path = ensure_storage(self.data_dir)


    def tearDown(self):
        self.temp.cleanup()


    def _read_cvs_rows(self, path: Path):
        with path.open("r", newline="", encoding="utf-8") as csv_file:
            return list(csv.DictReader(csv_file))


    def test_ensure_storage_creates_files_with_headers(self):
        self.assertTrue(self.habits_path.exists())
        self.assertTrue(self.logs_path.exists())

        # Überprüfen der Header durch Lesen der ersten Zeile
        habits_rows = self._read_cvs_rows(self.habits_path)
        logs_rows = self._read_cvs_rows(self.logs_path)

        habits_header_line = self.habits_path.read_text(encoding="utf-8").splitlines()[0]
        logs_header_line = self.logs_path.read_text(encoding="utf-8").splitlines()[0]

        self.assertEqual(habits_header_line, ",".join(HABITS_HEADER))
        self.assertEqual(logs_header_line, ",".join(LOGS_HEADER))

        self.assertEqual(habits_rows, [])
        self.assertEqual(logs_rows, [])

    def test_habits_roundtrip_save_and_load(self):
        h1 = Habit.create(
            name="Drink water",
            type="good",
            period="daily",
            frequency=0,
            start_date=date(2026, 3, 3),
        )
        h2 = Habit.create(
            name="No sugar",
            type="bad",
            period="weekly",
            frequency=3,
            start_date=date(2026, 3, 3),
        )

        save_habits(self.habits_path, [h1, h2])
        loaded = load_habits(self.habits_path)

        self.assertEqual(loaded, [h1, h2])

    def test_upsert_log_inserts_then_updates(self):
        # Wir erstellen eine Gewohnheit und speichern sie (damit sie „in der Welt“ existiert)
        h = Habit.create(
            name="Read 10 min",
            type="good",
            period="daily",
            frequency=0,
            start_date=date(2026, 3, 3),
        )
        save_habits(self.habits_path, [h])

        d = date(2026, 3, 3)

        first = LogEntry.create(habit_id=h.habit_id, date_value=d, status="success")
        upsert_log(self.logs_path, first)

        second = LogEntry.create(habit_id=h.habit_id, date_value=d, status="fail")
        upsert_log(self.logs_path, second)

        logs = load_logs(self.logs_path)

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].habit_id, h.habit_id)
        self.assertEqual(logs[0].date, d)
        self.assertEqual(logs[0].status, "fail")

    def test_add_habit_appends(self):
        h = Habit.create(
            name="Meditate",
            type="good",
            period="daily",
            frequency=0,
            start_date=date(2026, 3, 3),
        )

        add_habit(self.habits_path, h)
        loaded = load_habits(self.habits_path)

        self.assertEqual(loaded, [h])

    def test_set_habit_active_deactivates(self):
        h = Habit.create(
            name="Meditate",
            type="good",
            period="daily",
            frequency=0,
            start_date=date(2026, 3, 3),
        )
        add_habit(self.habits_path, h)

        updated = set_habit_active(self.habits_path, h.habit_id, False)
        self.assertFalse(updated.active)

        loaded = load_habits(self.habits_path)
        self.assertEqual(len(loaded), 1)
        self.assertFalse(loaded[0].active)
        self.assertEqual(loaded[0].habit_id, h.habit_id)


if __name__ == "__main__":
    unittest.main()