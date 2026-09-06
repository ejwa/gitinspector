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

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector.metrics import MetricsLogic

def measure(sample, extension):
	base = os.path.dirname(os.path.realpath(__file__))

	with open(os.path.join(base, "resources", sample), "rb") as source:
		cyclomatic_complexity = MetricsLogic.get_cyclomatic_complexity(source, extension)

	with open(os.path.join(base, "resources", sample), "rb") as source:
		eloc = MetricsLogic.get_eloc(source, extension)

	return (cyclomatic_complexity, eloc)

def cognitive(sample, extension):
	base = os.path.dirname(os.path.realpath(__file__))

	with open(os.path.join(base, "resources", sample), "rb") as source:
		return MetricsLogic.get_cognitive_complexity(source, extension)

class SwiftMetricsTest(unittest.TestCase):
	def test_branches_are_counted_once_and_words_containing_keywords_are_not(self):
		self.assertEqual(measure("metrics_sample.swift", "swift"), (26, 35))

class GoMetricsTest(unittest.TestCase):
	def test_branches_and_exits_are_counted(self):
		self.assertEqual(measure("metrics_sample.go", "go"), (25, 37))

class TypeScriptMetricsTest(unittest.TestCase):
	def test_branches_and_exits_are_counted_for_both_extensions(self):
		self.assertEqual(measure("metrics_sample.ts", "ts"), (22, 30))
		self.assertEqual(measure("metrics_sample.ts", "tsx"), (22, 30))

class RustMetricsTest(unittest.TestCase):
	def test_match_arms_and_loops_are_counted_and_keywords_inside_words_are_not(self):
		self.assertEqual(measure("metrics_sample.rs", "rs"), (31, 45))

class PhpMetricsTest(unittest.TestCase):
	def test_elseif_and_string_cases_are_counted_once(self):
		self.assertEqual(measure("metrics_sample.php", "php"), (22, 34))

class CognitiveComplexityTest(unittest.TestCase):
	def test_a_branch_costs_more_the_deeper_it_is_nested(self):
		self.assertEqual(cognitive("cognitive_sample.js", "js"), 11)
		self.assertEqual(cognitive("cognitive_sample.py", "py"), 10)

	def test_every_language_with_a_token_set_is_measured(self):
		self.assertEqual(cognitive("metrics_sample.swift", "swift"), 9)
		self.assertEqual(cognitive("metrics_sample.go", "go"), 9)
		self.assertEqual(cognitive("metrics_sample.ts", "ts"), 7)
		self.assertEqual(cognitive("metrics_sample.ts", "tsx"), 7)
		self.assertEqual(cognitive("metrics_sample.php", "php"), 8)
		self.assertEqual(cognitive("metrics_sample.rs", "rs"), 13)

	def test_a_language_without_a_token_set_is_left_alone(self):
		self.assertEqual(cognitive("commented_file.tex", "tex"), -1)
