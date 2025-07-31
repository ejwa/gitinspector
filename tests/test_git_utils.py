"""Comprehensive tests for git_utils module."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from gitinspector.git_utils import (
    find_git_command,
    run_git_command,
    get_git_repository_root,
    is_git_repository,
    is_bare_repository,
    get_git_dir,
    GitCommandError,
    GitNotFoundError,
)


class TestGitUtils(unittest.TestCase):
    """Test suite for git_utils module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('shutil.which')
    def test_find_git_command_success(self, mock_which):
        """Test successful git command detection."""
        mock_which.return_value = '/usr/bin/git'
        result = find_git_command()
        self.assertEqual(result, '/usr/bin/git')
        mock_which.assert_called_once_with('git')

    @patch('shutil.which')
    def test_find_git_command_fallback_success(self, mock_which):
        """Test git command detection with fallback paths."""
        mock_which.return_value = None
        
        # Mock Path.exists() to return True only for the first fallback path
        def mock_exists(self):
            return str(self) == '/usr/local/bin/git'
        
        with patch.object(Path, 'exists', mock_exists):
            result = find_git_command()
            # Should return the first fallback path that exists
            self.assertEqual(result, '/usr/local/bin/git')

    @patch('shutil.which')
    @patch('pathlib.Path.exists')
    def test_find_git_command_not_found(self, mock_exists, mock_which):
        """Test git command not found error."""
        mock_which.return_value = None
        mock_exists.return_value = False
        
        with self.assertRaises(GitNotFoundError) as cm:
            find_git_command()
        
        self.assertIn("Git command not found in PATH", str(cm.exception))

    @patch('gitinspector.git_utils.find_git_command')
    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run, mock_find_git):
        """Test successful git command execution."""
        mock_find_git.return_value = '/usr/bin/git'
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'test output'
        mock_result.stderr = b''
        mock_run.return_value = mock_result
        
        result = run_git_command(['status'])
        
        self.assertEqual(result, mock_result)
        mock_run.assert_called_once_with(
            ['/usr/bin/git', 'status'],
            cwd=None,
            capture_output=True,
            check=False,
            input=None
        )

    @patch('gitinspector.git_utils.find_git_command')
    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run, mock_find_git):
        """Test git command execution failure."""
        mock_find_git.return_value = '/usr/bin/git'
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b'error message'
        mock_run.return_value = mock_result
        
        with self.assertRaises(GitCommandError) as cm:
            run_git_command(['invalid-command'], check=True)
        
        self.assertIn("Git command failed", str(cm.exception))
        self.assertIn("error message", str(cm.exception))

    @patch('gitinspector.git_utils.find_git_command')
    def test_run_git_command_git_not_found(self, mock_find_git):
        """Test git command execution when git is not found."""
        mock_find_git.side_effect = GitNotFoundError("Git not found")
        
        with self.assertRaises(GitNotFoundError):
            run_git_command(['status'])

    @patch('gitinspector.git_utils.run_git_command')
    def test_get_git_repository_root_success(self, mock_run_git):
        """Test successful git repository root detection."""
        mock_result = MagicMock()
        mock_result.stdout = b'/path/to/repo\n'
        mock_run_git.return_value = mock_result
        
        result = get_git_repository_root()
        
        self.assertEqual(result, Path('/path/to/repo'))
        mock_run_git.assert_called_once_with(
            ['rev-parse', '--show-toplevel'],
            cwd=None
        )

    @patch('gitinspector.git_utils.run_git_command')
    def test_get_git_repository_root_failure(self, mock_run_git):
        """Test git repository root detection failure."""
        mock_run_git.side_effect = GitCommandError("Not a git repository")
        
        with self.assertRaises(GitCommandError) as cm:
            get_git_repository_root()
        
        self.assertIn("Not in a git repository", str(cm.exception))

    @patch('gitinspector.git_utils.run_git_command')
    def test_is_git_repository_true(self, mock_run_git):
        """Test git repository detection - positive case."""
        mock_result = MagicMock()
        mock_run_git.return_value = mock_result
        
        result = is_git_repository()
        
        self.assertTrue(result)
        mock_run_git.assert_called_once_with(['rev-parse', '--git-dir'], cwd=None)

    @patch('gitinspector.git_utils.run_git_command')
    def test_is_git_repository_false(self, mock_run_git):
        """Test git repository detection - negative case."""
        mock_run_git.side_effect = GitCommandError("Not a git repository")
        
        result = is_git_repository()
        
        self.assertFalse(result)

    @patch('gitinspector.git_utils.run_git_command')
    def test_is_git_repository_git_not_found(self, mock_run_git):
        """Test git repository detection when git command not found."""
        mock_run_git.side_effect = GitNotFoundError("Git not found")
        
        result = is_git_repository()
        
        self.assertFalse(result)

    @patch('gitinspector.git_utils.run_git_command')
    def test_is_bare_repository_true(self, mock_run_git):
        """Test bare repository detection - positive case."""
        mock_result = MagicMock()
        mock_result.stdout = b'true\n'
        mock_run_git.return_value = mock_result
        
        result = is_bare_repository()
        
        self.assertTrue(result)
        mock_run_git.assert_called_once_with(
            ['rev-parse', '--is-bare-repository'],
            cwd=None
        )

    @patch('gitinspector.git_utils.run_git_command')
    def test_is_bare_repository_false(self, mock_run_git):
        """Test bare repository detection - negative case."""
        mock_result = MagicMock()
        mock_result.stdout = b'false\n'
        mock_run_git.return_value = mock_result
        
        result = is_bare_repository()
        
        self.assertFalse(result)

    @patch('gitinspector.git_utils.run_git_command')
    def test_is_bare_repository_error(self, mock_run_git):
        """Test bare repository detection error."""
        mock_run_git.side_effect = GitCommandError("Not a git repository")
        
        with self.assertRaises(GitCommandError):
            is_bare_repository()

    @patch('gitinspector.git_utils.run_git_command')
    def test_get_git_dir_absolute_path(self, mock_run_git):
        """Test git directory detection - absolute path."""
        mock_result = MagicMock()
        mock_result.stdout = b'/path/to/repo/.git\n'
        mock_run_git.return_value = mock_result
        
        result = get_git_dir()
        
        self.assertEqual(result, Path('/path/to/repo/.git'))

    @patch('gitinspector.git_utils.run_git_command')
    def test_get_git_dir_relative_path(self, mock_run_git):
        """Test git directory detection - relative path."""
        mock_result = MagicMock()
        mock_result.stdout = b'.git\n'
        mock_run_git.return_value = mock_result
        
        result = get_git_dir('/some/path')
        
        self.assertEqual(result, Path('/some/path/.git'))

    @patch('gitinspector.git_utils.run_git_command')
    def test_get_git_dir_error(self, mock_run_git):
        """Test git directory detection error."""
        mock_run_git.side_effect = GitCommandError("Not a git repository")
        
        with self.assertRaises(GitCommandError):
            get_git_dir()

    def test_run_git_command_with_input(self):
        """Test git command execution with input data."""
        with patch('gitinspector.git_utils.find_git_command') as mock_find_git, \
             patch('subprocess.run') as mock_run:
            
            mock_find_git.return_value = '/usr/bin/git'
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            run_git_command(['apply'], input_data='patch content')
            
            mock_run.assert_called_once_with(
                ['/usr/bin/git', 'apply'],
                cwd=None,
                capture_output=True,
                check=False,
                input=b'patch content'
            )

    def test_run_git_command_with_cwd(self):
        """Test git command execution with working directory."""
        with patch('gitinspector.git_utils.find_git_command') as mock_find_git, \
             patch('subprocess.run') as mock_run:
            
            mock_find_git.return_value = '/usr/bin/git'
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            run_git_command(['status'], cwd='/some/path')
            
            mock_run.assert_called_once_with(
                ['/usr/bin/git', 'status'],
                cwd='/some/path',
                capture_output=True,
                check=False,
                input=None
            )

    def test_run_git_command_no_capture_output(self):
        """Test git command execution without capturing output."""
        with patch('gitinspector.git_utils.find_git_command') as mock_find_git, \
             patch('subprocess.run') as mock_run:
            
            mock_find_git.return_value = '/usr/bin/git'
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            run_git_command(['status'], capture_output=False)
            
            mock_run.assert_called_once_with(
                ['/usr/bin/git', 'status'],
                cwd=None,
                capture_output=False,
                check=False,
                input=None
            )


