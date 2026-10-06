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

from __future__ import unicode_literals
import itertools
import random

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector.changes import AuthorInfo
from gitinspector.timeline import TimelineData
from .harness import Repository, analyze_changes

WIDTHS = (9, 24)

class FakeChanges(object):
	def __init__(self, periods):
		self.authordateinfo = {}

		for (year, changes) in enumerate(periods, 1900):
			for (author, (insertions, deletions)) in enumerate(changes):
				info = AuthorInfo()
				(info.insertions, info.deletions) = (insertions, deletions)
				self.authordateinfo[("{0}-01-15".format(year), "author{0}".format(author))] = info

	def get_authordateinfo_list(self):
		return self.authordateinfo

	def get_latest_email_by_author(self, name):
		return ""

def signs_of(changes, max_width):
	timeline = TimelineData(FakeChanges([changes]), False)
	return [timeline.get_author_signs_in_period("author{0}".format(author), "1900-01", max_width)
	        for author in range(len(changes))]

#The search that get_author_signs_in_period replaced. It stepped once per author checked rather than once per
#round, so with several authors its answer hung on the order the entries came out of a dict.
def searched_signs_of(changes, max_width):
	total = float(sum(insertions + deletions for (insertions, deletions) in changes))
	multiplier = 0

	while True:
		for (insertions, deletions) in changes:
			if multiplier * (insertions + deletions) / total > max_width:
				return [(int(multiplier * (i / total)), int(multiplier * (d / total))) for (i, d) in changes]

			multiplier += 0.25

def random_periods(count):
	generator = random.Random(97)
	periods = []

	while len(periods) < count:
		changes = [(generator.randint(0, 200), generator.randint(0, 200)) for _ in range(generator.randint(1, 4))]
		if sum(sum(change) for change in changes) > 0:
			periods.append(changes)

	return periods

class LoneAuthorTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add", {"a.py": "x = 1\n" * 10})
		self.timeline = TimelineData(analyze_changes(self.repository), False)

	def tearDown(self):
		self.repository.remove()

	def test_a_lone_author_fills_the_width(self):
		self.assertEqual(self.timeline.get_author_signs_in_period("Test Author", "2015-01", 24), (24, 0))
		self.assertEqual(self.timeline.get_author_signs_in_period("Test Author", "2015-01", 9), (9, 0))

	def test_an_absent_author_gets_no_signs(self):
		self.assertEqual(self.timeline.get_author_signs_in_period("Nobody", "2015-01", 24), (0, 0))

class SignsTest(unittest.TestCase):
	def test_the_busiest_author_sets_the_scale_for_everyone_in_the_period(self):
		self.assertEqual(signs_of([(5, 5)], 24), [(12, 12)])
		self.assertEqual(signs_of([(7, 0), (3, 0)], 24), [(24, 0), (10, 0)])
		self.assertEqual(signs_of([(3, 0), (7, 0)], 9), [(3, 0), (9, 0)])
		self.assertEqual(signs_of([(30, 10), (60, 0)], 24), [(12, 4), (24, 0)])

	def test_the_signs_match_the_search_wherever_its_entry_order_did_not_matter(self):
		compared = 0

		for changes in random_periods(100):
			for max_width in WIDTHS:
				orders = list(itertools.permutations(range(len(changes))))
				searched = set(tuple(searched_signs_of([changes[i] for i in order], max_width)[order.index(author)]
				                     for author in range(len(changes))) for order in orders)

				if len(searched) == 1:
					self.assertEqual(signs_of(changes, max_width), list(searched.pop()), changes)
					compared += 1

		self.assertTrue(compared > 100, compared)

	def test_the_busiest_author_fills_the_width_and_nobody_passes_it(self):
		for changes in random_periods(100):
			for max_width in WIDTHS:
				widths = [sum(signs) for signs in signs_of(changes, max_width)]
				self.assertTrue(max(widths) in (max_width - 1, max_width), (changes, widths))

	def test_the_busiest_author_fills_the_width_whatever_the_entry_order(self):
		changes = [(96, 0), (1, 0), (1, 0), (1, 0), (1, 0)]
		self.assertTrue(25 in [searched_signs_of(changes, 24)[0][0], searched_signs_of(changes[::-1], 24)[-1][0]])
		self.assertEqual(signs_of(changes, 24)[0], (24, 0))

	def test_a_period_without_changed_lines_gets_no_signs(self):
		self.assertEqual(signs_of([(0, 0), (0, 0)], 24), [(0, 0), (0, 0)])
