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
import shutil
import tempfile

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import languages

class ShippedDefinitionsTest(unittest.TestCase):
	def test_the_shipped_definitions_load(self):
		self.assertTrue(languages.get("py"))

	def test_the_extensions_left_without_a_value_stay_without_it(self):
		for extension in ["cc", "hh", "jsx", "html", "xhtml", "jspx"]:
			self.assertTrue("eloc" not in languages.get(extension), extension)
		for extension in ["h", "hh", "hpp", "jsx"]:
			self.assertTrue("cyclomatic" not in languages.get(extension), extension)
			self.assertTrue("cognitive" not in languages.get(extension), extension)

	def test_values_are_read_from_the_file_that_defines_them(self):
		self.assertEqual(languages.get("h")["eloc"], 300)
		self.assertEqual(languages.get("xml")["eloc"], 1000)
		self.assertTrue(languages.get("tex")["comment"]["at_line_start"])

	def test_a_language_with_only_a_line_comment_is_flattened(self):
		self.assertEqual(languages.get("rlib"), {"comment": {"line": "//"}})

	def test_an_unknown_extension_has_no_definition(self):
		self.assertEqual(languages.get("unknown"), {})

class LoadedDefinitionsTest(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.mkdtemp(prefix="gitinspector-test-")

	def tearDown(self):
		shutil.rmtree(self.directory)

	def __write__(self, name, definition):
		with open(os.path.join(self.directory, name), "wb") as definition_file:
			definition_file.write(json.dumps(definition).encode("utf-8"))

	def test_an_override_replaces_a_value(self):
		self.__write__("first.json", {"extensions": ["a", "b"], "comment": {"line": "#"},
		                              "overrides": {"b": {"comment": {"line": "//"}}}})

		definitions = languages.load(self.directory)
		self.assertEqual(definitions["a"]["comment"], {"line": "#"})
		self.assertEqual(definitions["b"]["comment"], {"line": "//"})

	def test_a_null_override_removes_the_key(self):
		self.__write__("first.json", {"extensions": ["a", "b"], "eloc": 500, "overrides": {"b": {"eloc": None}}})

		definitions = languages.load(self.directory)
		self.assertEqual(definitions["a"]["eloc"], 500)
		self.assertTrue("eloc" not in definitions["b"])

	def test_a_note_is_left_out_of_the_definition(self):
		self.__write__("first.json", {"extensions": ["a"], "eloc": 500, "note": "Why."})
		self.assertEqual(languages.load(self.directory)["a"], {"eloc": 500})

	def test_an_unknown_top_level_key_is_rejected(self):
		self.__write__("first.json", {"extensions": ["a"], "unknown": 1})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_an_unknown_key_in_an_override_is_rejected(self):
		self.__write__("first.json", {"extensions": ["a"], "eloc": 500, "overrides": {"a": {"elco": None}}})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_an_override_that_is_not_an_object_is_rejected(self):
		self.__write__("first.json", {"extensions": ["a"], "overrides": {"a": None}})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_missing_extensions_is_rejected(self):
		self.__write__("first.json", {"comment": {"line": "#"}})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_extensions_given_as_a_string_are_rejected(self):
		self.__write__("first.json", {"extensions": "py"})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_a_token_block_without_both_lists_is_rejected(self):
		self.__write__("first.json", {"extensions": ["a"], "cyclomatic": {"branches": ["if"]}})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_a_malformed_file_is_named(self):
		with open(os.path.join(self.directory, "broken.json"), "wb") as definition_file:
			definition_file.write(b"{\"extensions\": [\"a\"],}")

		try:
			languages.load(self.directory)
			self.fail("A malformed file was accepted.")
		except ValueError as error:
			self.assertTrue("broken.json" in str(error))

	def test_an_extension_defined_by_two_files_is_rejected(self):
		self.__write__("first.json", {"extensions": ["a"]})
		self.__write__("second.json", {"extensions": ["a"]})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_an_override_for_an_unknown_extension_is_rejected(self):
		self.__write__("first.json", {"extensions": ["a"], "overrides": {"b": {"eloc": 500}}})
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_a_directory_without_json_files_is_rejected(self):
		self.assertRaises(ValueError, languages.load, self.directory)

	def test_a_missing_directory_is_rejected(self):
		self.assertRaises(ValueError, languages.load, os.path.join(self.directory, "missing"))
