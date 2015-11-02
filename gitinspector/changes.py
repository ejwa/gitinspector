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

from __future__ import unicode_literals
import bisect
import datetime
import multiprocessing
import os
import subprocess
import threading
from .localization import N_
from . import extensions, filtering, format, interval, terminal

CHANGES_PER_THREAD = 200
NUM_THREADS = multiprocessing.cpu_count()

__thread_lock__ = threading.BoundedSemaphore(NUM_THREADS)
__changes_lock__ = threading.Lock()

class FileDiff(object):
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
		string = string.split("|")[0].strip().strip("{}").strip("\"").strip("'")
		return os.path.splitext(string)[1][1:]

	@staticmethod
	def get_filename(string):
		return string.split("|")[0].strip().strip("{}").strip("\"").strip("'")

	@staticmethod
	def is_valid_extension(string):
		extension = FileDiff.get_extension(string)

		for i in extensions.get():
			if (extension == "" and i == "*") or extension == i or i == '**':
				return True
		return False

class Commit(object):
	def __init__(self, string):
		self.filediffs = []
		commit_line = string.split("|")

		if commit_line.__len__() == 5:
			self.timestamp = commit_line[0]
			self.date = commit_line[1]
			self.sha = commit_line[2]
			self.author = commit_line[3].strip()
			self.email = commit_line[4].strip()

	def __lt__(self, other):
		return self.timestamp.__lt__(other.timestamp) # only used for sorting; we just consider the timestamp.

	def add_filediff(self, filediff):
		self.filediffs.append(filediff)

	def get_filediffs(self):
		return self.filediffs

	@staticmethod
	def get_author_and_email(string):
		commit_line = string.split("|")

		if commit_line.__len__() == 5:
			return (commit_line[3].strip(), commit_line[4].strip())

	@staticmethod
	def is_commit_line(string):
		return string.split("|").__len__() == 5

class AuthorInfo(object):
	email = None
	insertions = 0
	deletions = 0
	commits = 0

