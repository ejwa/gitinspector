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
import atexit
import getopt
import os
import sys
from .blame import Blame
from .changes import Changes
from .config import GitConfig
from .metrics import MetricsLogic
from . import (basedir, clone, extensions, filtering, format, help, interval,
               localization, optval, terminal, version)
from .output import outputable
from .output.blameoutput import BlameOutput
from .output.changesoutput import ChangesOutput
from .output.extensionsoutput import ExtensionsOutput
from .output.filteringoutput import FilteringOutput
from .output.metricsoutput import MetricsOutput
from .output.responsibilitiesoutput import ResponsibilitiesOutput
from .output.timelineoutput import TimelineOutput

localization.init()

class Runner(object):
	def __init__(self):
		self.hard = False
		self.include_metrics = False
		self.list_file_types = False
		self.localize_output = False
		self.responsibilities = False
		self.grading = False
		self.timeline = False
		self.useweeks = False

	def process(self, repos):
		localization.check_compatibility(version.__version__)

		if not self.localize_output:
			localization.disable()

		terminal.skip_escapes(not sys.stdout.isatty())
		terminal.set_stdout_encoding()
		previous_directory = os.getcwd()
		summed_blames = None
		summed_changes = None
		summed_metrics = None

		for repo in repos:
			os.chdir(repo.location)
			repo = repo if len(repos) > 1 else None
			changes = Changes(repo, self.hard)
			summed_blames = Blame(repo, self.hard, self.useweeks, changes) + summed_blames
			summed_changes = changes + summed_changes

			if self.include_metrics:
				summed_metrics = MetricsLogic() + summed_metrics

			if sys.stdout.isatty() and format.is_interactive_format():
				terminal.clear_row()
		else:
			os.chdir(previous_directory)

		format.output_header(repos)
		outputable.output(ChangesOutput(changes))

		if changes.get_commits():
			outputable.output(BlameOutput(summed_changes, summed_blames))

			if self.timeline:
				outputable.output(TimelineOutput(summed_changes, self.useweeks))

			if self.include_metrics:
				outputable.output(MetricsOutput(summed_metrics))

			if self.responsibilities:
				outputable.output(ResponsibilitiesOutput(summed_changes, summed_blames))

			outputable.output(FilteringOutput())

			if self.list_file_types:
				outputable.output(ExtensionsOutput())

		format.output_footer()
		os.chdir(previous_directory)

def __check_python_version__():
	if sys.version_info < (2, 6):
		python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])
		sys.exit(_("gitinspector requires at least Python 2.6 to run (version {0} was found).").format(python_version))

def __get_validated_git_repos__(repos_relative):
	if not repos_relative:
		repos_relative = "."

	repos = []

	#Try to clone the repos or return the same directory and bail out.
	for repo in repos_relative:
		cloned_repo = clone.create(repo)
		basedir_path = basedir.get_basedir_git(cloned_repo.location)

		if cloned_repo.name == None:
			cloned_repo.name = os.path.basename(basedir_path)

		repos.append(cloned_repo)

	return repos

def main():
	terminal.check_terminal_encoding()
	terminal.set_stdin_encoding()
	argv = terminal.convert_command_line_to_utf8()
	run = Runner()
	repos = []

	try:
		opts, args = optval.gnu_getopt(argv[1:], "f:F:hHlLmrTwx:", ["exclude=", "file-types=", "format=",
		                                         "hard:true", "help", "list-file-types:true", "localize-output:true",
		                                         "metrics:true", "responsibilities:true", "since=", "grading:true",
		                                         "timeline:true", "until=", "version", "weeks:true"])
		repos = __get_validated_git_repos__(set(args))

		#We need the repos above to be set before we read the git config.
		GitConfig(run, repos[-1].location).read()
		clear_x_on_next_pass = True

		for o, a in opts:
			if o in("-h", "--help"):
				help.output()
				sys.exit(0)
			elif o in("-f", "--file-types"):
				extensions.define(a)
			elif o in("-F", "--format"):
				if not format.select(a):
					raise format.InvalidFormatError(_("specified output format not supported."))
			elif o == "-H":
				run.hard = True
			elif o == "--hard":
				run.hard = optval.get_boolean_argument(a)
			elif o == "-l":
				run.list_file_types = True
			elif o == "--list-file-types":
				run.list_file_types = optval.get_boolean_argument(a)
			elif o == "-L":
				run.localize_output = True
			elif o == "--localize-output":
				run.localize_output = optval.get_boolean_argument(a)
			elif o == "-m":
				run.include_metrics = True
			elif o == "--metrics":
				run.include_metrics = optval.get_boolean_argument(a)
			elif o == "-r":
				run.responsibilities = True
			elif o == "--responsibilities":
				run.responsibilities = optval.get_boolean_argument(a)
			elif o == "--since":
				interval.set_since(a)
			elif o == "--version":
				version.output()
				sys.exit(0)
			elif o == "--grading":
				grading = optval.get_boolean_argument(a)
				run.include_metrics = grading
				run.list_file_types = grading
				run.responsibilities = grading
				run.grading = grading
				run.hard = grading
				run.timeline = grading
				run.useweeks = grading
			elif o == "-T":
				run.timeline = True
			elif o == "--timeline":
				run.timeline = optval.get_boolean_argument(a)
			elif o == "--until":
				interval.set_until(a)
			elif o == "-w":
				run.useweeks = True
			elif o == "--weeks":
				run.useweeks = optval.get_boolean_argument(a)
			elif o in("-x", "--exclude"):
				if clear_x_on_next_pass:
					clear_x_on_next_pass = False
					filtering.clear()
				filtering.add(a)

		__check_python_version__()
		run.process(repos)

	except (filtering.InvalidRegExpError, format.InvalidFormatError, optval.InvalidOptionArgument, getopt.error) as exception:
		print(sys.argv[0], "\b:", exception.msg, file=sys.stderr)
		print(_("Try `{0} --help' for more information.").format(sys.argv[0]), file=sys.stderr)
		sys.exit(2)

@atexit.register
def cleanup():
	clone.delete()

if __name__ == "__main__":
	main()
