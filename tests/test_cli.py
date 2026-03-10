import unittest
from datetime import date

from models import Habit
from cli import (
    format_habit_line,
    normalize_habit_type,
    normalize_period,
    parse_frequency_for_period,
    parse_date_or_today,
)


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

    def test_parse_frequency_for_period(self):
        self.assertEqual(parse_frequency_for_period("daily", "999"), 0)
        self.assertEqual(parse_frequency_for_period("weekly", "3"), 3)
        with self.assertRaises(ValueError):
            parse_frequency_for_period("weekly", "")
        with self.assertRaises(ValueError):
            parse_frequency_for_period("weekly", "0")

    def test_parse_date_or_today_empty_returns_today(self):
        fake_today = date(2026, 3, 5)
        result = parse_date_or_today("", today_value=fake_today)
        self.assertEqual(result, fake_today)

    def test_parse_date_or_today_parses_iso_date(self):
        result = parse_date_or_today("2026-03-01", today_value=date(2026, 3, 5))
        self.assertEqual(result, date(2026, 3, 1))

    def test_parse_date_or_today_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_date_or_today("03/01/2026", today_value=date(2026, 3, 5))

if __name__ == "__main__":
    unittest.main()