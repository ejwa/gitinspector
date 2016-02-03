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
from localization import N_
from outputable import Outputable
import terminal
import textwrap

DEFAULT_EXTENSIONS = ["java", "c", "cc", "cpp", "h", "hh", "hpp", "py", "glsl", "rb", "js", "sql"]

__extensions__ = DEFAULT_EXTENSIONS
__located_extensions__ = set()

def get():
	return __extensions__

def define(string):
	global __extensions__
	__extensions__ = string.split(",")

def add_located(string):
	if len(string) == 0:
		__located_extensions__.add("*")
	else:
		__located_extensions__.add(string)

def get_located():
	return __located_extensions__

EXTENSIONS_INFO_TEXT = N_("The extensions below were found in the repository history")
EXTENSIONS_MARKED_TEXT = N_("(extensions used during statistical analysis are marked)")

class Extensions(Outputable):
	@staticmethod
	def is_marked(extension):
		if extension in __extensions__ or "**" in __extensions__:
			return True

		return False

	def output_html(self):
		if __located_extensions__:
			extensions_xml = "<div><div class=\"box\">"
			extensions_xml += "<p>{0} {1}.</p><p>".format(_(EXTENSIONS_INFO_TEXT), _(EXTENSIONS_MARKED_TEXT))

			for i in sorted(__located_extensions__):
				if Extensions.is_marked(i):
					extensions_xml += "<strong>" + i + "</strong>"
				else:
					extensions_xml += i
				extensions_xml += " "

			extensions_xml += "</p></div></div>"
			print(extensions_xml)

	def output_text(self):
		if __located_extensions__:
			print("\n" + textwrap.fill("{0} {1}:".format(_(EXTENSIONS_INFO_TEXT), _(EXTENSIONS_MARKED_TEXT)),
			      width=terminal.get_size()[0]))

			for i in sorted(__located_extensions__):
				if Extensions.is_marked(i):
					print("[" + terminal.__bold__ + i + terminal.__normal__ + "]", end=" ")
				else:
					print (i, end=" ")
			print("")

	def output_xml(self):
		if __located_extensions__:
			message_xml = "\t\t<message>" + _(EXTENSIONS_INFO_TEXT) + "</message>\n"
			used_extensions_xml = ""
			unused_extensions_xml = ""

			for i in sorted(__located_extensions__):
				if Extensions.is_marked(i):
					used_extensions_xml += "\t\t\t<extension>" + i + "</extension>\n"
				else:
					unused_extensions_xml += "\t\t\t<extension>" + i + "</extension>\n"

			print("\t<extensions>\n" + message_xml + "\t\t<used>\n" + used_extensions_xml + "\t\t</used>\n" +
			      "\t\t<unused>\n" + unused_extensions_xml + "\t\t</unused>\n" + "\t</extensions>")
