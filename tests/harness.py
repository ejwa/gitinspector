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
import os
import shutil
import subprocess
import tempfile
from gitinspector import blame, changes, extensions, filtering, format, interval

DEFAULT_AUTHOR = "Test Author"
DEFAULT_EMAIL = "test@example.com"
DEFAULT_DATE = "2015-01-01T12:00:00+0000"

def __native__(value):
	# Python 2 wants byte strings in process arguments and environments.
	return value if isinstance(value, str) else value.encode("utf-8")

class Repository(object):
	def __init__(self):
		self.location = tempfile.mkdtemp(prefix="gitinspector-test-")
		self.git("init", "-q")
		self.git("config", "user.name", DEFAULT_AUTHOR)
		self.git("config", "user.email", DEFAULT_EMAIL)
		self.git("config", "commit.gpgsign", "false")
		self.default_branch = self.git("symbolic-ref", "--short", "HEAD")

	def remove(self):
		shutil.rmtree(self.location)

	def git(self, *arguments, **environment):
		env = dict(os.environ)
		env.update((key, __native__(value)) for key, value in environment.items())
		command = ["git"] + [__native__(argument) for argument in arguments]
		output = subprocess.check_output(command, cwd=self.location, env=env, stderr=subprocess.STDOUT)
		return output.decode("utf-8", "replace").strip()

	def commit(self, message, files, author=DEFAULT_AUTHOR, email=DEFAULT_EMAIL, date=DEFAULT_DATE):
		for name, content in files.items():
			target = open(os.path.join(self.location, name), "wb")
			target.write(content.encode("utf-8"))
			target.close()

		self.git("add", "--", *files)
		self.git("commit", "-q", "-m", message, GIT_AUTHOR_NAME=author, GIT_AUTHOR_EMAIL=email, GIT_AUTHOR_DATE=date,
		         GIT_COMMITTER_NAME=author, GIT_COMMITTER_EMAIL=email, GIT_COMMITTER_DATE=date)
		return self.git("rev-parse", "HEAD")

	def branch(self, name):
		self.git("checkout", "-q", "-b", name)

	def checkout(self, name):
		self.git("checkout", "-q", name)

	def merge(self, name, message, date=DEFAULT_DATE):
		self.git("merge", "-q", "--no-ff", "-m", message, name, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
		return self.git("rev-parse", "HEAD")

def __inside__(repository, analysis):
	previous_directory = os.getcwd()
	os.chdir(repository.location)

	try:
		return analysis()
	finally:
		os.chdir(previous_directory)

def analyze_changes(repository, since=None, until=None, file_types="**", hard=False, exclude=None):
	interval.clear()
	filtering.clear()
	extensions.define(file_types)
	format.select("xml")

	if since:
		interval.set_since(since)
	if until:
		interval.set_until(until)
	if exclude:
		filtering.add(exclude)

	return __inside__(repository, lambda: changes.Changes(None, hard))

def analyze_blame(repository, analyzed_changes, hard=False, useweeks=False):
	return __inside__(repository, lambda: blame.Blame(None, hard, useweeks, analyzed_changes))
