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
import json
import sys
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal
from ..blame import Blame
from .outputable import Outputable

BLAME_INFO_TEXT = N_("Below are the number of rows from each author that have survived and are still "
                     "intact in the current revision")

class BlameOutput(Outputable):
	def __init__(self, changes, blame):
		if format.is_interactive_format():
			print("")

		self.changes = changes
		self.blame = blame
		Outputable.__init__(self)

	def output_html(self):
		blame_xml = "<div><div class=\"box\">"
		blame_xml += "<p>" + _(BLAME_INFO_TEXT) + ".</p><div><table id=\"blame\" class=\"git\">"
		blame_xml += "<thead><tr> <th>{0}</th> <th>{1}</th> <th>{2}</th> <th>{3}</th> <th>{4}</th> </tr></thead>".format(
		             _("Author"), _("Rows"), _("Stability"), _("Age"), _("% in comments"))
		blame_xml += "<tbody>"
		chart_data = ""
		blames = sorted(self.blame.get_summed_blames().items())
		total_blames = 0

		for i in blames:
			total_blames += i[1].rows

		for i, entry in enumerate(blames):
			work_percentage = str("{0:.2f}".format(100.0 * entry[1].rows / total_blames))
			blame_xml += "<tr " + ("class=\"odd\">" if i % 2 == 1 else ">")

			if format.get_selected() == "html":
				author_email = self.changes.get_latest_email_by_author(entry[0])
				blame_xml += "<td><img src=\"{0}\"/>{1}</td>".format(gravatar.get_url(author_email), entry[0])
			else:
				blame_xml += "<td>" + entry[0] + "</td>"

			blame_xml += "<td>" + str(entry[1].rows) + "</td>"
			blame_xml += "<td>" + ("{0:.1f}".format(Blame.get_stability(entry[0], entry[1].rows, self.changes)) + "</td>")
			blame_xml += "<td>" + "{0:.1f}".format(float(entry[1].skew) / entry[1].rows) + "</td>"
			blame_xml += "<td>" + "{0:.2f}".format(100.0 * entry[1].comments / entry[1].rows) + "</td>"
			blame_xml += "<td style=\"display: none\">" + work_percentage + "</td>"
			blame_xml += "</tr>"
			chart_data += "{{label: {0}, data: {1}}}".format(json.dumps(entry[0]), work_percentage)

			if blames[-1] != entry:
				chart_data += ", "

		blame_xml += "<tfoot><tr> <td colspan=\"5\">&nbsp;</td> </tr></tfoot></tbody></table>"
		blame_xml += "<div class=\"chart\" id=\"blame_chart\"></div></div>"
		blame_xml += "<script type=\"text/javascript\">"
		blame_xml += "    blame_plot = $.plot($(\"#blame_chart\"), [{0}], {{".format(chart_data)
		blame_xml += "        series: {"
		blame_xml += "            pie: {"
		blame_xml += "                innerRadius: 0.4,"
		blame_xml += "                show: true,"
		blame_xml += "                combine: {"
		blame_xml += "                    threshold: 0.01,"
		blame_xml += "                    label: \"" + _("Minor Authors") + "\""
		blame_xml += "                }"
		blame_xml += "            }"
		blame_xml += "        }, grid: {"
		blame_xml += "            hoverable: true"
		blame_xml += "        }"
		blame_xml += "    });"
		blame_xml += "</script></div></div>"

		print(blame_xml)

	def output_json(self):
		message_xml = "\t\t\t\"message\": \"" + _(BLAME_INFO_TEXT) + "\",\n"
		blame_xml = ""

		for i in sorted(self.blame.get_summed_blames().items()):
			author_email = self.changes.get_latest_email_by_author(i[0])

			name_xml = "\t\t\t\t\"name\": \"" + i[0] + "\",\n"
			gravatar_xml = "\t\t\t\t\"gravatar\": \"" + gravatar.get_url(author_email) + "\",\n"
			rows_xml = "\t\t\t\t\"rows\": " + str(i[1].rows) + ",\n"
			stability_xml = ("\t\t\t\t\"stability\": " + "{0:.1f}".format(Blame.get_stability(i[0], i[1].rows,
			                 self.changes)) + ",\n")
			age_xml = ("\t\t\t\t\"age\": " + "{0:.1f}".format(float(i[1].skew) / i[1].rows) + ",\n")
			percentage_in_comments_xml = ("\t\t\t\t\"percentage_in_comments\": " + "{0:.2f}".format(100.0 * i[1].comments / i[1].rows) +
			                              "\n")
			blame_xml += ("{\n" + name_xml + gravatar_xml + rows_xml + stability_xml + age_xml +
			             percentage_in_comments_xml + "\t\t\t},")
		else:
			blame_xml = blame_xml[:-1]

		print(",\n\t\t\"blame\": {\n" + message_xml + "\t\t\t\"authors\": [\n\t\t\t" + blame_xml + "]\n\t\t}", end="")

	def output_text(self):
		if sys.stdout.isatty() and format.is_interactive_format():
			terminal.clear_row()

		print(textwrap.fill(_(BLAME_INFO_TEXT) + ":", width=terminal.get_size()[0]) + "\n")
		terminal.printb(terminal.ljust(_("Author"), 21) + terminal.rjust(_("Rows"), 10) + terminal.rjust(_("Stability"), 15) +
		                terminal.rjust(_("Age"), 13) + terminal.rjust(_("% in comments"), 20))

		for i in sorted(self.blame.get_summed_blames().items()):
			print(terminal.ljust(i[0], 20)[0:20 - terminal.get_excess_column_count(i[0])], end=" ")
			print(str(i[1].rows).rjust(10), end=" ")
			print("{0:.1f}".format(Blame.get_stability(i[0], i[1].rows, self.changes)).rjust(14), end=" ")
			print("{0:.1f}".format(float(i[1].skew) / i[1].rows).rjust(12), end=" ")
			print("{0:.2f}".format(100.0 * i[1].comments / i[1].rows).rjust(19))

	def output_xml(self):
		message_xml = "\t\t<message>" + _(BLAME_INFO_TEXT) + "</message>\n"
		blame_xml = ""

		for i in sorted(self.blame.get_summed_blames().items()):
			author_email = self.changes.get_latest_email_by_author(i[0])

			name_xml = "\t\t\t\t<name>" + i[0] + "</name>\n"
			gravatar_xml = "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
			rows_xml = "\t\t\t\t<rows>" + str(i[1].rows) + "</rows>\n"
			stability_xml = ("\t\t\t\t<stability>" + "{0:.1f}".format(Blame.get_stability(i[0], i[1].rows,
			                 self.changes)) + "</stability>\n")
			age_xml = ("\t\t\t\t<age>" + "{0:.1f}".format(float(i[1].skew) / i[1].rows) + "</age>\n")
			percentage_in_comments_xml = ("\t\t\t\t<percentage-in-comments>" + "{0:.2f}".format(100.0 * i[1].comments / i[1].rows) +
			                              "</percentage-in-comments>\n")
			blame_xml += ("\t\t\t<author>\n" + name_xml + gravatar_xml + rows_xml + stability_xml + age_xml +
			             percentage_in_comments_xml + "\t\t\t</author>\n")

		print("\t<blame>\n" + message_xml + "\t\t<authors>\n" + blame_xml + "\t\t</authors>\n\t</blame>")
