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

from changes import FileDiff
import comment
import missing
import multiprocessing
import re
import system
import sys
import terminal
import threading

class BlameEntry:
	rows = 0
	comments = 0

thread_lock = threading.BoundedSemaphore(1) # multiprocessing.cpu_count())
blame_lock = threading.Lock()

class BlameThread(threading.Thread):
	def __init__(self, repo, blame_string, extension, blames):
		thread_lock.acquire() # Lock controlling the number of threads running
		threading.Thread.__init__(self)

		self.repo = repo
		self.blame_string = blame_string
		self.extension = extension
		self.blames = blames

	def run(self):
		git_blame_r = system.run(self.repo, self.blame_string)
		is_inside_comment = False

		for j in git_blame_r.readlines():
			if Blame.is_blame_line(j):
				author = Blame.get_author(j)
				content = Blame.get_content(j)
				blame_lock.acquire() # Global lock used to protect calls from here...

				if self.blames.get(author, None) == None:
					self.blames[author] = BlameEntry()

				if comment.is_comment(self.extension, content):
					self.blames[author].comments += 1
				if is_inside_comment:
					if comment.has_comment_end(self.extension, content):
						is_inside_comment = False
					else:
						self.blames[author].comments += 1
				elif comment.has_comment_begining(self.extension, content):
					is_inside_comment = True

				self.blames[author].rows += 1
				blame_lock.release() # ...to here.

		thread_lock.release() # Lock controlling the number of threads running

class Blame:
	def __init__(self, repo, hard):
		self.blames = {}
		ls_tree_r = system.run(repo, "git ls-tree --name-only -r HEAD")
		lines = ls_tree_r.readlines()

		for i,row in enumerate(lines):
			if FileDiff.is_valid_extension(row):
				if not missing.add(repo, row.strip()):
					blame_string = "git blame -w {0} \"".format("-C -C -M" if hard else "") + row.strip() + "\""
					thread = BlameThread(repo, blame_string, FileDiff.get_extension(row), self.blames)
					thread.run() # change to start() to enable threads.

					if hard:
						Blame.output_progress(i, len(lines))

	@staticmethod
	def output_progress(pos, length):
		if sys.stdout.isatty():
			terminal.clear_row()
			print "\bChecking how many rows belong to each author (Progress): " + str(100 * pos / length) + "%",
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

def output(repo, hard):
	print ""
	blame = Blame(repo, hard)

	if hard:
		terminal.clear_row()

	print "\bBelow is the number of rows from each author that have survived and"
	print "are still intact in the current revision:\n"
	terminal.printb("Author".ljust(21) + "Rows".rjust(10) + "% in comments".rjust(16))
	for i in sorted(blame.blames.items()):
		print i[0].ljust(20)[0:20],
		print str(i[1].rows).rjust(10),
		print "{0:.2f}".format(100.0 * i[1].comments / i[1].rows).rjust(15)