class ChangesThread(threading.Thread):
	def __init__(self, hard, changes, first_hash, second_hash, offset):
		__thread_lock__.acquire() # Lock controlling the number of threads running
		threading.Thread.__init__(self)

		self.hard = hard
		self.changes = changes
		self.first_hash = first_hash
		self.second_hash = second_hash
		self.offset = offset

	@staticmethod
	def create(hard, changes, first_hash, second_hash, offset):
		thread = ChangesThread(hard, changes, first_hash, second_hash, offset)
		thread.daemon = True
		thread.start()

	def run(self):
		git_log_r = subprocess.Popen(filter(None, ["git", "log", "--reverse", "--pretty=%ct|%cd|%H|%aN|%aE",
		                             "--stat=100000,8192", "--no-merges", "-w", interval.get_since(),
		                             interval.get_until(), "--date=short"] + (["-C", "-C", "-M"] if self.hard else []) +
		                             [self.first_hash + self.second_hash]), bufsize=1, stdout=subprocess.PIPE).stdout
		lines = git_log_r.readlines()
		git_log_r.close()

		commit = None
		found_valid_extension = False
		is_filtered = False
		commits = []

		__changes_lock__.acquire() # Global lock used to protect calls from here...

		for i in lines:
			j = i.strip().decode("unicode_escape", "ignore")
			j = j.encode("latin-1", "replace")
			j = j.decode("utf-8", "replace")

			if Commit.is_commit_line(j):
				(author, email) = Commit.get_author_and_email(j)
				self.changes.emails_by_author[author] = email
				self.changes.authors_by_email[email] = author

			if Commit.is_commit_line(j) or i is lines[-1]:
				if found_valid_extension:
					bisect.insort(commits, commit)

				found_valid_extension = False
				is_filtered = False
				commit = Commit(j)

				if Commit.is_commit_line(j) and \
				   (filtering.set_filtered(commit.author, "author") or \
				   filtering.set_filtered(commit.email, "email") or \
				   filtering.set_filtered(commit.sha, "revision") or \
				   filtering.set_filtered(commit.sha, "message")):
					is_filtered = True

			if FileDiff.is_filediff_line(j) and not \
			   filtering.set_filtered(FileDiff.get_filename(j)) and not is_filtered:
				extensions.add_located(FileDiff.get_extension(j))

				if FileDiff.is_valid_extension(j):
					found_valid_extension = True
					filediff = FileDiff(j)
					commit.add_filediff(filediff)

		self.changes.commits[self.offset // CHANGES_PER_THREAD] = commits
		__changes_lock__.release() # ...to here.
		__thread_lock__.release() # Lock controlling the number of threads running

PROGRESS_TEXT = N_("Fetching and calculating primary statistics (1 of 2): {0:.0f}%")

class Changes(object):
	authors = {}
	authors_dateinfo = {}
	authors_by_email = {}
	emails_by_author = {}

	def __init__(self, repo, hard):
		self.commits = []
		git_log_hashes_r = subprocess.Popen(filter(None, ["git", "rev-list", "--reverse", "--no-merges",
		                                    interval.get_since(), interval.get_until(), "HEAD"]), bufsize=1,
		                                    stdout=subprocess.PIPE).stdout
		lines = git_log_hashes_r.readlines()
		git_log_hashes_r.close()

		if len(lines) > 0:
			progress_text = _(PROGRESS_TEXT)
			if repo != None:
				progress_text = "[%s] " % repo.name + progress_text

			self.commits = [None] * (len(lines) // CHANGES_PER_THREAD + 1)
			first_hash = ""

			for i, entry in enumerate(lines):
				if i % CHANGES_PER_THREAD == CHANGES_PER_THREAD - 1:
					entry = entry.decode("utf-8", "replace").strip()
					second_hash = entry
					ChangesThread.create(hard, self, first_hash, second_hash, i)
					first_hash = entry + ".."

					if format.is_interactive_format():
						terminal.output_progress(progress_text, i, len(lines))
			else:
				entry = entry.decode("utf-8", "replace").strip()
				second_hash = entry
				ChangesThread.create(hard, self, first_hash, second_hash, i)

		# Make sure all threads have completed.
		for i in range(0, NUM_THREADS):
			__thread_lock__.acquire()

		# We also have to release them for future use.
		for i in range(0, NUM_THREADS):
			__thread_lock__.release()

		self.commits = [item for sublist in self.commits for item in sublist]

		if len(self.commits) > 0:
			if interval.has_interval() and len(self.commits) > 0:
				interval.set_ref(self.commits[-1].sha)

			self.first_commit_date = datetime.date(int(self.commits[0].date[0:4]), int(self.commits[0].date[5:7]),
			                                       int(self.commits[0].date[8:10]))
			self.last_commit_date = datetime.date(int(self.commits[-1].date[0:4]), int(self.commits[-1].date[5:7]),
			                                      int(self.commits[-1].date[8:10]))

	def __add__(self, other):
		if other == None:
			return self

		self.authors.update(other.authors)
		self.authors_dateinfo.update(other.authors_dateinfo)
		self.authors_by_email.update(other.authors_by_email)
		self.emails_by_author.update(other.emails_by_author)

		for commit in other.commits:
			bisect.insort(self.commits, commit)

		return self

	def get_commits(self):
		return self.commits

	@staticmethod
	def modify_authorinfo(authors, key, commit):
		if authors.get(key, None) == None:
			authors[key] = AuthorInfo()

		if commit.get_filediffs():
			authors[key].commits += 1

		for j in commit.get_filediffs():
			authors[key].insertions += j.insertions
			authors[key].deletions += j.deletions

	def get_authorinfo_list(self):
		if not self.authors:
			for i in self.commits:
				Changes.modify_authorinfo(self.authors, i.author, i)

		return self.authors

	def get_authordateinfo_list(self):
		if not self.authors_dateinfo:
			for i in self.commits:
				Changes.modify_authorinfo(self.authors_dateinfo, (i.date, i.author), i)

		return self.authors_dateinfo

	def get_latest_author_by_email(self, name):
		if not hasattr(name, "decode"):
			name = str.encode(name)

		name = name.decode("unicode_escape", "ignore")
		return self.authors_by_email[name]

	def get_latest_email_by_author(self, name):
		return self.emails_by_author[name]
