
import unittest
from pathlib import Path

from lastmile_ai.data.load_dataset import load_dataset


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "reference" / "LastMile_AI_Step1_Master_Dataset.xlsx"
)


class TestLastMileDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Load the approved dataset once
        before running all tests.
        """
        cls.data = load_dataset(DATASET_PATH)
        cls.residents = cls.data["Residents"]

    def test_total_residents(self):
        """
        Validate that the dataset contains
        exactly 1,000 residents.
        """
        self.assertEqual(
            len(self.residents),
            1000
        )

    def test_unique_resident_ids(self):
        """
        Check that all Resident IDs are
        unique and non-missing.
        """
        resident_ids = self.residents["Resident ID"]

        self.assertEqual(
            resident_ids.nunique(),
            1000
        )

        self.assertEqual(
            resident_ids.duplicated().sum(),
            0
        )

        self.assertEqual(
            resident_ids.isna().sum(),
            0
        )



    def test_zone_distribution(self):
        """
        Validate the approved population distribution.
        """
        expected_zones = {
            "Zone A": 400,
            "Zone B": 350,
            "Zone C": 250
        }

        actual_zones = (
            self.residents["Zone"]
            .value_counts()
            .to_dict()
        )

        self.assertEqual(actual_zones, expected_zones)



    def test_population_characteristics(self):
        """
        Validate approved synthetic population characteristics.
        """

        expected_counts = {
            "Elderly 65+": 150,
            "Policy Age 60+": 228,
            "Hearing impairment": 80,
            "Visual impairment": 60,
            "Limited internet": 250,
            "Weak mobile coverage": 120,
            "Emergency app installed": 600
        }

        for column, expected_count in expected_counts.items():

            values = (
                self.residents[column]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            self.assertTrue(
                values.isin(["yes", "no"]).all(),
                f"Invalid Yes/No value in {column}"
            )

            actual_count = int(values.eq("yes").sum())

            with self.subTest(characteristic=column):
                self.assertEqual(
                    actual_count,
                    expected_count,
                    f"{column}: expected {expected_count}, "
                    f"found {actual_count}"
                )



    def test_ev01_sms_failure(self):
        """
        Validate EV01 SMS failure distribution.
        """

        sms_values = (
            self.residents["SMS failed EV01"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        # Ensure all values are valid
        self.assertTrue(
            sms_values.isin(["yes", "no"]).all(),
            "Invalid SMS failed EV01 values"
        )

        # Identify affected residents
        sms_failed = sms_values.eq("yes")

        # Expected failures by zone
        expected_failures = {
            "Zone A": 0,
            "Zone B": 245,
            "Zone C": 0
        }

        actual_failures = (
            self.residents.loc[sms_failed, "Zone"]
            .value_counts()
            .to_dict()
        )

        # Check total affected residents
        self.assertEqual(
            int(sms_failed.sum()),
            245,
            "Incorrect total EV01 failures"
        )

        # Check distribution across zones
        for zone, expected_count in expected_failures.items():

            with self.subTest(zone=zone):
                self.assertEqual(
                    actual_failures.get(zone, 0),
                    expected_count,
                    f"Incorrect EV01 failures in {zone}"
                )

        # Ensure no unexpected affected zones
        self.assertEqual(
            set(actual_failures) - set(expected_failures),
            set(),
            "Unexpected affected zones found"
        )



    def test_b_lite_accessibility(self):
        """
        Validate approved B-Lite accessibility profiles.
        """

        def yes_flag(column):
            values = (
                self.residents[column]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            self.assertTrue(
                values.isin(["yes", "no"]).all(),
                f"Invalid Yes/No values in {column}"
            )

            return values.eq("yes")

        expected_hearing = {
            "Zone A": (31, 9),
            "Zone B": (30, 0),
            "Zone C": (19, 6)
        }

        expected_visual = {
            "Zone A": (24, 7),
            "Zone B": (20, 0),
            "Zone C": (16, 5)
        }

        hearing = yes_flag("Hearing impairment")
        voice_usable = yes_flag("Voice usable")

        visual = yes_flag("Visual impairment")
        signage_readable = yes_flag("Signage readable")

        # Validate hearing profiles
        for zone, (expected_total, expected_usable) in expected_hearing.items():

            in_zone = self.residents["Zone"].eq(zone)

            actual_total = int((in_zone & hearing).sum())
            actual_usable = int(
                (in_zone & hearing & voice_usable).sum()
            )

            with self.subTest(group="Hearing", zone=zone):
                self.assertEqual(actual_total, expected_total)
                self.assertEqual(actual_usable, expected_usable)

        # Validate visual profiles
        for zone, (expected_total, expected_readable) in expected_visual.items():

            in_zone = self.residents["Zone"].eq(zone)

            actual_total = int((in_zone & visual).sum())
            actual_readable = int(
                (in_zone & visual & signage_readable).sum()
            )

            with self.subTest(group="Visual", zone=zone):
                self.assertEqual(actual_total, expected_total)
                self.assertEqual(actual_readable, expected_readable)

        # Overall approved totals
        self.assertEqual(
            int((hearing & voice_usable).sum()),
            15
        )

        self.assertEqual(
            int((visual & signage_readable).sum()),
            12
        )



    def test_channels_and_notes(self):
        """
        Validate approved channels and preserve documentation notes.
        """

        channels = self.data["Channel Records"]
        notes = self.data["Channel Notes"]
        original = self.data["Channels"]

        expected_channels = {
            "CH01": ("SMS", 0.90),
            "CH02": ("Mobile app", 0.70),
            "CH03": ("Automated voice call", 0.85),
            "CH04": ("Public siren", 0.75),
            "CH05": ("Digital signage", 0.40)
        }

        # Validate channel count and IDs
        self.assertEqual(len(channels), 5)

        actual_ids = channels["Channel ID"].tolist()

        self.assertEqual(len(set(actual_ids)), 5)
        self.assertEqual(
            set(actual_ids),
            set(expected_channels)
        )

        # Validate individual channel details
        for channel_id, (expected_name, expected_reach) in expected_channels.items():

            row = channels.loc[
                channels["Channel ID"] == channel_id
            ].iloc[0]

            with self.subTest(channel=channel_id):

                self.assertEqual(
                    str(row["Channel"]).strip(),
                    expected_name
                )

                self.assertAlmostEqual(
                    float(row["Synthetic reach assumption"]),
                    expected_reach
                )

        # Validate documentation notes
        self.assertEqual(len(notes), 4)

        # Ensure documentation notes are preserved exactly
        original_notes = original.loc[
            notes.index
        ]

        self.assertTrue(
            notes.equals(original_notes),
            "Documentation notes were modified"
        )

        # Account for every original row
        empty_rows = int(
            original.isna().all(axis=1).sum()
        )

        self.assertEqual(empty_rows, 1)

        self.assertEqual(
            len(channels) + len(notes) + empty_rows,
            len(original)
        )



    def test_event_timeline(self):
        """
        Validate approved event IDs and simulated times.
        """

        events = self.data["Event Timeline"]

        time_column = (
            "Simulated time (T+MM:SS; minutes:seconds)"
        )

        expected_events = {
            "START": "T+00:00",
            "EV01": "T+02:00",
            "EV02": "T+04:00",
            "EV03": "T+06:00",
            "EVAL": "T+07:00+"
        }

        # Validate number of event records
        self.assertEqual(len(events), 5)

        # Validate missing and duplicate IDs
        self.assertEqual(
            int(events["Event ID"].isna().sum()),
            0
        )

        self.assertEqual(
            int(events["Event ID"].duplicated().sum()),
            0
        )

        # Read actual event IDs and times
        actual_events = dict(
            zip(
                events["Event ID"],
                events[time_column]
            )
        )

        self.assertEqual(
            actual_events,
            expected_events
        )

        # Check chronological order
        self.assertEqual(
            events["Event ID"].tolist(),
            list(expected_events.keys())
        )

        



    def test_age_consistency(self):
        """
        Validate resident ages and age classification flags.
        """

        import pandas as pd

        ages = pd.to_numeric(
            self.residents["Age"],
            errors="coerce"
        )

        # Validate ages
        self.assertTrue(ages.notna().all())
        self.assertTrue((ages >= 0).all())
        self.assertTrue((ages % 1 == 0).all())

        # Calculate age classifications
        actual_65_plus = ages >= 65
        actual_60_plus = ages >= 60
        actual_60_64 = (ages >= 60) & (ages < 65)

        # Validate approved counts
        self.assertEqual(int(actual_65_plus.sum()), 150)
        self.assertEqual(int(actual_60_plus.sum()), 228)
        self.assertEqual(int(actual_60_64.sum()), 78)

        # Validate individual classification flags
        for column, expected_flags in [
            ("Elderly 65+", actual_65_plus),
            ("Policy Age 60+", actual_60_plus)
        ]:

            values = (
                self.residents[column]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            # Reject missing or invalid classifications
            self.assertTrue(
                values.isin(["yes", "no"]).all(),
                f"Invalid values in {column}"
            )

            recorded_flags = values.eq("yes")

            with self.subTest(column=column):
                self.assertTrue(
                    (
                        expected_flags.to_numpy(dtype=bool)
                        ==
                        recorded_flags.to_numpy(dtype=bool)
                    ).all(),
                    f"Age classification mismatch in {column}"
                )



    def test_data_quality(self):
        """
        Validate required columns, missing values,
        and allowed Yes/No values.
        """

        required_columns = [
            "Resident ID",
            "Zone",
            "Age",
            "Elderly 65+",
            "Policy Age 60+",
            "Hearing impairment",
            "Visual impairment",
            "Limited internet",
            "Weak mobile coverage",
            "Emergency app installed",
            "In siren area",
            "In signage area",
            "SMS failed EV01",
            "Voice usable",
            "Signage readable"
        ]

        # Check required columns
        missing_columns = [
            col for col in required_columns
            if col not in self.residents.columns
        ]

        self.assertEqual(
            missing_columns,
            [],
            f"Missing required columns: {missing_columns}"
        )

        # Check missing values
        missing_values = (
            self.residents[required_columns]
            .isna()
            .sum()
        )

        self.assertEqual(
            int(missing_values.sum()),
            0,
            f"Missing values found: {missing_values.to_dict()}"
        )

        # Validate Yes/No columns
        yes_no_columns = [
            col for col in required_columns
            if col not in ["Resident ID", "Zone", "Age"]
        ]

        for column in yes_no_columns:

            values = (
                self.residents[column]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            with self.subTest(column=column):
                self.assertTrue(
                    values.isin(["yes", "no"]).all(),
                    f"Invalid Yes/No values in {column}"
                )

        # Check approved zones
        self.assertEqual(
            set(self.residents["Zone"]),
            {"Zone A", "Zone B", "Zone C"}
        )



    def test_ev01_outage_duration(self):
        """
        Validate the five-minute EV01 outage
        using actual event timeline values.
        """

        events = self.data["Event Timeline"]

        time_column = (
            "Simulated time (T+MM:SS; minutes:seconds)"
        )

        # Read event times directly from the dataset
        event_times = events.set_index("Event ID")[time_column]

        ev01_time = str(event_times.loc["EV01"]).strip()
        eval_time = str(event_times.loc["EVAL"]).strip()

        def time_to_seconds(value):
            cleaned = value.removeprefix("T+").rstrip("+")

            minutes, seconds = cleaned.split(":")

            return int(minutes) * 60 + int(seconds)

        outage_start = time_to_seconds(ev01_time)
        outage_end = time_to_seconds(eval_time)

        # Validate the approved five-minute interval
        self.assertEqual(
            outage_end - outage_start,
            5 * 60,
            "EV01 outage duration must be 5 minutes"
        )

        # Confirm EVAL is an end/reference marker
        self.assertTrue(
            eval_time.endswith("+"),
            "EVAL must remain a reference marker"
        )


if __name__ == "__main__":
    unittest.main()
