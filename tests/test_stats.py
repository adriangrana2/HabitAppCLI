import unittest
from datetime import date

from models import LogEntry
from stats import count_statuses


class TestStats(unittest.TestCase):
    def test_count_statuses(self):
        habit_id = "H1"
        other_id = "H2"

        logs = [
            LogEntry(log_id="1", habit_id=habit_id, date=date(2026, 3, 1), status="success"),
            LogEntry(log_id="2", habit_id=habit_id, date=date(2026, 3, 2), status="fail"),
            LogEntry(log_id="3", habit_id=habit_id, date=date(2026, 3, 3), status="skip"),
            LogEntry(log_id="4", habit_id=other_id, date=date(2026, 3, 3), status="success"),
        ]

        result = count_statuses(logs, habit_id)

        self.assertEqual(result["success"], 1)
        self.assertEqual(result["fail"], 1)
        self.assertEqual(result["skip"], 1)


if __name__ == "__main__":
    unittest.main()