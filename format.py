# coding: utf-8
#
# Copyright © 2012 Ejwa Software. All rights reserved.
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
import os
import terminal

__available_formats__ = ["html", "text", "xml"]
__default_format__ = __available_formats__[1]
__selected_format__ = __default_format__

class InvalidFormatError(Exception):
	pass

def select(format):
	global __selected_format__
	__selected_format__ = format

	return format in __available_formats__

def is_interactive_format():
	global __selected_format__
	return __selected_format__ == "text"

def output_header():
	if __selected_format__ == "html":
		pass
	elif __selected_format__ == "text":
		pass
	else:
		print("<gitinspector>")

def output_footer():
	if __selected_format__ == "html":
		pass
	elif __selected_format__ == "text":
		pass
	else:
		print("</gitinspector>")
 
def call_output_function(html_function, text_function, xml_function, *parameters):
	if __selected_format__ == "html":
		template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "html.template")
		file_r = open(template_path, "rb")
		template = file_r.read().decode("utf-8", "replace")
		html_function(template, *parameters)
	elif __selected_format__ == "text":
		text_function(*parameters)
	else:
		xml_function(*parameters)
