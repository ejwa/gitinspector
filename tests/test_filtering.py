import unittest
from gitinspector import filtering

TEST_STRING = 'arbitrary'


class TestFiltering(unittest.TestCase):

    def test_InvalidRegExpError(self):
        with self.assertRaises(filtering.InvalidRegExpError):
            raise filtering.InvalidRegExpError(TEST_STRING)

    def test_get(self):
        expected = filtering.__filters__
        actual = filtering.get()
        self.assertEqual(expected, actual)

    def test_add(self):
        filtering.add(TEST_STRING)
        expected = [{TEST_STRING}, set()]
        actual = filtering.get()['file']
        self.assertEqual(expected, actual)

    def test_get_filered(self):
        filtering.add(TEST_STRING)
        expected = set()
        actual = filtering.get_filered()
        self.assertEqual(expected, actual)

    def test_has_filtered(self):
        self.assertFalse(filtering.has_filtered())

    def test_set_filtered(self):
        test_commit_sha = '53d81bcd2612dbc47e73c71ee43baae83c1ec252'
        return_value = filtering.set_filtered(test_commit_sha)
        self.assertFalse(return_value)
