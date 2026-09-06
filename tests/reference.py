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

# The statistics here are gathered with other git commands and other parsing than gitinspector uses, so that
# reports can be checked against a source that does not share their code.

from __future__ import unicode_literals
import os
import re
import subprocess
from collections import defaultdict
from multiprocessing.pool import ThreadPool

RENAME = re.compile(r"^(.*)\{(.*) => (.*)\}(.*)$")
TOP_LEVEL_RENAME = re.compile(r"^(.*) => (.*)$")
BLAME_HEADER = re.compile(r"^[0-9a-f]{40} \d+ \d+( \d+)?$")
NO_EXTENSION = "*"
BLAME_THREADS = 8

def git(location, *arguments):
	with open(os.devnull, "w") as null:
		output = subprocess.check_output(["git"] + list(arguments), cwd=location, stderr=null)

	return output.decode("utf-8", "replace")

def branch_of(location):
	try:
		return git(location, "symbolic-ref", "--short", "-q", "HEAD").strip()
	except subprocess.CalledProcessError:
		return git(location, "rev-parse", "--short", "HEAD").strip()

def changed_path(numstat_path):
	match = RENAME.match(numstat_path)

	if match:
		return match.group(1) + match.group(3) + match.group(4)

	match = TOP_LEVEL_RENAME.match(numstat_path)
	return match.group(2) if match else numstat_path

def extension_of(path):
	return os.path.splitext(path)[1][1:] or NO_EXTENSION

class Author(object):
	def __init__(self):
		self.commits = 0
		self.insertions = 0
		self.deletions = 0
		self.emails = set()

class Statistics(object):
	def __init__(self, location, file_types, since=None, until=None):
		self.location = location
		self.file_types = file_types.split(",")
		self.since = since
		self.ref = "HEAD"
		self.authors = {}
		self.names_by_email = defaultdict(set)
		self.located = set()
		self.modified_lines_by_period = defaultdict(int)
		self.authors_by_period = defaultdict(set)
		self.lines_by_email_and_file = defaultdict(int)
		self.__read_log__(since, until)
		self.__read_blame__()

	def wants(self, extension):
		return "**" in self.file_types or extension in self.file_types

	def contributors(self):
		return dict((name, author) for (name, author) in self.authors.items() if author.commits > 0)

	def ambiguous_names(self):
		return set(name for names in self.names_by_email.values() if len(names) > 1 for name in names)

	def __name_of__(self, email):
		names = self.names_by_email[email]
		return next(iter(names)) if len(names) == 1 else None

	def blamed_lines(self):
		return sum(lines for ((email, path), lines) in self.lines_by_email_and_file.items() if email in self.names_by_email)

	def blamed_lines_by_name(self):
		return self.__blamed_lines_by__(lambda name, path: name)

	def blamed_lines_by_name_and_file(self):
		return self.__blamed_lines_by__(lambda name, path: (name, path))

	def __blamed_lines_by__(self, key):
		lines_by_key = defaultdict(int)

		for ((email, path), lines) in self.lines_by_email_and_file.items():
			name = self.__name_of__(email)

			if name is not None:
				lines_by_key[key(name, path)] += lines

		return lines_by_key

	def __read_log__(self, since, until):
		arguments = ["log", "--no-merges", "-w", "--numstat", "--date=short", "--format=commit|%H|%ct|%cd|%aN|%aE"]
		arguments += ["--since=" + since] if since else []
		arguments += ["--until=" + until] if until else []
		newest = (0, None)
		author = None

		for line in git(self.location, *arguments + ["HEAD"]).splitlines():
			if line.startswith("commit|"):
				(sha, timestamp, date, name, email) = line.split("|")[1:]
				self.names_by_email[email].add(name)
				author = self.authors.setdefault(name, Author())
				author.emails.add(email)
				counted = False
			elif line.strip():
				(added, deleted, path) = line.split("\t", 2)

				if added == "-" or int(added) + int(deleted) == 0:
					continue

				extension = extension_of(changed_path(path))
				self.located.add(extension)

				if self.wants(extension):
					if not counted:
						counted = True
						author.commits += 1
						self.authors_by_period[date[0:7]].add(name)
						newest = max(newest, (int(timestamp), sha))

					author.insertions += int(added)
					author.deletions += int(deleted)
					self.modified_lines_by_period[date[0:7]] += int(added) + int(deleted)

		if (since or until) and newest[1]:
			self.ref = newest[1]

	def __read_blame__(self):
		paths = [path for path in git(self.location, "ls-tree", "-r", "--name-only", "-z", self.ref).split("\0")
		         if path and extension_of(path) in self.located and self.wants(extension_of(path))]
		pool = ThreadPool(BLAME_THREADS)

		try:
			for (path, lines_by_email) in zip(paths, pool.map(self.__blame__, paths)):
				for (email, lines) in lines_by_email.items():
					self.lines_by_email_and_file[(email, path)] += lines
		finally:
			pool.close()
			pool.join()

	def __blame__(self, path):
		arguments = ["blame", "--porcelain", "-w"] + (["--since=" + self.since] if self.since else [])

		try:
			porcelain = git(self.location, *arguments + [self.ref, "--", path])
		except subprocess.CalledProcessError:
			return {}

		lines_by_sha = defaultdict(int)
		email_by_sha = {}
		boundary = set()
		sha = None

		for line in porcelain.splitlines():
			if BLAME_HEADER.match(line):
				sha = line[0:40]
				lines_by_sha[sha] += 1
			elif line.startswith("author-mail <"):
				email_by_sha[sha] = line[len("author-mail <"):-1]
			elif line == "boundary":
				boundary.add(sha)

		lines_by_email = defaultdict(int)

		for (sha, lines) in lines_by_sha.items():
			if not (self.since and sha in boundary):
				lines_by_email[email_by_sha[sha]] += lines

		return lines_by_email
