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
import re
import system
import terminal

class BlameEntry:
	rows = 0
	comments = 0

class Blame:
	def __init__(self, repo, hard):
		self.blames = {}
		ls_tree_r = system.run(repo, "git ls-tree --name-only -r HEAD")

		for i in ls_tree_r.readlines():
			if FileDiff.is_valid_extension(i):
				if not missing.add(repo, i.strip()):
					git_blame_r = system.run(repo, "git blame -w {0} \"".format("-C -M" if hard else "") +
					                         i.strip() + "\"")
					is_inside_comment = False

					for j in git_blame_r.readlines():
						if Blame.is_blame_line(j):
							author = Blame.get_author(j)
							content = Blame.get_content(j)

							if self.blames.get(author, None) == None:
								self.blames[author] = BlameEntry()

							if comment.is_comment(FileDiff.get_extension(i), content):
								self.blames[author].comments += 1
							if is_inside_comment:
								if comment.has_comment_end(FileDiff.get_extension(i), content):
									is_inside_comment = False
								else:
									self.blames[author].comments += 1
							elif comment.has_comment_begining(FileDiff.get_extension(i), content):
								is_inside_comment = True

							self.blames[author].rows += 1

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
	blame = Blame(repo, hard)

	print "\nBelow is the number of rows from each author that have survived and"
	print "are still intact in the current revision:\n"
	terminal.printb("Author".ljust(21) + "Rows".rjust(10) + "% in comments".rjust(16))
	for i in sorted(blame.blames.items()):
		print i[0].ljust(20)[0:20],
		print str(i[1].rows).rjust(10),
		print "{0:.2f}".format(100.0 * i[1].comments / i[1].rows).rjust(15)
