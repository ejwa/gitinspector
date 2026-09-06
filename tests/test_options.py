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
import sys
import tempfile

try:
	import unittest2 as unittest
except ImportError:
	import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def run_outside_a_repository(*options):
	directory = tempfile.mkdtemp(prefix="gitinspector-test-")
	env = dict(os.environ)
	env["PYTHONIOENCODING"] = "utf-8"
	env["PYTHONPATH"] = os.pathsep.join(filter(None, [PROJECT_ROOT, os.getenv("PYTHONPATH")]))
	env["LANGUAGE"] = "C"

	try:
		process = subprocess.Popen([sys.executable, "-m", "gitinspector.gitinspector"] + list(options),
		                           cwd=directory, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(output, errors) = process.communicate()

		return (process.returncode, output.decode("utf-8", "replace"), errors.decode("utf-8", "replace"))
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
