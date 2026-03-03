import csv
import tempfile
import unittest
from pathlib import Path
from storage import ensure_storage, HABITS_HEADER, LOGS_HEADER

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


if __name__ == "__main__":
    unittest.main()