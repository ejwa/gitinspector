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
import json
import os
import subprocess
import sys

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from .harness import Repository

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

#The interval sits a fortnight away from every commit, so that no boundary depends on a time zone.
SINCE = "2015-01-15"
UNTIL = "2015-05-15"

def lines(count, prefix):
	return "".join("%s %d\n" % (prefix, number) for number in range(1, count + 1))

def report(locations, *options):
	env = dict(os.environ)
	env["PYTHONIOENCODING"] = "utf-8"
	env["LANGUAGE"] = "C"
	command = [sys.executable, "-m", "gitinspector.gitinspector", "-F", "json", "-f", "**"]
	process = subprocess.Popen(command + list(options) + list(locations), cwd=PROJECT_ROOT, env=env,
	                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(output, errors) = process.communicate()

	if process.returncode != 0:
		raise AssertionError("gitinspector failed with {0}: {1}".format(process.returncode,
		                     errors.decode("utf-8", "replace")))

	return json.loads(output.decode("utf-8"))["gitinspector"]

def changes_of(reported):
	return dict((author["name"], [author["commits"], author["insertions"], author["deletions"]])
	            for author in reported["changes"]["authors"])

def blame_of(reported):
	return dict((author["name"], author["lines"]) for author in reported["blame"]["authors"])

def summed(reports, of):
	expected = {}

	for reported in reports:
		for (name, value) in of(reported).items():
			if isinstance(value, list):
				running = expected.setdefault(name, [0] * len(value))
				for index in range(len(value)):
					running[index] += value[index]
			else:
				expected[name] = expected.get(name, 0) + value

	return expected

#Alpha commits to both repositories, which is what a merge of the author totals has to get right.
def build_repositories():
	first = Repository()
	first.commit("a", {"a.py": lines(10, "a")}, "Alpha", "alpha@example.com", "2015-01-01T12:00:00+0000")
	first.commit("b", {"b.py": lines(20, "b")}, "Alpha", "alpha@example.com", "2015-02-01T12:00:00+0000")
	first.commit("c", {"c.py": lines(5, "c")}, "Beta", "beta@example.com", "2015-03-01T12:00:00+0000")

	second = Repository()
	second.commit("d", {"d.py": lines(7, "d")}, "Alpha", "alpha@example.com", "2015-04-01T12:00:00+0000")
	second.commit("e", {"e.py": lines(8, "e")}, "Gamma", "gamma@example.com", "2015-05-01T12:00:00+0000")
	second.commit("f", {"e.py": lines(5, "e")}, "Gamma", "gamma@example.com", "2015-06-01T12:00:00+0000")

	return (first, second)

class SeveralRepositoriesTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.repositories = build_repositories()
		cls.locations = [repository.location for repository in cls.repositories]
		cls.separate = [report([location]) for location in cls.locations]
		cls.together = report(cls.locations)

	@classmethod
	def tearDownClass(cls):
		for repository in cls.repositories:
			repository.remove()

	def test_each_repository_on_its_own_is_counted_as_committed(self):
		self.assertEqual(changes_of(self.separate[0]), {"Alpha": [2, 30, 0], "Beta": [1, 5, 0]})
		self.assertEqual(changes_of(self.separate[1]), {"Alpha": [1, 7, 0], "Gamma": [2, 8, 3]})

	def test_the_authors_of_both_repositories_are_added_together(self):
		self.assertEqual(changes_of(self.together),
		                 {"Alpha": [3, 37, 0], "Beta": [1, 5, 0], "Gamma": [2, 8, 3]})
		self.assertEqual(changes_of(self.together), summed(self.separate, changes_of))

	def test_the_total_is_the_sum_of_the_separate_totals(self):
		totals = [reported["changes"]["total"] for reported in self.separate]
		self.assertEqual([totals[0][key] for key in ("commits", "insertions", "deletions")], [3, 35, 0])
		self.assertEqual([totals[1][key] for key in ("commits", "insertions", "deletions")], [3, 15, 3])

		for key in ("commits", "insertions", "deletions"):
			self.assertEqual(self.together["changes"]["total"][key], totals[0][key] + totals[1][key], key)

	def test_the_surviving_lines_are_added_together(self):
		self.assertEqual(blame_of(self.together), {"Alpha": 37, "Beta": 5, "Gamma": 5})
		self.assertEqual(blame_of(self.together), summed(self.separate, blame_of))

	def test_every_repository_is_named_in_the_header(self):
		self.assertEqual(self.together["repositories"],
		                 [os.path.basename(location) for location in self.locations])

class SeveralRepositoriesIntervalTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.repositories = build_repositories()
		cls.locations = [repository.location for repository in cls.repositories]
		interval = ["--timeline", "--since=" + SINCE, "--until=" + UNTIL]
		cls.separate = [report([location], *interval) for location in cls.locations]
		cls.together = report(cls.locations, *interval)

	@classmethod
	def tearDownClass(cls):
		for repository in cls.repositories:
			repository.remove()

	def test_the_interval_leaves_out_the_commits_around_it(self):
		self.assertEqual(changes_of(self.separate[0]), {"Alpha": [1, 20, 0], "Beta": [1, 5, 0]})
		self.assertEqual(changes_of(self.separate[1]), {"Alpha": [1, 7, 0], "Gamma": [1, 8, 0]})

	def test_the_authors_of_both_repositories_are_added_together(self):
		self.assertEqual(changes_of(self.together),
		                 {"Alpha": [2, 27, 0], "Beta": [1, 5, 0], "Gamma": [1, 8, 0]})
		self.assertEqual(changes_of(self.together), summed(self.separate, changes_of))

	def test_the_total_is_the_sum_of_the_separate_totals(self):
		totals = [reported["changes"]["total"] for reported in self.separate]
		self.assertEqual([totals[0][key] for key in ("commits", "insertions", "deletions")], [2, 25, 0])
		self.assertEqual([totals[1][key] for key in ("commits", "insertions", "deletions")], [2, 15, 0])
		self.assertEqual([self.together["changes"]["total"][key]
		                  for key in ("commits", "insertions", "deletions")], [4, 40, 0])

	def test_the_timeline_stays_inside_the_interval(self):
		periods = [period["name"] for period in self.together["timeline"]["periods"]]

		self.assertTrue(periods)
		self.assertTrue(all(SINCE[0:7] <= period <= UNTIL[0:7] for period in periods), periods)
