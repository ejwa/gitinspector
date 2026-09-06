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

from gitinspector import changes
from .harness import Repository, analyze_changes

WINDOW_START = "2018-05-07T15:02:00+0000"
WINDOW_END = "2018-05-07T15:03:00+0000"

def authors_of(analyzed_changes):
	return [commit.author for commit in analyzed_changes.get_commits()]

class EncodingTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	def test_non_ascii_names_are_preserved(self):
		files = {"fil_ö.py": "print(1)\n", "say \"hi\".py": "print(2)\n", "plain.py": "print(3)\n"}
		self.repository.commit("add", files, "Jörg Müller", "jorg@example.com")

		result = analyze_changes(self.repository)
		self.assertEqual(authors_of(result), ["Jörg Müller"])
		self.assertEqual(result.get_latest_author_by_email("jorg@example.com"), "Jörg Müller")
		self.assertEqual(sorted(filediff.name for filediff in result.get_commits()[0].get_filediffs()), sorted(files))

class IntervalTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	def test_commits_inside_the_interval_are_found(self):
		self.repository.commit("before", {"a.py": "a\n"}, "Zero Author", "zero@example.com", "2018-05-07T15:01:00+0000")
		self.repository.commit("first", {"b.py": "b\n"}, "First Author", "first@example.com", "2018-05-07T15:02:05+0000")
		self.repository.commit("second", {"c.py": "c\n"}, "Second Author", "second@example.com", "2018-05-07T15:02:30+0000")
		self.repository.commit("after", {"d.py": "d\n"}, "Third Author", "third@example.com", "2018-05-07T15:04:00+0000")

		result = analyze_changes(self.repository, WINDOW_START, WINDOW_END)
		self.assertEqual(authors_of(result), ["First Author", "Second Author"])

	def test_commits_on_merged_branches_are_found(self):
		self.repository.commit("base", {"base.py": "base\n"}, "Zero Author", "zero@example.com", "2018-05-07T15:01:00+0000")
		self.repository.branch("feature")
		self.repository.commit("feature", {"feature.py": "f\n"}, "First Author", "first@example.com", "2018-05-07T15:02:05+0000")
		self.repository.checkout(self.repository.default_branch)
		self.repository.commit("master", {"master.py": "m\n"}, "Second Author", "second@example.com", "2018-05-07T15:02:30+0000")
		self.repository.merge("feature", "merge", "2018-05-07T15:04:00+0000")

		result = analyze_changes(self.repository, WINDOW_START, WINDOW_END)
		self.assertEqual(authors_of(result), ["First Author", "Second Author"])

		result = analyze_changes(self.repository)
		self.assertEqual(authors_of(result), ["Zero Author", "First Author", "Second Author"])

class ThreadingTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.changes_per_thread = changes.CHANGES_PER_THREAD
		changes.CHANGES_PER_THREAD = 2

	def tearDown(self):
		changes.CHANGES_PER_THREAD = self.changes_per_thread
		self.repository.remove()

	def test_commits_are_gathered_across_threads(self):
		self.repository.commit("one", {"one.py": "1\n"}, "One", "one@example.com", "2018-05-07T15:01:00+0000")
		self.repository.commit("two", {"two.py": "2\n2\n"}, "Two", "two@example.com", "2018-05-07T15:02:00+0000")
		self.repository.branch("feature")
		self.repository.commit("three", {"three.py": "3\n"}, "Three", "three@example.com", "2018-05-07T15:03:00+0000")
		self.repository.checkout(self.repository.default_branch)
		self.repository.commit("four", {"four.py": "4\n"}, "Four", "four@example.com", "2018-05-07T15:04:00+0000")
		self.repository.merge("feature", "merge", "2018-05-07T15:05:00+0000")
		self.repository.commit("five", {"five.py": "5\n"}, "Five", "five@example.com", "2018-05-07T15:06:00+0000")

		result = analyze_changes(self.repository)
		self.assertEqual(authors_of(result), ["One", "Two", "Three", "Four", "Five"])

		authorinfo = result.get_authorinfo_list()
		self.assertEqual(sorted(authorinfo), ["Five", "Four", "One", "Three", "Two"])
		self.assertEqual([authorinfo[author].commits for author in sorted(authorinfo)], [1, 1, 1, 1, 1])
		self.assertEqual(sum(authorinfo[author].insertions for author in authorinfo), 6)
