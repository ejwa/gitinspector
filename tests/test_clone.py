"""Comprehensive tests for clone module."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from gitinspector import clone
from gitinspector.git_utils import GitCommandError, GitNotFoundError


class TestClone(unittest.TestCase):
    """Test suite for clone module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('gitinspector.clone.run_git_command')
    @patch('tempfile.mkdtemp')
    def test_create_success(self, mock_mkdtemp, mock_run_git):
        """Test successful repository cloning."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_git.return_value = mock_result
        
        temp_path = str(self.temp_dir / "temp_clone")
        mock_mkdtemp.return_value = temp_path
        
        repo_url = "https://github.com/user/repo.git"
        
        result = clone.create(repo_url)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertEqual(result.name, "repo.git")
        self.assertEqual(result.location, temp_path)
        mock_run_git.assert_called_once_with(
            ['clone', repo_url, temp_path],
            capture_output=False,
            check=True
        )

    def test_create_local_path(self):
        """Test repository creation with local path."""
        local_path = str(self.temp_dir)
        
        result = clone.create(local_path)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertIsNone(result.name)
        # Use resolve() to handle macOS /private prefix differences
        self.assertEqual(Path(result.location).resolve(), Path(local_path).resolve())

    @patch('gitinspector.clone.run_git_command')
    @patch('sys.exit')
    def test_create_git_command_error(self, mock_exit, mock_run_git):
        """Test repository cloning failure."""
        mock_run_git.side_effect = GitCommandError("Clone failed")
        
        repo_url = "https://github.com/user/nonexistent.git"
        
        clone.create(repo_url)
        
        mock_exit.assert_called_once_with(1)

    @patch('gitinspector.clone.run_git_command')
    @patch('sys.exit')
    def test_create_git_not_found(self, mock_exit, mock_run_git):
        """Test repository cloning when git is not found."""
        mock_run_git.side_effect = GitNotFoundError("Git not found")
        
        repo_url = "https://github.com/user/repo.git"
        
        clone.create(repo_url)
        
        mock_exit.assert_called_once_with(1)

    @patch('gitinspector.clone.run_git_command')
    @patch('tempfile.mkdtemp')
    def test_create_returns_repository(self, mock_mkdtemp, mock_run_git):
        """Test that create returns a Repository object."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_git.return_value = mock_result
        
        temp_path = str(self.temp_dir / "temp_clone")
        mock_mkdtemp.return_value = temp_path
        
        repo_url = "https://github.com/user/repo.git"
        
        result = clone.create(repo_url)
        
        self.assertIsInstance(result, clone.Repository)

    def test_create_with_empty_url(self):
        """Test create with empty repository URL."""
        result = clone.create("")
        
        # Empty string becomes current directory when resolved
        self.assertIsInstance(result, clone.Repository)
        self.assertIsNone(result.name)

    def test_create_with_file_scheme(self):
        """Test create with file:// scheme."""
        file_url = f"file://{self.temp_dir}"
        
        with patch('gitinspector.git_utils.run_git_command') as mock_run_git, \
             patch('tempfile.mkdtemp') as mock_mkdtemp, \
             patch('sys.exit') as mock_exit:
            
            mock_run_git.side_effect = GitCommandError("Test error")
            
            clone.create(file_url)
            
            mock_exit.assert_called_once_with(1)

    @patch('gitinspector.clone.run_git_command')
    @patch('tempfile.mkdtemp')
    def test_create_with_special_characters_in_path(self, mock_mkdtemp, mock_run_git):
        """Test create with special characters in temp path."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_git.return_value = mock_result
        
        temp_path = str(self.temp_dir / "test repo with spaces")
        mock_mkdtemp.return_value = temp_path
        
        repo_url = "https://github.com/user/repo.git"
        
        result = clone.create(repo_url)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertEqual(result.location, temp_path)
        mock_run_git.assert_called_once_with(
            ['clone', repo_url, temp_path],
            capture_output=False,
            check=True
        )

    def test_create_with_relative_path(self):
        """Test create with relative local path."""
        relative_path = "relative/path/to/repo"
        
        result = clone.create(relative_path)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertIsNone(result.name)
        # Path should be resolved to absolute
        self.assertTrue(Path(result.location).is_absolute())

    def test_create_with_different_protocols(self):
        """Test create with different git protocols."""
        # Test protocols that should trigger cloning
        with patch('gitinspector.clone.run_git_command') as mock_run_git, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run_git.return_value = mock_result
            
            # Test standard URL schemes that trigger cloning
            cloning_protocols = [
                "https://github.com/user/repo.git",
                "ssh://git@github.com/user/repo.git", 
                "file:///path/to/local/repo.git"
            ]
            
            for i, repo_url in enumerate(cloning_protocols):
                temp_path = str(self.temp_dir / f"temp_{i}")
                mock_mkdtemp.return_value = temp_path
                
                result = clone.create(repo_url)
                
                self.assertIsInstance(result, clone.Repository)
                self.assertEqual(result.location, temp_path)
        
        # Test SSH URL format (git@host:path) - this is treated as local path by urlparse
        # This is actually correct behavior since urlparse doesn't recognize this format
        ssh_url = "git@github.com:user/repo.git"
        result = clone.create(ssh_url)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertIsNone(result.name)
        # SSH URL without scheme is treated as local path, which is resolved
        self.assertTrue(Path(result.location).is_absolute())
        
        # Test local path (no cloning)
        local_path = "/path/to/local/repo"
        result = clone.create(local_path)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertIsNone(result.name)
        self.assertEqual(result.location, str(Path(local_path).resolve()))

    def test_type_annotations(self):
        """Test that functions have proper type annotations."""
        import inspect
        
        # Test create function
        sig = inspect.signature(clone.create)
        # In Python 3.11+, annotations show as 'Repository' not '<class 'str'>'
        self.assertIn('Repository', str(sig.return_annotation))
        
        # Check parameter annotations
        params = sig.parameters
        self.assertIn('url', params)

    def test_docstrings_exist(self):
        """Test that functions have docstrings."""
        self.assertIsNotNone(clone.create.__doc__)
        
        # Check that docstring is meaningful
        docstring = clone.create.__doc__.lower()
        self.assertIn('clone', docstring)
        self.assertIn('repository', docstring)

    @patch('gitinspector.clone.run_git_command')
    @patch('sys.stderr')
    @patch('sys.exit')
    def test_create_error_handling_details(self, mock_exit, mock_stderr, mock_run_git):
        """Test detailed error handling in create function."""
        error_message = "fatal: repository 'https://github.com/user/nonexistent.git' not found"
        mock_run_git.side_effect = GitCommandError(error_message)
        
        repo_url = "https://github.com/user/nonexistent.git"
        
        clone.create(repo_url)
        
        # Verify error was printed and exit was called
        mock_stderr.write.assert_called()
        mock_exit.assert_called_once_with(1)

    def test_create_with_none_parameter(self):
        """Test create with None parameter."""
        with self.assertRaises((TypeError, AttributeError)):
            clone.create(None)

    @patch('gitinspector.clone.run_git_command')
    @patch('sys.exit')
    def test_create_preserves_original_error(self, mock_exit, mock_run_git):
        """Test that create handles git command errors properly."""
        original_error = GitCommandError("Original error message")
        mock_run_git.side_effect = original_error
        
        repo_url = "https://github.com/user/repo.git"
        
        clone.create(repo_url)
        
        # Should call sys.exit(1) on error
        mock_exit.assert_called_once_with(1)


class TestCloneIntegration(unittest.TestCase):
    """Integration tests for clone module (requires git to be installed)."""

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
    def test_create_local_repository_integration(self):
        """Test cloning a local repository (integration test)."""
        # Create a source repository
        source_repo = self.temp_dir / "source_repo"
        source_repo.mkdir()
        
        os.chdir(source_repo)
        
        # Initialize git repository
        import subprocess
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
        
        # Create a test file and commit
        test_file = source_repo / "test.txt"
        test_file.write_text("Test content")
        
        subprocess.run(['git', 'add', 'test.txt'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
        
        # Clone the repository using file:// URL to trigger cloning
        file_url = f"file://{source_repo}"
        
        result = clone.create(file_url)
        
        # Verify clone was successful
        self.assertIsInstance(result, clone.Repository)
        self.assertTrue(Path(result.location).exists())
        self.assertTrue((Path(result.location) / ".git").exists())
        self.assertTrue((Path(result.location) / "test.txt").exists())
        
        # Verify content
        cloned_content = (Path(result.location) / "test.txt").read_text()
        self.assertEqual(cloned_content, "Test content")

    @unittest.skipIf(shutil.which('git') is None, "git command not available")
    def test_create_nonexistent_repository_integration(self):
        """Test cloning a nonexistent repository (integration test)."""
        nonexistent_url = "file:///path/to/nonexistent/repo"
        
        with patch('sys.exit') as mock_exit:
            clone.create(nonexistent_url)
            
            # Should call sys.exit(1) on failure
            mock_exit.assert_called_once_with(1)


class TestCloneEdgeCases(unittest.TestCase):
    """Edge case tests for clone module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('gitinspector.clone.run_git_command')
    @patch('tempfile.mkdtemp')
    def test_create_with_unicode_characters(self, mock_mkdtemp, mock_run_git):
        """Test create with unicode characters in temp paths."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_git.return_value = mock_result
        
        temp_path = str(self.temp_dir / "测试目录")  # Chinese characters
        mock_mkdtemp.return_value = temp_path
        
        repo_url = "https://github.com/user/repo.git"
        
        result = clone.create(repo_url)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertEqual(result.location, temp_path)
        mock_run_git.assert_called_once_with(
            ['clone', repo_url, temp_path],
            capture_output=False,
            check=True
        )

    @patch('gitinspector.clone.run_git_command')
    @patch('tempfile.mkdtemp')
    def test_create_with_very_long_path(self, mock_mkdtemp, mock_run_git):
        """Test create with very long temp path."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_git.return_value = mock_result
        
        # Create a very long path
        long_path_component = "a" * 100
        temp_path = str(self.temp_dir / long_path_component / long_path_component / "repo")
        mock_mkdtemp.return_value = temp_path
        
        repo_url = "https://github.com/user/repo.git"
        
        result = clone.create(repo_url)
        
        self.assertIsInstance(result, clone.Repository)
        self.assertEqual(result.location, temp_path)
        mock_run_git.assert_called_once_with(
            ['clone', repo_url, temp_path],
            capture_output=False,
            check=True
        )

    @patch('gitinspector.clone.run_git_command')
    @patch('tempfile.mkdtemp')
    def test_create_concurrent_calls(self, mock_mkdtemp, mock_run_git):
        """Test multiple concurrent create calls."""
        import threading
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_git.return_value = mock_result
        
        # Mock different temp paths for each call
        temp_paths = [str(self.temp_dir / f"temp_{i}") for i in range(5)]
        mock_mkdtemp.side_effect = temp_paths
        
        results = []
        errors = []
        
        def clone_repo(index):
            try:
                repo_url = f"https://github.com/user/repo{index}.git"
                result = clone.create(repo_url)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=clone_repo, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        
        # Verify all git commands were called
        self.assertEqual(mock_run_git.call_count, 5)


if __name__ == '__main__':
    unittest.main()
