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
import json
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal
from .outputable import Outputable, html_toggle_button

HISTORICAL_INFO_TEXT = N_("The following historical commit information, by author, was found in the repository")
NO_COMMITED_FILES_TEXT = N_("No commited files with the specified extensions were found")
TOTAL_TEXT = N_("Total")

def __get_totals__(authorinfo_list):
	commits = insertions = deletions = 0

	for authorinfo in authorinfo_list.values():
		commits += authorinfo.commits
		insertions += authorinfo.insertions
		deletions += authorinfo.deletions

	return (commits, insertions, deletions, float(insertions + deletions))

def __get_percentage__(insertions, deletions, total_changes):
	return 0 if total_changes == 0 else (insertions + deletions) / total_changes * 100

class ChangesOutput(Outputable):
	def __init__(self, changes):
		self.changes = changes
		Outputable.__init__(self)

	def output_html(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		(total_commits, total_insertions, total_deletions, total_changes) = __get_totals__(authorinfo_list)
		total_percentage = __get_percentage__(total_insertions, total_deletions, total_changes)
		changes_xml = "<div><div class=\"box\">"
		chart_data = ""

		if authorinfo_list:
			changes_xml += "<h1>" + _(HISTORICAL_INFO_TEXT) + "</h1>"
			changes_xml += html_toggle_button(_("Show minor authors"))
			changes_xml += "<div class=\"row\"><div class=\"col-md-8 table-responsive\"><table id=\"changes\" class=\"table\">"
			changes_xml += "<thead><tr> <th>{0}</th> <th>{1}</th> <th>{2}</th> <th>{3}</th> <th>{4}</th>".format(
			               _("Author"), _("Commits"), _("Insertions"), _("Deletions"), _("% of changes"))
			changes_xml += "</tr></thead><tbody>"

			for i, entry in enumerate(sorted(authorinfo_list)):
				authorinfo = authorinfo_list.get(entry)
				percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)

				if format.get_selected() == "html":
					changes_xml += "<tr><td><img src=\"{0}\"/>{1}</td>".format(
					               gravatar.get_url(self.changes.get_latest_email_by_author(entry)), entry)
				else:
					changes_xml += "<tr><td>" + entry + "</td>"

				changes_xml += "<td>" + str(authorinfo.commits) + "</td>"
				changes_xml += "<td>" + str(authorinfo.insertions) + "</td>"
				changes_xml += "<td>" + str(authorinfo.deletions) + "</td>"
				changes_xml += "<td>" + "{0:.2f}".format(percentage) + "</td>"
				changes_xml += "</tr>"
				chart_data += "{{label: {0}, data: {1}}}".format(json.dumps(entry), "{0:.2f}".format(percentage))

				if sorted(authorinfo_list)[-1] != entry:
					chart_data += ", "

			#The total belongs in a tfoot; the report script only ever looks at tbody rows.
			changes_xml += "</tbody><tfoot><tr><td><strong>" + _(TOTAL_TEXT) + "</strong></td>"
			changes_xml += "<td><strong>" + str(total_commits) + "</strong></td>"
			changes_xml += "<td><strong>" + str(total_insertions) + "</strong></td>"
			changes_xml += "<td><strong>" + str(total_deletions) + "</strong></td>"
			changes_xml += "<td><strong>" + "{0:.2f}".format(total_percentage) + "</strong></td>"
			changes_xml += "</tr></tfoot>"
			changes_xml += "</table></div><div class=\"chart col-md-4\" id=\"changes_chart\"></div></div>"
			changes_xml += "<script type=\"text/javascript\">"
			changes_xml += "    changes_plot = $.plot($(\"#changes_chart\"), [{0}], {{".format(chart_data)
			changes_xml += "        series: {"
			changes_xml += "            pie: {"
			changes_xml += "                innerRadius: 0.4,"
			changes_xml += "                show: true,"
			changes_xml += "                combine: {"
			changes_xml += "                    threshold: MINOR_AUTHOR_PERCENTAGE / 100,"
			changes_xml += "                    label: \"" + _("Minor Authors") + "\""
			changes_xml += "                }"
			changes_xml += "            }"
			changes_xml += "        }, grid: {"
			changes_xml += "            hoverable: true"
			changes_xml += "        }"
			changes_xml += "    });"
			changes_xml += "</script>"
		else:
			changes_xml += "<h1>" + _(NO_COMMITED_FILES_TEXT) + "</h1>"

		changes_xml += "</div></div>"
		print(changes_xml)

	def output_json(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		(total_commits, total_insertions, total_deletions, total_changes) = __get_totals__(authorinfo_list)
		total_percentage = __get_percentage__(total_insertions, total_deletions, total_changes)

		if authorinfo_list:
			message_json = "\t\t\t\"message\": \"" + _(HISTORICAL_INFO_TEXT) + "\",\n"
			changes_json = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)
				name_json = "\t\t\t\t\"name\": \"" + i + "\",\n"
				email_json = "\t\t\t\t\"email\": \"" + author_email + "\",\n"
				gravatar_json = "\t\t\t\t\"gravatar\": \"" + gravatar.get_url(author_email) + "\",\n"
				commits_json = "\t\t\t\t\"commits\": " + str(authorinfo.commits) + ",\n"
				insertions_json = "\t\t\t\t\"insertions\": " + str(authorinfo.insertions) + ",\n"
				deletions_json = "\t\t\t\t\"deletions\": " + str(authorinfo.deletions) + ",\n"
				percentage_json = "\t\t\t\t\"percentage_of_changes\": " + "{0:.2f}".format(percentage) + "\n"

				changes_json += ("{\n" + name_json + email_json + gravatar_json + commits_json +
				                 insertions_json + deletions_json + percentage_json + "\t\t\t}")
				changes_json += ","
			else:
				changes_json = changes_json[:-1]

			total_json = ("\t\t\t\"total\": {\n\t\t\t\t\"commits\": " + str(total_commits) + ",\n" +
			              "\t\t\t\t\"insertions\": " + str(total_insertions) + ",\n" +
			              "\t\t\t\t\"deletions\": " + str(total_deletions) + ",\n" +
			              "\t\t\t\t\"percentage_of_changes\": " + "{0:.2f}".format(total_percentage) + "\n\t\t\t}\n")

			print("\t\t\"changes\": {\n" + message_json + "\t\t\t\"authors\": [\n\t\t\t" + changes_json + "],\n" +
			      total_json + "\t\t}", end="")
		else:
			print("\t\t\"exception\": \"" + _(NO_COMMITED_FILES_TEXT) + "\"")

	def output_text(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		(total_commits, total_insertions, total_deletions, total_changes) = __get_totals__(authorinfo_list)
		total_percentage = __get_percentage__(total_insertions, total_deletions, total_changes)

		if authorinfo_list:
			print(textwrap.fill(_(HISTORICAL_INFO_TEXT) + ":", width=terminal.get_size()[0]) + "\n")
			terminal.printb(terminal.ljust(_("Author"), 21) + terminal.rjust(_("Commits"), 13) +
			                terminal.rjust(_("Insertions"), 14) + terminal.rjust(_("Deletions"), 15) +
					terminal.rjust(_("% of changes"), 16))

			for i in sorted(authorinfo_list):
				authorinfo = authorinfo_list.get(i)
				percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)

				print(terminal.ljust(i, 20)[0:20 - terminal.get_excess_column_count(i)], end=" ")
				print(str(authorinfo.commits).rjust(13), end=" ")
				print(str(authorinfo.insertions).rjust(13), end=" ")
				print(str(authorinfo.deletions).rjust(14), end=" ")
				print("{0:.2f}".format(percentage).rjust(15))

			#terminal.rjust measures the string; str() gives it bytes on Python 2, which it cannot measure.
			terminal.printb(terminal.ljust(_(TOTAL_TEXT), 21) + terminal.rjust("{0}".format(total_commits), 13) +
			                terminal.rjust("{0}".format(total_insertions), 14) +
			                terminal.rjust("{0}".format(total_deletions), 15) +
			                terminal.rjust("{0:.2f}".format(total_percentage), 16))
		else:
			print(_(NO_COMMITED_FILES_TEXT) + ".")

	def output_xml(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		(total_commits, total_insertions, total_deletions, total_changes) = __get_totals__(authorinfo_list)
		total_percentage = __get_percentage__(total_insertions, total_deletions, total_changes)

		if authorinfo_list:
			message_xml = "\t\t<message>" + _(HISTORICAL_INFO_TEXT) + "</message>\n"
			changes_xml = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)
				name_xml = "\t\t\t\t<name>" + i + "</name>\n"
				email_xml = "\t\t\t\t<email>" + author_email + "</email>\n"
				gravatar_xml = "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
				commits_xml = "\t\t\t\t<commits>" + str(authorinfo.commits) + "</commits>\n"
				insertions_xml = "\t\t\t\t<insertions>" + str(authorinfo.insertions) + "</insertions>\n"
				deletions_xml = "\t\t\t\t<deletions>" + str(authorinfo.deletions) + "</deletions>\n"
				percentage_xml = "\t\t\t\t<percentage-of-changes>" + "{0:.2f}".format(percentage) + "</percentage-of-changes>\n"

				changes_xml += ("\t\t\t<author>\n" + name_xml + email_xml + gravatar_xml + commits_xml +
				                insertions_xml + deletions_xml + percentage_xml + "\t\t\t</author>\n")

			total_xml = ("\t\t<total>\n\t\t\t<commits>" + str(total_commits) + "</commits>\n" +
			             "\t\t\t<insertions>" + str(total_insertions) + "</insertions>\n" +
			             "\t\t\t<deletions>" + str(total_deletions) + "</deletions>\n" +
			             "\t\t\t<percentage-of-changes>" + "{0:.2f}".format(total_percentage) +
			             "</percentage-of-changes>\n\t\t</total>\n")

			print("\t<changes>\n" + message_xml + "\t\t<authors>\n" + changes_xml + "\t\t</authors>\n" +
			      total_xml + "\t</changes>")
		else:
			print("\t<changes>\n\t\t<exception>" + _(NO_COMMITED_FILES_TEXT) + "</exception>\n\t</changes>")
