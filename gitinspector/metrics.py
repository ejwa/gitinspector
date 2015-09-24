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
from localization import N_
from outputable import Outputable
from changes import FileDiff
import comment
import filtering
import interval
import re
import subprocess

__metric_eloc__ = {"java": 500, "c": 500, "cpp": 500, "cs": 500, "h": 300, "hpp": 300, "php": 500, "py": 500, "glsl": 1000,
                   "rb": 500, "js": 500, "sql": 1000, "xml": 1000}

__metric_cc_tokens__ = [[["java", "js", "c", "cc", "cpp"], ["else", "for\s+\(.*\)", "if\s+\(.*\)", "case\s+\w+:",
                                                            "default:", "while\s+\(.*\)"],
                                                           ["assert", "break", "continue", "return"]],
                       [["cs"], ["else", "for\s+\(.*\)", "foreach\s+\(.*\)", "goto\s+\w+:", "if\s+\(.*\)", "case\s+\w+:",
                                 "default:", "while\s+\(.*\)"],
                                ["assert", "break", "continue", "return"]],
                       [["py"], ["^\s+elif .*:$", "^\s+else:$", "^\s+for .*:", "^\s+if .*:$", "^\s+while .*:$"],
                                ["^\s+assert", "break", "continue", "return"]]]

METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD = 50
METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD = 0.75

class MetricsLogic:
	def __init__(self):
		self.eloc = {}
		self.cyclomatic_complexity = {}
		self.cyclomatic_complexity_density = {}

		ls_tree_r = subprocess.Popen(["git", "ls-tree", "--name-only", "-r", interval.get_ref()], bufsize=1,
		                             stdout=subprocess.PIPE).stdout

		for i in ls_tree_r.readlines():
			i = i.strip().decode("unicode_escape", "ignore")
			i = i.encode("latin-1", "replace")
			i = i.decode("utf-8", "replace").strip("\"").strip("'").strip()

			if FileDiff.is_valid_extension(i) and not filtering.set_filtered(FileDiff.get_filename(i)):
				file_r = subprocess.Popen(["git", "show", interval.get_ref() + ":{0}".format(i.strip())],
				                          bufsize=1, stdout=subprocess.PIPE).stdout.readlines()

				extension = FileDiff.get_extension(i)
				lines = MetricsLogic.get_eloc(file_r, extension)
				cycc = MetricsLogic.get_cyclomatic_complexity(file_r, extension)

				if __metric_eloc__.get(extension, None) != None and __metric_eloc__[extension] < lines:
					self.eloc[i.strip()] = lines

				if METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD < cycc:
					self.cyclomatic_complexity[i.strip()] = cycc

				if lines > 0 and METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD < cycc / float(lines):
					self.cyclomatic_complexity_density[i.strip()] = cycc / float(lines)

	@staticmethod
	def get_cyclomatic_complexity(file_r, extension):
		is_inside_comment = False
		cc_counter = 0

		entry_tokens = None
		exit_tokens = None

		for i in __metric_cc_tokens__:
			if extension in i[0]:
				entry_tokens = i[1]
				exit_tokens = i[2]

		if entry_tokens or exit_tokens:
			for i in file_r:
				i = i.decode("utf-8", "replace")
				(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, i)

				if not is_inside_comment and not comment.is_comment(extension, i):
					for j in entry_tokens:
						if re.search(j, i, re.DOTALL):
							cc_counter += 2
					for j in exit_tokens:
						if re.search(j, i, re.DOTALL):
							cc_counter += 1
			return cc_counter

		return -1

	@staticmethod
	def get_eloc(file_r, extension):
		is_inside_comment = False
		eloc_counter = 0

		for i in file_r:
			i = i.decode("utf-8", "replace")
			(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, i)

			if not is_inside_comment and not comment.is_comment(extension, i):
				eloc_counter += 1

		return eloc_counter

ELOC_INFO_TEXT = N_("The following files are suspiciously big (in order of severity)")
CYCLOMATIC_COMPLEXITY_TEXT = N_("The following files have an elevated cyclomatic complexity (in order of severity)")
CYCLOMATIC_COMPLEXITY_DENSITY_TEXT = N_("The following files have an elevated cyclomatic complexity density " \
                                        "(in order of severity)")
METRICS_MISSING_INFO_TEXT = N_("No metrics violations were found in the repository")

METRICS_VIOLATION_SCORES = [[1.0, "minimal"], [1.25, "minor"], [1.5, "medium"], [2.0, "bad"], [3.0, "severe"]]

def __get_metrics_score__(ceiling, value):
	for i in reversed(METRICS_VIOLATION_SCORES):
		if value > ceiling * i[0]:
			return i[1]

