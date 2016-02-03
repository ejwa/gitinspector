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
from changes import FileDiff
import comment
import datetime
import extensions
import filtering
import format
import gravatar
import interval
import json
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
	skew = 0 # Used when calculating average code age.
	comments = 0

__thread_lock__ = threading.BoundedSemaphore(NUM_THREADS)
__blame_lock__ = threading.Lock()

AVG_DAYS_PER_MONTH = 30.4167

class BlameThread(threading.Thread):
	def __init__(self, useweeks, changes, blame_command, extension, blames, filename):
		__thread_lock__.acquire() # Lock controlling the number of threads running
		threading.Thread.__init__(self)

		self.useweeks = useweeks
		self.changes = changes
		self.blame_command = blame_command
		self.extension = extension
		self.blames = blames
		self.filename = filename

		self.is_inside_comment = False

	def __clear_blamechunk_info__(self):
		self.blamechunk_email = None
		self.blamechunk_is_last = False
		self.blamechunk_is_prior = False
		self.blamechunk_revision = None
		self.blamechunk_time = None

	def __handle_blamechunk_content__(self, content):
		author = None
		(comments, self.is_inside_comment) = comment.handle_comment_block(self.is_inside_comment, self.extension, content)

		if self.blamechunk_is_prior and interval.get_since():
			return
		try:
			author = self.changes.get_latest_author_by_email(self.blamechunk_email)
		except KeyError:
			return

		if not filtering.set_filtered(author, "author") and not \
		       filtering.set_filtered(self.blamechunk_email, "email") and not \
		       filtering.set_filtered(self.blamechunk_revision, "revision"):

			__blame_lock__.acquire() # Global lock used to protect calls from here...

			if self.blames.get((author, self.filename), None) == None:
				self.blames[(author, self.filename)] = BlameEntry()

			self.blames[(author, self.filename)].comments += comments
			self.blames[(author, self.filename)].rows += 1

			if (self.blamechunk_time - self.changes.first_commit_date).days > 0:
				self.blames[(author, self.filename)].skew += ((self.changes.last_commit_date - self.blamechunk_time).days /
				                                             (7.0 if self.useweeks else AVG_DAYS_PER_MONTH))

			__blame_lock__.release() # ...to here.

	def run(self):
		git_blame_r = subprocess.Popen(self.blame_command, bufsize=1, stdout=subprocess.PIPE).stdout
		rows = git_blame_r.readlines()
		git_blame_r.close()

		self.__clear_blamechunk_info__()

		#pylint: disable=W0201
		for j in range(0, len(rows)):
			row = rows[j].decode("utf-8", "replace").strip()
			keyval = row.split(" ", 2)

			if self.blamechunk_is_last:
				self.__handle_blamechunk_content__(row)
				self.__clear_blamechunk_info__()
			elif keyval[0] == "boundary":
				self.blamechunk_is_prior = True
			elif keyval[0] == "author-mail":
				self.blamechunk_email = keyval[1].lstrip("<").rstrip(">")
			elif keyval[0] == "author-time":
				self.blamechunk_time = datetime.date.fromtimestamp(int(keyval[1]))
			elif keyval[0] == "filename":
				self.blamechunk_is_last = True
			elif Blame.is_revision(keyval[0]):
				self.blamechunk_revision = keyval[0]

		__thread_lock__.release() # Lock controlling the number of threads running

PROGRESS_TEXT = N_("Checking how many rows belong to each author (Progress): {0:.0f}%")

class Blame:
	def __init__(self, hard, useweeks, changes):
		self.blames = {}
		ls_tree_r = subprocess.Popen(["git", "ls-tree", "--name-only", "-r", interval.get_ref()], bufsize=1,
		                             stdout=subprocess.PIPE).stdout
		lines = ls_tree_r.readlines()
		ls_tree_r.close()

		for i, row in enumerate(lines):
			row = row.strip().decode("unicode_escape", "ignore")
			row = row.encode("latin-1", "replace")
			row = row.decode("utf-8", "replace").strip("\"").strip("'").strip()

			if FileDiff.get_extension(row) in extensions.get_located() and FileDiff.is_valid_extension(row) and not \
			   filtering.set_filtered(FileDiff.get_filename(row)):
				blame_command = filter(None, ["git", "blame", "--line-porcelain", "-w"] + \
						(["-C", "-C", "-M"] if hard else []) +
				                [interval.get_since(), interval.get_ref(), "--", row])
				thread = BlameThread(useweeks, changes, blame_command, FileDiff.get_extension(row),
				                     self.blames, row.strip())
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
	def is_revision(string):
		revision = re.search("([0-9a-f]{40})", string)

		if revision == None:
			return False

		return revision.group(1).strip()

	@staticmethod
	def get_stability(author, blamed_rows, changes):
		if author in changes.get_authorinfo_list():
			author_insertions = changes.get_authorinfo_list()[author].insertions
			return 100 if author_insertions == 0 else 100.0 * blamed_rows / author_insertions
		return 100

	@staticmethod
	def get_time(string):
		time = re.search(" \(.*?(\d\d\d\d-\d\d-\d\d)", string)
		return time.group(1).strip()

	def get_summed_blames(self):
		summed_blames = {}
		for i in self.blames.items():
			if summed_blames.get(i[0][0], None) == None:
				summed_blames[i[0][0]] = BlameEntry()

			summed_blames[i[0][0]].rows += i[1].rows
			summed_blames[i[0][0]].skew += i[1].skew
			summed_blames[i[0][0]].comments += i[1].comments

		return summed_blames

