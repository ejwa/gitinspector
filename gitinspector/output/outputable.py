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
from .. import format

class Outputable(object):
	def output_html(self):
		raise NotImplementedError(_("HTML output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

	def output_json(self):
		raise NotImplementedError(_("JSON output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

	def output_text(self):
		raise NotImplementedError(_("Text output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

	def output_xml(self):
		raise NotImplementedError(_("XML output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

def output(outputable):
	if format.get_selected() == "html" or format.get_selected() == "htmlembedded":
		outputable.output_html()
	elif format.get_selected() == "json":
		outputable.output_json()
	elif format.get_selected() == "text":
		outputable.output_text()
	else:
		outputable.output_xml()
