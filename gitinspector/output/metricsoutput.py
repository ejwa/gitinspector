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
from ..changes import FileDiff
from ..localization import N_
from ..metrics import (__metric_eloc__, METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD, METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD)
from .outputable import Outputable

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

class MetricsOutput(Outputable):
	def __init__(self, metrics):
		self.metrics = metrics
		Outputable.__init__(self)

	def output_text(self):
		if not self.metrics.eloc and not self.metrics.cyclomatic_complexity and not self.metrics.cyclomatic_complexity_density:
			print("\n" + _(METRICS_MISSING_INFO_TEXT) + ".")

		if self.metrics.eloc:
			print("\n" + _(ELOC_INFO_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in self.metrics.eloc.items()]), reverse=True):
				print(_("{0} ({1} estimated lines of code)").format(i[1], str(i[0])))

		if self.metrics.cyclomatic_complexity:
			print("\n" + _(CYCLOMATIC_COMPLEXITY_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity.items()]), reverse=True):
				print(_("{0} ({1} in cyclomatic complexity)").format(i[1], str(i[0])))

		if self.metrics.cyclomatic_complexity_density:
			print("\n" + _(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity_density.items()]), reverse=True):
				print(_("{0} ({1:.3f} in cyclomatic complexity density)").format(i[1], i[0]))

	def output_html(self):
		metrics_xml = "<div><div class=\"box\" id=\"metrics\">"

		if not self.metrics.eloc and not self.metrics.cyclomatic_complexity and not self.metrics.cyclomatic_complexity_density:
			metrics_xml += "<p>" + _(METRICS_MISSING_INFO_TEXT) + ".</p>"

		if self.metrics.eloc:
			metrics_xml += "<div><h4>" + _(ELOC_INFO_TEXT) + ".</h4>"
			for num, i in enumerate(sorted(set([(j, i) for (i, j) in self.metrics.eloc.items()]), reverse=True)):
				metrics_xml += "<div class=\"" + __get_metrics_score__(__metric_eloc__[FileDiff.get_extension(i[1])], i[0]) + \
				               (" odd\">" if num % 2 == 1 else "\">") + \
				               _("{0} ({1} estimated lines of code)").format(i[1], str(i[0])) + "</div>"
			metrics_xml += "</div>"

		if self.metrics.cyclomatic_complexity:
			metrics_xml += "<div><h4>" +  _(CYCLOMATIC_COMPLEXITY_TEXT) + "</h4>"
			for num, i in enumerate(sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity.items()]), reverse=True)):
				metrics_xml += "<div class=\"" + __get_metrics_score__(METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD, i[0]) + \
				               (" odd\">" if num % 2 == 1 else "\">") + \
				               _("{0} ({1} in cyclomatic complexity)").format(i[1], str(i[0])) + "</div>"
			metrics_xml += "</div>"

		if self.metrics.cyclomatic_complexity_density:
			metrics_xml += "<div><h4>" +  _(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT) + "</h4>"
			for num, i in enumerate(sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity_density.items()]), reverse=True)):
				metrics_xml += "<div class=\"" + __get_metrics_score__(METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD, i[0]) + \
				               (" odd\">" if num % 2 == 1 else "\">") + \
				               _("{0} ({1:.3f} in cyclomatic complexity density)").format(i[1], i[0]) + "</div>"
			metrics_xml += "</div>"

		metrics_xml += "</div></div>"
		print(metrics_xml)

	def output_json(self):
		if not self.metrics.eloc and not self.metrics.cyclomatic_complexity and not self.metrics.cyclomatic_complexity_density:
			print(",\n\t\t\"metrics\": {\n\t\t\t\"message\": \"" + _(METRICS_MISSING_INFO_TEXT) + "\"\n\t\t}", end="")
		else:
			eloc_json = ""

			if self.metrics.eloc:
				for i in sorted(set([(j, i) for (i, j) in self.metrics.eloc.items()]), reverse=True):
					eloc_json += "{\n\t\t\t\t\"type\": \"estimated-lines-of-code\",\n"
					eloc_json += "\t\t\t\t\"file_name\": \"" + i[1] + "\",\n"
					eloc_json += "\t\t\t\t\"value\": " + str(i[0]) + "\n"
					eloc_json += "\t\t\t},"
				else:
					if not self.metrics.cyclomatic_complexity:
						eloc_json = eloc_json[:-1]

			if self.metrics.cyclomatic_complexity:
				for i in sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity.items()]), reverse=True):
					eloc_json += "{\n\t\t\t\t\"type\": \"cyclomatic-complexity\",\n"
					eloc_json += "\t\t\t\t\"file_name\": \"" + i[1] + "\",\n"
					eloc_json += "\t\t\t\t\"value\": " + str(i[0]) + "\n"
					eloc_json += "\t\t\t},"
				else:
					if not self.metrics.cyclomatic_complexity_density:
						eloc_json = eloc_json[:-1]

			if self.metrics.cyclomatic_complexity_density:
				for i in sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity_density.items()]), reverse=True):
					eloc_json += "{\n\t\t\t\t\"type\": \"cyclomatic-complexity-density\",\n"
					eloc_json += "\t\t\t\t\"file_name\": \"" + i[1] + "\",\n"
					eloc_json += "\t\t\t\t\"value\": {0:.3f}\n".format(i[0])
					eloc_json += "\t\t\t},"
				else:
					eloc_json = eloc_json[:-1]

			print(",\n\t\t\"metrics\": {\n\t\t\t\"violations\": [\n\t\t\t" + eloc_json + "]\n\t\t}", end="")
	def output_xml(self):
		if not self.metrics.eloc and not self.metrics.cyclomatic_complexity and not self.metrics.cyclomatic_complexity_density:
			print("\t<metrics>\n\t\t<message>" + _(METRICS_MISSING_INFO_TEXT) + "</message>\n\t</metrics>")
		else:
			eloc_xml = ""

			if self.metrics.eloc:
				for i in sorted(set([(j, i) for (i, j) in self.metrics.eloc.items()]), reverse=True):
					eloc_xml += "\t\t\t<estimated-lines-of-code>\n"
					eloc_xml += "\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
					eloc_xml += "\t\t\t\t<value>" + str(i[0]) + "</value>\n"
					eloc_xml += "\t\t\t</estimated-lines-of-code>\n"

			if self.metrics.cyclomatic_complexity:
				for i in sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity.items()]), reverse=True):
					eloc_xml += "\t\t\t<cyclomatic-complexity>\n"
					eloc_xml += "\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
					eloc_xml += "\t\t\t\t<value>" + str(i[0]) + "</value>\n"
					eloc_xml += "\t\t\t</cyclomatic-complexity>\n"

			if self.metrics.cyclomatic_complexity_density:
				for i in sorted(set([(j, i) for (i, j) in self.metrics.cyclomatic_complexity_density.items()]), reverse=True):
					eloc_xml += "\t\t\t<cyclomatic-complexity-density>\n"
					eloc_xml += "\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
					eloc_xml += "\t\t\t\t<value>{0:.3f}</value>\n".format(i[0])
					eloc_xml += "\t\t\t</cyclomatic-complexity-density>\n"

			print("\t<metrics>\n\t\t<violations>\n" + eloc_xml + "\t\t</violations>\n\t</metrics>")