class Metrics(Outputable):
	def output_text(self):
		metrics_logic = MetricsLogic()

		if not metrics_logic.eloc and not metrics_logic.cyclomatic_complexity and not metrics_logic.cyclomatic_complexity_density:
			print("\n" + _(METRICS_MISSING_INFO_TEXT) + ".")

		if metrics_logic.eloc:
			print("\n" + _(ELOC_INFO_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				print(_("{0} ({1} estimated lines of code)").format(i[1], str(i[0])))

		if metrics_logic.cyclomatic_complexity:
			print("\n" + _(CYCLOMATIC_COMPLEXITY_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.cyclomatic_complexity.items()]), reverse = True):
				print(_("{0} ({1} in cyclomatic complexity)").format(i[1], str(i[0])))

		if metrics_logic.cyclomatic_complexity_density:
			print("\n" + _(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.cyclomatic_complexity_density.items()]), reverse = True):
				print(_("{0} ({1:.3f} in cyclomatic complexity density)").format(i[1], i[0]))

	def output_html(self):
		metrics_logic = MetricsLogic()
		metrics_xml = "<div><div class=\"box\" id=\"metrics\">"

		if not metrics_logic.eloc and not metrics_logic.cyclomatic_complexity and not metrics_logic.cyclomatic_complexity_density:
			metrics_xml += "<p>" + _(METRICS_MISSING_INFO_TEXT) + ".</p>"

		if metrics_logic.eloc:
			metrics_xml += "<div><h4>" + _(ELOC_INFO_TEXT) + ".</h4>"
			for num, i in enumerate(sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True)):
				metrics_xml += "<div class=\"" + __get_metrics_score__(__metric_eloc__[FileDiff.get_extension(i[1])], i[0]) + \
				               (" odd\">" if num % 2 == 1 else "\">") + \
				               _("{0} ({1} estimated lines of code)").format(i[1], str(i[0])) + "</div>"
			metrics_xml += "</div>"

		if metrics_logic.cyclomatic_complexity:
			metrics_xml += "<div><h4>" +  _(CYCLOMATIC_COMPLEXITY_TEXT) + "</h4>"
			for num, i in enumerate(sorted(set([(j, i) for (i, j) in metrics_logic.cyclomatic_complexity.items()]), reverse = True)):
				metrics_xml += "<div class=\"" + __get_metrics_score__(METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD, i[0]) + \
				               (" odd\">" if num % 2 == 1 else "\">") + \
				               _("{0} ({1} in cyclomatic complexity)").format(i[1], str(i[0])) + "</div>"
			metrics_xml += "</div>"

		if metrics_logic.cyclomatic_complexity_density:
			metrics_xml += "<div><h4>" +  _(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT) + "</h4>"
			for num, i in enumerate(sorted(set([(j, i) for (i, j) in metrics_logic.cyclomatic_complexity_density.items()]), reverse = True)):
				metrics_xml += "<div class=\"" + __get_metrics_score__(METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD, i[0]) + \
				               (" odd\">" if num % 2 == 1 else "\">") + \
				               _("{0} ({1:.3f} in cyclomatic complexity density)").format(i[1], i[0]) + "</div>"
			metrics_xml += "</div>"

		metrics_xml += "</div></div>"
		print(metrics_xml)

	def output_xml(self):
		metrics_logic = MetricsLogic()

		if not metrics_logic.eloc and not metrics_logic.cyclomatic_complexity and not metrics_logic.cyclomatic_complexity_density:
			print("\t<metrics>\n\t\t<message>" + _(METRICS_MISSING_INFO_TEXT) + "</message>\n\t</metrics>")
		else:
			eloc_xml = ""

			if metrics_logic.eloc:
				for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
					eloc_xml += "\t\t\t<estimated-lines-of-code>\n"
					eloc_xml += "\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
					eloc_xml += "\t\t\t\t<value>" + str(i[0]) + "</value>\n"
					eloc_xml += "\t\t\t</estimated-lines-of-code>\n"

			if metrics_logic.cyclomatic_complexity:
				for i in sorted(set([(j, i) for (i, j) in metrics_logic.cyclomatic_complexity.items()]), reverse = True):
					eloc_xml += "\t\t\t<cyclomatic-complexity>\n"
					eloc_xml += "\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
					eloc_xml += "\t\t\t\t<value>" + str(i[0]) + "</value>\n"
					eloc_xml += "\t\t\t</cyclomatic-complexity>\n"

			if metrics_logic.cyclomatic_complexity_density:
				for i in sorted(set([(j, i) for (i, j) in metrics_logic.cyclomatic_complexity_density.items()]), reverse = True):
					eloc_xml += "\t\t\t<cyclomatic-complexity-density>\n"
					eloc_xml += "\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
					eloc_xml += "\t\t\t\t<value>{0:.3f}</value>\n".format(i[0])
					eloc_xml += "\t\t\t</cyclomatic-complexity-density>\n"

			print("\t<metrics>\n\t\t<violations>\n" + eloc_xml + "\t\t</violations>\n\t</metrics>")
