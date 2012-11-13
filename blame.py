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
from changes import FileDiff
import comment
import filtering
import format
import missing
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
	def __init__(self, blame_string, extension, blames, filename):
		__thread_lock__.acquire() # Lock controlling the number of threads running
		threading.Thread.__init__(self)

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
				author = Blame.get_author(j)
				content = Blame.get_content(j)
				__blame_lock__.acquire() # Global lock used to protect calls from here...

				if self.blames.get((author, self.filename), None) == None:
					self.blames[(author, self.filename)] = BlameEntry()

				if comment.is_comment(self.extension, content):
					self.blames[(author, self.filename)].comments += 1
				if is_inside_comment:
					if comment.has_comment_end(self.extension, content):
						is_inside_comment = False
					else:
						self.blames[(author, self.filename)].comments += 1
				elif comment.has_comment_begining(self.extension, content):
					is_inside_comment = True

				self.blames[(author, self.filename)].rows += 1
				__blame_lock__.release() # ...to here.

		git_blame_r.close()
		__thread_lock__.release() # Lock controlling the number of threads running

class Blame:
	def __init__(self, hard):
		self.blames = {}
		ls_tree_r = subprocess.Popen("git ls-tree --name-only -r HEAD", shell=True, bufsize=1, stdout=subprocess.PIPE).stdout
		lines = ls_tree_r.readlines()

		for i, row in enumerate(lines):
			row = row.decode("utf-8", "replace")
			if FileDiff.is_valid_extension(row) and not filtering.set_filtered(FileDiff.get_filename(row)):
				if not missing.add(row.strip()):
					blame_string = "git blame -w {0} \"".format("-C -C -M" if hard else "") + row.strip() + "\""
					thread = BlameThread(blame_string, FileDiff.get_extension(row), self.blames, row.strip())
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
			print("\bChecking how many rows belong to each author (Progress): {0:.0f}%".format(100 * pos / length), end="")
			sys.stdout.flush()

	@staticmethod
	def is_blame_line(string):
		return string.find(" (") != -1

	@staticmethod
	def get_author(string):
		author = re.search(" \((.*?)\d\d\d\d-\d\d-\d\d", string)
		return re.sub("[^\w ]", "", author.group(1)).strip()

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

def get(hard):
	global __blame__
	if __blame__ == None:
		__blame__ = Blame(hard)

	return __blame__

__blame_info_text__ = ("Below are the number of rows from each author that have survived and are still "
                       "intact in the current revision")

def output_html(hard):
	print("HTML output not yet supported.")

def output_text(hard):
	print("")
	get(hard)

	if hard and sys.stdout.isatty():
		terminal.clear_row()

	print(textwrap.fill(__blame_info_text__ + ":", width=terminal.get_size()[0]) + "\n")
	terminal.printb("Author".ljust(21) + "Rows".rjust(10) + "% in comments".rjust(16))
	for i in sorted(__blame__.get_summed_blames().items()):
		print(i[0].ljust(20)[0:20], end=" ")
		print(str(i[1].rows).rjust(10), end=" ")
		print("{0:.2f}".format(100.0 * i[1].comments / i[1].rows).rjust(15))

def output_xml(hard):
	get(hard)

	message_xml = "\t\t<message>" + __blame_info_text__ + "</message>\n"
	blame_xml = ""

	for i in sorted(__blame__.get_summed_blames().items()):
		name_xml = "\t\t\t\t<name>" + i[0] + "</name>\n"
		rows_xml = "\t\t\t\t<rows>" + str(i[1].rows) + "</rows>\n"
		percentage_in_comments_xml = ("\t\t\t\t<percentage-in-comments>" + "{0:.2f}".format(100.0 * i[1].comments / i[1].rows) +
		                              "</percentage-in-comments>\n")
		blame_xml += "\t\t\t<author>\n" + name_xml + rows_xml + percentage_in_comments_xml + "\t\t\t</author>\n"

	print("\t<blame>\n" + message_xml + "\t\t<authors>\n" + blame_xml + "\t\t</authors>\n\t</blame>")
