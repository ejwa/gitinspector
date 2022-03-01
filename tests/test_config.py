import unittest
from gitinspector import config


class TestConfig(unittest.TestCase):

    def test_GitConfig_init(self):
        expected_run = 'run'
        expected_repo = 'repo'
        expected_global_only = False
        test_config = config.GitConfig(expected_run, expected_repo)
        self.assertEqual(expected_run, test_config.run)
        self.assertEqual(expected_repo, test_config.repo)
        self.assertEqual(expected_global_only, test_config.global_only)

    def test_read_git_config_unknown_variable(self):
        expected_return_value = ''
        test_config = config.GitConfig('arbitrary', '.')
        actual_return_value = test_config.__read_git_config__('unknown')
        self.assertEqual(expected_return_value, actual_return_value)

    def test_read_git_config_string_unknown(self):
        expected_return_value = (False, None)
        test_config = config.GitConfig('arbitrary', '.')
        actual_return_value = test_config.__read_git_config_string__('unknown')
        self.assertEqual(expected_return_value, actual_return_value)

    def test_read(self):
        class Dummy():
            pass
        test_config = config.GitConfig(Dummy(), '.')

        with self.assertRaises(AttributeError):
            self.assertFalse(test_config.run.hard)

        test_config.read()
        self.assertFalse(test_config.run.hard)
