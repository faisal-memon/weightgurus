import csv
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.modules.setdefault("requests", MagicMock())
from main import WeightGurus


class WeightGurusTests(unittest.TestCase):
    def test_clean_operations_removes_only_exact_deleted_row(self):
        operations = [
            {
                "operationType": "create",
                "weight": 1505,
                "entryTimestamp": "2020-01-01T10:00:00Z",
                "serverTimestamp": "2020-01-01T10:00:00Z",
            },
            {
                "operationType": "create",
                "weight": 1505,
                "entryTimestamp": "2020-01-02T10:00:00Z",
                "serverTimestamp": "2020-01-02T10:00:00Z",
            },
            {
                "operationType": "delete",
                "weight": 1505,
                "entryTimestamp": "2020-01-02T10:00:00Z",
                "serverTimestamp": "2020-01-03T10:00:00Z",
            },
            {
                "operationType": "create",
                "weight": 1520,
                "entryTimestamp": "2020-01-05T10:00:00Z",
                "serverTimestamp": "2020-01-05T10:00:00Z",
            },
        ]

        cleaned = WeightGurus._clean_operations(operations)

        self.assertEqual(
            cleaned,
            [
                {
                    "operationType": "create",
                    "weight": 1505,
                    "entryTimestamp": "2020-01-01T10:00:00Z",
                    "serverTimestamp": "2020-01-01T10:00:00Z",
                },
                {
                    "operationType": "create",
                    "weight": 1520,
                    "entryTimestamp": "2020-01-05T10:00:00Z",
                    "serverTimestamp": "2020-01-05T10:00:00Z",
                },
            ],
        )

    def test_clean_operations_removes_malformed_future_rows(self):
        operations = [
            {
                "operationType": "create",
                "weight": 1558,
                "entryTimestamp": "2036-02-08T06:44:34.000Z",
                "serverTimestamp": "2020-08-23T18:41:40.110Z",
            },
            {
                "operationType": "delete",
                "weight": 1558,
                "entryTimestamp": "2036-02-08T06:44:34.000Z",
                "serverTimestamp": "2020-10-15T18:25:21.114Z",
            },
            {
                "operationType": "create",
                "weight": 1478,
                "entryTimestamp": "2026-02-20T17:18:13.000Z",
                "serverTimestamp": "2026-02-20T17:19:33.579Z",
            },
        ]

        cleaned = WeightGurus._clean_operations(operations)

        self.assertEqual(
            cleaned,
            [
                {
                    "operationType": "create",
                    "weight": 1478,
                    "entryTimestamp": "2026-02-20T17:18:13.000Z",
                    "serverTimestamp": "2026-02-20T17:19:33.579Z",
                }
            ],
        )

    def test_format_csv_row_matches_expected_shape(self):
        with patch.dict("os.environ", {"WG_CSV_TIMEZONE": "America/Phoenix"}, clear=False):
            row = WeightGurus._format_csv_row(
                {
                    "weight": 1507,
                    "bodyFat": 148,
                    "muscleMass": 420,
                    "water": 649,
                    "bmi": 216,
                    "boneMass": 0,
                    "entryTimestamp": "2019-12-31T01:47:04Z",
                }
            )

        self.assertEqual(
            row,
            {
                "weight_lb": "150.7",
                "body_fat_pct": "14.8",
                "muscle_mass_pct": "42",
                "water_pct": "64.9",
                "bmi": "21.6",
                "bone_mass_pct": "0",
                "datetime": "2019-12-30T18:47:04-07:00",
            },
        )

    def test_save_all_csv_uses_cleaned_operations_and_friendly_columns(self):
        api_operations = [
            {
                "operationType": "create",
                "weight": 1507,
                "bodyFat": 148,
                "muscleMass": 420,
                "water": 649,
                "bmi": 216,
                "entryTimestamp": "2019-12-31T01:47:04Z",
                "serverTimestamp": "2019-12-31T01:47:04Z",
            },
            {
                "operationType": "delete",
                "weight": 1507,
                "entryTimestamp": "2019-12-31T01:47:04Z",
                "serverTimestamp": "2019-12-31T18:47:04Z",
            },
            {
                "operationType": "create",
                "weight": 1479,
                "bodyFat": 142,
                "muscleMass": 424,
                "water": 654,
                "bmi": 212,
                "entryTimestamp": "2019-12-31T06:01:06Z",
                "serverTimestamp": "2019-12-31T06:01:06Z",
            },
            {
                "operationType": "create",
                "weight": 6703,
                "bodyFat": 67,
                "muscleMass": 250,
                "water": 730,
                "bmi": 962,
                "entryTimestamp": "2106-02-07T06:28:15.000Z",
                "serverTimestamp": "2026-02-25T16:12:22.954Z",
            },
        ]

        client = WeightGurus("user@example.com", "secret")

        with tempfile.NamedTemporaryFile("w+", newline="", suffix=".csv") as temp_file:
            with patch.dict("os.environ", {"WG_CSV_TIMEZONE": "America/Phoenix"}, clear=False):
                with patch.object(client, "_WeightGurus__do_login"), patch.object(
                    client,
                    "_WeightGurus__get_weight_history",
                    return_value={"operations": api_operations},
                ):
                    csv_path = client.save_all_csv(temp_file.name)

            self.assertEqual(csv_path, temp_file.name)

            temp_file.seek(0)
            rows = list(csv.DictReader(temp_file))

        self.assertEqual(
            rows,
            [
                {
                    "weight_lb": "147.9",
                    "body_fat_pct": "14.2",
                    "muscle_mass_pct": "42.4",
                    "water_pct": "65.4",
                    "bmi": "21.2",
                    "bone_mass_pct": "0",
                    "datetime": "2019-12-30T23:01:06-07:00",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
