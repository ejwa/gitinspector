# coding: utf-8
#
# Copyright © 2026 Ejwa Hosting AB. All rights reserved.
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
from __future__ import unicode_literals
import codecs
import io
import sys

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import localization, terminal

#A Windows console reports cp65001, which the interpreters gitinspector supports do not all know;
#the ones that do need another name to stand in for it.
def __unknown_encoding__():
	for name in ["cp65001", "cp65001-gitinspector"]:
		try:
			codecs.lookup(name)
		except LookupError:
			return name

	raise AssertionError("every candidate encoding is known to this interpreter")

UNKNOWN_ENCODING = __unknown_encoding__()

class Stream(object):
	def __init__(self, encoding, isatty=False):
		self.encoding = encoding
		self.buffer = io.BytesIO()
		self.line_buffering = False
		self.written = []
		self.tty = isatty

	def isatty(self):
		return self.tty

	def write(self, text):
		self.written.append(text)

	def flush(self):
		pass

	#Python 2 wraps this object itself, Python 3 wraps its buffer; the text may arrive through either.
	def text(self):
		written = [i.decode("utf-8", "replace") if isinstance(i, bytes) else i for i in self.written]
		return "".join(written) + self.buffer.getvalue().decode("utf-8", "replace")

class UnknownTerminalEncodingTest(unittest.TestCase):
	def setUp(self):
		localization.init()
		self.replaced = (sys.stdout, sys.stderr, sys.stdin, sys.argv)
		sys.stderr = Stream("utf-8")

	def tearDown(self):
		(sys.stdout, sys.stderr, sys.stdin, sys.argv) = self.replaced

	def test_the_encoding_is_named_in_a_warning(self):
		sys.stdout = Stream(UNKNOWN_ENCODING, isatty=True)
		sys.stdin = Stream(UNKNOWN_ENCODING, isatty=True)

		terminal.check_terminal_encoding()

		self.assertIn(UNKNOWN_ENCODING, sys.stderr.text())
		self.assertIn("PYTHONIOENCODING", sys.stderr.text())

	def test_a_configured_encoding_is_not_complained_about(self):
		sys.stdout = Stream("utf-8", isatty=True)
		sys.stdin = Stream("utf-8", isatty=True)

		terminal.check_terminal_encoding()

		self.assertEqual(sys.stderr.text(), "")

	def test_a_terminal_without_an_encoding_is_still_complained_about(self):
		sys.stdout = Stream(None, isatty=True)
		sys.stdin = Stream(None, isatty=True)

		terminal.check_terminal_encoding()

		self.assertIn("PYTHONIOENCODING", sys.stderr.text())

	def test_the_command_line_is_decoded_instead_of_giving_up(self):
		sys.stdin = Stream(UNKNOWN_ENCODING)
		sys.argv = ["gitinspector", "--since=2015-01-01", "a repository"]

		self.assertEqual(terminal.convert_command_line_to_utf8(), sys.argv)

	def test_stdout_is_written_through_utf8_instead(self):
		console = Stream(UNKNOWN_ENCODING, isatty=True)
		sys.stdout = console

		terminal.set_stdout_encoding()
		print("Jörg Müller")
		sys.stdout.flush()

		self.assertIn("Jörg Müller", console.text())

	def test_stderr_is_replaced_when_it_cannot_carry_a_warning(self):
		console = Stream(UNKNOWN_ENCODING)
		sys.stderr = console

		terminal.set_stderr_encoding()

		self.assertIsNot(sys.stderr, console)
		print("Jörg Müller", file=sys.stderr)
		sys.stderr.flush()
		self.assertIn("Jörg Müller", console.text())

	def test_a_usable_stderr_is_left_alone(self):
		console = Stream("utf-8")
		sys.stderr = console

		terminal.set_stderr_encoding()

		self.assertIs(sys.stderr, console)
