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
import changes
import filtering
import format
import gravatar
import interval
import multiprocessing
import re
import subprocess
import sys
import terminal
import textwrap
import threading

NUM_THREADS = multiprocessing.cpu_count()

class BlameEntry:
	rows = 0
	comments = 0

__thread_lock__ = threading.BoundedSemaphore(NUM_THREADS)
__blame_lock__ = threading.Lock()

class BlameThread(threading.Thread):
	def __init__(self, changes, blame_string, extension, blames, filename):
		__thread_lock__.acquire() # Lock controlling the number of threads running
		threading.Thread.__init__(self)

		self.changes = changes
		self.blame_string = blame_string
		self.extension = extension
		self.blames = blames
		self.filename = filename

	def run(self):
		git_blame_r = subprocess.Popen(self.blame_string, shell=True, bufsize=1, stdout=subprocess.PIPE).stdout
		is_inside_comment = False

		for j in git_blame_r.readlines():
			j = j.decode("utf-8", "replace")
			if Blame.is_blame_line(j):
				content = Blame.get_content(j)
				(comments, is_inside_comment) = comment.handle_comment_block(is_inside_comment, self.extension, content)

				if Blame.is_prior(j) and interval.get_since():
					continue

				email = Blame.get_author_email(j)
				author = self.changes.get_latest_author_by_email(email)
				__blame_lock__.acquire() # Global lock used to protect calls from here...

				if not filtering.set_filtered(author, "author") and not filtering.set_filtered(email, "email"):
					if self.blames.get((author, self.filename), None) == None:
						self.blames[(author, self.filename)] = BlameEntry()

					self.blames[(author, self.filename)].comments += comments
					self.blames[(author, self.filename)].rows += 1

				__blame_lock__.release() # ...to here.

		git_blame_r.close()
		__thread_lock__.release() # Lock controlling the number of threads running

PROGRESS_TEXT = N_("Checking how many rows belong to each author (Progress): {0:.0f}%")

class Blame:
	def __init__(self, hard, changes):
		self.blames = {}
		ls_tree_r = subprocess.Popen("git ls-tree --name-only -r " + interval.get_ref(), shell=True, bufsize=1,
		                             stdout=subprocess.PIPE).stdout
		lines = ls_tree_r.readlines()

		for i, row in enumerate(lines):
			row = row.strip().decode("unicode_escape", "ignore")
			row = row.encode("latin-1", "replace")
			row = row.decode("utf-8", "replace").strip("\"").strip("'").strip()

			if FileDiff.is_valid_extension(row) and not filtering.set_filtered(FileDiff.get_filename(row)):
				blame_string = "git blame -e -w {0} ".format("-C -C -M" if hard else "") + \
				               interval.get_since() + interval.get_ref() + " -- \"" + row + "\""
				thread = BlameThread(changes, blame_string, FileDiff.get_extension(row), self.blames, row.strip())
				thread.daemon = True
				thread.start()

				if hard:
					Blame.output_progress(i, len(lines))

		# Make sure all threads have completed.
		for i in range(0, NUM_THREADS):
			__thread_lock__.acquire()

	@staticmethod
	def output_progress(pos, length):
		if sys.stdout.isatty() and format.is_interactive_format():
			terminal.clear_row()
			print(_(PROGRESS_TEXT).format(100 * pos / length), end="")
			sys.stdout.flush()

	@staticmethod
	def is_blame_line(string):
		return string.find(" (") != -1

	@staticmethod
	def is_prior(string):
		return string[0] == "^"

	@staticmethod
	def get_author_email(string):
		author_email = re.search(" \((.*?)\d\d\d\d-\d\d-\d\d", string)
		return author_email.group(1).strip().lstrip("<").rstrip(">")

	@staticmethod
	def get_content(string):
		content = re.search(" \d+\)(.*)", string)
		return content.group(1).lstrip()

	def get_summed_blames(self):
		summed_blames = {}
		for i in self.blames.items():
			if summed_blames.get(i[0][0], None) == None:
				summed_blames[i[0][0]] = BlameEntry()

			summed_blames[i[0][0]].rows += i[1].rows
			summed_blames[i[0][0]].comments += i[1].comments

		return summed_blames

__blame__ = None

def get(hard, changes):
	global __blame__
	if __blame__ == None:
		__blame__ = Blame(hard, changes)

	return __blame__

BLAME_INFO_TEXT = N_("Below are the number of rows from each author that have survived and are still "
                     "intact in the current revision")

