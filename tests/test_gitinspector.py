import unittest
import json
import pytest
from gitinspector import gitinspector

TEST_STRING = 'arbitrary'


class TestGitInspector(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_Runner(self):
        test_runner = gitinspector.Runner()
        expected_attrs = {
            "hard": False,
            "include_metrics": False,
            "list_file_types": False,
            "localize_output": False,
            "responsibilities": False,
            "grading": False,
            "timeline": False,
            "useweeks": False
        }
        for key, val in expected_attrs.items():
            self.assertEqual(getattr(test_runner, key), val)

    def test_main(self):
        self.maxDiff = None
        gitinspector.main()
        out, err = self.capsys.readouterr()
        json.loads(out)
        self.assertEqual(err, '')
