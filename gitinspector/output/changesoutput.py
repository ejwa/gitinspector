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
import textwrap
from ..localization import N_
from xml.sax.saxutils import escape
from .. import format, gravatar, terminal
from .outputable import (Outputable, author_color, html_author_cell, html_card, html_diverging_cell,
                         html_diverging_header, html_header_cell, html_number_cell, html_share, html_stats, html_table)

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

	def __html_avatar_url__(self, author):
		return gravatar.get_url(self.changes.get_latest_email_by_author(author)) if format.get_selected() == "html" else None

	def output_html(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		(total_commits, total_insertions, total_deletions, total_changes) = __get_totals__(authorinfo_list)
		total_percentage = __get_percentage__(total_insertions, total_deletions, total_changes)

		if not authorinfo_list:
			print(html_card(_(NO_COMMITED_FILES_TEXT), ""))
			return

		authors = sorted(authorinfo_list)
		#The diverging bars share one scale so that the insertions of one author can be compared to
		#the deletions of another, and not only to the ones next to them.
		widest = max([max(authorinfo_list[author].insertions, authorinfo_list[author].deletions) for author in authors])
		rows = ""
		shares = []

		for i, entry in enumerate(authors):
			authorinfo = authorinfo_list.get(entry)
			percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)
			shares.append((entry, percentage, author_color(i)))

			rows += "<tr data-gi-searchable=\"authors\">"
			rows += html_author_cell(entry, i, self.__html_avatar_url__(entry))
			rows += html_number_cell(_("Commits"), authorinfo.commits)
			rows += html_diverging_cell(authorinfo.deletions, authorinfo.insertions, widest)
			rows += html_number_cell(_("% of changes"), "{0:.2f}".format(percentage))
			rows += "</tr>"

		headers = ("<thead><tr>" + html_header_cell(_("Author")) + html_header_cell(_("Commits"), True) +
		           html_diverging_header(_("Deletions"), _("Insertions")) +
		           html_header_cell(_("% of changes"), True) + "</tr></thead>")

		#The total belongs in a tfoot; the report script only ever sorts and hides tbody rows.
		total = ("<tfoot><tr><td>" + _(TOTAL_TEXT) + "</td>" +
		         html_number_cell(_("Commits"), total_commits) +
		         "<td class=\"gi-diverge\"><div><span class=\"gi-del-num\">−" + str(total_deletions) + "</span>" +
		         "<span class=\"gi-spacer\"></span><span class=\"gi-ins-num\">+" + str(total_insertions) + "</span></div></td>" +
		         html_number_cell(_("% of changes"), "{0:.2f}".format(total_percentage)) + "</tr></tfoot>")

		body = html_share(shares, _("Minor Authors")) + html_table("changes", headers + "<tbody>" + rows + "</tbody>" + total)

		print(html_stats(((_("Commits"), total_commits),
		                  (_("Insertions"), "<span class=\"gi-add\">+{0}</span>".format(total_insertions)),
		                  (_("Deletions"), "<span class=\"gi-del\">−{0}</span>".format(total_deletions)),
		                  (_(format.AUTHORS_TEXT), len(authors)))))
		print(html_card(_(HISTORICAL_INFO_TEXT), body))

	def output_json(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		(total_commits, total_insertions, total_deletions, total_changes) = __get_totals__(authorinfo_list)
		total_percentage = __get_percentage__(total_insertions, total_deletions, total_changes)

		if authorinfo_list:
			message_json = "\t\t\t\"message\": " + format.json_string(_(HISTORICAL_INFO_TEXT)) + ",\n"
			changes_json = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)
				name_json = "\t\t\t\t\"name\": " + format.json_string(i) + ",\n"
				email_json = "\t\t\t\t\"email\": " + format.json_string(author_email) + ",\n"
				gravatar_json = "\t\t\t\t\"gravatar\": " + format.json_string(gravatar.get_url(author_email)) + ",\n"
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
			print("\t\t\"exception\": " + format.json_string(_(NO_COMMITED_FILES_TEXT)))

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
			message_xml = "\t\t<message>" + escape(_(HISTORICAL_INFO_TEXT)) + "</message>\n"
			changes_xml = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = __get_percentage__(authorinfo.insertions, authorinfo.deletions, total_changes)
				name_xml = "\t\t\t\t<name>" + escape(i) + "</name>\n"
				email_xml = "\t\t\t\t<email>" + escape(author_email) + "</email>\n"
				gravatar_xml = "\t\t\t\t<gravatar>" + escape(gravatar.get_url(author_email)) + "</gravatar>\n"
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
			print("\t<changes>\n\t\t<exception>" + escape(_(NO_COMMITED_FILES_TEXT)) + "</exception>\n\t</changes>")
