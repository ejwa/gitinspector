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
import glob
import os
import shutil
import subprocess
import tempfile

try:
	import unittest2 as unittest
except ImportError:
	import unittest

TRANSLATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                            "gitinspector", "translations")

def catalogs():
	return sorted(glob.glob(os.path.join(TRANSLATIONS, "messages_*.po")))

def msgfmt(*arguments):
	env = dict(os.environ)
	env["LC_ALL"] = "C"
	process = subprocess.Popen(["msgfmt"] + list(arguments), env=env,
	                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = process.communicate()[0]

	return (process.returncode, output.decode("utf-8", "replace").strip())

def gettext_tools_are_available():
	try:
		msgfmt("--version")
		return True
	except OSError:
		return False

def messages_of(path):
	with open(path, "rb") as catalog:
		return gettext.GNUTranslations(catalog)._catalog

@unittest.skipUnless(gettext_tools_are_available(), "The gettext tools are needed to read the translations")
class TranslationTest(unittest.TestCase):
	def test_every_translation_passes_the_format_checks(self):
		for source in catalogs():
			(status, output) = msgfmt("--check", "-o", os.devnull, source)
			self.assertEqual(status, 0, "{0} is rejected by msgfmt:\n{1}".format(os.path.basename(source), output))

	def test_every_translation_is_compiled_from_its_current_source(self):
		directory = tempfile.mkdtemp(prefix="gitinspector-test-")

		try:
			for source in catalogs():
				rebuilt = os.path.join(directory, "messages.mo")
				(status, output) = msgfmt("-o", rebuilt, source)

				self.assertEqual(status, 0, output)
				self.assertTrue(messages_of(source[:-3] + ".mo") == messages_of(rebuilt),
				                "{0} was not regenerated after its source changed".format(
				                os.path.basename(source[:-3] + ".mo")))
		finally:
			shutil.rmtree(directory)
