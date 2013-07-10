# coding: utf-8
#
# Copyright © 2013 Ejwa Software. All rights reserved.
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
import subprocess

def __read_git_config__(run, variable, destination=None):
	if destination == None:
		destination = variable

	previous_directory = os.getcwd()
	os.chdir(run.repo)
	setting = subprocess.Popen("git config inspector." + variable, shell=True, bufsize=1,
	                           stdout=subprocess.PIPE).stdout
	os.chdir(previous_directory)

	try:
		setting = setting.readlines()[0]
		setting = setting.decode("utf-8", "replace").strip()

		if setting == "True" or setting == "true" or setting == "t" or setting == "1":
			vars(run.opts)[destination] = True
		elif setting == "False" or setting == "false" or setting == "f" or setting == "0":
			vars(run.opts)[destination] = False
		return True

	except IndexError:
		return False

def init(run):
	__read_git_config__(run, "checkout-missing", "checkout_missing")
	__read_git_config__(run, "file-types", "file_types")
	__read_git_config__(run, "exclude")
	__read_git_config__(run, "format")
	__read_git_config__(run, "hard")
	__read_git_config__(run, "list-file-types", "list_file_types")
	__read_git_config__(run, "metrics")
	__read_git_config__(run, "responsibilities")
	__read_git_config__(run, "weeks", "useweeks")
	__read_git_config__(run, "since")
	__read_git_config__(run, "until")
	__read_git_config__(run, "timeline")

	if __read_git_config__(run, "grading"):
		run.opts.hard = True
		run.opts.list_file_types = True
		run.opts.metrics = True
		run.opts.responsibilities = True
		run.opts.timeline = True
		run.opts.useweeks = True
