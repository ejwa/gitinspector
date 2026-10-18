# coding: utf-8
#
# Copyright © 2014-2026 Ejwa Hosting AB. All rights reserved.
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

from __future__ import unicode_literals
import os
import shutil
import subprocess
import sys
import tempfile

try:
	from urllib.parse import urlparse
except:
	from urlparse import urlparse

__cloned_paths__ = []

#A colon in the host, a drive letter or a path that really exists is part of the repository, not a branch.
def split_branch(argument):
	scheme_end = argument.find("://")
	path_start = 0 if scheme_end < 0 else argument.find("/", scheme_end + 3) + 1 or len(argument)
	separator = argument.rfind(":", path_start)
	branch = argument[separator + 1:]

	if separator < 1 or not branch or branch[0] in "/\\" or os.path.exists(argument):
		return (argument, None)

	return (argument[:separator], branch)

def create(url, ref=None):
	class Repository(object):
		def __init__(self, name, location):
			self.name = name
			self.location = location
			self.branch = None
			self.ref = ref

	parsed_url = urlparse(url)

	if parsed_url.scheme == "file" or parsed_url.scheme == "git" or parsed_url.scheme == "http" or \
	   parsed_url.scheme == "https" or parsed_url.scheme == "ssh":
		path = tempfile.mkdtemp(suffix=".gitinspector")
		git_clone = subprocess.Popen(["git", "clone"] + (["--branch", ref] if ref else []) + [url, path], stdout=sys.stderr)
		git_clone.wait()

		if git_clone.returncode != 0:
			sys.exit(git_clone.returncode)

		__cloned_paths__.append(path)
		return Repository(os.path.basename(parsed_url.path), path)

	return Repository(None, os.path.abspath(url))

def delete():
	for path in __cloned_paths__:
		shutil.rmtree(path, ignore_errors=True)