class BlameOutput(Outputable):
	def __init__(self, hard):
		if format.is_interactive_format():
			print("")

		self.hard = hard
		self.changes = changes.get(hard)
		get(self.hard, self.changes)
		Outputable.__init__(self)

	def output_html(self):
		blame_xml = "<div><div class=\"box\">"
		blame_xml += "<p>" + _(BLAME_INFO_TEXT) + ".</p><div><table id=\"blame\" class=\"git\">"
		blame_xml += "<thead><tr> <th>{0}</th> <th>{1}</th> <th>{2}</th> </tr></thead>".format(_("Author"),
		             _("Rows"), _("% in comments"))
		blame_xml += "<tbody>"
		chart_data = ""
		blames = sorted(__blame__.get_summed_blames().items())
		total_blames = 0

		for i in blames:
			total_blames += i[1].rows

		for i, entry in enumerate(blames):
			work_percentage = str("{0:.2f}".format(100.0 * entry[1].rows / total_blames))
			blame_xml += "<tr " + ("class=\"odd\">" if i % 2 == 1 else ">")

			if format.get_selected() == "html":
				author_email = self.changes.get_latest_email_by_author(entry[0])
				blame_xml += "<td><img src=\"{0}\"/>{1}</td>".format(gravatar.get_url(author_email), entry[0])
			else:
				blame_xml += "<td>" + entry[0] + "</td>"

			blame_xml += "<td>" + str(entry[1].rows) + "</td>"
			blame_xml += "<td>" + "{0:.2f}".format(100.0 * entry[1].comments / entry[1].rows) + "</td>"
			blame_xml += "<td style=\"display: none\">" + work_percentage + "</td>"
			blame_xml += "</tr>"
			chart_data += "{{label: \"{0}\", data: {1}}}".format(entry[0], work_percentage)

			if blames[-1] != entry:
				chart_data += ", "

		blame_xml += "<tfoot><tr> <td colspan=\"3\">&nbsp;</td> </tr></tfoot></tbody></table>"
		blame_xml += "<div class=\"chart\" id=\"blame_chart\"></div></div>"
		blame_xml += "<script type=\"text/javascript\">"
		blame_xml += "    $.plot($(\"#blame_chart\"), [{0}], {{".format(chart_data)
		blame_xml += "        series: {"
		blame_xml += "            pie: {"
		blame_xml += "                innerRadius: 0.4,"
		blame_xml += "                show: true,"
		blame_xml += "                combine: {"
		blame_xml += "                    threshold: 0.01,"
		blame_xml += "                    label: \"" + _("Minor Authors") + "\""
		blame_xml += "                }"
		blame_xml += "            }"
		blame_xml += "        }, grid: {"
		blame_xml += "            hoverable: true"
		blame_xml += "        }"
		blame_xml += "    });"
		blame_xml += "</script></div></div>"

		print(blame_xml)

	def output_text(self):
		if sys.stdout.isatty() and format.is_interactive_format():
			terminal.clear_row()

		print(textwrap.fill(_(BLAME_INFO_TEXT) + ":", width=terminal.get_size()[0]) + "\n")
		terminal.printb(_("Author").ljust(21) + _("Rows").rjust(10) + _("% in comments").rjust(20))

		for i in sorted(__blame__.get_summed_blames().items()):
			print(i[0].ljust(20)[0:20], end=" ")
			print(str(i[1].rows).rjust(10), end=" ")
			print("{0:.2f}".format(100.0 * i[1].comments / i[1].rows).rjust(19))

	def output_xml(self):
		message_xml = "\t\t<message>" + _(BLAME_INFO_TEXT) + "</message>\n"
		blame_xml = ""

		for i in sorted(__blame__.get_summed_blames().items()):
			author_email = self.changes.get_latest_email_by_author(i[0])

			name_xml = "\t\t\t\t<name>" + i[0] + "</name>\n"
			gravatar_xml = "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
			rows_xml = "\t\t\t\t<rows>" + str(i[1].rows) + "</rows>\n"
			percentage_in_comments_xml = ("\t\t\t\t<percentage-in-comments>" + "{0:.2f}".format(100.0 * i[1].comments / i[1].rows) +
			                              "</percentage-in-comments>\n")
			blame_xml += "\t\t\t<author>\n" + name_xml + gravatar_xml + rows_xml + percentage_in_comments_xml + "\t\t\t</author>\n"

		print("\t<blame>\n" + message_xml + "\t\t<authors>\n" + blame_xml + "\t\t</authors>\n\t</blame>")