class TestGitUtilsIntegration(unittest.TestCase):
    """Integration tests for git_utils module (requires git to be installed)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @unittest.skipIf(shutil.which('git') is None, "git command not available")
    def test_find_git_command_real(self):
        """Test finding real git command."""
        git_path = find_git_command()
        self.assertTrue(Path(git_path).exists())
        self.assertTrue(Path(git_path).is_file())

    @unittest.skipIf(shutil.which('git') is None, "git command not available")
    def test_is_git_repository_real_non_repo(self):
        """Test git repository detection on non-repository directory."""
        os.chdir(self.temp_dir)
        result = is_git_repository()
        self.assertFalse(result)

    @unittest.skipIf(shutil.which('git') is None, "git command not available")
    def test_git_repository_operations_real(self):
        """Test git repository operations on a real repository."""
        os.chdir(self.temp_dir)
        
        # Initialize a git repository
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        
        # Test repository detection
        self.assertTrue(is_git_repository())
        self.assertFalse(is_bare_repository())
        
        # Test getting repository root - resolve both paths for comparison
        repo_root = get_git_repository_root()
        self.assertEqual(repo_root.resolve(), self.temp_dir.resolve())
        
        # Test getting git directory
        git_dir = get_git_dir()
        self.assertTrue(git_dir.exists())
        self.assertTrue((git_dir / 'HEAD').exists())


if __name__ == '__main__':
    unittest.main()
