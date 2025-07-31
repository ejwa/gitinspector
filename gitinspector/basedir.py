# coding: utf-8
#
# Copyright 2012-2015 Ejwa Software. All rights reserved.
#
# This file is part of gitinspector.
#
# gitinspector is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gitinspector is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gitinspector. If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union
from .git_utils import GitCommandError, get_git_repository_root, is_bare_repository, get_git_dir


def get_basedir() -> str:
    """Get the base directory of the gitinspector package."""
    if hasattr(sys, "frozen"):  # exists when running via py2exe
        return sys.prefix
    else:
        return str(Path(__file__).parent.resolve())


def get_basedir_git(path: Optional[Union[str, Path]] = None) -> str:
    """
    Get the base directory of a git repository.

    Args:
        path: Optional path to check (defaults to current directory)

    Returns:
        str: Absolute path to the git repository base directory

    Raises:
        SystemExit: If not in a git repository or git command fails
    """
    try:
        if is_bare_repository(path):
            # For bare repositories, return the git directory path
            git_dir = get_git_dir(path)
            return str(git_dir.resolve())
        else:
            # For regular repositories, return the working tree root
            repo_root = get_git_repository_root(path)
            return str(repo_root.resolve())
    except GitCommandError as e:
        current_path = Path(path).resolve() if path else Path.cwd()
        sys.exit(f'Error processing git repository at "{current_path}": {e}')