__blame__ = None

def get(hard, useweeks, changes):
	global __blame__
	if __blame__ == None:
		__blame__ = Blame(hard, useweeks, changes)

	return __blame__

BLAME_INFO_TEXT = N_("Below are the number of rows from each author that have survived and are still "
                     "intact in the current revision")

class BlameOutput(Outputable):
	def __init__(self, changes, hard, useweeks):
		if format.is_interactive_format():
			print("")

		self.changes = changes
		self.hard = hard
		self.useweeks = useweeks
		get(self.hard, self.useweeks, self.changes)
		Outputable.__init__(self)

	def output_html(self):
		blame_xml = "<div><div class=\"box\">"
		blame_xml += "<p>" + _(BLAME_INFO_TEXT) + ".</p><div><table id=\"blame\" class=\"git\">"
		blame_xml += "<thead><tr> <th>{0}</th> <th>{1}</th> <th>{2}</th> <th>{3}</th> <th>{4}</th> </tr></thead>".format(
		             _("Author"), _("Rows"), _("Stability"), _("Age"), _("% in comments"))
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
			blame_xml += "<td>" + ("{0:.1f}".format(Blame.get_stability(entry[0], entry[1].rows, self.changes)) + "</td>")
			blame_xml += "<td>" + "{0:.1f}".format(float(entry[1].skew) / entry[1].rows) + "</td>"
			blame_xml += "<td>" + "{0:.2f}".format(100.0 * entry[1].comments / entry[1].rows) + "</td>"
			blame_xml += "<td style=\"display: none\">" + work_percentage + "</td>"
			blame_xml += "</tr>"
			chart_data += "{{label: {0}, data: {1}}}".format(json.dumps(entry[0]), work_percentage)

			if blames[-1] != entry:
				chart_data += ", "

		blame_xml += "<tfoot><tr> <td colspan=\"5\">&nbsp;</td> </tr></tfoot></tbody></table>"
		blame_xml += "<div class=\"chart\" id=\"blame_chart\"></div></div>"
		blame_xml += "<script type=\"text/javascript\">"
		blame_xml += "    blame_plot = $.plot($(\"#blame_chart\"), [{0}], {{".format(chart_data)
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
		terminal.printb(terminal.ljust(_("Author"), 21) + terminal.rjust(_("Rows"), 10) + terminal.rjust(_("Stability"), 15) +
		                terminal.rjust(_("Age"), 13) + terminal.rjust(_("% in comments"), 20))

		for i in sorted(__blame__.get_summed_blames().items()):
			print(terminal.ljust(i[0], 20)[0:20 - terminal.get_excess_column_count(i[0])], end=" ")
			print(str(i[1].rows).rjust(10), end=" ")
			print("{0:.1f}".format(Blame.get_stability(i[0], i[1].rows, self.changes)).rjust(14), end=" ")
			print("{0:.1f}".format(float(i[1].skew) / i[1].rows).rjust(12), end=" ")
			print("{0:.2f}".format(100.0 * i[1].comments / i[1].rows).rjust(19))

	def output_xml(self):
		message_xml = "\t\t<message>" + _(BLAME_INFO_TEXT) + "</message>\n"
		blame_xml = ""

		for i in sorted(__blame__.get_summed_blames().items()):
			author_email = self.changes.get_latest_email_by_author(i[0])

			name_xml = "\t\t\t\t<name>" + i[0] + "</name>\n"
			gravatar_xml = "\t\t\t\t<gravatar>" + gravatar.get_url(author_email) + "</gravatar>\n"
			rows_xml = "\t\t\t\t<rows>" + str(i[1].rows) + "</rows>\n"
			stability_xml = ("\t\t\t\t<stability>" + "{0:.1f}".format(Blame.get_stability(i[0], i[1].rows,
			                 self.changes)) + "</stability>\n")
			age_xml = ("\t\t\t\t<age>" + "{0:.1f}".format(float(i[1].skew) / i[1].rows) + "</age>\n")
			percentage_in_comments_xml = ("\t\t\t\t<percentage-in-comments>" + "{0:.2f}".format(100.0 * i[1].comments / i[1].rows) +
			                              "</percentage-in-comments>\n")
			blame_xml += ("\t\t\t<author>\n" + name_xml + gravatar_xml + rows_xml + stability_xml + age_xml +
			             percentage_in_comments_xml + "\t\t\t</author>\n")

		print("\t<blame>\n" + message_xml + "\t\t<authors>\n" + blame_xml + "\t\t</authors>\n\t</blame>")
