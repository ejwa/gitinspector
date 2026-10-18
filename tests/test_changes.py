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

from gitinspector import changes
from .harness import NAMES_ARE_UNRESTRICTED, Repository, analyze_blame, analyze_changes, analyze_metrics

WINDOW_START = "2018-05-07T15:02:00+0000"
WINDOW_END = "2018-05-07T15:03:00+0000"

def authors_of(analyzed_changes):
	return [commit.author for commit in analyzed_changes.get_commits()]

def blamed_lines(analyzed_blame):
	return dict((author, entry.lines) for (author, entry) in analyzed_blame.get_summed_blames().items())

class EncodingTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	@unittest.skipUnless(NAMES_ARE_UNRESTRICTED, "Windows does not allow a quote in a file name")
	def test_non_ascii_names_are_preserved(self):
		files = {"fil_ö.py": "print(1)\n", "say \"hi\".py": "print(2)\n", "plain.py": "print(3)\n"}
		self.repository.commit("add", files, "Jörg Müller", "jorg@example.com")

		result = analyze_changes(self.repository)
		self.assertEqual(authors_of(result), ["Jörg Müller"])
		self.assertEqual(result.get_latest_author_by_email("jorg@example.com"), "Jörg Müller")
		self.assertEqual(sorted(filediff.name for filediff in result.get_commits()[0].get_filediffs()), sorted(files))

class AuthorlessCommitTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	def test_a_commit_without_an_author_is_named_instead_of_left_blank(self):
		self.repository.commit("first", {"a.py": "x = 1\n"}, "One", "one@example.com")
		self.repository.commit_without_an_author("second", {"b.py": "y = 2\n"})

		result = analyze_changes(self.repository)
		authorinfo = result.get_authorinfo_list()

		self.assertEqual(sorted(authorinfo), ["No Author", "One"])
		self.assertEqual(authorinfo["No Author"].commits, 1)
		self.assertEqual(authorinfo["No Author"].insertions, 1)

class FieldSeparatorTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	@unittest.skipUnless(NAMES_ARE_UNRESTRICTED, "Windows does not allow a bar in a file name")
	def test_a_pipe_in_a_file_name_is_still_read_as_a_diffstat(self):
		self.repository.commit("first", {"a|b|c.py": "x = 1\n"}, "One", "one@example.com")
		self.repository.commit("second", {"plain.py": "y = 2\n"}, "Two", "two@example.com")

		result = analyze_changes(self.repository)

		self.assertEqual(authors_of(result), ["One", "Two"])
		self.assertEqual(sorted(filediff.name for commit in result.get_commits()
		                        for filediff in commit.get_filediffs()), ["a|b|c.py", "plain.py"])
		self.assertEqual(result.get_authorinfo_list()["One"].insertions, 1)

	def test_a_pipe_in_a_name_or_an_email_is_not_read_as_a_diffstat(self):
		self.repository.commit("first", {"a.py": "x = 1\n"}, "Pipe|Name", "pipe|user@example.com")
		self.repository.commit("second", {"b.py": "y = 2\n"}, "Pipe|Name", "pipe|user@example.com")

		result = analyze_changes(self.repository)

		self.assertEqual(authors_of(result), ["Pipe|Name", "Pipe|Name"])
		self.assertEqual(result.get_latest_email_by_author("Pipe|Name"), "pipe|user@example.com")
		self.assertEqual(sorted(filediff.name for commit in result.get_commits()
		                        for filediff in commit.get_filediffs()), ["a.py", "b.py"])

class AuthorIdentityTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	def test_an_email_is_named_after_its_newest_commit(self):
		self.repository.commit("first", {"a.py": "x = 1\n"}, "New Name", "x@example.com", "2015-03-01T12:00:00+0000")
		self.repository.commit("second", {"a.py": "x = 1\ny = 2\n"}, "Old Name", "x@example.com",
		                       "2015-01-01T12:00:00+0000")

		result = analyze_changes(self.repository)
		self.assertEqual(result.get_latest_author_by_email("x@example.com"), "New Name")

	def test_a_name_gets_the_email_of_its_newest_commit(self):
		self.repository.commit("first", {"a.py": "x = 1\n"}, "Same Name", "new@example.com", "2015-03-01T12:00:00+0000")
		self.repository.commit("second", {"a.py": "x = 1\ny = 2\n"}, "Same Name", "old@example.com",
		                       "2015-01-01T12:00:00+0000")

		result = analyze_changes(self.repository)
		self.assertEqual(result.get_latest_email_by_author("Same Name"), "new@example.com")

class WhitespaceOnlyCommitTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()

	def tearDown(self):
		self.repository.remove()

	#git log -w prints a header and a blank line but no diffstat for such a commit, which used to leave
	#the log ending on an empty line and every empty line in it looking like the last one.
	def test_a_trailing_commit_that_only_changes_whitespace_is_analyzed(self):
		self.repository.commit("first", {"a.py": "x = 1\n"}, "One", "one@example.com", "2018-05-07T15:01:00+0000")
		self.repository.commit("second", {"b.py": "y = 2\n"}, "Two", "two@example.com", "2018-05-07T15:02:00+0000")
		self.repository.commit("reindent", {"a.py": "    x = 1\n"}, "Three", "three@example.com", WINDOW_END)

		result = analyze_changes(self.repository)

		self.assertEqual(authors_of(result), ["One", "Two"])
		self.assertEqual(sorted(filediff.name for commit in result.get_commits()
		                        for filediff in commit.get_filediffs()), ["a.py", "b.py"])

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

	def test_an_interval_open_at_either_end_is_bounded_by_the_other(self):
		self.repository.commit("before", {"a.py": "a\n"}, "Zero Author", "zero@example.com", "2018-05-07T15:01:00+0000")
		self.repository.commit("after", {"b.py": "b\n"}, "Third Author", "third@example.com", "2018-05-07T15:04:00+0000")

		self.assertEqual(authors_of(analyze_changes(self.repository, since=WINDOW_START)), ["Third Author"])
		self.assertEqual(authors_of(analyze_changes(self.repository, until=WINDOW_END)), ["Zero Author"])

	def test_the_blame_leaves_out_lines_from_before_the_interval(self):
		self.repository.commit("before", {"a.py": "1\n2\n"}, "Zero Author", "zero@example.com", "2018-05-07T15:01:00+0000")
		self.repository.commit("inside", {"a.py": "1\n2\n3\n"}, "First Author", "first@example.com", "2018-05-07T15:02:30+0000")

		result = analyze_changes(self.repository, since=WINDOW_START)
		self.assertEqual(blamed_lines(analyze_blame(self.repository, result)), {"First Author": 1})

	def test_the_blame_is_read_at_the_end_of_the_interval(self):
		self.repository.commit("before", {"b.py": "b\n"}, "Zero Author", "zero@example.com", "2018-05-07T15:01:00+0000")
		self.repository.commit("inside", {"a.py": "1\n2\n"}, "First Author", "first@example.com", "2018-05-07T15:02:30+0000")
		self.repository.commit("after", {"a.py": "1\n"}, "Third Author", "third@example.com", "2018-05-07T15:04:00+0000")

		result = analyze_changes(self.repository, WINDOW_START, WINDOW_END)
		self.assertEqual(blamed_lines(analyze_blame(self.repository, result)), {"First Author": 2})

	def test_the_blame_counts_the_lines_of_a_first_commit_inside_the_interval(self):
		self.repository.commit("inside", {"a.py": "1\n2\n"}, "First Author", "first@example.com", "2018-05-07T15:02:30+0000")

		result = analyze_changes(self.repository, since=WINDOW_START)
		self.assertEqual(blamed_lines(analyze_blame(self.repository, result)), {"First Author": 2})

class RevisionIntervalTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.first = self.repository.commit("first", {"a.py": "1\n"}, "Zero Author", "zero@example.com",
		                                    "2018-05-07T15:01:00+0000")
		self.second = self.repository.commit("second", {"a.py": "1\n2\n"}, "First Author", "first@example.com",
		                                     "2018-05-07T15:02:30+0000")
		self.repository.git("tag", "start")
		self.third = self.repository.commit("third", {"b.py": "b\n"}, "Third Author", "third@example.com",
		                                    "2018-05-07T15:04:00+0000")

	def tearDown(self):
		self.repository.remove()

	def test_a_since_revision_keeps_itself_and_leaves_out_what_came_before(self):
		for since in ("rev:start", "rev:" + self.second):
			self.assertEqual(authors_of(analyze_changes(self.repository, since=since)), ["First Author", "Third Author"])

	def test_a_since_revision_at_the_root_keeps_everything(self):
		result = analyze_changes(self.repository, since="rev:" + self.first)
		self.assertEqual(authors_of(result), ["Zero Author", "First Author", "Third Author"])

	def test_an_until_revision_keeps_itself(self):
		result = analyze_changes(self.repository, until="rev:" + self.second)
		self.assertEqual(authors_of(result), ["Zero Author", "First Author"])

	def test_revisions_bound_the_interval_at_both_ends(self):
		result = analyze_changes(self.repository, "rev:start", "rev:" + self.second)
		self.assertEqual(authors_of(result), ["First Author"])

	def test_the_same_revision_at_both_ends_keeps_only_itself(self):
		result = analyze_changes(self.repository, "rev:start", "rev:start")
		self.assertEqual(authors_of(result), ["First Author"])

	def test_a_revision_and_a_date_bound_the_interval_together(self):
		self.assertEqual(authors_of(analyze_changes(self.repository, "rev:start", WINDOW_END)), ["First Author"])
		self.assertEqual(authors_of(analyze_changes(self.repository, WINDOW_START, "rev:" + self.third)),
		                 ["First Author", "Third Author"])

	def test_the_blame_leaves_out_lines_from_the_since_revision_and_before(self):
		result = analyze_changes(self.repository, "rev:start", "rev:" + self.second)
		self.assertEqual(blamed_lines(analyze_blame(self.repository, result)), {"First Author": 1})

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

class BranchTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("base", {"base.py": "base\n"}, "Zero Author", "zero@example.com", "2018-05-07T15:01:00+0000")
		self.repository.branch("feature")
		self.repository.commit("feature", {"big.py": "x = 1\n" * 501}, "Feature Author", "feature@example.com",
		                       "2018-05-07T15:02:05+0000")
		self.repository.checkout(self.repository.default_branch)
		self.repository.commit("main", {"main.py": "m\n"}, "Main Author", "main@example.com", "2018-05-07T15:02:30+0000")

	def tearDown(self):
		self.repository.remove()

	def test_the_commits_of_the_branch_are_found_instead_of_those_of_head(self):
		self.assertEqual(authors_of(analyze_changes(self.repository)), ["Zero Author", "Main Author"])
		self.assertEqual(authors_of(analyze_changes(self.repository, branch="feature")), ["Zero Author", "Feature Author"])

	def test_the_branch_is_not_checked_out(self):
		analyze_changes(self.repository, branch="feature")
		self.assertEqual(self.repository.git("symbolic-ref", "--short", "HEAD"), self.repository.default_branch)

	def test_the_lines_of_the_branch_are_blamed(self):
		result = analyze_blame(self.repository, analyze_changes(self.repository, branch="feature"))
		self.assertEqual(blamed_lines(result), {"Zero Author": 1, "Feature Author": 501})

	def test_the_files_of_the_branch_are_measured(self):
		analyze_changes(self.repository, branch="feature")
		self.assertEqual(analyze_metrics(self.repository).eloc, {"big.py": 501})

	def test_a_date_bound_cuts_the_history_of_the_branch(self):
		result = analyze_changes(self.repository, until="2018-05-07T15:01:30+0000", branch="feature")
		self.assertEqual(authors_of(result), ["Zero Author"])
