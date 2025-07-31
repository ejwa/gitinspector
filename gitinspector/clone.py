# coding: utf-8
#
# Copyright © 2014 Ejwa Software. All rights reserved.
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

import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from .git_utils import run_git_command, GitCommandError, GitNotFoundError

__cloned_paths__: List[Path] = []


class Repository:
	"""Represents a git repository with name and location."""

	def __init__(self, name: Optional[str], location: str) -> None:
		self.name = name
		self.location = location


def create(url: str) -> Repository:
	"""
	Create a Repository object, cloning remote URLs or using local paths.

	Args:
		url: URL or path to the repository

	Returns:
		Repository: Repository object with name and location

	Raises:
		SystemExit: If git clone fails
		GitNotFoundError: If git command is not found
	"""
	parsed_url = urlparse(url)

	# Check if this is a remote URL that needs cloning
	if parsed_url.scheme in ("file", "git", "http", "https", "ssh"):
		try:
			# Create temporary directory for cloning
			temp_dir = Path(tempfile.mkdtemp(suffix=".gitinspector"))

			# Clone the repository using our improved git command detection
			run_git_command(
				["clone", url, str(temp_dir)],
				capture_output=False,  # Let git output go to stderr
				check=True
			)

			__cloned_paths__.append(temp_dir)
			return Repository(Path(parsed_url.path).name, str(temp_dir))

		except (GitCommandError, GitNotFoundError) as e:
			print(f"Error cloning repository: {e}", file=sys.stderr)
			sys.exit(1)

	# For local paths, just return as-is
	local_path = Path(url).resolve()
	return Repository(None, str(local_path))


def delete() -> None:
	"""
	Clean up all cloned repositories by removing their temporary directories.
	"""
	for path in __cloned_paths__:
		if path.exists():
			shutil.rmtree(path, ignore_errors=True)
	__cloned_paths__.clear()
