"""Git utility functions with improved command detection and path handling."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union


class GitCommandError(Exception):
    """Raised when git command execution fails."""
    pass


class GitNotFoundError(Exception):
    """Raised when git command cannot be found in PATH."""
    pass


def find_git_command() -> str:
    """
    Find the git command in the system PATH.
    
    Returns:
        str: Path to the git executable
        
    Raises:
        GitNotFoundError: If git command cannot be found
    """
    git_cmd = shutil.which("git")
    if git_cmd is None:
        # Try common locations as fallback
        common_paths = [
            "/usr/bin/git",
            "/usr/local/bin/git",
            "/opt/homebrew/bin/git",  # macOS Homebrew on Apple Silicon
            "/opt/local/bin/git",     # macOS MacPorts
        ]
        
        for path in common_paths:
            if Path(path).exists():
                git_cmd = path
                break
        
        if git_cmd is None:
            raise GitNotFoundError(
                "Git command not found in PATH. Please install Git or ensure it's in your PATH."
            )
    
    return git_cmd


def run_git_command(
    args: List[str],
    cwd: Optional[Union[str, Path]] = None,
    capture_output: bool = True,
    check: bool = True,
    input_data: Optional[str] = None,
) -> subprocess.CompletedProcess[bytes]:
    """
    Run a git command with improved error handling.
    
    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit code
        input_data: Optional input data to pass to the command
        
    Returns:
        subprocess.CompletedProcess: Result of the command execution
        
    Raises:
        GitNotFoundError: If git command cannot be found
        GitCommandError: If git command fails and check=True
    """
    git_cmd = find_git_command()
    full_cmd = [git_cmd] + args
    
    try:
        result = subprocess.run(
            full_cmd,
            cwd=cwd,
            capture_output=capture_output,
            check=False,  # We'll handle checking ourselves
            input=input_data.encode() if input_data else None,
        )
        
        if check and result.returncode != 0:
            error_msg = f"Git command failed: {' '.join(full_cmd)}"
            if result.stderr:
                error_msg += f"\nError: {result.stderr.decode('utf-8', errors='replace')}"
            raise GitCommandError(error_msg)
        
        return result
        
    except FileNotFoundError as e:
        raise GitNotFoundError(f"Failed to execute git command: {e}")


def get_git_repository_root(path: Optional[Union[str, Path]] = None) -> Path:
    """
    Get the root directory of a git repository.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        Path: Root directory of the git repository
        
    Raises:
        GitCommandError: If not in a git repository or command fails
    """
    try:
        result = run_git_command(
            ["rev-parse", "--show-toplevel"],
            cwd=path,
        )
        return Path(result.stdout.decode('utf-8').strip())
    except GitCommandError:
        raise GitCommandError("Not in a git repository or git repository root not found")


def is_git_repository(path: Optional[Union[str, Path]] = None) -> bool:
    """
    Check if a directory is a git repository.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        bool: True if the path is a git repository
    """
    try:
        run_git_command(["rev-parse", "--git-dir"], cwd=path)
        return True
    except (GitCommandError, GitNotFoundError):
        return False


def is_bare_repository(path: Optional[Union[str, Path]] = None) -> bool:
    """
    Check if a git repository is bare.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        bool: True if the repository is bare
        
    Raises:
        GitCommandError: If not in a git repository
    """
    try:
        result = run_git_command(
            ["rev-parse", "--is-bare-repository"],
            cwd=path,
        )
        return result.stdout.decode('utf-8').strip().lower() == "true"
    except GitCommandError:
        raise GitCommandError("Not in a git repository")


def get_git_dir(path: Optional[Union[str, Path]] = None) -> Path:
    """
    Get the .git directory path.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        Path: Path to the .git directory
        
    Raises:
        GitCommandError: If not in a git repository
    """
    try:
        result = run_git_command(
            ["rev-parse", "--git-dir"],
            cwd=path,
        )
        git_dir = result.stdout.decode('utf-8').strip()
        return Path(git_dir) if Path(git_dir).is_absolute() else Path(path or ".") / git_dir
    except GitCommandError:
        raise GitCommandError("Not in a git repository")
