# coding: utf-8
#
# Copyright © 2012-2013 Ejwa Software. All rights reserved.
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
from outputable import Outputable
import terminal
import textwrap

__default_extensions__ = ["java", "c", "cpp", "h", "hpp", "py", "glsl", "rb", "js", "sql"]
__extensions__ = __default_extensions__
__located_extensions__ = set()

def get():
	return __extensions__

def define(string):
	global __extensions__
	__extensions__ = string.split(",")

def add_located(string):
	if len(string) > 0:
		__located_extensions__.add(string)

__extensions_info_text__ = "The extensions below were found in the repository history"

class Extensions(Outputable):
	def output_html(self):
		if __located_extensions__:
			extensions_xml = "<div><div class=\"box\">"
			extensions_xml += "<p>" + __extensions_info_text__ + " (extensions used during statistical analysis are marked).</p><p>"

			for i in __located_extensions__:
				if i in __extensions__:
					extensions_xml += "<strong>" + i + "</strong>"
				else:
					extensions_xml += i
				extensions_xml += " "

			extensions_xml += "</p></div></div>"
			print(extensions_xml)

	def output_text(self):
		if __located_extensions__:
			print("\n" + textwrap.fill(__extensions_info_text__ + "\n(extensions used during statistical analysis are marked):",
			      width=terminal.get_size()[0]))

			for i in __located_extensions__:
				if i in __extensions__:
					print("[" + terminal.__bold__ + i + terminal.__normal__ + "]", end=" ")
				else:
					print (i, end=" ")
			print("")

	def output_xml(self):
		if __located_extensions__:
			message_xml = "\t\t<message>" + __extensions_info_text__ + "</message>\n"
			used_extensions_xml = ""
			unused_extensions_xml = ""

			for i in __located_extensions__:
				if i in __extensions__:
					used_extensions_xml += "\t\t\t<extension>" + i + "</extension>\n"
				else:
					unused_extensions_xml += "\t\t\t<extension>" + i + "</extension>\n"

			print("\t<extensions>\n" + message_xml + "\t\t<used>\n" + used_extensions_xml + "\t\t</used>\n" +
			      "\t\t<unused>\n" + unused_extensions_xml + "\t\t</unused>\n" + "\t</extensions>")
