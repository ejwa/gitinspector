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
import shutil
import subprocess
import sys
import tempfile

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

	def release(self, *arguments, **environment):
		env = dict(os.environ)
		# The script discovers tests with "unittest discover", which Python 2.6 does not have.
		if sys.version_info >= (2, 7):
			env[str("PYTHON")] = sys.executable

		env[str("PYTHONDONTWRITEBYTECODE")] = str("1")
		env.update((str(name), str(value)) for name, value in environment.items())

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

	def assert_spelled(self, revision, version, package):
		self.assertIn('__version__ = "{0}"'.format(version).encode("utf-8"), self.file_at(revision, "gitinspector/version.py"))
		self.assertIn(":man version: {0}\n".format(version).encode("utf-8"), self.file_at(revision, "docs/gitinspector.txt"))
		self.assertIn('"version": "{0}"'.format(package).encode("utf-8"), self.file_at(revision, "package.json"))

		for path in CATALOGS:
			self.assertIn("Project-Id-Version: gitinspector {0}\\n\"".format(version).encode("utf-8"), self.file_at(revision, path))
		for path in COMPILED:
			self.assertIn("gitinspector {0}\n".format(version).encode("utf-8"), self.file_at(revision, path))

	def test_a_release_makes_the_release_commit_the_tag_and_the_next_commit(self):
		self.prepare()
		(status, output) = self.release()

		self.assertEqual(status, 0, output)
		self.assertEqual(self.repository.git("log", "--format=%s").splitlines(),
		                 ["Bump the version number to 0.5.3dev", "Bump the version number to 0.5.2", "Initial"])
		self.assertEqual(self.repository.git("tag"), "v0.5.2")
		self.assertEqual(self.repository.git("rev-parse", "v0.5.2"), self.repository.git("rev-parse", "HEAD~1"))
		self.assertEqual(self.repository.git("cat-file", "-t", "v0.5.2"), "commit")
		self.assertEqual(self.repository.git("status", "--porcelain"), "")

	def test_the_release_commit_carries_the_release_version_everywhere(self):
		self.prepare()
		self.release()

		self.assert_spelled("v0.5.2", "0.5.2", "0.5.2")

	def test_the_next_commit_carries_the_development_version_everywhere(self):
		self.prepare()
		self.release()

		self.assert_spelled("HEAD", "0.5.3dev", "0.5.3-dev-1")

	def test_the_revision_bump_raises_the_second_number(self):
		self.prepare()
		(status, output) = self.release("--bump=revision")

		self.assertEqual(status, 0, output)
		self.assert_spelled("HEAD", "0.6.0dev", "0.6.0-dev-1")

	def test_the_version_bump_raises_the_first_number(self):
		self.prepare()
		(status, output) = self.release("--bump=version")

		self.assertEqual(status, 0, output)
		self.assert_spelled("HEAD", "1.0.0dev", "1.0.0-dev-1")

	def test_the_third_number_is_raised_as_a_number(self):
		self.prepare(version="0.5.9dev", package="0.5.9-dev-1")
		(status, output) = self.release()

		self.assertEqual(status, 0, output)
		self.assertEqual(self.repository.git("tag"), "v0.5.9")
		self.assert_spelled("HEAD", "0.5.10dev", "0.5.10-dev-1")

	def test_the_push_commands_are_printed_but_not_run(self):
		self.prepare()
		(status, output) = self.release()

		self.assertIn("git push && git push origin v0.5.2", output)
		self.assertEqual(self.repository.git("remote"), "")

	def test_failing_tests_leave_everything_as_it_was(self):
		self.prepare(passing=False)
		(status, output) = self.release()

		self.assertNotEqual(status, 0)
		self.assertEqual(self.repository.git("status", "--porcelain"), "")
		self.assert_nothing_changed()

	def test_skipping_the_tests_releases_despite_a_failing_suite(self):
		self.prepare(passing=False)
		(status, output) = self.release("--skip-tests")

		self.assertEqual(status, 0, output)
		self.assertEqual(self.repository.git("tag"), "v0.5.2")

	def test_a_file_without_a_version_line_aborts_and_restores(self):
		self.prepare()
		self.repository.commit("Drop the man version", {"docs/gitinspector.txt": ":doctype: manpage\n"})
		before = self.repository.git("rev-parse", "HEAD")
		(status, output) = self.release("--skip-tests")

		self.assertNotEqual(status, 0)
		self.assertIn("docs/gitinspector.txt did not take the version", output)
		self.assertEqual(self.repository.git("rev-parse", "HEAD"), before)
		self.assertEqual(self.repository.git("tag"), "")
		self.assertEqual(self.repository.git("status", "--porcelain"), "")

	def install_hook(self, name, body):
		path = os.path.join(self.repository.location, ".git", "hooks", name)

		with open(path, "w") as hook:
			hook.write("#!/bin/sh\n" + body)

		os.chmod(path, 0o755)

	def test_a_commit_that_fails_leaves_everything_as_it_was(self):
		self.prepare()
		self.install_hook("pre-commit", "exit 1\n")
		(status, output) = self.release("--skip-tests")

		self.assertNotEqual(status, 0)
		self.assertEqual(self.repository.git("status", "--porcelain"), "")
		self.assert_nothing_changed()

	def test_a_failed_development_commit_takes_the_release_back_too(self):
		self.prepare()
		self.install_hook("commit-msg", 'grep -q "dev" "$1" && exit 1\nexit 0\n')
		(status, output) = self.release("--skip-tests")

		self.assertNotEqual(status, 0)
		self.assertEqual(self.repository.git("status", "--porcelain"), "")
		self.assert_nothing_changed()

	def test_a_sed_that_wants_a_backup_suffix_is_satisfied(self):
		self.prepare()
		directory = tempfile.mkdtemp(prefix="gitinspector-test-")

		try:
			with open(os.path.join(directory, "sed"), "w") as stub:
				stub.write('#!/bin/sh\n[ "$1" = "-i" ] && { echo "sed: -i needs a suffix" >&2; exit 1; }\nPATH="${PATH#*:}"\nexec sed "$@"\n')

			os.chmod(os.path.join(directory, "sed"), 0o755)
			(status, output) = self.release("--skip-tests", PATH=directory + os.pathsep + os.environ["PATH"])
		finally:
			shutil.rmtree(directory)

		self.assertEqual(status, 0, output)
		self.assert_spelled("HEAD", "0.5.3dev", "0.5.3-dev-1")
