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

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import git
from .harness import Repository

class DecodingTest(unittest.TestCase):
	def test_utf8_is_decoded(self):
		self.assertEqual(git.decode("Jörg".encode("utf-8")), "Jörg")

	def test_other_bytes_fall_back_to_latin1(self):
		self.assertEqual(git.decode(b"J\xf6rg"), "Jörg")

class UnquotingTest(unittest.TestCase):
	def test_unquoted_paths_are_left_alone(self):
		self.assertEqual(git.unquote("plain/file.py"), "plain/file.py")

	def test_octal_escapes_are_decoded_as_utf8(self):
		self.assertEqual(git.unquote("\"fil_\\303\\266.py\""), "fil_ö.py")

	def test_character_escapes_are_decoded(self):
		self.assertEqual(git.unquote("\"say \\\"hi\\\"\\t\\\\.py\""), "say \"hi\"\t\\.py")

class BranchTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.first = self.repository.commit("first", {"a.py": "a\n"})
		self.repository.commit("second", {"b.py": "b\n"})

	def tearDown(self):
		self.repository.remove()

	def test_the_checked_out_branch_is_reported(self):
		self.assertEqual(git.get_branch(self.repository.location), self.repository.default_branch)
		self.repository.branch("feature")
		self.assertEqual(git.get_branch(self.repository.location), "feature")

	def test_a_detached_head_reports_the_commit(self):
		self.repository.checkout(self.first)
		self.assertEqual(git.get_branch(self.repository.location), self.first[0:7])
