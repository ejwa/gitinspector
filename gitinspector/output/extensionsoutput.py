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
import textwrap
from ..localization import N_
from .. import extensions, terminal
from .outputable import Outputable


EXTENSIONS_INFO_TEXT = N_("The extensions below were found in the repository history")
EXTENSIONS_MARKED_TEXT = N_("(extensions used during statistical analysis are marked)")

class ExtensionsOutput(Outputable):
	@staticmethod
	def is_marked(extension):
		if extension in extensions.__extensions__ or "**" in extensions.__extensions__:
			return True

		return False

	def output_html(self):
		if extensions.__located_extensions__:
			extensions_xml = "<div><div class=\"box\">"
			extensions_xml += "<p>{0} {1}.</p><p>".format(_(EXTENSIONS_INFO_TEXT), _(EXTENSIONS_MARKED_TEXT))

			for i in sorted(extensions.__located_extensions__):
				if ExtensionsOutput.is_marked(i):
					extensions_xml += "<strong>" + i + "</strong>"
				else:
					extensions_xml += i
				extensions_xml += " "

			extensions_xml += "</p></div></div>"
			print(extensions_xml)

	def output_json(self):
		if extensions.__located_extensions__:
			message_json = "\t\t\t\"message\": \"" + _(EXTENSIONS_INFO_TEXT) + "\",\n"
			used_extensions_json = ""
			unused_extensions_json = ""

			for i in sorted(extensions.__located_extensions__):
				if ExtensionsOutput.is_marked(i):
					used_extensions_json += "\"" + i + "\", "
				else:
					unused_extensions_json += "\"" + i + "\", "

			used_extensions_json = used_extensions_json[:-2]
			unused_extensions_json = unused_extensions_json[:-2]

			print(",\n\t\t\"extensions\": {\n" + message_json + "\t\t\t\"used\": [ " + used_extensions_json +
			      " ],\n\t\t\t\"unused\": [ " + unused_extensions_json + " ]\n" + "\t\t}", end="")

	def output_text(self):
		if extensions.__located_extensions__:
			print("\n" + textwrap.fill("{0} {1}:".format(_(EXTENSIONS_INFO_TEXT), _(EXTENSIONS_MARKED_TEXT)),
			      width=terminal.get_size()[0]))

			for i in sorted(extensions.__located_extensions__):
				if ExtensionsOutput.is_marked(i):
					print("[" + terminal.__bold__ + i + terminal.__normal__ + "]", end=" ")
				else:
					print (i, end=" ")
			print("")

	def output_xml(self):
		if extensions.__located_extensions__:
			message_xml = "\t\t<message>" + _(EXTENSIONS_INFO_TEXT) + "</message>\n"
			used_extensions_xml = ""
			unused_extensions_xml = ""

			for i in sorted(extensions.__located_extensions__):
				if ExtensionsOutput.is_marked(i):
					used_extensions_xml += "\t\t\t<extension>" + i + "</extension>\n"
				else:
					unused_extensions_xml += "\t\t\t<extension>" + i + "</extension>\n"

			print("\t<extensions>\n" + message_xml + "\t\t<used>\n" + used_extensions_xml + "\t\t</used>\n" +
			      "\t\t<unused>\n" + unused_extensions_xml + "\t\t</unused>\n" + "\t</extensions>")
