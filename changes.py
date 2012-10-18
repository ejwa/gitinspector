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
import extensions
import filtering
import re
import os
import subprocess
import terminal
import textwrap

class FileDiff:
	def __init__(self, string):
		commit_line = string.split("|")

		if commit_line.__len__() == 2:
			self.name = commit_line[0].strip()
			self.insertions = commit_line[1].count("+")
			self.deletions = commit_line[1].count("-")

	@staticmethod
	def is_filediff_line(string):
		string = string.split("|")
		return string.__len__() == 2 and string[1].find("Bin") == -1 and ('+' in string[1] or '-' in string[1])

	@staticmethod
	def get_extension(string):
		string = string.split("|")[0].strip().strip("{}")
		return os.path.splitext(string)[1][1:]

	@staticmethod
	def get_filename(string):
		string = string.split("|")[0].strip().strip("{}")
		return string.strip()

	@staticmethod
	def is_valid_extension(string):
		extension = FileDiff.get_extension(string)

		for i in extensions.get():
			if extension == i:
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
	def __init__(self, hard):
		self.commits = []
		git_log_r = subprocess.Popen("git log --pretty='%ad|%t|%aN|%s' --stat=100000,8192 --no-merges -w " +
		                             "{0} --date=short".format("-C -C -M" if hard else ""),
		                             shell=True, bufsize=1, stdout=subprocess.PIPE).stdout
		commit = None
		found_valid_extension = False
		lines = git_log_r.readlines()

		for i in lines:
			i = i.decode("utf-8", "replace")
			if Commit.is_commit_line(i) or i == lines[-1]:
				if found_valid_extension:
					self.commits.append(commit)

				found_valid_extension = False
				commit = Commit(i)

			if FileDiff.is_filediff_line(i) and not filtering.set_filtered(FileDiff.get_filename(i)):
				extensions.add_located(FileDiff.get_extension(i))

				if FileDiff.is_valid_extension(i):
					found_valid_extension = True
					filediff = FileDiff(i)
					commit.add_filediff(filediff)

	def get_commits(self):
		return self.commits

	@staticmethod
	def __modify_authorinfo__(authors, key, commit):
		if authors.get(key, None) == None:
			authors[key] = AuthorInfo()

		if commit.get_filediffs():
			authors[key].commits += 1

		for j in commit.get_filediffs():
			authors[key].insertions += j.insertions
			authors[key].deletions += j.deletions

	def get_authorinfo_list(self):
		authors = {}
		for i in self.commits:
			Changes.__modify_authorinfo__(authors, i.author, i)

		return authors

	def get_authordateinfo_list(self):
		authors = {}
		for i in self.commits:
			Changes.__modify_authorinfo__(authors, (i.date, i.author), i)

		return authors

__changes__ = None

def get(hard):
	global __changes__
	if __changes__ == None:
		__changes__ = Changes(hard)

	return __changes__

__historical_info_text__ = "The following historical commit information, by author, was found in the repository"

def output_html(string, hard):
	print("HTML output not yet supported.")

def output_text(hard):
	authorinfo_list = get(hard).get_authorinfo_list()
	total_changes = 0.0

	for i in authorinfo_list:
		total_changes += authorinfo_list.get(i).insertions
		total_changes += authorinfo_list.get(i).deletions

	if authorinfo_list:
		print(textwrap.fill(__historical_info_text__, width=terminal.get_size()[0]))
		terminal.printb("Author".ljust(21) + "Commits   " + "Insertions   " + "Deletions   " + "% of changes")

		for i in sorted(authorinfo_list):
			authorinfo = authorinfo_list.get(i)
			percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100

			print(i.ljust(20)[0:20], end=" ")
			print(str(authorinfo.commits).rjust(7), end=" ")
			print(str(authorinfo.insertions).rjust(12), end=" ")
			print(str(authorinfo.deletions).rjust(11), end=" ")
			print("{0:.2f}".format(percentage).rjust(14))
	else:
		print("No commited files with the specified extensions were found.")

def output_xml(hard):
	authorinfo_list = get(hard).get_authorinfo_list()
	total_changes = 0.0

	for i in authorinfo_list:
		total_changes += authorinfo_list.get(i).insertions
		total_changes += authorinfo_list.get(i).deletions

	if authorinfo_list:
		message_xml = "\t\t<message>" + __historical_info_text__ + "</message>\n"
		changes_xml = ""

		for i in sorted(authorinfo_list):
			authorinfo = authorinfo_list.get(i)
			percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100

			name_xml = "\t\t\t\t<name>" + i + "</name>\n"
			commits_xml = "\t\t\t\t<commits>" + str(authorinfo.commits) + "</commits>\n"
			insertions_xml = "\t\t\t\t<insertions>" + str(authorinfo.insertions) + "</insertions>\n"
			deletions_xml = "\t\t\t\t<deletions>" + str(authorinfo.deletions) + "</deletions>\n"
			percentage_xml = "\t\t\t\t<percentage-of-changes>" + "{0:.2f}".format(percentage) + "</percentage-of-changes>\n"

			changes_xml += ("\t\t\t<author>\n" + name_xml + commits_xml + insertions_xml +
			                deletions_xml + percentage_xml + "\t\t\t</author>\n")

		print("\t<changes>\n" + message_xml + "\t\t<authors>\n" + changes_xml + "\t\t</authors>\n\t</changes>")
	else:
		print("\t<changes>\n\t\t<exception>" + "No commited files with the specified extensions were found." +
		      "</exception>\n\t</changes>")
