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
import subprocess

def __read_git_config__(variable, default_value):
	setting = subprocess.Popen("git config inspector." + variable, shell=True, bufsize=1,
	                           stdout=subprocess.PIPE).stdout
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
	missing.set_checkout_missing(__read_git_config__("checkout-missing", False))
	extensions.define(__read_git_config__("file-types", ",".join(extensions.get())))

	exclude = __read_git_config__("exclude", None):
	if exclude != None:
		filtering.add(exclude)

	if not __read_git_config__("format", format.get_selected()):
		raise format.InvalidFormatError(_("specified output format not supported."))

	run.hard = __read_git_config__("hard", False)
	run.list_file_types = __read_git_config__("list-file-types", False)
	run.include_metrics = __read_git_config__("metrics", False)
	run.responsibilities = __read_git_config__("responsibilities", False)
	run.useweeks = __read_git_config__("weeks", False)

	since =  __read_git_config__("since", None)
	if since != None:
		interval.set_since(since)

	until = __read_git_config__("until", None)
	if until != None:
		interval.set_until(until)

	run.timeline = __read_git_config__("timeline", False)

	if __read_git_config__("grading", False):
		run.include_metrics = True
		run.list_file_types = True
		run.responsibilities = True
		run.grading = True
		run.hard = True
		run.timeline = True
		run.useweeks = True
