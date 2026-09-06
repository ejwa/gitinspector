# coding: utf-8
#
# Copyright © 2012-2026 Ejwa Hosting AB. All rights reserved.
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
from xml.sax.saxutils import escape
from ..localization import N_
from .. import format
from .outputable import Outputable, html_card, html_cards, html_file_row, html_files

ELOC_INFO_TEXT = N_("The following files are suspiciously big (in order of severity)")
CYCLOMATIC_COMPLEXITY_TEXT = N_("The following files have an elevated cyclomatic complexity (in order of severity)")
CYCLOMATIC_COMPLEXITY_DENSITY_TEXT = N_("The following files have an elevated cyclomatic complexity density " \
                                        "(in order of severity)")
COGNITIVE_COMPLEXITY_TEXT = N_("The following files have an elevated cognitive complexity (in order of severity)")
METRICS_MISSING_INFO_TEXT = N_("No metrics violations were found in the repository")

def __sorted_violations__(violations):
	return sorted(set([(value, name) for (name, value) in violations.items()]), reverse=True)

def __html_violations__(title, violations, template, color=None):
	if not violations:
		return ""

	sorted_violations = __sorted_violations__(violations)
	widest = sorted_violations[0][0]
	rows = [html_file_row(name, template.format(value), value, widest, color) for (value, name) in sorted_violations]

	return html_card(title, html_files(rows), pad=True)

def __json_violation__(kind, name, value):
	return ("{\n\t\t\t\t\"type\": \"" + kind + "\",\n\t\t\t\t\"file_name\": " + format.json_string(name) + ",\n" +
	        "\t\t\t\t\"value\": " + value + "\n\t\t\t}")

def __xml_violation__(kind, name, value):
	return ("\t\t\t<" + kind + ">\n\t\t\t\t<file-name>" + escape(name) + "</file-name>\n" +
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
		if not self.has_violations():
			print(html_card(_(METRICS_MISSING_INFO_TEXT), "", pad=True))
			return

		cards = [__html_violations__(_(ELOC_INFO_TEXT), self.metrics.eloc, "{0}", "var(--del)"),
		         __html_violations__(_(CYCLOMATIC_COMPLEXITY_TEXT), self.metrics.cyclomatic_complexity, "{0}"),
		         __html_violations__(_(CYCLOMATIC_COMPLEXITY_DENSITY_TEXT), self.metrics.cyclomatic_complexity_density,
		                             "{0:.3f}"),
		         __html_violations__(_(COGNITIVE_COMPLEXITY_TEXT), self.metrics.cognitive_complexity, "{0}")]

		print(html_cards(cards))

	def output_json(self):
		if not self.has_violations():
			print(",\n\t\t\"metrics\": {\n\t\t\t\"message\": " + format.json_string(_(METRICS_MISSING_INFO_TEXT)) +
			      "\n\t\t}", end="")
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
			print("\t<metrics>\n\t\t<message>" + escape(_(METRICS_MISSING_INFO_TEXT)) + "</message>\n\t</metrics>")
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
