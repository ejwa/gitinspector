# coding: utf-8
#
# Copyright © 2012-2026 Ejwa Hosting AB. All rights reserved.
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

from __future__ import division
from __future__ import unicode_literals
import bisect
import datetime
import os
import subprocess
import threading
from .localization import N_
from . import extensions, filtering, format, git, interval, terminal, workers

CHANGES_PER_THREAD = 200

__changes_lock__ = threading.Lock()

class FileDiff(object):
	def __init__(self, string):
		commit_line = FileDiff.__split__(string)

		if commit_line.__len__() == 2:
			self.name = FileDiff.get_filename(string)
			self.insertions = commit_line[1].count("+")
			self.deletions = commit_line[1].count("-")

	#The counts of a diffstat never contain a bar, but a file name may, so the last one separates them.
	@staticmethod
	def __split__(string):
		return string.rsplit("|", 1)

	@staticmethod
	def is_filediff_line(string):
		string = FileDiff.__split__(string)
		return string.__len__() == 2 and string[1].find("Bin") == -1 and ('+' in string[1] or '-' in string[1])

	@staticmethod
	def get_extension(string):
		return os.path.splitext(FileDiff.get_filename(string))[1][1:]

	@staticmethod
	def get_filename(string):
		return git.unquote(FileDiff.__split__(string)[0].strip()).strip("{}")

	@staticmethod
	def is_valid_extension(string):
		extension = FileDiff.get_extension(string)

		for i in extensions.get():
			if (extension == "" and i == "*") or extension == i or i == '**':
				return True
		return False

#A name or an email may contain anything but a NUL, which is why the fields of a commit line are
#separated by one; a pipe would make an author called "a|b" look like a line of the diffstat.
COMMIT_FIELD_SEPARATOR = "\x00"

class Commit(object):
	def __init__(self, string):
		self.filediffs = []
		commit_line = string.split(COMMIT_FIELD_SEPARATOR)

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
	def is_commit_line(string):
		return string.split(COMMIT_FIELD_SEPARATOR).__len__() == 5

class AuthorInfo(object):
	email = None
	insertions = 0
	deletions = 0
	commits = 0

class ChangesThread(workers.Worker):
	def __init__(self, hard, changes, hashes, index):
		workers.Worker.__init__(self)

		self.hard = hard
		self.changes = changes
		self.hashes = hashes
		self.index = index

	def work(self):
		# The hashes go on the command line rather than through a pipe, since concurrently spawned children inherit
		# each other's pipes on Python 2 and then deadlock waiting for the end of their input.
		lines = workers.output_of(["git", "log", "--no-walk=unsorted", "--pretty=%ct%x00%cd%x00%H%x00%aN%x00%aE",
		                           "--stat=100000,8192", "--no-merges", "-w", "--date=short"] +
		                          (["-C", "-C", "-M"] if self.hard else []) + self.hashes).splitlines()

		commit = None
		found_valid_extension = False
		is_filtered = False
		commits = []

		with __changes_lock__:
			for i in lines:
				j = git.decode(i.strip())

				if Commit.is_commit_line(j):
					if found_valid_extension:
						bisect.insort(commits, commit)

					found_valid_extension = False
					is_filtered = False
					commit = Commit(j)
					self.changes.remember_author(commit)

					if filtering.set_filtered(commit.author, "author") or \
					   filtering.set_filtered(commit.email, "email") or \
					   filtering.set_filtered(commit.sha, "revision") or \
					   filtering.set_filtered(commit.sha, "message"):
						is_filtered = True

				if FileDiff.is_filediff_line(j) and not \
				   filtering.set_filtered(FileDiff.get_filename(j)) and not is_filtered:
					extensions.add_located(FileDiff.get_extension(j))

					if FileDiff.is_valid_extension(j):
						found_valid_extension = True
						filediff = FileDiff(j)
						commit.add_filediff(filediff)

			if found_valid_extension:
				bisect.insort(commits, commit)

			self.changes.commits[self.index] = commits

PROGRESS_TEXT = N_("Fetching and calculating primary statistics (1 of 2): {0:.0f}%")

class Changes(object):
	def __init__(self, repo, hard):
		self.commits = []
		self.authors = {}
		self.authors_dateinfo = {}
		self.latest_commit_by_email = {}
		self.latest_commit_by_author = {}
		interval.set_ref("HEAD")
		git_rev_list_p = subprocess.Popen(filter(None, ["git", "rev-list", "--reverse", "--no-merges",
		                                  interval.get_since(), interval.get_until(), "HEAD"]),
		                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		lines = git_rev_list_p.communicate()[0].splitlines()
		git_rev_list_p.stdout.close()

		if git_rev_list_p.returncode == 0 and len(lines) > 0:
			progress_text = _(PROGRESS_TEXT)
			if repo != None:
				progress_text = "[%s] " % repo.name + progress_text

			hashes = [entry.decode("utf-8", "replace").strip() for entry in lines]
			chunks = [hashes[i:i + CHANGES_PER_THREAD] for i in range(0, len(hashes), CHANGES_PER_THREAD)]
			self.commits = [None] * len(chunks)

			for i, chunk in enumerate(chunks):
				ChangesThread(hard, self, chunk, i).start()

				if format.is_interactive_format():
					terminal.output_progress(progress_text, i * CHANGES_PER_THREAD, len(hashes))

		workers.join()
		self.commits = [item for sublist in self.commits for item in sublist]

		if len(self.commits) > 0:
			if interval.has_interval():
				interval.set_ref(self.commits[-1].sha)

			self.first_commit_date = datetime.date(int(self.commits[0].date[0:4]), int(self.commits[0].date[5:7]),
			                                       int(self.commits[0].date[8:10]))
			self.last_commit_date = datetime.date(int(self.commits[-1].date[0:4]), int(self.commits[-1].date[5:7]),
			                                      int(self.commits[-1].date[8:10]))

	def __iadd__(self, other):
		try:
			self.authors.update(other.authors)
			self.authors_dateinfo.update(other.authors_dateinfo)
			for commit in list(other.latest_commit_by_email.values()) + list(other.latest_commit_by_author.values()):
				self.remember_author(commit)

			for commit in other.commits:
				bisect.insort(self.commits, commit)
			if not self.commits and not other.commits:
				self.commits = []

			return self
		except AttributeError:
			return other

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

	def remember_author(self, commit):
		Changes.__remember_latest__(self.latest_commit_by_email, commit.email, commit)
		Changes.__remember_latest__(self.latest_commit_by_author, commit.author, commit)

	@staticmethod
	def __remember_latest__(latest_commits, key, commit):
		latest = latest_commits.get(key)

		if latest is None or (latest.timestamp, latest.sha) < (commit.timestamp, commit.sha):
			latest_commits[key] = commit

	def get_latest_author_by_email(self, email):
		return self.latest_commit_by_email[email].author

	def get_latest_email_by_author(self, name):
		return self.latest_commit_by_author[name].email
