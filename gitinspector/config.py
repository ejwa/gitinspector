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
import extensions
import filtering
import format
import interval
import missing
import os
import subprocess

def __read_git_config__(repo, variable, default_value):
	previous_directory = os.getcwd()
	os.chdir(repo)
	setting = subprocess.Popen("git config inspector." + variable, shell=True, bufsize=1,
	                           stdout=subprocess.PIPE).stdout
	os.chdir(previous_directory)

	try:
		setting = setting.readlines()[0]
		setting = setting.decode("utf-8", "replace").strip()

		if default_value == True or default_value == False:
			if setting == "True" or setting == "true" or setting == "1":
				return True
			elif setting == "False" or setting == "false" or setting == "0":
				return False

			return False
		elif setting == "":
			return default_value

		return setting

	except IndexError:
		return default_value

def init(run):
	missing.set_checkout_missing(__read_git_config__(run.repo, "checkout-missing", False))
	extensions.define(__read_git_config__(run.repo, "file-types", ",".join(extensions.get())))

	exclude = __read_git_config__(run.repo, "exclude", None)
	if exclude != None:
		filtering.add(exclude)

	output_format = __read_git_config__(run.repo, "format", None)
	if output_format != None:
		if not format.select(output_format):
			raise format.InvalidFormatError(_("specified output format not supported."))

	run.hard = __read_git_config__(run.repo, "hard", False)
	run.list_file_types = __read_git_config__(run.repo, "list-file-types", False)
	run.include_metrics = __read_git_config__(run.repo, "metrics", False)
	run.responsibilities = __read_git_config__(run.repo, "responsibilities", False)
	run.useweeks = __read_git_config__(run.repo, "weeks", False)

	since =  __read_git_config__(run.repo, "since", None)
	if since != None:
		interval.set_since(since)

	until = __read_git_config__(run.repo, "until", None)
	if until != None:
		interval.set_until(until)

	run.timeline = __read_git_config__(run.repo, "timeline", False)

	if __read_git_config__(run.repo, "grading", False):
		run.include_metrics = True
		run.list_file_types = True
		run.responsibilities = True
		run.grading = True
		run.hard = True
		run.timeline = True
		run.useweeks = True
