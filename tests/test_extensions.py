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
import re

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector.extensions import DEFAULT_EXTENSIONS

__documents__ = ["README.md", "DESCRIPTION.txt", os.path.join("docs", "gitinspector.txt"),
                 os.path.join("docs", "gitinspector.1")]

__documented_extensions__ = re.compile(r"default(?: extensions used are)?: ([a-z0-9,]+)")

def documented_in(document):
	base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

	with open(os.path.join(base, document), "rb") as source:
		content = source.read().decode("utf-8", "replace")

	return [listed.split(",") for listed in __documented_extensions__.findall(content)]

class DefaultExtensionsTest(unittest.TestCase):
	def test_php_is_analyzed_without_asking_for_it(self):
		self.assertIn("php", DEFAULT_EXTENSIONS)

	def test_every_document_lists_the_default_extensions(self):
		for document in __documents__:
			listed = documented_in(document)
			self.assertTrue(listed, "{0} does not document the default extensions".format(document))

			for extensions in listed:
				self.assertEqual(extensions, DEFAULT_EXTENSIONS,
				                 "{0} does not list the default extensions".format(document))
