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

import extensions
import os
import re
import sysrun
import terminal

class FileDiff:
	def __init__(self, string):
		commit_line = string.split("|")

		if commit_line.__len__() == 2:
			self.name = commit_line[0].strip()
			self.insertions = commit_line[1].count("+")
			self.deletions = commit_line[1].count("-")

	@staticmethod
	def is_filediff_line(string):
		s = string.split("|")
		return s.__len__() == 2 and s[1].find("Bin") == -1

	@staticmethod
	def get_extension(string):
		s = string.split("|")[0].strip().strip("{}")
		return os.path.splitext(s)[1][1:]

	@staticmethod
	def is_valid_extension(string):
		s = FileDiff.get_extension(string)

		for i in extensions.get():
			if s == i:
				return True
		return False

class Commit:
	def __init__(self, string):
		self.filediffs = []
		commit_line = string.split("|")

		if commit_line.__len__() == 4:
			self.date = commit_line[0]
			self.sha = commit_line[1]
			self.author = re.sub("[^\w ]", "", commit_line[2].strip())
			self.message = commit_line[3].strip()

	def add_filediff(self, filediff):
		self.filediffs.append(filediff)

	def get_filediffs(self):
		return self.filediffs

	@staticmethod
	def is_commit_line(string):
		return string.split("|").__len__() == 4

class AuthorInfo:
	insertions = 0
	deletions = 0
	commits = 0

class Changes:
	def __init__(self, repo, hard):
		self.commits = []
		f = sysrun.run(repo, "git log --pretty='%ad|%t|%aN|%s' --stat=100000 --no-merges --ignore-space-change " +
		                     "-C {0} --date=short".format("-C" if hard else ""))
		commit = None
		found_valid_extension = False

		for i in f.readlines():
			if Commit.is_commit_line(i):
				if found_valid_extension:
					self.commits.append(commit)

				found_valid_extension = False
				commit = Commit(i)

			if FileDiff.is_filediff_line(i):
				extensions.add_located(FileDiff.get_extension(i))

				if FileDiff.is_valid_extension(i):
					found_valid_extension = True
					filediff = FileDiff(i)
					commit.add_filediff(filediff)

	def get_commits(self):
		return self.commits

	def __modify_authorinfo__(self, authors, key, commit):
		if authors.get(key, None) == None:
			authors[key] = AuthorInfo()

		authors[key].commits += 1
		for j in commit.get_filediffs():
			authors[key].insertions += j.insertions
			authors[key].deletions += j.deletions

	def get_authorinfo_list(self):
		authors = {}
		for i in self.commits:
			self.__modify_authorinfo__(authors, i.author, i)

		return authors

	def get_authordateinfo_list(self):
		authors = {}
		for i in self.commits:
			self.__modify_authorinfo__(authors, (i.date, i.author), i)

		return authors

changes = None

def get(repo, hard):
	global changes
	if changes == None:
		changes = Changes(repo, hard)

	return changes

def output(repo, hard):
	get(repo, hard)
	authorinfo_list = changes.get_authorinfo_list()
	total_changes = 0.0

	for i in authorinfo_list:
		total_changes += authorinfo_list.get(i).insertions
		total_changes += authorinfo_list.get(i).deletions

	if authorinfo_list:
		print "The following historical commit information, by author, was found in the"
		print "repository:\n"
		terminal.printb("Author".ljust(21) + "Commits   " + "Insertions   " + "Deletions   " + "% of changes")

		for i in sorted(authorinfo_list):
			authorinfo = authorinfo_list.get(i)
			percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100

			print i.ljust(20)[0:20],
			print str(authorinfo.commits).rjust(7),
			print str(authorinfo.insertions).rjust(12),
			print str(authorinfo.deletions).rjust(11),
			print "{0:.2f}".format(percentage).rjust(14)
	else:
		print "No commited files with the specified extensions were found."
