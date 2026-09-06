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
import sys
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal
from ..blame import Blame
from .outputable import (Outputable, author_color, author_indices, html_author_cell, html_card,
                         html_header_cell, html_meter_cell, html_number_cell, html_share, html_table, percentage)

BLAME_INFO_TEXT = N_("Below are the number of lines from each author that have survived and are still "
                     "intact in the current revision")

class BlameOutput(Outputable):
	def __init__(self, changes, blame, forcemonths):
		if format.is_interactive_format():
			print("")

		self.changes = changes
		self.blame = blame
		self.forcemonths = forcemonths
		Outputable.__init__(self)

	def output_html(self):
		blames = sorted(self.blame.get_summed_blames().items())
		total_blames = sum(entry[1].lines for entry in blames)
		months = self.forcemonths and self.blame.useweeks
		indices = author_indices(self.changes.get_authorinfo_list())
		rows = ""
		shares = []

		for (author, blame) in blames:
			index = indices.get(author, 0)
			work_percentage = percentage(blame.lines, total_blames)
			url = gravatar.get_url(self.changes.get_latest_email_by_author(author)) if format.get_selected() == "html" else None
			shares.append((author, work_percentage, author_color(index)))

			rows += "<tr data-gi-searchable=\"authors\">"
			rows += html_author_cell(author, index, url)
			rows += html_number_cell(_("Lines"), blame.lines)
			rows += html_number_cell(_("Stability"), "{0:.1f}".format(Blame.get_stability(author, blame.lines, self.changes)))

			if months:
				rows += html_number_cell(_("Age, months"), "{0:.1f}".format(float(blame.get_skew(True)) / blame.lines))

			rows += html_number_cell(_("Age, weeks") if months else _("Age"), "{0:.1f}".format(float(blame.get_skew()) / blame.lines))
			rows += html_number_cell(_("% in comments"), "{0:.2f}".format(percentage(blame.comments, blame.lines)))
			rows += html_meter_cell(_("% of total"), work_percentage, author_color(index))
			rows += "</tr>"

		headers = "<thead><tr>" + html_header_cell(_("Author")) + html_header_cell(_("Lines"), True) + \
		          html_header_cell(_("Stability"), True)

		if months:
			headers += html_header_cell(_("Age, months"), True)

		headers += html_header_cell(_("Age, weeks") if months else _("Age"), True) + \
		           html_header_cell(_("% in comments"), True) + html_header_cell(_("% of total"), True) + "</tr></thead>"

		body = html_share(shares, _("Minor Authors")) + html_table("blame", headers + "<tbody>" + rows + "</tbody>")
		print(html_card(_(BLAME_INFO_TEXT), body))

	def output_json(self):
		message_json = "\t\t\t\"message\": \"" + _(BLAME_INFO_TEXT) + "\",\n"
		blame_json = ""

		for i in sorted(self.blame.get_summed_blames().items()):
			author_email = self.changes.get_latest_email_by_author(i[0])

			name_json = "\t\t\t\t\"name\": \"" + i[0] + "\",\n"
			email_json = "\t\t\t\t\"email\": \"" + author_email + "\",\n"
			gravatar_json = "\t\t\t\t\"gravatar\": \"" + gravatar.get_url(author_email) + "\",\n"
			lines_json = "\t\t\t\t\"lines\": " + str(i[1].lines) + ",\n"
			stability_json = ("\t\t\t\t\"stability\": " + "{0:.1f}".format(Blame.get_stability(i[0], i[1].lines,
			                  self.changes)) + ",\n")
			if self.forcemonths and self.blame.useweeks:
				age_json = ("\t\t\t\t\"age_months\": " + "{0:.1f}".format(float(i[1].get_skew(True)) / i[1].lines) + ",\n")
				age_t_name = "age_weeks"
			else:
				age_json = ""
				age_t_name = "age"
			age_json += (("\t\t\t\t\"%s\": " % age_t_name) + "{0:.1f}".format(float(i[1].get_skew()) / i[1].lines) + ",\n")
			percentage_in_comments_json = ("\t\t\t\t\"percentage_in_comments\": " +
			                               "{0:.2f}".format(100.0 * i[1].comments / i[1].lines) + "\n")
			blame_json += ("{\n" + name_json + email_json + gravatar_json + lines_json + stability_json + age_json +
			              percentage_in_comments_json + "\t\t\t},")
		else:
			blame_json = blame_json[:-1]

		print(",\n\t\t\"blame\": {\n" + message_json + "\t\t\t\"authors\": [\n\t\t\t" + blame_json + "]\n\t\t}", end="")

	def output_text(self):
		if sys.stdout.isatty() and format.is_interactive_format():
			terminal.clear_line()

		print(textwrap.fill(_(BLAME_INFO_TEXT) + ":", width=terminal.get_size()[0]) + "\n")
		if self.forcemonths and self.blame.useweeks:
			fparams = (18, 8, 10, 12, 14)
		else:
			fparams = (20, 10, 14, 12, 19)
		auwidth, lwidth, swidth, awidth, cwidth = fparams
		prints = terminal.ljust(_("Author"), auwidth + 1) + terminal.rjust(_("Lines"), lwidth) + terminal.rjust(_("Stability"), swidth + 1)
		if self.forcemonths and self.blame.useweeks:
			prints += terminal.rjust(_("Age, months"), awidth + 1) + terminal.rjust(_("Age, weeks"), awidth + 1)
		else:
			prints += terminal.rjust(_("Age"), awidth + 1)
		prints += terminal.rjust(_("% in comments"), cwidth + 1)
		terminal.printb(prints)

		for i in sorted(self.blame.get_summed_blames().items()):
			print(terminal.ljust(i[0], auwidth)[0:auwidth - terminal.get_excess_column_count(i[0])], end=" ")
			print(str(i[1].lines).rjust(lwidth), end=" ")
			print("{0:.1f}".format(Blame.get_stability(i[0], i[1].lines, self.changes)).rjust(swidth), end=" ")
			if self.forcemonths and self.blame.useweeks:
				print("{0:.1f}".format(float(i[1].get_skew(True)) / i[1].lines).rjust(awidth), end=" ")
			print("{0:.1f}".format(float(i[1].get_skew()) / i[1].lines).rjust(awidth), end=" ")
			print("{0:.2f}".format(100.0 * i[1].comments / i[1].lines).rjust(cwidth))

	def output_xml(self):
		message_xml = "\t\t<message>" + _(BLAME_INFO_TEXT) + "</message>\n"
		blame_xml = ""

		for i in sorted(self.blame.get_summed_blames().items()):
			author_email = self.changes.get_latest_email_by_author(i[0])

			name_xml = "\t\t\t\t<name>" + i[0] + "</name>\n"
			email_xml = "\t\t\t\t<email>" + author_email + "</email>\n"
			gravatar_xml = "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
			lines_xml = "\t\t\t\t<lines>" + str(i[1].lines) + "</lines>\n"
			stability_xml = ("\t\t\t\t<stability>" + "{0:.1f}".format(Blame.get_stability(i[0], i[1].lines,
			                 self.changes)) + "</stability>\n")
			if self.forcemonths and self.blame.useweeks:
				age_xml = ("\t\t\t\t<age_months>" + "{0:.1f}".format(float(i[1].get_skew(True)) / i[1].lines) + "</age_months>\n")
				age_t_name = "age_weeks"
			else:
				age_xml = ""
				age_t_name = "age"
			age_xml += (("\t\t\t\t<%s>" % age_t_name) + "{0:.1f}".format(float(i[1].get_skew()) / i[1].lines) + ("</%s>\n" % age_t_name))
			percentage_in_comments_xml = ("\t\t\t\t<percentage-in-comments>" + "{0:.2f}".format(100.0 * i[1].comments / i[1].lines) +
			                              "</percentage-in-comments>\n")
			blame_xml += ("\t\t\t<author>\n" + name_xml + email_xml + gravatar_xml + lines_xml + stability_xml +
			              age_xml + percentage_in_comments_xml + "\t\t\t</author>\n")

		print("\t<blame>\n" + message_xml + "\t\t<authors>\n" + blame_xml + "\t\t</authors>\n\t</blame>")
