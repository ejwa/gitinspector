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
from xml.sax.saxutils import escape
from ..localization import N_
from .. import format, gravatar, terminal
from .. import responsibilities as resp
from .outputable import (Outputable, author_color, author_indices, html_avatar, html_card, html_file_row)

RESPONSIBILITIES_INFO_TEXT = N_("The following responsibilities, by author, were found in the current "
                                "revision of the repository (comments are excluded from the line count, "
                                "if possible)")
MOSTLY_RESPONSIBLE_FOR_TEXT = N_("is mostly responsible for")

#As many files as the text output lists, which is as many as an author can be usefully held to.
RESPONSIBILITIES_PER_AUTHOR = 10

def __summary__(responsibilities):
	return "{0}: {1} · {2} eloc".format(_(format.FILES_TEXT), len(responsibilities),
	                                    sum(entry[0] for entry in responsibilities))

class ResponsibilitiesOutput(Outputable):
	def __init__(self, changes, blame):
		self.changes = changes
		self.blame = blame
		Outputable.__init__(self)

	def output_text(self):
		print("\n" + textwrap.fill(_(RESPONSIBILITIES_INFO_TEXT) + ":", width=terminal.get_size()[0]))

		for i in sorted(set(i[0] for i in self.blame.blames)):
			responsibilities = sorted(((i[1], i[0]) for i in resp.Responsibilities.get(self.blame, i)), reverse=True)

			if responsibilities:
				print("\n" + i, _(MOSTLY_RESPONSIBLE_FOR_TEXT) + ":")

				for j, entry in enumerate(responsibilities):
					(width, _unused) = terminal.get_size()
					width -= 7

					print(str(entry[0]).rjust(6), end=" ")
					print("...%s" % entry[1][-width+3:] if len(entry[1]) > width else entry[1])

					if j >= 9:
						break

	def output_html(self):
		indices = author_indices(self.changes.get_authorinfo_list())
		rows = ""

		for author in sorted(set(i[0] for i in self.blame.blames)):
			responsibilities = sorted(((i[1], i[0]) for i in resp.Responsibilities.get(self.blame, author)), reverse=True)

			if not responsibilities:
				continue

			index = indices.get(author, 0)
			url = gravatar.get_url(self.changes.get_latest_email_by_author(author), size=22) \
			      if format.get_selected() == "html" else None
			shown = responsibilities[0:RESPONSIBILITIES_PER_AUTHOR]
			panel = "gi-resp-" + "{0}".format(index)
			files = [html_file_row(name, "{0} eloc".format(eloc), eloc, shown[0][0], author_color(index))
			         for (eloc, name) in shown]

			rows += ("<div class=\"gi-resp-row\" data-gi-searchable=\"authors\">"
			         "<button type=\"button\" data-gi-toggle=\"{0}\" aria-expanded=\"false\">"
			         "<span class=\"gi-chev\">▸</span>{1}<span class=\"gi-resp-name\">{2}</span>"
			         "<span class=\"gi-resp-summary\">{3}</span></button>"
			         "<div class=\"gi-resp-files gi-hidden\" id=\"{0}\">{4}</div></div>".format(
			         panel, html_avatar(author, index, url), escape(author),
			         escape(__summary__(responsibilities)), "".join(files)))

		print(html_card(_(RESPONSIBILITIES_INFO_TEXT), rows))

	def output_json(self):
		message_json = "\t\t\t\"message\": \"" + _(RESPONSIBILITIES_INFO_TEXT) + "\",\n"
		resp_json = ""

		for i in sorted(set(i[0] for i in self.blame.blames)):
			responsibilities = sorted(((i[1], i[0]) for i in resp.Responsibilities.get(self.blame, i)), reverse=True)

			if responsibilities:
				author_email = self.changes.get_latest_email_by_author(i)

				resp_json += "{\n"
				resp_json += "\t\t\t\t\"name\": \"" + i + "\",\n"
				resp_json += "\t\t\t\t\"email\": \"" + author_email + "\",\n"
				resp_json += "\t\t\t\t\"gravatar\": \"" + gravatar.get_url(author_email) + "\",\n"
				resp_json += "\t\t\t\t\"files\": [\n\t\t\t\t"

				for j, entry in enumerate(responsibilities):
					resp_json += "{\n"
					resp_json += "\t\t\t\t\t\"name\": \"" + entry[1] + "\",\n"
					resp_json += "\t\t\t\t\t\"lines\": " + str(entry[0]) + "\n"
					resp_json += "\t\t\t\t},"

					if j >= 9:
						break

				resp_json = resp_json[:-1]
				resp_json += "]\n\t\t\t},"

		resp_json = resp_json[:-1]
		print(",\n\t\t\"responsibilities\": {\n" + message_json + "\t\t\t\"authors\": [\n\t\t\t" + resp_json + "]\n\t\t}", end="")

	def output_xml(self):
		message_xml = "\t\t<message>" + _(RESPONSIBILITIES_INFO_TEXT) + "</message>\n"
		resp_xml = ""

		for i in sorted(set(i[0] for i in self.blame.blames)):
			responsibilities = sorted(((i[1], i[0]) for i in resp.Responsibilities.get(self.blame, i)), reverse=True)
			if responsibilities:
				author_email = self.changes.get_latest_email_by_author(i)

				resp_xml += "\t\t\t<author>\n"
				resp_xml += "\t\t\t\t<name>" + i + "</name>\n"
				resp_xml += "\t\t\t\t<email>" + author_email + "</email>\n"
				resp_xml += "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
				resp_xml += "\t\t\t\t<files>\n"

				for j, entry in enumerate(responsibilities):
					resp_xml += "\t\t\t\t\t<file>\n"
					resp_xml += "\t\t\t\t\t\t<name>" + entry[1] + "</name>\n"
					resp_xml += "\t\t\t\t\t\t<lines>" + str(entry[0]) + "</lines>\n"
					resp_xml += "\t\t\t\t\t</file>\n"

					if j >= 9:
						break

				resp_xml += "\t\t\t\t</files>\n"
				resp_xml += "\t\t\t</author>\n"

		print("\t<responsibilities>\n" + message_xml + "\t\t<authors>\n" + resp_xml + "\t\t</authors>\n\t</responsibilities>")
