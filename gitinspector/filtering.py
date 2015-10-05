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
import re
import subprocess
import terminal
import textwrap

__filters__ = {"file": [set(), set()], "author": [set(), set()], "email": [set(), set()], "revision": [set(), set()],
               "message" : [set(), None]}

class InvalidRegExpError(ValueError):
	def __init__(self, msg):
		super(InvalidRegExpError, self).__init__(msg)
		self.msg = msg

def get():
	return __filters__

def __add_one__(string):
	for i in __filters__:
		if (i + ":").lower() == string[0:len(i) + 1].lower():
			__filters__[i][0].add(string[len(i) + 1:])
			return
	__filters__["file"][0].add(string)

def add(string):
	rules = string.split(",")
	for rule in rules:
		__add_one__(rule)

def clear():
	for i in __filters__:
		__filters__[i][0] = set()

def get_filered(filter_type="file"):
	return __filters__[filter_type][1]

def has_filtered():
	for i in __filters__:
		if __filters__[i][1]:
			return True
	return False

def __find_commit_message__(sha):
	git_show_r = subprocess.Popen(filter(None, ["git", "show", "-s", "--pretty=%B", "-w", sha]), bufsize=1,
	                              stdout=subprocess.PIPE).stdout

	commit_message = git_show_r.read()
	git_show_r.close()

	commit_message = commit_message.strip().decode("unicode_escape", "ignore")
	commit_message = commit_message.encode("latin-1", "replace")
	return commit_message.decode("utf-8", "replace")

def set_filtered(string, filter_type="file"):
	string = string.strip()

	if len(string) > 0:
		for i in __filters__[filter_type][0]:
			search_for = string

			if filter_type == "message":
				search_for = __find_commit_message__(string)
			try:
				if re.search(i, search_for) != None:
					if filter_type == "message":
						__add_one__("revision:" + string)
					else:
						__filters__[filter_type][1].add(string)
					return True
			except:
				raise InvalidRegExpError(_("invalid regular expression specified"))
	return False

FILTERING_INFO_TEXT = N_("The following files were excluded from the statistics due to the specified exclusion patterns")
FILTERING_AUTHOR_INFO_TEXT = N_("The following authors were excluded from the statistics due to the specified exclusion patterns")
FILTERING_EMAIL_INFO_TEXT = N_("The authors with the following emails were excluded from the statistics due to the specified " \
                               "exclusion patterns")
FILTERING_COMMIT_INFO_TEXT = N_("The following commit revisions were excluded from the statistics due to the specified " \
                                "exclusion patterns")

class Filtering(Outputable):
	@staticmethod
	def __output_html_section__(info_string, filtered):
		filtering_xml = ""

		if filtered:
			filtering_xml += "<p>" + info_string + "."+ "</p>"

			for i in filtered:
				filtering_xml += "<p>" + i + "</p>"

		return filtering_xml

	def output_html(self):
		if has_filtered():
			filtering_xml = "<div><div class=\"box\">"
			Filtering.__output_html_section__(_(FILTERING_INFO_TEXT), __filters__["file"][1])
			Filtering.__output_html_section__(_(FILTERING_AUTHOR_INFO_TEXT), __filters__["author"][1])
			Filtering.__output_html_section__(_(FILTERING_EMAIL_INFO_TEXT), __filters__["email"][1])
			Filtering.__output_html_section__(_(FILTERING_COMMIT_INFO_TEXT), __filters__["revision"][1])
			filtering_xml += "</div></div>"

			print(filtering_xml)

	@staticmethod
	def __output_text_section__(info_string, filtered):
		if filtered:
			print("\n" + textwrap.fill(info_string + ":", width=terminal.get_size()[0]))

			for i in filtered:
				(width, _unused) = terminal.get_size()
				print("...%s" % i[-width+3:] if len(i) > width else i)

	def output_text(self):
		Filtering.__output_text_section__(_(FILTERING_INFO_TEXT), __filters__["file"][1])
		Filtering.__output_text_section__(_(FILTERING_AUTHOR_INFO_TEXT), __filters__["author"][1])
		Filtering.__output_text_section__(_(FILTERING_EMAIL_INFO_TEXT), __filters__["email"][1])
		Filtering.__output_text_section__(_(FILTERING_COMMIT_INFO_TEXT), __filters__["revision"][1])

	@staticmethod
	def __output_xml_section__(info_string, filtered, container_tagname):
		if filtered:
			message_xml = "\t\t\t<message>" +info_string + "</message>\n"
			filtering_xml = ""

			for i in filtered:
				filtering_xml += "\t\t\t\t<entry>".format(container_tagname) + i + "</entry>\n".format(container_tagname)

			print("\t\t<{0}>".format(container_tagname))
			print(message_xml + "\t\t\t<entries>\n" + filtering_xml + "\t\t\t</entries>\n")
			print("\t\t</{0}>".format(container_tagname))

	def output_xml(self):
		if has_filtered():
			print("\t<filtering>")
			Filtering.__output_xml_section__(_(FILTERING_INFO_TEXT), __filters__["file"][1], "files")
			Filtering.__output_xml_section__(_(FILTERING_AUTHOR_INFO_TEXT), __filters__["author"][1], "authors")
			Filtering.__output_xml_section__(_(FILTERING_EMAIL_INFO_TEXT), __filters__["email"][1], "emails")
			Filtering.__output_xml_section__(_(FILTERING_COMMIT_INFO_TEXT), __filters__["revision"][1], "revision")
			print("\t</filtering>")
