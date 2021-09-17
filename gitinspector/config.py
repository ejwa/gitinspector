# coding: utf-8
#
# Copyright © 2013-2015 Ejwa Software. All rights reserved.
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
from . import extensions, filtering, format, interval, optval

class GitConfig(object):
	def __init__(self, run, repo, global_only=False):
		self.run = run
		self.repo = repo
		self.global_only = global_only

	def __read_git_config__(self, variable):
		previous_directory = os.getcwd()
		os.chdir(self.repo)
		setting = subprocess.Popen(filter(None, ["git", "config", "--global" if self.global_only else "",
		                           "inspector." + variable]), bufsize=1, stdout=subprocess.PIPE).stdout
		os.chdir(previous_directory)

		try:
			setting = setting.readlines()[0]
			setting = setting.decode("utf-8", "replace").strip()
		except IndexError:
			setting = ""

		return setting

	def __read_git_config_bool__(self, variable):
		try:
			variable = self.__read_git_config__(variable)
			return optval.get_boolean_argument(False if variable == "" else variable)
		except optval.InvalidOptionArgument:
			return False

	def __read_git_config_string__(self, variable):
		string = self.__read_git_config__(variable)
		return (True, string) if len(string) > 0 else (False, None)

	def read(self):
		var = self.__read_git_config_string__("file-types")
		if var[0]:
			extensions.define(var[1])

		var = self.__read_git_config_string__("exclude")
		if var[0]:
			filtering.add(var[1])

		var = self.__read_git_config_string__("format")
		if var[0] and not format.select(var[1]):
			raise format.InvalidFormatError(_("specified output format not supported."))

		self.run.hard = self.__read_git_config_bool__("hard")
		self.run.list_file_types = self.__read_git_config_bool__("list-file-types")
		self.run.localize_output = self.__read_git_config_bool__("localize-output")
		self.run.metrics = self.__read_git_config_bool__("metrics")
		self.run.responsibilities = self.__read_git_config_bool__("responsibilities")
		self.run.useweeks = self.__read_git_config_bool__("weeks")

		var = self.__read_git_config_string__("since")
		if var[0]:
			interval.set_since(var[1])

		var = self.__read_git_config_string__("until")
		if var[0]:
			interval.set_until(var[1])

		self.run.timeline = self.__read_git_config_bool__("timeline")

		if self.__read_git_config_bool__("grading"):
			self.run.hard = True
			self.run.list_file_types = True
			self.run.metrics = True
			self.run.responsibilities = True
			self.run.timeline = True
			self.run.useweeks = True
