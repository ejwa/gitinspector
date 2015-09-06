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

from __future__ import unicode_literals

import shutil
import subprocess
import sys
import tempfile

__cloned_path__ = None

def create(url):
	if url.startswith("file://") or url.startswith("git://") or url.startswith("http://") or \
	   url.startswith("https://") or url.startswith("ssh://"):
		global __cloned_path__

		location = tempfile.mkdtemp(suffix=".gitinspector")
		git_clone = subprocess.Popen(["git", "clone", url, location], bufsize=1, stdout=sys.stderr)
		git_clone.wait()

		if git_clone.returncode != 0:
			sys.exit(git_clone.returncode)

		__cloned_path__ = location
		return location
	return url

def delete():
	if __cloned_path__:
		shutil.rmtree(__cloned_path__, ignore_errors=True)
