"""Comprehensive tests for basedir module."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from gitinspector import basedir
from gitinspector.git_utils import GitCommandError


class TestBasedirModule(unittest.TestCase):
    """Test suite for basedir module."""

    def setUp(self):
        """Set up test fixtures."""
        self.TEST_BASEDIR = Path(os.path.dirname(os.path.abspath(__file__)))
        self.PROJECT_BASEDIR = Path(self.TEST_BASEDIR).parent
        self.MODULE_BASEDIR = Path(self.PROJECT_BASEDIR, 'gitinspector')
        self.CWD = os.getcwd()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_get_basedir_normal_execution(self):
        """Test get_basedir under normal execution."""
        expected = str(self.MODULE_BASEDIR)
        actual = basedir.get_basedir()
        self.assertEqual(expected, actual)
        
    def test_get_basedir_returns_string(self):
        """Test that get_basedir returns a string."""
        result = basedir.get_basedir()
        self.assertIsInstance(result, str)
        
    def test_get_basedir_path_exists(self):
        """Test that get_basedir returns an existing path."""
        result = basedir.get_basedir()
        self.assertTrue(Path(result).exists())
        
    @patch('sys.frozen', True, create=True)
    @patch('sys.prefix', '/frozen/app/path')
    def test_get_basedir_frozen_application(self):
        """Test get_basedir for frozen application (py2exe)."""
        result = basedir.get_basedir()
        self.assertEqual(result, '/frozen/app/path')

    @patch('gitinspector.basedir.is_bare_repository')
    @patch('gitinspector.basedir.get_git_dir')
    def test_get_basedir_git_bare_repository(self, mock_get_git_dir, mock_is_bare):
        """Test get_basedir_git for bare repository."""
        mock_is_bare.return_value = True
        mock_get_git_dir.return_value = Path('/path/to/bare/repo.git')
        
        result = basedir.get_basedir_git()
        
        self.assertEqual(result, '/path/to/bare/repo.git')
        mock_is_bare.assert_called_once_with(None)
        mock_get_git_dir.assert_called_once_with(None)
        
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('gitinspector.basedir.get_git_repository_root')
    def test_get_basedir_git_regular_repository(self, mock_get_repo_root, mock_is_bare):
        """Test get_basedir_git for regular repository."""
        mock_is_bare.return_value = False
        mock_get_repo_root.return_value = Path('/path/to/repo')
        
        result = basedir.get_basedir_git()
        
        self.assertEqual(result, '/path/to/repo')
        mock_is_bare.assert_called_once_with(None)
        mock_get_repo_root.assert_called_once_with(None)
        
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('gitinspector.basedir.get_git_repository_root')
    def test_get_basedir_git_with_path_parameter(self, mock_get_repo_root, mock_is_bare):
        """Test get_basedir_git with specific path parameter."""
        test_path = '/some/test/path'
        mock_is_bare.return_value = False
        mock_get_repo_root.return_value = Path('/path/to/repo')
        
        result = basedir.get_basedir_git(test_path)
        
        self.assertEqual(result, '/path/to/repo')
        mock_is_bare.assert_called_once_with(test_path)
        mock_get_repo_root.assert_called_once_with(test_path)
        
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('gitinspector.basedir.get_git_repository_root')
    def test_get_basedir_git_with_pathlib_path(self, mock_get_repo_root, mock_is_bare):
        """Test get_basedir_git with pathlib.Path parameter."""
        test_path = Path('/some/test/path')
        mock_is_bare.return_value = False
        mock_get_repo_root.return_value = Path('/path/to/repo')
        
        result = basedir.get_basedir_git(test_path)
        
        self.assertEqual(result, '/path/to/repo')
        mock_is_bare.assert_called_once_with(test_path)
        mock_get_repo_root.assert_called_once_with(test_path)
        
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('sys.exit')
    def test_get_basedir_git_command_error_no_path(self, mock_exit, mock_is_bare):
        """Test get_basedir_git when GitCommandError is raised without path."""
        mock_is_bare.side_effect = GitCommandError("Not a git repository")
        
        basedir.get_basedir_git()
        
        mock_exit.assert_called_once()
            
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('sys.exit')
    def test_get_basedir_git_command_error_with_path(self, mock_exit, mock_is_bare):
        """Test get_basedir_git when GitCommandError is raised with path."""
        test_path = '/some/test/path'
        mock_is_bare.side_effect = GitCommandError("Not a git repository")
        
        basedir.get_basedir_git(test_path)
        
        mock_exit.assert_called_once()
            
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('gitinspector.basedir.get_git_dir')
    def test_get_basedir_git_bare_repo_with_relative_path(self, mock_get_git_dir, mock_is_bare):
        """Test get_basedir_git for bare repository with relative git dir."""
        mock_is_bare.return_value = True
        # Mock a relative path that needs resolution
        mock_git_dir = MagicMock()
        mock_git_dir.resolve.return_value = Path('/resolved/path/to/repo.git')
        mock_get_git_dir.return_value = mock_git_dir
        
        result = basedir.get_basedir_git()
        
        self.assertEqual(result, '/resolved/path/to/repo.git')
        mock_git_dir.resolve.assert_called_once()
        
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('gitinspector.basedir.get_git_repository_root')
    def test_get_basedir_git_regular_repo_with_relative_path(self, mock_get_repo_root, mock_is_bare):
        """Test get_basedir_git for regular repository with relative root path."""
        mock_is_bare.return_value = False
        # Mock a relative path that needs resolution
        mock_repo_root = MagicMock()
        mock_repo_root.resolve.return_value = Path('/resolved/path/to/repo')
        mock_get_repo_root.return_value = mock_repo_root
        
        result = basedir.get_basedir_git()
        
        self.assertEqual(result, '/resolved/path/to/repo')
        mock_repo_root.resolve.assert_called_once()
        
    def test_get_basedir_git_returns_string(self):
        """Test that get_basedir_git returns a string."""
        with patch('gitinspector.basedir.is_bare_repository') as mock_is_bare, \
             patch('gitinspector.basedir.get_git_repository_root') as mock_get_repo_root:
            
            mock_is_bare.return_value = False
            mock_get_repo_root.return_value = Path('/test/path')
            
            result = basedir.get_basedir_git()
            self.assertIsInstance(result, str)
            
    def test_type_annotations(self):
        """Test that functions have proper type annotations."""
        import inspect
        
        # Test get_basedir function
        sig = inspect.signature(basedir.get_basedir)
        # In Python 3.11+, annotations show as 'str' not '<class 'str'>'
        self.assertIn('str', str(sig.return_annotation))
        
        # Test get_basedir_git function
        sig = inspect.signature(basedir.get_basedir_git)
        self.assertIn('str', str(sig.return_annotation))
        
        # Check parameter annotations
        params = sig.parameters
        self.assertIn('path', params)
        
    def test_docstrings_exist(self):
        """Test that functions have docstrings."""
        self.assertIsNotNone(basedir.get_basedir.__doc__)
        self.assertIsNotNone(basedir.get_basedir_git.__doc__)
        
        # Check that docstrings are meaningful
        self.assertIn('base directory', basedir.get_basedir.__doc__.lower())
        self.assertIn('git repository', basedir.get_basedir_git.__doc__.lower())
        
    @patch('gitinspector.basedir.is_bare_repository')
    @patch('sys.exit')
    def test_get_basedir_git_error_message_format(self, mock_exit, mock_is_bare):
        """Test that error messages are properly formatted."""
        test_error = "Custom git error message"
        mock_is_bare.side_effect = GitCommandError(test_error)
        
        basedir.get_basedir_git('/test/path')
        
        # Verify sys.exit was called
        mock_exit.assert_called_once()
        
        # Get the error message passed to sys.exit
        error_message = mock_exit.call_args[0][0]
        
        # Verify error message contains expected components
        self.assertIn('Error processing git repository', error_message)
        self.assertIn('/test/path', error_message)
        self.assertIn(test_error, error_message)


class TestBasedirIntegration(unittest.TestCase):
    """Integration tests for basedir module."""
    
    def test_get_basedir_integration(self):
        """Test get_basedir integration with real file system."""
        result = basedir.get_basedir()
        
        # Should be a valid path
        self.assertTrue(Path(result).exists())
        
        # Should be the gitinspector package directory
        self.assertTrue(Path(result).is_dir())
        
        # Should contain expected files
        expected_files = ['__init__.py', 'gitinspector.py']
        for expected_file in expected_files:
            self.assertTrue((Path(result) / expected_file).exists())
            
    def test_get_basedir_git_integration_current_repo(self):
        """Test get_basedir_git integration with current repository."""
        # This test assumes we're running in a git repository
        try:
            result = basedir.get_basedir_git()
            
            # Should be a valid path
            self.assertTrue(Path(result).exists())
            self.assertTrue(Path(result).is_dir())
            
            # Should be a git repository (contains .git)
            git_dir = Path(result) / '.git'
            self.assertTrue(git_dir.exists() or 
                          any(p.name == '.git' for p in Path(result).parents))
            
        except SystemExit:
            # If not in a git repository, that's also a valid test result
            self.skipTest("Not running in a git repository")


if __name__ == '__main__':
    unittest.main()
