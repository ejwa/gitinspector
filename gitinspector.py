#!/usr/bin/python
# coding: utf-8
#
# Copyright © 2012-2013 Ejwa Software. All rights reserved.
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
import blame
import changes
import extensions
import filtering
import format
import getopt
import help
import interval
import metrics
import missing
import os
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
		self.repo = "."
		self.responsibilities = False
		self.grading = False
		self.timeline = False
		self.useweeks = False

	def output(self):
		terminal.skip_escapes(not sys.stdout.isatty())
		terminal.set_stdout_encoding()
		previous_directory = os.getcwd()
		os.chdir(self.repo)
		format.output_header()
		outputable.output(changes.ChangesOutput(self.hard))

		if changes.get(self.hard).get_commits():
			outputable.output(blame.BlameOutput(self.hard))

			if self.timeline:
				outputable.output(timeline.Timeline(changes.get(self.hard), self.useweeks))

			if self.include_metrics:
				outputable.output(metrics.Metrics())

			if self.responsibilities:
				outputable.output(responsibilities.ResponsibilitiesOutput(self.hard))

			outputable.output(missing.Missing())
			outputable.output(filtering.Filtering())

			if self.list_file_types:
				outputable.output(extensions.Extensions())

		format.output_footer()
		os.chdir(previous_directory)

if __name__ == "__main__":
	__run__ = Runner()

	try:
		__opts__, __args__ = getopt.gnu_getopt(sys.argv[1:], "cf:F:hHlmrTwx:", ["checkout-missing", "exclude=",
		                                                     "file-types=", "format=", "hard", "help", "list-file-types",
		                                                     "metrics", "responsibilities", "since=", "grading",
		                                                     "timeline", "until=", "version"])
		for o, a in __opts__:
			if o in("-c", "--checkout-missing"):
				missing.set_checkout_missing(True)
			elif o in("-h", "--help"):
				help.output()
				sys.exit(0)
			elif o in("-f", "--file-types"):
				extensions.define(a)
			elif o in("-F", "--format"):
				if not format.select(a):
					raise format.InvalidFormatError("specified output format not supported.")
			elif o in("-H", "--hard"):
				__run__.hard = True
			elif o in("-l", "--list-file-types"):
				__run__.list_file_types = True
			elif o in("-m", "--metrics"):
				__run__.include_metrics = True
			elif o in("-r", "--responsibilities"):
				__run__.responsibilities = True
			elif o in("--since"):
				interval.set_since(a)
			elif o in("--version"):
				version.output()
				sys.exit(0)
			elif o in("--grading"):
				__run__.include_metrics = True
				__run__.list_file_types = True
				__run__.responsibilities = True
				__run__.grading = True
				__run__.hard = True
				__run__.timeline = True
				__run__.useweeks = True
			elif o in("-T", "--timeline"):
				__run__.timeline = True
			elif o in("--until"):
				interval.set_until(a)
			elif o in("-w"):
				__run__.useweeks = True
			elif o in("-x", "--exclude"):
				filtering.add(a)
		for arg in __args__:
			__run__.repo = arg

	except (format.InvalidFormatError, getopt.error) as msg:
		print(sys.argv[0], "\b:", msg)
		print("Try `", sys.argv[0], "--help' for more information.")
		sys.exit(2)

	__run__.output()
