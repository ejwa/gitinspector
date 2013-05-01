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
import interval
import os
import subprocess
import terminal
import textwrap

__checkout_missing__ = False
__missing_files__ =  set()

def add(file_name):
	if not interval.has_interval() and not os.path.exists(file_name):
		if __checkout_missing__:
			subprocess.call("git checkout \"" + file_name.strip() + "\"", shell=True)
		else:
			__missing_files__.add(file_name)
			return True
	return False

def set_checkout_missing(checkout):
	global __checkout_missing__
	__checkout_missing__ = checkout

__missing_info_text__ = ("The following files were missing in the repository and were therefore not "
                         "completely included in the statistical analysis. To include them, you can "
                         "either checkout manually using git or use the -c option in gitinspector")

class Missing(Outputable):
	def output_html(self):
		if __missing_files__:
			missing_xml = "<div><div class=\"box\">"
			missing_xml += "<p>" + __missing_info_text__ + ".</p>"

			for missing in __missing_files__:
				missing_xml += "<p class=\"error\">" + missing + "</p>"

			missing_xml += "</div></div>"
			print(missing_xml)

	def output_text(self):
		if __missing_files__:
			print("\n" + textwrap.fill(__missing_info_text__ + ":", width=terminal.get_size()[0]))

			for missing in __missing_files__:
				(width, _) = terminal.get_size()
				print("...%s" % missing[-width+3:] if len(missing) > width else missing)

	def output_xml(self):
		if __missing_files__:
			message_xml = "\t\t<message>" + __missing_info_text__ + "</message>\n"
			missing_xml = ""

			for missing in __missing_files__:
				missing_xml += "\t\t\t<file>" + missing + "</file>\n"

			print("\t<missing>\n" + message_xml + "\t\t<files>\n" + missing_xml + "\t\t</files>\n\t</missing>")
