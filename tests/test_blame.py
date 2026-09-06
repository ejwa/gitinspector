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

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from .harness import Repository, analyze_blame, analyze_changes

class SpecialFilenameTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	def test_files_with_quotes_in_their_names_are_blamed(self):
		files = {"`file_with_backticks`.txt": "one\ntwo\nthree\n",
		         "file 'with' single quotes.txt": "four\nfive\n",
		         "plain.txt": "six\n"}
		self.repository.commit("add files", files)

		analyzed_changes = analyze_changes(self.repository)
		result = analyze_blame(self.repository, analyzed_changes)

		blamed_files = sorted(filename for (author, filename) in result.blames)
		self.assertEqual(blamed_files, sorted(files))
		self.assertEqual(sum(entry.lines for entry in result.blames.values()), 6)

	def test_non_ascii_names_are_blamed(self):
		files = {"fil_ö.py": "print(1)\nprint(2)\n", "say \"hi\".py": "print(3)\n"}
		self.repository.commit("add files", files, "Jörg Müller", "jorg@example.com")

		analyzed_changes = analyze_changes(self.repository)
		result = analyze_blame(self.repository, analyzed_changes)

		self.assertEqual(sorted(result.blames), [("Jörg Müller", "fil_ö.py"), ("Jörg Müller", "say \"hi\".py")])
		self.assertEqual(sum(entry.lines for entry in result.blames.values()), 3)
