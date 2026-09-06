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
import gettext
import os
import sys

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import localization

class LanguageDetectionTest(unittest.TestCase):
	def setUp(self):
		self.environment = dict(os.environ)

		for variable in localization.LANGUAGE_VARIABLES:
			os.environ.pop(variable, None)

	def tearDown(self):
		os.environ.clear()
		os.environ.update(self.environment)

	@unittest.skipIf(sys.platform == "win32", "Windows falls back to the language of the user account")
	def test_no_language_variables_means_no_language(self):
		self.assertEqual(localization.__get_language__(), None)

	def test_language_is_taken_from_lang(self):
		os.environ["LANG"] = "sv_SE.UTF-8"
		self.assertEqual(localization.__get_language__(), "sv")

	def test_language_list_takes_precedence(self):
		os.environ["LANG"] = "sv_SE.UTF-8"
		os.environ["LANGUAGE"] = "de_DE:sv"
		self.assertEqual(localization.__get_language__(), "de")

	def test_lc_all_takes_precedence_over_lang(self):
		os.environ["LANG"] = "sv_SE.UTF-8"
		os.environ["LC_ALL"] = "fr_FR.UTF-8"
		self.assertEqual(localization.__get_language__(), "fr")

	def test_empty_variables_are_ignored(self):
		os.environ["LC_ALL"] = ""
		os.environ["LANG"] = "pl_PL"
		self.assertEqual(localization.__get_language__(), "pl")

class TranslationLoadingTest(unittest.TestCase):
	def test_existing_catalog_is_loaded(self):
		self.assertIsInstance(localization.__load_translation__("sv"), gettext.GNUTranslations)

	def test_missing_catalog_falls_back_to_no_translation(self):
		self.assertIsInstance(localization.__load_translation__("xx"), gettext.NullTranslations)
		self.assertNotIsInstance(localization.__load_translation__("xx"), gettext.GNUTranslations)
