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

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector.timeline import TimelineData
from .harness import Repository, analyze_changes

class MultiplierTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add", {"a.py": "x = 1\n" * 10})
		self.timeline = TimelineData(analyze_changes(self.repository), False)

	def tearDown(self):
		self.repository.remove()

	def test_the_multiplier_is_the_first_step_that_overflows_the_width(self):
		self.assertEqual(self.timeline.get_multiplier("2015-01", 24), 24.25)
		self.assertEqual(self.timeline.get_multiplier("2015-01", 9), 9.25)

	def test_the_multiplier_stays_the_same_when_asked_again(self):
		self.assertEqual(self.timeline.get_multiplier("2015-01", 24), self.timeline.get_multiplier("2015-01", 24))
