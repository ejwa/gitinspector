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
import tempfile

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import clone
from .harness import NAMES_ARE_UNRESTRICTED

class SplitBranchTest(unittest.TestCase):
	def test_a_branch_is_split_off_a_path(self):
		self.assertEqual(clone.split_branch("repo:feature"), ("repo", "feature"))
		self.assertEqual(clone.split_branch("../repo:feature"), ("../repo", "feature"))

	def test_the_current_directory_and_a_one_letter_name_take_a_branch(self):
		self.assertEqual(clone.split_branch(".:feature"), (".", "feature"))
		self.assertEqual(clone.split_branch("r:feature"), ("r", "feature"))
		self.assertEqual(clone.split_branch(":feature"), (":feature", None))

	def test_a_branch_may_contain_slashes(self):
		self.assertEqual(clone.split_branch("repo:issue/28"), ("repo", "issue/28"))

	def test_an_argument_without_a_branch_is_left_alone(self):
		self.assertEqual(clone.split_branch("repo"), ("repo", None))
		self.assertEqual(clone.split_branch("repo:"), ("repo:", None))

	def test_a_drive_letter_is_not_a_branch(self):
		self.assertEqual(clone.split_branch("C:\\repo"), ("C:\\repo", None))
		self.assertEqual(clone.split_branch("C:/repo"), ("C:/repo", None))
		self.assertEqual(clone.split_branch("C:\\repo:feature"), ("C:\\repo", "feature"))

	def test_the_scheme_and_the_port_of_a_url_are_not_a_branch(self):
		self.assertEqual(clone.split_branch("https://host/x.git"), ("https://host/x.git", None))
		self.assertEqual(clone.split_branch("ssh://host:22/x.git"), ("ssh://host:22/x.git", None))
		self.assertEqual(clone.split_branch("ssh://host:22"), ("ssh://host:22", None))

	def test_a_branch_is_split_off_a_url(self):
		self.assertEqual(clone.split_branch("https://host/x.git:feature"), ("https://host/x.git", "feature"))
		self.assertEqual(clone.split_branch("ssh://host:22/x.git:issue/28"), ("ssh://host:22/x.git", "issue/28"))

	@unittest.skipUnless(NAMES_ARE_UNRESTRICTED, "Windows does not allow a colon in a file name")
	def test_a_path_that_exists_is_never_split(self):
		directory = tempfile.mkdtemp(prefix="gitinspector-test-")
		colon = os.path.join(directory, "repo:feature")

		try:
			os.mkdir(colon)
			self.assertEqual(clone.split_branch(colon), (colon, None))
		finally:
			shutil.rmtree(directory)
