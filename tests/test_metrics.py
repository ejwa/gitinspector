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

class SwiftMetricsTest(unittest.TestCase):
	def test_branches_are_counted_once_and_words_containing_keywords_are_not(self):
		self.assertEqual(measure("metrics_sample.swift", "swift"), (26, 35))

class GoMetricsTest(unittest.TestCase):
	def test_branches_and_exits_are_counted(self):
		self.assertEqual(measure("metrics_sample.go", "go"), (25, 37))
