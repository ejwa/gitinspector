import unittest
from gitinspector import interval

TEST_STRING = 'arbitrary'


class TestInterval(unittest.TestCase):

    def test_has_interval(self):
        actual = interval.has_interval()
        self.assertFalse(actual)

    def test_get_since(self):
        expected = ''
        actual = interval.get_since()
        self.assertEqual(expected, actual)

    def test_set_since(self):
        expected = '--since=' + TEST_STRING
        interval.set_since(TEST_STRING)
        actual = interval.get_since()
        self.assertEqual(expected, actual)
