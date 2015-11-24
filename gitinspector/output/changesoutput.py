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
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal
from .outputable import Outputable

HISTORICAL_INFO_TEXT = N_("The following historical commit information, by author, was found")
NO_COMMITED_FILES_TEXT = N_("No commited files with the specified extensions were found")

class ChangesOutput(Outputable):
	def __init__(self, changes):
		self.changes = changes
		Outputable.__init__(self)

	def output_html(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		total_changes = 0.0
		changes_xml = "<div><div class=\"box\">"
		chart_data = ""

		for i in authorinfo_list:
			total_changes += authorinfo_list.get(i).insertions
			total_changes += authorinfo_list.get(i).deletions

		if authorinfo_list:
			changes_xml += "<p>" + _(HISTORICAL_INFO_TEXT) + ".</p><div><table id=\"changes\" class=\"git\">"
			changes_xml += "<thead><tr> <th>{0}</th> <th>{1}</th> <th>{2}</th> <th>{3}</th> <th>{4}</th>".format(
			               _("Author"), _("Commits"), _("Insertions"), _("Deletions"), _("% of changes"))
			changes_xml += "</tr></thead><tbody>"

			for i, entry in enumerate(sorted(authorinfo_list)):
				authorinfo = authorinfo_list.get(entry)
				percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100

				changes_xml += "<tr " + ("class=\"odd\">" if i % 2 == 1 else ">")

				if format.get_selected() == "html":
					changes_xml += "<td><img src=\"{0}\"/>{1}</td>".format(
					               gravatar.get_url(self.changes.get_latest_email_by_author(entry)), entry)
				else:
					changes_xml += "<td>" + entry + "</td>"

				changes_xml += "<td>" + str(authorinfo.commits) + "</td>"
				changes_xml += "<td>" + str(authorinfo.insertions) + "</td>"
				changes_xml += "<td>" + str(authorinfo.deletions) + "</td>"
				changes_xml += "<td>" + "{0:.2f}".format(percentage) + "</td>"
				changes_xml += "</tr>"
				chart_data += "{{label: {0}, data: {1}}}".format(json.dumps(entry), "{0:.2f}".format(percentage))

				if sorted(authorinfo_list)[-1] != entry:
					chart_data += ", "

			changes_xml += ("<tfoot><tr> <td colspan=\"5\">&nbsp;</td> </tr></tfoot></tbody></table>")
			changes_xml += "<div class=\"chart\" id=\"changes_chart\"></div></div>"
			changes_xml += "<script type=\"text/javascript\">"
			changes_xml += "    changes_plot = $.plot($(\"#changes_chart\"), [{0}], {{".format(chart_data)
			changes_xml += "        series: {"
			changes_xml += "            pie: {"
			changes_xml += "                innerRadius: 0.4,"
			changes_xml += "                show: true,"
			changes_xml += "                combine: {"
			changes_xml += "                    threshold: 0.01,"
			changes_xml += "                    label: \"" + _("Minor Authors") + "\""
			changes_xml += "                }"
			changes_xml += "            }"
			changes_xml += "        }, grid: {"
			changes_xml += "            hoverable: true"
			changes_xml += "        }"
			changes_xml += "    });"
			changes_xml += "</script>"
		else:
			changes_xml += "<p>" + _(NO_COMMITED_FILES_TEXT) + ".</p>"

		changes_xml += "</div></div>"
		print(changes_xml)

	def output_json(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		total_changes = 0.0

		for i in authorinfo_list:
			total_changes += authorinfo_list.get(i).insertions
			total_changes += authorinfo_list.get(i).deletions

		if authorinfo_list:
			message_json = "\t\t\t\"message\": \"" + _(HISTORICAL_INFO_TEXT) + "\",\n"
			changes_json = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100
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

			print("\t\t\"changes\": {\n" + message_json + "\t\t\t\"authors\": [\n\t\t\t" + changes_json + "]\n\t\t}", end="")
		else:
			print("\t\t\"exception\": \"" + _(NO_COMMITED_FILES_TEXT) + "\"")

	def output_text(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		total_changes = 0.0

		for i in authorinfo_list:
			total_changes += authorinfo_list.get(i).insertions
			total_changes += authorinfo_list.get(i).deletions

		if authorinfo_list:
			print(textwrap.fill(_(HISTORICAL_INFO_TEXT) + ":", width=terminal.get_size()[0]) + "\n")
			terminal.printb(terminal.ljust(_("Author"), 21) + terminal.rjust(_("Commits"), 13) +
			                terminal.rjust(_("Insertions"), 14) + terminal.rjust(_("Deletions"), 15) +
					terminal.rjust(_("% of changes"), 16))

			for i in sorted(authorinfo_list):
				authorinfo = authorinfo_list.get(i)
				percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100

				print(terminal.ljust(i, 20)[0:20 - terminal.get_excess_column_count(i)], end=" ")
				print(str(authorinfo.commits).rjust(13), end=" ")
				print(str(authorinfo.insertions).rjust(13), end=" ")
				print(str(authorinfo.deletions).rjust(14), end=" ")
				print("{0:.2f}".format(percentage).rjust(15))
		else:
			print(_(NO_COMMITED_FILES_TEXT) + ".")

	def output_xml(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		total_changes = 0.0

		for i in authorinfo_list:
			total_changes += authorinfo_list.get(i).insertions
			total_changes += authorinfo_list.get(i).deletions

		if authorinfo_list:
			message_xml = "\t\t<message>" + _(HISTORICAL_INFO_TEXT) + "</message>\n"
			changes_xml = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100
				name_xml = "\t\t\t\t<name>" + i + "</name>\n"
				email_xml = "\t\t\t\t<email>" + author_email + "</email>\n"
				gravatar_xml = "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
				commits_xml = "\t\t\t\t<commits>" + str(authorinfo.commits) + "</commits>\n"
				insertions_xml = "\t\t\t\t<insertions>" + str(authorinfo.insertions) + "</insertions>\n"
				deletions_xml = "\t\t\t\t<deletions>" + str(authorinfo.deletions) + "</deletions>\n"
				percentage_xml = "\t\t\t\t<percentage-of-changes>" + "{0:.2f}".format(percentage) + "</percentage-of-changes>\n"

				changes_xml += ("\t\t\t<author>\n" + name_xml + email_xml + gravatar_xml + commits_xml +
				                insertions_xml + deletions_xml + percentage_xml + "\t\t\t</author>\n")

			print("\t<changes>\n" + message_xml + "\t\t<authors>\n" + changes_xml + "\t\t</authors>\n\t</changes>")
		else:
			print("\t<changes>\n\t\t<exception>" + _(NO_COMMITED_FILES_TEXT) + "</exception>\n\t</changes>")
