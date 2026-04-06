#!/usr/bin/env python3
from cmath import nan
from datetime import datetime, timedelta
import json
import csv
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

def transform_weight(weight):
    """
    Transforms normal weight in pounds to Weight Gurus format

    :param weight: Weight in pounds
    :return: Weight Guru format
    """
    try:
        weight = str(weight).replace('.', '')
        transformed_weight = int(weight)
        return transformed_weight
    except ValueError:
        try:
            transformed_weight = int(float(weight))
            return transformed_weight
        except ValueError:
            print(f"Caught ValueError! '{weight}' is not a number.")


class WeightGurus:
    CSV_FIELDNAMES = [
        "weight_lb",
        "body_fat_pct",
        "muscle_mass_pct",
        "water_pct",
        "bmi",
        "bone_mass_pct",
        "datetime",
    ]

    def __init__(self, username, password):
        self.login_data = {
            'email': username,
            'password': password,
            'web': True
        }
        self.headers = None
        self.start_date = 'start=1970-01-01T01:00:00.504Z'
        self.weight_history = None
        self.add_weight = {}

    def __do_login(self):
        req = requests.post('https://api.weightgurus.com/v3/account/login', data=self.login_data)
        try:
            json_data = req.json()
            self.headers = {'authorization': f"Bearer {json_data['accessToken']}"
                            }
        except Exception as e:
            print(f"Caught Exception reading JSON: {e}")

    def __get_weight_history(self, start_date=None):
        if start_date:
            self.start_date = f"start={start_date}"
        req = requests.get(f'https://api.weightgurus.com/v3/operation/?{self.start_date}', headers=self.headers)
        try:
            json_data = req.json()
        except Exception as e:
            print(f"Caught Exception reading JSON: {e}")
            json_data = None
        return json_data

    def get_all(self):
        self.__do_login()
        return json.dumps(self.__get_weight_history(), indent=4, sort_keys=True)

    def save_all_csv(self, filename=None):
        """
        Fetches the full weight history and writes it to a CSV file.

        The output file can be set via the environment variable
        ``WG_CSV_FILE``. If the variable is not set the
        default ``weights.csv`` will be used.

        Parameters
        ----------
        filename: str, optional
            Path to the output CSV file. If ``None`` the value from the
            environment variable (or the default) is used.

        Returns
        -------
        str or None
            The path of the created CSV file, or ``None`` if the write
            failed.
        """
        # Resolve filename from env or default
        if filename is None:
            filename = os.getenv("WG_CSV_FILE", "weights.csv")

        self.__do_login()
        data = self.__get_weight_history()
        if not data or "operations" not in data:
            print("No data to write to CSV.")
            return None
        operations = self._clean_operations(data["operations"])
        if not operations:
            print("No operations found.")
            return None
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(self._format_csv_rows(operations))
        return filename

    def get_since_date(self, start_date):
        self.__do_login()
        return json.dumps(self.__get_weight_history(start_date), indent=4, sort_keys=True)

    def get_latest(self):
        self.__do_login()
        weight_data = self.__get_weight_history()
        return json.dumps(weight_data['operations'][-1])
    
    def get_unremoved_entries(self):
        self.__do_login()
        operations = self.__get_weight_history()["operations"]
        operations = self._clean_operations(operations)
        return json.dumps(operations, indent=4, sort_keys=True)


    @staticmethod
    def _clean_operations(operations: list):
        operations = WeightGurus._remove_malformed_operations(list(operations))
        return WeightGurus._remove_deleted_operations(operations)

    @staticmethod
    def _remove_malformed_operations(operations):
        return [
            operation
            for operation in operations
            if not WeightGurus._is_malformed_operation(operation)
        ]

    @staticmethod
    def _is_malformed_operation(operation):
        entry_timestamp = operation.get("entryTimestamp")
        server_timestamp = operation.get("serverTimestamp")
        if not entry_timestamp or not server_timestamp:
            return False

        entry_date = datetime.fromisoformat(entry_timestamp.replace("Z", "+00:00"))
        server_date = datetime.fromisoformat(server_timestamp.replace("Z", "+00:00"))
        return entry_date > server_date + timedelta(days=1)

    @staticmethod
    def _remove_deleted_operations(operations):
        cleaned_operations = [
            operation
            for operation in operations
            if operation.get("operationType") != "delete"
        ]
        deleted_operations = [
            operation
            for operation in operations
            if operation.get("operationType") == "delete"
        ]

        for deleted_operation in deleted_operations:
            cleaned_operations = WeightGurus._remove_operation_deleted(
                cleaned_operations, deleted_operation
            )

        return cleaned_operations

    @staticmethod
    def _remove_operation_deleted(operations, deleted_operation):
        deleted_match_removed = False
        remaining_operations = []

        for current_operation in operations:
            if (
                not deleted_match_removed
                and WeightGurus._is_deleted_operation(
                    current_operation, deleted_operation
                )
            ):
                deleted_match_removed = True
                continue

            remaining_operations.append(current_operation)

        return remaining_operations

    @staticmethod
    def _is_deleted_operation(current_operation, deleted_operation):
        return (
            current_operation.get("weight") == deleted_operation.get("weight")
            and current_operation.get("entryTimestamp")
            == deleted_operation.get("entryTimestamp")
        )

    @staticmethod
    def _get_csv_timezone():
        timezone_name = os.getenv("WG_CSV_TIMEZONE") or os.getenv("TZ")
        if not timezone_name:
            return ZoneInfo("UTC")

        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    @staticmethod
    def _format_datetime_for_csv(timestamp):
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.astimezone(WeightGurus._get_csv_timezone()).isoformat()

    @staticmethod
    def _wg_num_to_float(number):
        number = str(number)
        if len(number) <= 1:
            raise Exception(
                "Unsure of how weight guru handles numbers this small"
            )

        try:
            whole_number = int(number[:-1])
        except ValueError:
            return nan

        try:
            decimal_point = int(number[-1]) / 10
        except ValueError:
            return nan

        return whole_number + decimal_point

    @staticmethod
    def _format_decimal(value, force_one_decimal=False):
        if value is None:
            value = 0

        if force_one_decimal:
            return f"{value:.1f}"

        formatted = f"{value:.1f}".rstrip("0").rstrip(".")
        return formatted or "0"

    @staticmethod
    def _format_csv_metric(value, suffix="", force_one_decimal=False):
        if value in (None, "", 0, "0"):
            numeric_value = 0
        else:
            numeric_value = WeightGurus._wg_num_to_float(value)

        return f"{WeightGurus._format_decimal(numeric_value, force_one_decimal)}{suffix}"

    @staticmethod
    def _format_csv_timestamp(operation):
        timestamp = operation.get("entryTimestamp") or operation.get("serverTimestamp")
        if not timestamp:
            return ""

        return WeightGurus._format_datetime_for_csv(timestamp)

    @staticmethod
    def _format_csv_row(operation):
        return {
            "weight_lb": WeightGurus._format_csv_metric(
                operation.get("weight"), force_one_decimal=True
            ),
            "body_fat_pct": WeightGurus._format_csv_metric(
                operation.get("bodyFat")
            ),
            "muscle_mass_pct": WeightGurus._format_csv_metric(
                operation.get("muscleMass")
            ),
            "water_pct": WeightGurus._format_csv_metric(
                operation.get("water")
            ),
            "bmi": WeightGurus._format_csv_metric(operation.get("bmi")),
            "bone_mass_pct": WeightGurus._format_csv_metric(
                operation.get("boneMass")
            ),
            "datetime": WeightGurus._format_csv_timestamp(operation),
        }

    @staticmethod
    def _format_csv_rows(operations):
        return [
            WeightGurus._format_csv_row(operation)
            for operation in sorted(
                operations,
                key=lambda operation: operation.get("entryTimestamp")
                or operation.get("serverTimestamp")
                or "",
            )
        ]


    def manual_entry(self, weight, bmi=None, body_fat=None, muscle_mass=None, water=None):
        """
        Weight Gurus has a weird way of adding weight, they want integer values (numbers) without decimals.
        This requires you to take you weight and remove the decimal. So, 100.0 pounds would be 1000 when you add it.
        """
        self.__do_login()
        self.headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, ' \
                                     'like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        self.headers['content-type'] = 'application/json'
        if bmi:
            self.add_weight['bmi'] = int(bmi)
        if body_fat:
            self.add_weight['bodyFat'] = int(body_fat)
        self.add_weight['entryTimestamp'] = str(datetime.now())
        if muscle_mass:
            self.add_weight['muscleMass'] = int(muscle_mass)
        self.add_weight['operationType'] = 'create'
        self.add_weight['source'] = 'manual'
        if water:
            self.add_weight['water'] = int(water)
        if weight is None:
            print("You need to provide your weight")
            exit(1)
            return False
        weight = transform_weight(weight)
        self.add_weight['weight'] = weight
        req = requests.post('https://api.weightgurus.com/v3/operation',
                            data=json.dumps(self.add_weight),
                            headers=self.headers)
        status_code = req.status_code
        if status_code == 201:
            print("Successfully added weight!")
            return req.json()


if __name__ == "__main__":
    username = os.getenv('WG_USERNAME')
    password = os.getenv('WG_PASSWORD')
    if not username or not password:
        raise RuntimeError('WG_USERNAME and WG_PASSWORD env vars must be set')
    weight_gurus = WeightGurus(username, password)
    csv_path = weight_gurus.save_all_csv()
    if csv_path:
        print(f"✅ Weight data saved successfully at {csv_path} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"❌ Failed to save CSV at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
