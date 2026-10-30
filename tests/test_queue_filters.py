import unittest

import pandas as pd

from app.queue_filters import filter_case_queue


class QueueFilterTests(unittest.TestCase):
    def setUp(self):
        self.cases = pd.DataFrame({
            "Case ID": ["DH000001", "DH000002", "DH000003", "DH000004"],
            "Policy Number": ["PET.001", "PETX001", "PET000003", "PET000004"],
            "Client Number": ["CL000001", "CL000002", "CL000003", None],
            "Agent Working": [None, "DH001", "DH002", "  "],
        }, index=[11, 17, 23, 42])

    def test_searches_identifiers_and_treats_punctuation_literally(self):
        for term, expected in [
            (" dh000003 ", ["DH000003"]),
            ("cl000002", ["DH000002"]),
            ("PET.001", ["DH000001"]),
            ("PET.*", []),
        ]:
            with self.subTest(term=term):
                actual = filter_case_queue(self.cases, term)
                self.assertEqual(actual["Case ID"].tolist(), expected)

    def test_assignment_filters_combine_with_search(self):
        unassigned = filter_case_queue(self.cases, assignment_mode="unassigned")
        self.assertEqual(unassigned["Case ID"].tolist(), ["DH000001", "DH000004"])
        assigned = filter_case_queue(
            self.cases, "petx", assignment_mode="agent", agent_id="DH001"
        )
        self.assertEqual(assigned["Case ID"].tolist(), ["DH000002"])
        mismatch = filter_case_queue(
            self.cases, "petx", assignment_mode="agent", agent_id="DH002"
        )
        self.assertTrue(mismatch.empty)

    def test_preserves_original_rows_and_returns_positional_index(self):
        before = self.cases.copy(deep=True)
        actual = filter_case_queue(
            self.cases, assignment_mode="agent", agent_id="DH002"
        )
        pd.testing.assert_frame_equal(self.cases, before)
        self.assertEqual(actual.index.tolist(), [0])
        self.assertEqual(actual.iloc[0]["Case ID"], "DH000003")


if __name__ == "__main__":
    unittest.main()
