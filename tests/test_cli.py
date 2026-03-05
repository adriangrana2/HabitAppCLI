import unittest
from datetime import date

from models import Habit
from cli import format_habit_line, normalize_habit_type, normalize_period


class TestCLI(unittest.TestCase):
    def test_format_habit_line_daily_no_frequency(self):
        h = Habit.create(
            name="Drink water",
            type="good",
            period="daily",
            frequency=0,
            start_date=date(2026, 3, 3),
        )
        line = format_habit_line(h)
        self.assertIn(h.habit_id, line)
        self.assertIn("daily", line)
        self.assertNotIn("freq=", line)

    def test_format_habit_line_weekly_includes_frequency(self):
        h = Habit.create(
            name="No sugar",
            type="bad",
            period="weekly",
            frequency=3,
            start_date=date(2026, 3, 3),
        )
        line = format_habit_line(h)
        self.assertIn("weekly", line)
        self.assertIn("freq=3/week", line)


    def test_normalize_habit_type(self):
        self.assertEqual(normalize_habit_type("g"), "good")
        self.assertEqual(normalize_habit_type("BAD"), "bad")
        with self.assertRaises(ValueError):
            normalize_habit_type("x")

    def test_normalize_period(self):
        self.assertEqual(normalize_period("d"), "daily")
        self.assertEqual(normalize_period("Weekly"), "weekly")
        with self.assertRaises(ValueError):
            normalize_period("month")

if __name__ == "__main__":
    unittest.main()