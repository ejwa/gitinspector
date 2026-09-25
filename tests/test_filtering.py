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

from gitinspector import changes, filtering
from .harness import Repository, analyze_blame, analyze_changes, analyze_metrics

def rules(filter_type):
	return filtering.get()[filter_type][0]

def blamed_lines(analyzed_blame):
	return dict((author, entry.lines) for (author, entry) in analyzed_blame.get_summed_blames().items())

def insertions(analyzed_changes):
	authorinfo = analyzed_changes.get_authorinfo_list()
	return dict((author, authorinfo[author].insertions) for author in authorinfo)

class RuleTest(unittest.TestCase):
	def setUp(self):
		filtering.clear()

	def tearDown(self):
		filtering.clear()

	def test_a_rule_without_a_kind_filters_files(self):
		filtering.add("docs/")
		self.assertEqual(rules("file"), set(["docs/"]))

	def test_the_kind_of_a_rule_is_case_insensitive(self):
		filtering.add("Author:Bob,EMAIL:bob@,Revision:abc,message:wip")
		self.assertEqual((rules("author"), rules("email"), rules("revision"), rules("message")),
		                 (set(["Bob"]), set(["bob@"]), set(["abc"]), set(["wip"])))

	def test_rules_are_separated_by_commas_and_added_together(self):
		filtering.add("a.py,author:Bob")
		filtering.add("b.py")
		self.assertEqual((rules("file"), rules("author")), (set(["a.py", "b.py"]), set(["Bob"])))

	def test_clearing_forgets_both_the_rules_and_what_they_matched(self):
		filtering.add("a.py")
		filtering.set_filtered("a.py")
		filtering.clear()

		self.assertEqual((rules("file"), filtering.get_filered()), (set(), set()))
		self.assertFalse(filtering.has_filtered())

	def test_a_rule_is_a_regular_expression_searched_anywhere(self):
		filtering.add(r"^src/.*\.py$")
		self.assertTrue(filtering.set_filtered("src/a.py"))
		self.assertFalse(filtering.set_filtered("lib/src/a.py"))
		self.assertFalse(filtering.set_filtered("src/a.pyc"))

	def test_what_a_rule_matched_is_remembered_for_the_report(self):
		filtering.add("author:^B")
		filtering.set_filtered("Bob", "author")
		filtering.set_filtered("Alice", "author")

		self.assertEqual(filtering.get_filered("author"), set(["Bob"]))
		self.assertTrue(filtering.has_filtered())

	def test_an_invalid_rule_raises(self):
		filtering.add("author:[")
		self.assertRaises(filtering.InvalidRegExpError, filtering.set_filtered, "Bob", "author")

class AnalysisTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.first = self.repository.commit("add a", {"a.py": "1\n2\n"}, "Alice", "alice@example.com")
		self.second = self.repository.commit("add b", {"b.py": "1\n2\n3\n"}, "Bob", "bob@example.com")
		self.third = self.repository.commit("wip on c", {"c.py": "1\n"}, "Alice", "alice@example.com")

	def tearDown(self):
		filtering.clear()
		self.repository.remove()

	def analyze(self, exclude):
		analyzed_changes = analyze_changes(self.repository, exclude=exclude)
		return (insertions(analyzed_changes), blamed_lines(analyze_blame(self.repository, analyzed_changes)))

	def test_nothing_is_left_out_without_a_rule(self):
		self.assertEqual(self.analyze(None), ({"Alice": 3, "Bob": 3}, {"Alice": 3, "Bob": 3}))

	def test_a_file_rule_leaves_out_the_file(self):
		self.assertEqual(self.analyze("b.py"), ({"Alice": 3}, {"Alice": 3}))
		self.assertEqual(filtering.get_filered(), set(["b.py"]))

	def test_an_author_rule_leaves_out_the_author(self):
		self.assertEqual(self.analyze("author:^Bob$"), ({"Alice": 3}, {"Alice": 3}))
		self.assertEqual(filtering.get_filered("author"), set(["Bob"]))

	def test_an_email_rule_leaves_out_the_author_behind_the_email(self):
		self.assertEqual(self.analyze("email:alice@"), ({"Bob": 3}, {"Bob": 3}))
		self.assertEqual(filtering.get_filered("email"), set(["alice@example.com"]))

	def test_a_revision_rule_leaves_out_the_commit(self):
		self.assertEqual(self.analyze("revision:" + self.first[0:10]), ({"Alice": 1, "Bob": 3}, {"Alice": 1, "Bob": 3}))
		self.assertEqual(filtering.get_filered("revision"), set([self.first]))

	def test_a_revision_rule_leaves_out_only_its_own_lines_of_a_file(self):
		self.repository.commit("grow a", {"a.py": "1\n2\n3\n4\n5\n"}, "Alice", "alice@example.com")
		self.assertEqual(self.analyze("revision:" + self.first[0:10])[1], {"Alice": 4, "Bob": 3})

	def test_a_message_rule_leaves_out_the_commit_and_its_lines(self):
		self.assertEqual(self.analyze("message:^wip"), ({"Alice": 2, "Bob": 3}, {"Alice": 2, "Bob": 3}))
		self.assertEqual(rules("revision"), set([self.third]))

	def test_rules_of_different_kinds_are_combined(self):
		self.assertEqual(self.analyze("a.py,author:Bob"), ({"Alice": 1}, {"Alice": 1}))

	def test_a_file_rule_leaves_out_the_metrics_of_the_file(self):
		self.repository.commit("grow", {"big.py": "x = 1\n" * 501, "huge.py": "x = 1\n" * 501}, "Bob", "bob@example.com")
		analyze_changes(self.repository, exclude="huge")

		self.assertEqual(list(analyze_metrics(self.repository).eloc), ["big.py"])

class IntervalTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add", {"a.py": "1\n2\n3\n4\n"}, "Alice", "alice@example.com", "2018-05-01T10:00:00+0000")
		self.repository.commit("cut", {"a.py": "1\n"}, "Bob", "bob@example.com", "2018-05-02T10:00:00+0000")

	def tearDown(self):
		filtering.clear()
		self.repository.remove()

	def test_the_blame_is_read_at_the_end_of_the_interval_even_when_its_last_commit_is_left_out(self):
		for exclude in ["author:Bob", "email:bob@", "message:cut"]:
			analyzed_changes = analyze_changes(self.repository, until="2018-05-03", exclude=exclude)
			self.assertEqual(blamed_lines(analyze_blame(self.repository, analyzed_changes)), {"Alice": 1}, exclude)

#Threading the analysis of the changes once broke every rule without any test noticing, so the rules are
#checked again with the commits spread over several threads.
class ThreadedAnalysisTest(AnalysisTest):
	def setUp(self):
		self.changes_per_thread = changes.CHANGES_PER_THREAD
		changes.CHANGES_PER_THREAD = 1
		AnalysisTest.setUp(self)

	def tearDown(self):
		changes.CHANGES_PER_THREAD = self.changes_per_thread
		AnalysisTest.tearDown(self)
