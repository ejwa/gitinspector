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
import os
import subprocess
import sys

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from .harness import Repository

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "create-release.sh")
TRANSLATIONS = "gitinspector/translations"
CATALOGS = [TRANSLATIONS + "/messages.pot", TRANSLATIONS + "/messages_de.po", TRANSLATIONS + "/messages_sv.po"]
COMPILED = [TRANSLATIONS + "/messages_de.mo", TRANSLATIONS + "/messages_sv.mo"]

def tools_are_available():
	if sys.platform == "win32":
		return False

	try:
		for tool in ("bash", "msgfmt"):
			subprocess.Popen([str(tool), str("--version")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
		return True
	except OSError:
		return False

def catalog(version):
	return 'msgid ""\nmsgstr ""\n"Project-Id-Version: gitinspector {0}\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n'.format(version)

def stand_in_files(version="0.5.2dev", package="0.5.2-dev-1", passing=True):
	with open(SCRIPT, "rb") as source:
		script = source.read().decode("utf-8")

	files = {
		"create-release.sh": script,
		"test_stub.py": "import unittest\n\nclass Stub(unittest.TestCase):\n\tdef test_stub(self):\n\t\tself.assertTrue({0})\n".format(passing),
		"gitinspector/version.py": '__version__ = "{0}"\n'.format(version),
		"docs/gitinspector.txt": ":doctype: manpage\n:man version: {0}\n:man source: gitinspector\n".format(version),
		"package.json": '{{\n  "name": "gitinspector",\n  "version": "{0}",\n  "preferGlobal": true\n}}\n'.format(package)
	}

	for path in CATALOGS:
		files[path] = catalog(version)
	for path in COMPILED:
		files[path] = "stale"

	return files

@unittest.skipUnless(tools_are_available(), "bash and the gettext tools are needed to run the release script")
class ReleaseTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	def prepare(self, **options):
		files = stand_in_files(**options)

		for name in files:
			directory = os.path.dirname(os.path.join(self.repository.location, name))
			if not os.path.isdir(directory):
				os.makedirs(directory)

		self.start = self.repository.commit("Initial", files)

	def release(self, *arguments):
		env = dict(os.environ)
		env[str("PYTHON")] = sys.executable
		env[str("PYTHONDONTWRITEBYTECODE")] = str("1")

		with open(os.devnull) as nothing:
			process = subprocess.Popen([str("bash"), str("create-release.sh")] + [str(argument) for argument in arguments],
			                           cwd=self.repository.location, env=env, stdin=nothing,
			                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			output = process.communicate()[0]

		return (process.returncode, output.decode("utf-8", "replace"))

	def file_at(self, revision, path):
		process = subprocess.Popen([str("git"), str("show"), str("{0}:{1}".format(revision, path))],
		                           cwd=self.repository.location, stdout=subprocess.PIPE)
		return process.communicate()[0]

	def assert_nothing_changed(self):
		self.assertEqual(self.repository.git("rev-parse", "HEAD"), self.start)
		self.assertEqual(self.repository.git("tag"), "")

	def test_a_bump_other_than_the_three_levels_is_refused(self):
		self.prepare()
		(status, output) = self.release("--bump=sideways")

		self.assertNotEqual(status, 0)
		self.assertIn("Bump one of version, revision or revrevision", output)
		self.assert_nothing_changed()

	def test_help_describes_the_bump_levels_and_changes_nothing(self):
		self.prepare()
		(status, output) = self.release("--help")

		self.assertEqual(status, 0, output)
		self.assertIn("--bump=revrevision", output)
		self.assert_nothing_changed()

	def test_an_unexpected_argument_is_refused(self):
		self.prepare()
		(status, output) = self.release("0.6.0")

		self.assertNotEqual(status, 0)
		self.assertIn("Unexpected argument '0.6.0'", output)
		self.assert_nothing_changed()

	def test_a_dirty_tree_is_refused_and_left_alone(self):
		self.prepare()
		version_py = os.path.join(self.repository.location, "gitinspector", "version.py")

		with open(version_py, "a") as edited:
			edited.write("# my own edit\n")

		(status, output) = self.release()

		self.assertNotEqual(status, 0)
		self.assertIn("Working tree is not clean", output)
		with open(version_py) as untouched:
			self.assertIn("# my own edit", untouched.read())
		self.assert_nothing_changed()

	def test_a_version_that_is_not_a_development_version_is_refused(self):
		self.prepare(version="0.5.2", package="0.5.2")
		(status, output) = self.release()

		self.assertNotEqual(status, 0)
		self.assertIn("not a development version", output)
		self.assert_nothing_changed()

	def test_an_existing_tag_is_refused(self):
		self.prepare()
		self.repository.git("tag", "v0.5.2")
		(status, output) = self.release()

		self.assertNotEqual(status, 0)
		self.assertIn("Tag v0.5.2 already exists", output)
		self.assertEqual(self.repository.git("rev-parse", "HEAD"), self.start)
