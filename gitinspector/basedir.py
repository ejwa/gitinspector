# coding: utf-8
#
# Copyright © 2012-2015 Ejwa Software. All rights reserved.
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

import os
import subprocess
import sys

def get_basedir():
	if hasattr(sys, "frozen"): # exists when running via py2exe
		return sys.prefix
	else:
		return os.path.dirname(os.path.realpath(__file__))

def get_basedir_git(path=None):
	previous_directory = None

	if path != None:
		previous_directory = os.getcwd()
		os.chdir(path)

	bare_command = subprocess.Popen(["git", "rev-parse", "--is-bare-repository"], bufsize=1,
	                          stdout=subprocess.PIPE, stderr=open(os.devnull, "w"))

	isbare = bare_command.stdout.readlines()
	bare_command.wait()

	if bare_command.returncode != 0:
		sys.exit(_("Error processing git repository at \"%s\"." % os.getcwd()))

	isbare = (isbare[0].decode("utf-8", "replace").strip() == "true")
	absolute_path = None

	if isbare:
		absolute_path = subprocess.Popen(["git", "rev-parse", "--git-dir"], bufsize=1, stdout=subprocess.PIPE).stdout
	else:
		absolute_path = subprocess.Popen(["git", "rev-parse", "--show-toplevel"], bufsize=1,
		                                 stdout=subprocess.PIPE).stdout

	absolute_path = absolute_path.readlines()

	if len(absolute_path) == 0:
		sys.exit(_("Unable to determine absolute path of git repository."))

	if path != None:
		os.chdir(previous_directory)

	return absolute_path[0].decode("utf-8", "replace").strip()
