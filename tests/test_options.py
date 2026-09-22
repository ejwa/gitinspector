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

from __future__ import unicode_literals
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from .harness import Repository

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def __environment__():
	env = dict(os.environ)
	env["PYTHONIOENCODING"] = "utf-8"
	env["PYTHONPATH"] = os.pathsep.join(filter(None, [PROJECT_ROOT, os.getenv("PYTHONPATH")]))
	env["LANGUAGE"] = "C"

	return env

def __run__(directory, env, options):
	process = subprocess.Popen([sys.executable, "-m", "gitinspector.gitinspector"] + list(options),
	                           cwd=directory, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(output, errors) = process.communicate()

	return (process.returncode, output.decode("utf-8", "replace"), errors.decode("utf-8", "replace"))

def run_inside(directory, *options):
	return __run__(directory, __environment__(), options)

def run_outside_a_repository(*options):
	directory = tempfile.mkdtemp(prefix="gitinspector-test-")

	try:
		return run_inside(directory, *options)
	finally:
		shutil.rmtree(directory)

#The empty directory is both the working directory and the whole PATH, so no git can be found.
def run_without_git(*options):
	directory = tempfile.mkdtemp(prefix="gitinspector-test-")
	env = __environment__()
	env["PATH"] = directory

	try:
		return __run__(directory, env, options)
	finally:
		shutil.rmtree(directory)

class InformationalOptionsTest(unittest.TestCase):
	def test_the_version_is_shown_outside_a_repository(self):
		(status, output, errors) = run_outside_a_repository("--version")

		self.assertEqual(status, 0, "gitinspector --version failed with {0}: {1}".format(status, errors.strip()))
		self.assertIn("gitinspector", output)

	def test_the_help_is_shown_outside_a_repository(self):
		(status, output, errors) = run_outside_a_repository("--help")

		self.assertEqual(status, 0, "gitinspector --help failed with {0}: {1}".format(status, errors.strip()))
		self.assertIn("--file-types", output)

	def test_a_directory_that_is_no_repository_is_still_reported(self):
		(status, _, errors) = run_outside_a_repository()

		self.assertNotEqual(status, 0)
		self.assertIn("Error processing git repository", errors)

#Windows finds more than executables through the PATH, so emptying it there tests something else.
@unittest.skipIf(sys.platform == "win32", "An empty PATH does not only hide the git executable on Windows")
class MissingGitTest(unittest.TestCase):
	def test_the_missing_executable_is_reported(self):
		(status, _unused, errors) = run_without_git(".")
		#An interpreter with a broken .pth file writes noise of its own before ours, so the last
		#line is the one that has to be the message rather than the tail of a traceback.
		last_line = errors.strip().splitlines()[-1]

		self.assertNotEqual(status, 0)
		self.assertIn("git executable", last_line)

	def test_the_version_is_still_shown(self):
		(status, output, errors) = run_without_git("--version")

		self.assertEqual(status, 0, errors.strip())
		self.assertIn("gitinspector", output)

class RepositoryArgumentTest(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.mkdtemp(prefix="gitinspector-test-")

	def tearDown(self):
		shutil.rmtree(self.directory)

	def __assert_is_reported__(self, argument):
		(status, _unused, errors) = run_inside(self.directory, argument)
		#Anything the interpreter itself says comes first, so only the last line is ours.
		last_line = errors.strip().splitlines()[-1]

		self.assertNotEqual(status, 0)
		self.assertIn("Error processing git repository", last_line)

	def test_a_missing_directory_is_reported(self):
		self.__assert_is_reported__("unexisting-folder")

	def test_an_argument_that_is_a_file_is_reported(self):
		path = os.path.join(self.directory, "a.license")
		open(path, "w").close()

		self.__assert_is_reported__(path)

class ExclusionPatternTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add", {"a.py": "x = 1\n"})

	def tearDown(self):
		self.repository.remove()

	def test_an_invalid_author_pattern_is_reported_instead_of_hanging(self):
		(status, _unused, errors) = run_inside(self.repository.location, "-F", "json", "-x", "author:[")

		self.assertEqual(status, 2)
		self.assertIn("invalid regular expression", errors)

class ExclusionAndIntervalTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add a", {"a.py": "a\n", "c.py": "c\n"}, "Alice", "alice@example.com",
		                       "2018-05-01T10:00:00+0000")
		self.repository.commit("add b", {"b.py": "b\n"}, "Bob", "bob@example.com", "2018-06-01T10:00:00+0000")

	def tearDown(self):
		self.repository.remove()

	def report(self, *options):
		(status, output, errors) = run_inside(self.repository.location, "-F", "json", *options)
		self.assertEqual(status, 0, errors)
		return json.loads(output)["gitinspector"]

	def authors(self, *options):
		return sorted(author["name"] for author in self.report(*options)["changes"]["authors"])

	def test_what_the_rules_left_out_is_listed_by_kind(self):
		filtering = self.report("-x", "author:Bob", "-x", "a.py")["filtering"]
		self.assertEqual((filtering["authors"]["entries"], filtering["files"]["entries"]), (["Bob"], ["a.py"]))

	def test_the_rules_of_the_git_configuration_are_applied(self):
		self.repository.git("config", "inspector.exclude", "author:Bob")
		self.assertEqual(self.authors(), ["Alice"])

	def test_rules_on_the_command_line_replace_those_of_the_git_configuration(self):
		self.repository.git("config", "inspector.exclude", "author:Bob")
		self.assertEqual(self.authors("-x", "author:Alice"), ["Bob"])

	def test_the_interval_of_the_git_configuration_is_applied(self):
		self.repository.git("config", "inspector.since", "2018-05-15")
		self.assertEqual(self.authors(), ["Bob"])

		self.repository.git("config", "--unset", "inspector.since")
		self.repository.git("config", "inspector.until", "2018-05-15")
		self.assertEqual(self.authors(), ["Alice"])
