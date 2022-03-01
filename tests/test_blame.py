import os
import unittest
from pathlib import Path
from gitinspector import blame


class TestBlameModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.TEST_BASEDIR = Path(os.path.dirname(os.path.abspath(__file__)))
        self.PROJECT_BASEDIR = Path(self.TEST_BASEDIR).parent
        self.MODULE_BASEDIR = Path(self.PROJECT_BASEDIR, 'gitinspector')
        self.CWD = os.getcwd()

    def test_BlameEntry_attrs(self):
        blame_entry = blame.BlameEntry()
        expected = 0
        self.assertEqual(expected, blame_entry.rows)
        self.assertEqual(expected, blame_entry.skew)
        self.assertEqual(expected, blame_entry.comments)
