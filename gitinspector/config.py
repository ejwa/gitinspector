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
import optval
import os
import subprocess

def __read_git_config__(repo, variable):
	previous_directory = os.getcwd()
	os.chdir(repo)
	setting = subprocess.Popen(["git", "config", "inspector." + variable], bufsize=1, stdout=subprocess.PIPE).stdout
	os.chdir(previous_directory)

	try:
		setting = setting.readlines()[0]
		setting = setting.decode("utf-8", "replace").strip()
	except IndexError:
		setting = ""

	return setting

def __read_git_config_bool__(repo, variable):
	try:
		variable = __read_git_config__(repo, variable)
		return optval.get_boolean_argument(False if variable == "" else variable)
	except optval.InvalidOptionArgument:
		return False

def __read_git_config_string__(repo, variable):
	string = __read_git_config__(repo, variable)
	return (True, string) if len(string) > 0 else (False, None)

def init(run):
	var = __read_git_config_string__(run.repo, "file-types")
	if var[0]:
		extensions.define(var[1])

	var = __read_git_config_string__(run.repo, "exclude")
	if var[0]:
		filtering.add(var[1])

	var = __read_git_config_string__(run.repo, "format")
	if var[0] and not format.select(var[1]):
		raise format.InvalidFormatError(_("specified output format not supported."))

	run.hard = __read_git_config_bool__(run.repo, "hard")
	run.list_file_types = __read_git_config_bool__(run.repo, "list-file-types")
	run.localize_output = __read_git_config_bool__(run.repo, "localize-output")
	run.metrics = __read_git_config_bool__(run.repo, "metrics")
	run.responsibilities = __read_git_config_bool__(run.repo, "responsibilities")
	run.useweeks = __read_git_config_bool__(run.repo, "weeks")

	var = __read_git_config_string__(run.repo, "since")
	if var[0]:
		interval.set_since(var[1])

	var = __read_git_config_string__(run.repo, "until")
	if var[0]:
		interval.set_until(var[1])

	run.timeline = __read_git_config_bool__(run.repo, "timeline")

	if __read_git_config_bool__(run.repo, "grading"):
		run.hard = True
		run.list_file_types = True
		run.metrics = True
		run.responsibilities = True
		run.timeline = True
		run.useweeks = True
