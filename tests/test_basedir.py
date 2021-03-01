import os
import unittest
from pathlib import Path
from gitinspector import basedir


class TestBasedirModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.TEST_BASEDIR = Path(os.path.dirname(os.path.abspath(__file__)))
        self.PROJECT_BASEDIR = Path(self.TEST_BASEDIR).parent
        self.MODULE_BASEDIR = Path(self.PROJECT_BASEDIR, 'gitinspector')
        self.CWD = os.getcwd()

    def test_get_basedir(self):
        expected = str(self.MODULE_BASEDIR)
        actual = basedir.get_basedir()
        self.assertEqual(expected, actual)

    def test_get_basedir_git(self):
        expected = self.CWD
        actual = basedir.get_basedir_git()
        self.assertEqual(expected, actual)

    def test_get_basedir_git_with_path(self):
        expected = str(self.PROJECT_BASEDIR)
        actual = basedir.get_basedir_git(self.TEST_BASEDIR)
        self.assertEqual(expected, actual)
