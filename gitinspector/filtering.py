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
from __future__ import unicode_literals
from localization import N_
from outputable import Outputable
import re
import terminal
import textwrap

__filters__ = []
__filtered_files__ = set()

class InvalidRegExpError(ValueError):
	def __init__(self, msg):
		super(InvalidRegExpError, self).__init__(msg)
		self.msg = msg

def get():
	return __filters__

def add(string):
	__filters__.append(string)

def clear():
	global __filters__
	__filters__ = []

def get_filered():
	return __filtered_files__

def set_filtered(file_name):
	string = file_name.strip()

	if len(string) > 0:
		for i in __filters__:
			try:
				if re.search(i, string) != None:
					__filtered_files__.add(string)
					return True
			except:
				raise InvalidRegExpError(_("invalid regular expression specified"))
	return False

FILTERING_INFO_TEXT = N_("The following files were excluded from the statistics due to the specified exclusion patterns")

class Filtering(Outputable):
	def output_html(self):
		if __filtered_files__:
			filtering_xml = "<div><div class=\"box\">"
			filtering_xml += "<p>" + _(FILTERING_INFO_TEXT) + "."+ "</p>"

			for i in __filtered_files__:
				filtering_xml += "<p>" + i + "</p>"

			filtering_xml += "</div></div>"
			print(filtering_xml)

	def output_text(self):
		if __filtered_files__:
			print("\n" + textwrap.fill(_(FILTERING_INFO_TEXT) + ":", width=terminal.get_size()[0]))

			for i in __filtered_files__:
				(width, _unused) = terminal.get_size()
				print("...%s" % i[-width+3:] if len(i) > width else i)

	def output_xml(self):
		if __filtered_files__:
			message_xml = "\t\t<message>" + _(FILTERING_INFO_TEXT) + "</message>\n"
			filtering_xml = ""

			for i in __filtered_files__:
				filtering_xml += "\t\t\t<file>" + i + "</file>\n"

			print("\t<filering>\n" + message_xml + "\t\t<files>\n" + filtering_xml + "\t\t</files>\n\t</filtering>")
