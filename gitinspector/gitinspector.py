#!/usr/bin/env python
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

from __future__ import print_function
from __future__ import unicode_literals

import localization
localization.init()

import atexit
import basedir
import blame
import changes
import clone
import config
import extensions
import filtering
import format
import help
import interval
import getopt
import metrics
import os
import optval
import outputable
import responsibilities
import sys
import terminal
import timeline
import version

class Runner:
	def __init__(self):
		self.hard = False
		self.include_metrics = False
		self.list_file_types = False
		self.localize_output = False
		self.repo = "."
		self.responsibilities = False
		self.grading = False
		self.timeline = False
		self.useweeks = False

	def output(self):
		localization.check_compatibility(version.__version__)

		if not self.localize_output:
			localization.disable()

		terminal.skip_escapes(not sys.stdout.isatty())
		terminal.set_stdout_encoding()
		previous_directory = os.getcwd()

		os.chdir(self.repo)
		absolute_path = basedir.get_basedir_git()
		os.chdir(absolute_path)
		format.output_header()
		outputable.output(changes.ChangesOutput(self.hard))

		if changes.get(self.hard).get_commits():
			outputable.output(blame.BlameOutput(changes.get(self.hard), self.hard, self.useweeks))

			if self.timeline:
				outputable.output(timeline.Timeline(changes.get(self.hard), self.useweeks))

			if self.include_metrics:
				outputable.output(metrics.Metrics())

			if self.responsibilities:
				outputable.output(responsibilities.ResponsibilitiesOutput(self.hard, self.useweeks))

			outputable.output(filtering.Filtering())

			if self.list_file_types:
				outputable.output(extensions.Extensions())

		format.output_footer()
		os.chdir(previous_directory)

def __check_python_version__():
	if sys.version_info < (2, 6):
		python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])
		sys.exit(_("gitinspector requires at least Python 2.6 to run (version {0} was found).").format(python_version))

def main():
	terminal.check_terminal_encoding()
	terminal.set_stdin_encoding()
	argv = terminal.convert_command_line_to_utf8()
	__run__ = Runner()

	try:
		__opts__, __args__ = optval.gnu_getopt(argv[1:], "f:F:hHlLmrTwx:", ["exclude=", "file-types=", "format=",
		                                                 "hard:true", "help", "list-file-types:true",
		                                                 "localize-output:true", "metrics:true", "responsibilities:true",
		                                                 "since=", "grading:true", "timeline:true", "until=", "version",
		                                                 "weeks:true"])
		for arg in __args__:
			__run__.repo = arg

		#Try to clone the repo or return the same directory and bail out.
		__run__.repo = clone.create(__run__.repo)

		#We need the repo above to be set before we read the git config.
		config.init(__run__)
		clear_x_on_next_pass = True

		for o, a in __opts__:
			if o in("-h", "--help"):
				help.output()
				sys.exit(0)
			elif o in("-f", "--file-types"):
				extensions.define(a)
			elif o in("-F", "--format"):
				if not format.select(a):
					raise format.InvalidFormatError(_("specified output format not supported."))
			elif o == "-H":
				__run__.hard = True
			elif o == "--hard":
				__run__.hard = optval.get_boolean_argument(a)
			elif o == "-l":
				__run__.list_file_types = True
			elif o == "--list-file-types":
				__run__.list_file_types = optval.get_boolean_argument(a)
			elif o == "-L":
				__run__.localize_output = True
			elif o == "--localize-output":
				__run__.localize_output = optval.get_boolean_argument(a)
			elif o == "-m":
				__run__.include_metrics = True
			elif o == "--metrics":
				__run__.include_metrics = optval.get_boolean_argument(a)
			elif o == "-r":
				__run__.responsibilities = True
			elif o == "--responsibilities":
				__run__.responsibilities = optval.get_boolean_argument(a)
			elif o == "--since":
				interval.set_since(a)
			elif o == "--version":
				version.output()
				sys.exit(0)
			elif o == "--grading":
				grading = optval.get_boolean_argument(a)
				__run__.include_metrics = grading
				__run__.list_file_types = grading
				__run__.responsibilities = grading
				__run__.grading = grading
				__run__.hard = grading
				__run__.timeline = grading
				__run__.useweeks = grading
			elif o == "-T":
				__run__.timeline = True
			elif o == "--timeline":
				__run__.timeline = optval.get_boolean_argument(a)
			elif o == "--until":
				interval.set_until(a)
			elif o == "-w":
				__run__.useweeks = True
			elif o == "--weeks":
				__run__.useweeks = optval.get_boolean_argument(a)
			elif o in("-x", "--exclude"):
				if clear_x_on_next_pass:
					clear_x_on_next_pass = False
					filtering.clear()
				filtering.add(a)

		__check_python_version__()
		__run__.output()

	except (filtering.InvalidRegExpError, format.InvalidFormatError, optval.InvalidOptionArgument, getopt.error) as exception:
		print(sys.argv[0], "\b:", exception.msg, file=sys.stderr)
		print(_("Try `{0} --help' for more information.").format(sys.argv[0]), file=sys.stderr)
		sys.exit(2)

@atexit.register
def cleanup():
	clone.delete()

if __name__ == "__main__":
	main()
