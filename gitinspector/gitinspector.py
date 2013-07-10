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
from __future__ import unicode_literals

import localization
localization.init()

import blame
import changes
import config
import extensions
import filtering
import format
import help
import interval
import metrics
import missing
import os
import optval
import outputable
import responsibilities
import sys
import terminal
import timeline
import version

class Runner:
	def __init__(self, opts):
		self.opts = opts
		self.repo = "."

	def output(self):
		terminal.skip_escapes(not sys.stdout.isatty())
		terminal.set_stdout_encoding()
		previous_directory = os.getcwd()
		os.chdir(self.repo)

		if not format.select(self.opts.format):
			raise format.InvalidFormatError(_("specified output format not supported."))

		if not self.opts.localize_output:
			localization.disable()

		missing.set_checkout_missing(self.opts.checkout_missing)
		extensions.define(self.opts.file_types)

		if self.opts.since != None:
			interval.set_since(self.opts.since)

		if self.opts.until != None:
			interval.set_until(self.opts.until)

		for ex in self.opts.exclude:
			filtering.add(ex)

		format.output_header()
		outputable.output(changes.ChangesOutput(self.opts.hard))

		if changes.get(self.opts.hard).get_commits():
			outputable.output(blame.BlameOutput(self.opts.hard))

			if self.opts.timeline:
				outputable.output(timeline.Timeline(changes.get(self.opts.hard), self.opts.useweeks))

			if self.opts.metrics:
				outputable.output(metrics.Metrics())

			if self.opts.responsibilities:
				outputable.output(responsibilities.ResponsibilitiesOutput(self.opts.hard))

			outputable.output(missing.Missing())
			outputable.output(filtering.Filtering())

			if self.opts.list_file_types:
				outputable.output(extensions.Extensions())

		format.output_footer()
		os.chdir(previous_directory)

def __check_python_version__():
	if sys.version_info < (2, 6):
		python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])
		sys.exit(_("gitinspector requires at leat Python 2.6 to run (version {0} was found).").format(python_version))

def __handle_help__(__option__, __opt_str__, __value__, __parser__):
	help.output()
	sys.exit(0)

def __handle_version__(__option__, __opt_str__, __value__, __parser__):
	version.output()
	sys.exit(0)

def main():
	parser = optval.OptionParser(add_help_option=False)

	try:
		parser.add_option("-c", action="store_true", dest="checkout_missing")
		parser.add_option("-H", action="store_true", dest="hard")
		parser.add_option("-l", action="store_true", dest="list_file_types")
		parser.add_option("-L", action="store_true", dest="localize_output")
		parser.add_option("-m", action="store_true", dest="metrics")
		parser.add_option("-r", action="store_true", dest="responsibilities")
		parser.add_option("-T", action="store_true", dest="timeline")
		parser.add_option("-w", action="store_true", dest="useweeks")

		optval.add_option(parser,       "--checkout-missing", boolean=True)
		parser.add_option(        "-f", "--file-types", type="string", default=",".join(extensions.DEFAULT_EXTENSIONS))
		parser.add_option(        "-F", "--format", type="string", default=format.DEFAULT_FORMAT)
		optval.add_option(parser,       "--grading", boolean=True, multidest=["hard", "metrics", "list_file_types",
		                                             "responsibilities", "timeline", "useweeks"])
		parser.add_option(        "-h", "--help", action="callback", callback=__handle_help__)
		optval.add_option(parser,       "--hard", boolean=True)
		optval.add_option(parser,       "--list-file-types", boolean=True)
		optval.add_option(parser,       "--localize-output", boolean=True)
		optval.add_option(parser,       "--metrics", boolean=True)
		optval.add_option(parser,       "--responsibilities", boolean=True)
		parser.add_option(              "--since", type="string")
		optval.add_option(parser,       "--timeline", boolean=True)
		parser.add_option(              "--until", type="string")
		parser.add_option(              "--version", action="callback", callback=__handle_version__)
		optval.add_option(parser,       "--weeks", boolean=True, dest="useweeks")
		parser.add_option(        "-x", "--exclude", action="append", type="string", default=[])

		(opts, args) = parser.parse_args()
		__run__ = Runner(opts)

		for arg in args:
			__run__.repo = arg

		#We need the repo above to be set before we read the git config.
		config.init(__run__)

		parser.parse_args(values=opts)

	except (format.InvalidFormatError, optval.InvalidOptionArgument, optval.OptionParsingError) as msg:
		localization.enable()

		print(sys.argv[0], "\b:", end=" ")
		print(msg)
		print(_("Try `{0} --help' for more information.").format(sys.argv[0]))
		sys.exit(2)

	__check_python_version__()
	__run__.output()

if __name__ == "__main__":
	main()
