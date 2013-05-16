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
from changes import FileDiff
import codecs
import comment
import filtering
import missing
import subprocess

__metric_eloc__ = {"java": 500, "c": 500, "cpp": 500, "h": 300, "hpp": 300, "py": 500, "glsl": 1000,
                   "rb": 500, "js": 500, "sql": 1000, "xml": 1000}

class MetricsLogic:
	def __init__(self):
		self.eloc = {}
		ls_tree_r = subprocess.Popen("git ls-tree --name-only -r HEAD", shell=True, bufsize=1, stdout=subprocess.PIPE).stdout

		for i in ls_tree_r.readlines():
			i = codecs.getdecoder("unicode_escape")(i.strip())[0]
			i = i.encode("latin-1", "replace")
			i = i.decode("utf-8", "replace").strip("\"").strip("'").strip()

			if FileDiff.is_valid_extension(i) and not filtering.set_filtered(FileDiff.get_filename(i)):
				if not missing.add(i):
					file_r = open(i.strip(), "rb")
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
			if is_inside_comment and comment.has_comment_end(extension, j):
				is_inside_comment = False
			elif comment.has_comment_begining(extension, j):
				is_inside_comment = True

			if not is_inside_comment and not comment.is_comment(extension, j):
				eloc_counter += 1

		return eloc_counter

__eloc_info_text__ = "The following files are suspiciously big (in order of severity)"
__metrics_missing_info_text__ = "No metrics violations were found in the repository"

class Metrics(Outputable):
	def output_text(self):
		metrics_logic = MetricsLogic()

		if not metrics_logic.eloc:
			print("\n" + __metrics_missing_info_text__ + ".")
		else:
			print("\n" + __eloc_info_text__ + ":")
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				print(i[1] + " (" + str(i[0]) + " eloc)")

	def output_html(self):
		metrics_logic = MetricsLogic()
		metrics_xml = "<div><div class=\"box\">"

		if not metrics_logic.eloc:
			metrics_xml += "<p>" + __metrics_missing_info_text__ + ".</p>"
		else:
			metrics_xml += "<p>" + __eloc_info_text__ + ".</p>"
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				metrics_xml += "<p>" + i[1] + " (" + str(i[0]) + " eloc)</p>"

		metrics_xml += "</div></div>"
		print(metrics_xml)

	def output_xml(self):
		metrics_logic = MetricsLogic()

		if not metrics_logic.eloc:
			print("\t<metrics>\n\t\t<message>" + __metrics_missing_info_text__ + "</message>\n\t</metrics>")
		else:
			eloc_xml = ""
			for i in sorted(set([(j, i) for (i, j) in metrics_logic.eloc.items()]), reverse = True):
				eloc_xml += "\t\t\t\t\t<violation>\n"
				eloc_xml += "\t\t\t\t\t\t<file-name>" + i[1] + "</file-name>\n"
				eloc_xml += "\t\t\t\t\t\t<lines-of-code>" + str(i[0]) + "</lines-of-code>\n"
				eloc_xml += "\t\t\t\t\t</violation>\n"

			print("\t\t<metrics>\n\t\t\t<eloc>\n\t\t\t\t<message>" + __eloc_info_text__ +
			      "</message>\n\t\t\t\t<violations>\n" + eloc_xml + "\t\t\t\t</violations>\n\t\t\t</eloc>\n\t\t</metrics>")
