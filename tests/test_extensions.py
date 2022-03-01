import unittest
from gitinspector import extensions


class TestExtensions(unittest.TestCase):

    def test_001_extensions_get(self):
        expected = extensions.DEFAULT_EXTENSIONS
        actual = extensions.get()
        self.assertEqual(expected, actual)

    def test_002_extensions_define(self):
        expected = 'txt,md'
        extensions.define(expected)
        actual = extensions.get()
        self.assertEqual(expected.split(","), actual)

    def test_003_add_located(self):
        expected = set('*')
        extensions.add_located('')
        actual = extensions.get_located()
        self.assertEqual(expected, actual)

        expected = set(['ext', '*'])
        extensions.add_located('ext')
        actual = extensions.get_located()
        self.assertEqual(expected, actual)
