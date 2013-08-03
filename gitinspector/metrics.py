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
from changes import FileDiff
import comment
import filtering
import interval
import subprocess

__metric_eloc__ = {"java": 500, "c": 500, "cpp": 500, "h": 300, "hpp": 300, "php": 500, "py": 500, "glsl": 1000,
                   "rb": 500, "js": 500, "sql": 1000, "xml": 1000}

class MetricsLogic:
	def __init__(self):
		self.eloc = {}
		ls_tree_r = subprocess.Popen("git ls-tree --name-only -r " + interval.get_ref(), shell=True, bufsize=1,
		                             stdout=subprocess.PIPE).stdout

		for i in ls_tree_r.readlines():
			i = i.strip().decode("unicode_escape", "ignore")
			i = i.encode("latin-1", "replace")
			i = i.decode("utf-8", "replace").strip("\"").strip("'").strip()

			if FileDiff.is_valid_extension(i) and not filtering.set_filtered(FileDiff.get_filename(i)):
				file_r = subprocess.Popen("git show " + interval.get_ref() + ":" + i.strip(), shell=True, bufsize=1,
				                          stdout=subprocess.PIPE).stdout

				extension = FileDiff.get_extension(i)
				lines = MetricsLogic.get_eloc(file_r, extension)

				if __metric_eloc__.get(extension, None) != None and __metric_eloc__[extension] < lines:
					self.eloc[i.strip()] = lines

	@staticmethod
	def get_eloc(file_r, extension):
		is_inside_comment = False
		eloc_counter = 0

		for j in file_r.readlines():
			j = j.decode("utf-8", "replace")
			(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, j)

			if not is_inside_comment and not comment.is_comment(extension, j):
				eloc_counter += 1

		return eloc_counter

ELOC_INFO_TEXT = N_("The following files are suspiciously big (in order of severity)")
METRICS_MISSING_INFO_TEXT = N_("No metrics violations were found in the repository")

class Metrics(Outputable):
	def output_text(self):
		metrics_logic = MetricsLogic()

		if not metrics_logic.eloc:
			print("\n" + _(METRICS_MISSING_INFO_TEXT) + ".")
		else:
			print("\n" + _(ELOC_INFO_TEXT) + ":")
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				print(i[1] + " (" + str(i[0]) + " eloc)")

	def output_html(self):
		metrics_logic = MetricsLogic()
		metrics_xml = "<div><div class=\"box\">"

		if not metrics_logic.eloc:
			metrics_xml += "<p>" + _(METRICS_MISSING_INFO_TEXT) + ".</p>"
		else:
			metrics_xml += "<p>" + _(ELOC_INFO_TEXT) + ".</p>"
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				metrics_xml += "<p>" + i[1] + " (" + str(i[0]) + " eloc)</p>"

		metrics_xml += "</div></div>"
		print(metrics_xml)

	def output_xml(self):
		metrics_logic = MetricsLogic()

		if not metrics_logic.eloc:
			print("\t<metrics>\n\t\t<message>" + _(METRICS_MISSING_INFO_TEXT) + "</message>\n\t</metrics>")
		else:
			eloc_xml = ""
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				eloc_xml += "\t\t\t\t\t<violation>\n"
				eloc_xml += "\t\t\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
				eloc_xml += "\t\t\t\t\t\t<lines-of-code>" + str(i[0]) + "</lines-of-code>\n"
				eloc_xml += "\t\t\t\t\t</violation>\n"

			print("\t\t<metrics>\n\t\t\t<eloc>\n\t\t\t\t<message>" + _(ELOC_INFO_TEXT) +
			      "</message>\n\t\t\t\t<violations>\n" + eloc_xml + "\t\t\t\t</violations>\n\t\t\t</eloc>\n\t\t</metrics>")
