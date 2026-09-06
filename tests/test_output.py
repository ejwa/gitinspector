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
import subprocess
import sys

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from .harness import Repository

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def read_all(descriptor):
	output = b""

	while True:
		try:
			chunk = os.read(descriptor, 4096)
		except OSError:
			break
		if not chunk:
			break
		output += chunk

	return output

class OutputEncodingTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add", {"fil_ö.py": "print(1)\n"}, "Jörg Müller", "jorg@example.com")

	def tearDown(self):
		self.repository.remove()

	def run_gitinspector(self, stdout, encoding):
		env = dict(os.environ)
		env["PYTHONIOENCODING"] = encoding
		command = [sys.executable, "-m", "gitinspector.gitinspector", "-F", "text", "-f", "**", self.repository.location]
		return subprocess.Popen(command, cwd=PROJECT_ROOT, env=env, stdout=stdout, stderr=subprocess.PIPE)

	def test_redirected_output_is_utf8_whatever_the_terminal_encoding(self):
		process = self.run_gitinspector(subprocess.PIPE, "ascii")
		(output, errors) = process.communicate()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertIn("Jörg Müller".encode("utf-8"), output)

	@unittest.skipIf(sys.platform == "win32", "Pseudo terminals are only available on POSIX systems")
	def test_terminal_output_escapes_characters_the_terminal_cannot_show(self):
		import pty
		(master, slave) = pty.openpty()
		process = self.run_gitinspector(slave, "ascii")
		os.close(slave)
		output = read_all(master)
		os.close(master)
		errors = process.stderr.read()
		process.wait()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertIn(b"J\\xf6rg M\\xfcller", output)
