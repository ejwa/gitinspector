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
from ..metrics import (__metric_eloc__, METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD, METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD,
                       METRIC_COGNITIVE_COMPLEXITY_THRESHOLD)
from .outputable import Outputable

ELOC_INFO_TEXT = N_("The following files are suspiciously big (in order of severity)")
CYCLOMATIC_COMPLEXITY_TEXT = N_("The following files have an elevated cyclomatic complexity (in order of severity)")
CYCLOMATIC_COMPLEXITY_DENSITY_TEXT = N_("The following files have an elevated cyclomatic complexity density " \
                                        "(in order of severity)")
COGNITIVE_COMPLEXITY_TEXT = N_("The following files have an elevated cognitive complexity (in order of severity)")
METRICS_MISSING_INFO_TEXT = N_("No metrics violations were found in the repository")

METRICS_VIOLATION_SCORES = [[1.0, "minimal"], [1.25, "minor"], [1.5, "medium"], [2.0, "bad"], [3.0, "severe"]]

def __get_metrics_score__(ceiling, value):
	for i in reversed(METRICS_VIOLATION_SCORES):
		if value > ceiling * i[0]:
			return i[1]

def __sorted_violations__(violations):
	return sorted(set([(value, name) for (name, value) in violations.items()]), reverse=True)

def __html_violation__(score, text):
	return "<li class=\"list-group-item violation-{0}\">{1}</li>".format(score, text)

def __json_violation__(kind, name, value):
	return ("{\n\t\t\t\t\"type\": \"" + kind + "\",\n\t\t\t\t\"file_name\": \"" + name + "\",\n" +
	        "\t\t\t\t\"value\": " + value + "\n\t\t\t}")

def __xml_violation__(kind, name, value):
	return ("\t\t\t<" + kind + ">\n\t\t\t\t<file-name>" + name + "</file-name>\n" +
	        "\t\t\t\t<value>" + value + "</value>\n\t\t\t</" + kind + ">\n")

class MetricsOutput(Outputable):
	def __init__(self, metrics):
		self.metrics = metrics
		Outputable.__init__(self)

	def has_violations(self):
		return bool(self.metrics.eloc or self.metrics.cyclomatic_complexity or
		            self.metrics.cyclomatic_complexity_density or self.metrics.cognitive_complexity)

	def output_text(self):
		if not self.has_violations():
			print("\n" + _(METRICS_MISSING_INFO_TEXT) + ".")

		if self.metrics.eloc:
			print("\n" + _(ELOC_INFO_TEXT) + ":")
			for (value, name) in __sorted_violations__(self.metrics.eloc):
				print(_("{0} ({1} estimated lines of code)").format(name, str(value)))

		if self.metrics.cyclomatic_complexity:
			print("\n" + _(CYCLOMATIC_COMPLEXITY_TEXT) + ":")
			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity):
				print(_("{0} ({1} in cyclomatic complexity)").format(name, str(value)))

		if self.metrics.cyclomatic_complexity_density:
			print("\n" + _(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT) + ":")
			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity_density):
				print(_("{0} ({1:.3f} in cyclomatic complexity density)").format(name, value))

		if self.metrics.cognitive_complexity:
			print("\n" + _(COGNITIVE_COMPLEXITY_TEXT) + ":")
			for (value, name) in __sorted_violations__(self.metrics.cognitive_complexity):
				print(_("{0} ({1} in cognitive complexity)").format(name, str(value)))

	def output_html(self):
		metrics_xml = "<div><div class=\"box\" id=\"metrics\">"

		if not self.has_violations():
			metrics_xml += "<h1>" + _(METRICS_MISSING_INFO_TEXT) + "</h1>"

		if self.metrics.eloc:
			metrics_xml += "<h1>" + _(ELOC_INFO_TEXT) + "</h1><ul class=\"list-group\">"
			for (value, name) in __sorted_violations__(self.metrics.eloc):
				metrics_xml += __html_violation__(__get_metrics_score__(__metric_eloc__[FileDiff.get_extension(name)], value),
				                                  _("{0} ({1} estimated lines of code)").format(name, str(value)))
			metrics_xml += "</ul>"

		if self.metrics.cyclomatic_complexity:
			metrics_xml += "<h1>" + _(CYCLOMATIC_COMPLEXITY_TEXT) + "</h1><ul class=\"list-group\">"
			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity):
				metrics_xml += __html_violation__(__get_metrics_score__(METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD, value),
				                                  _("{0} ({1} in cyclomatic complexity)").format(name, str(value)))
			metrics_xml += "</ul>"

		if self.metrics.cyclomatic_complexity_density:
			metrics_xml += "<h1>" + _(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT) + "</h1><ul class=\"list-group\">"
			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity_density):
				metrics_xml += __html_violation__(__get_metrics_score__(METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD, value),
				                                  _("{0} ({1:.3f} in cyclomatic complexity density)").format(name, value))
			metrics_xml += "</ul>"

		if self.metrics.cognitive_complexity:
			metrics_xml += "<h1>" + _(COGNITIVE_COMPLEXITY_TEXT) + "</h1><ul class=\"list-group\">"
			for (value, name) in __sorted_violations__(self.metrics.cognitive_complexity):
				metrics_xml += __html_violation__(__get_metrics_score__(METRIC_COGNITIVE_COMPLEXITY_THRESHOLD, value),
				                                  _("{0} ({1} in cognitive complexity)").format(name, str(value)))
			metrics_xml += "</ul>"

		metrics_xml += "</div></div>"
		print(metrics_xml)

	def output_json(self):
		if not self.has_violations():
			print(",\n\t\t\"metrics\": {\n\t\t\t\"message\": \"" + _(METRICS_MISSING_INFO_TEXT) + "\"\n\t\t}", end="")
		else:
			violations = []

			for (value, name) in __sorted_violations__(self.metrics.eloc):
				violations.append(__json_violation__("estimated-lines-of-code", name, str(value)))

			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity):
				violations.append(__json_violation__("cyclomatic-complexity", name, str(value)))

			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity_density):
				violations.append(__json_violation__("cyclomatic-complexity-density", name, "{0:.3f}".format(value)))

			for (value, name) in __sorted_violations__(self.metrics.cognitive_complexity):
				violations.append(__json_violation__("cognitive-complexity", name, str(value)))

			print(",\n\t\t\"metrics\": {\n\t\t\t\"violations\": [\n\t\t\t" + ",".join(violations) + "]\n\t\t}", end="")

	def output_xml(self):
		if not self.has_violations():
			print("\t<metrics>\n\t\t<message>" + _(METRICS_MISSING_INFO_TEXT) + "</message>\n\t</metrics>")
		else:
			violations = ""

			for (value, name) in __sorted_violations__(self.metrics.eloc):
				violations += __xml_violation__("estimated-lines-of-code", name, str(value))

			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity):
				violations += __xml_violation__("cyclomatic-complexity", name, str(value))

			for (value, name) in __sorted_violations__(self.metrics.cyclomatic_complexity_density):
				violations += __xml_violation__("cyclomatic-complexity-density", name, "{0:.3f}".format(value))

			for (value, name) in __sorted_violations__(self.metrics.cognitive_complexity):
				violations += __xml_violation__("cognitive-complexity", name, str(value))

			print("\t<metrics>\n\t\t<violations>\n" + violations + "\t\t</violations>\n\t</metrics>")
