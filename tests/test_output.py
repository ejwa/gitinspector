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
import json
import os
import subprocess
import sys
from xml.etree import ElementTree

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from .harness import NAMES_ARE_UNRESTRICTED, Repository

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def read_all(descriptor):
	output = b""

	while True:
		try:
			chunk = os.read(descriptor, 4096)
		except OSError:
			break
		if not chunk:
			break
		output += chunk

	return output

def gitinspector_process(stdout, encoding, output_format, locations):
	env = dict(os.environ)
	env["PYTHONIOENCODING"] = encoding
	command = [sys.executable, "-m", "gitinspector.gitinspector", "-F", output_format, "-f", "**"] + list(locations)
	return subprocess.Popen(command, cwd=PROJECT_ROOT, env=env, stdout=stdout, stderr=subprocess.PIPE)

class OutputEncodingTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("add", {"fil_ö.py": "print(1)\n"}, "Jörg Müller", "jorg@example.com")

	def tearDown(self):
		self.repository.remove()

	def run_gitinspector(self, stdout, encoding, output_format="text", *locations):
		return gitinspector_process(stdout, encoding, output_format,
		                            list(locations) or [self.repository.location])

	def test_the_header_names_the_analyzed_branch(self):
		self.repository.branch("feature")
		process = self.run_gitinspector(subprocess.PIPE, "utf-8", "json")
		(output, errors) = process.communicate()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertEqual(json.loads(output.decode("utf-8"))["gitinspector"]["branch"], "feature")

	@unittest.skipUnless(NAMES_ARE_UNRESTRICTED, "Windows does not allow < > or a quote in a branch name")
	def test_markup_in_a_branch_name_is_escaped_in_every_format(self):
		branch = "x<script>&\"y'"
		self.repository.branch(branch)

		process = self.run_gitinspector(subprocess.PIPE, "utf-8", "json")
		(output, errors) = process.communicate()
		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertEqual(json.loads(output.decode("utf-8"))["gitinspector"]["branch"], branch)

		process = self.run_gitinspector(subprocess.PIPE, "utf-8", "xml")
		(output, errors) = process.communicate()
		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertEqual(ElementTree.fromstring(output).find("repository").get("branch"), branch)

		process = self.run_gitinspector(subprocess.PIPE, "utf-8", "html")
		(output, errors) = process.communicate()
		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertNotIn(b"<script>&", output)
		self.assertIn(b"&lt;script&gt;&amp;", output)

	@unittest.skipUnless(NAMES_ARE_UNRESTRICTED, "Windows does not allow a quote in a file name")
	def test_a_quote_in_an_author_name_keeps_the_json_and_the_xml_valid(self):
		#Git strips the angle brackets of a name itself; the quote, the ampersand and the backslash
		#are what an author can still carry into a report that is written without a serializer.
		name = "a&b\"c\\d"
		self.repository.commit("add", {"a\"b&c.py": "print(2)\n"}, name, "quote@example.com")

		process = self.run_gitinspector(subprocess.PIPE, "utf-8", "json")
		(output, errors) = process.communicate()
		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		reported = json.loads(output.decode("utf-8"))["gitinspector"]["changes"]["authors"]
		self.assertIn(name, [author["name"] for author in reported])

		process = self.run_gitinspector(subprocess.PIPE, "utf-8", "xml")
		(output, errors) = process.communicate()
		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		authors = ElementTree.fromstring(output).find("changes").find("authors")
		self.assertIn(name, [author.findtext("name") for author in authors])

	def test_the_header_names_the_branch_of_every_repository(self):
		other = Repository()
		other.commit("add", {"other.py": "print(2)\n"})
		other.branch("develop")

		try:
			process = self.run_gitinspector(subprocess.PIPE, "utf-8", "json", self.repository.location, other.location)
			(output, errors) = process.communicate()
		finally:
			other.remove()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertEqual(json.loads(output.decode("utf-8"))["gitinspector"]["branches"],
		                 [self.repository.default_branch, "develop"])

	def test_redirected_output_is_utf8_whatever_the_terminal_encoding(self):
		process = self.run_gitinspector(subprocess.PIPE, "ascii")
		(output, errors) = process.communicate()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertIn("Jörg Müller".encode("utf-8"), output)

	@unittest.skipIf(sys.platform == "win32", "Pseudo terminals are only available on POSIX systems")
	def test_terminal_output_escapes_characters_the_terminal_cannot_show(self):
		import pty
		(master, slave) = pty.openpty()
		process = self.run_gitinspector(slave, "ascii")
		os.close(slave)
		output = read_all(master)
		os.close(master)
		errors = process.stderr.read()
		process.wait()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		self.assertIn(b"J\\xf6rg M\\xfcller", output)

class ChangesTotalTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("first", {"a.py": "one\ntwo\nthree\n"}, "Author One", "one@example.com")
		self.repository.commit("second", {"b.py": "four\n"}, "Author Two", "two@example.com")
		self.repository.commit("third", {"a.py": "one\n"}, "Author Two", "two@example.com")

	def tearDown(self):
		self.repository.remove()

	def report(self, output_format):
		process = gitinspector_process(subprocess.PIPE, "utf-8", output_format, [self.repository.location])
		(output, errors) = process.communicate()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		return output.decode("utf-8")

	def reported_total(self):
		return json.loads(self.report("json"))["gitinspector"]["changes"]["total"]

	def test_the_json_total_sums_every_author(self):
		changes = json.loads(self.report("json"))["gitinspector"]["changes"]

		for field in ("commits", "insertions", "deletions"):
			self.assertEqual(changes["total"][field], sum(author[field] for author in changes["authors"]))

		self.assertGreater(changes["total"]["insertions"], 0)
		self.assertEqual(changes["total"]["percentage_of_changes"], 100)

	def test_the_xml_total_agrees_with_the_json_total(self):
		total = self.reported_total()
		reported = ElementTree.fromstring(self.report("xml").encode("utf-8")).find("changes").find("total")

		self.assertEqual(int(reported.findtext("commits")), total["commits"])
		self.assertEqual(int(reported.findtext("insertions")), total["insertions"])
		self.assertEqual(int(reported.findtext("deletions")), total["deletions"])
		self.assertEqual(float(reported.findtext("percentage-of-changes")), total["percentage_of_changes"])

	def test_the_text_table_ends_with_the_total(self):
		total = self.reported_total()
		lines = [line for line in self.report("text").splitlines() if line.startswith("Total")]

		self.assertEqual(len(lines), 1)
		self.assertEqual(lines[0].split()[1:], [str(total["commits"]), str(total["insertions"]),
		                                        str(total["deletions"]), "100.00"])

	def test_the_html_total_is_a_table_foot_below_the_authors(self):
		total = self.reported_total()
		table = self.report("html").split("<table id=\"changes\"")[1].split("</table>")[0]
		foot = table.split("<tfoot>")[1]

		self.assertLess(table.index("</tbody>"), table.index("<tfoot>"))
		self.assertIn(">+" + str(total["insertions"]) + "<", foot)
		self.assertIn(">−" + str(total["deletions"]) + "<", foot)
		self.assertIn(">" + str(total["commits"]) + "<", foot)

class HtmlReportTest(unittest.TestCase):
	def setUp(self):
		self.repository = Repository()
		self.repository.commit("first", {"a.py": "one\ntwo\n"}, "Author One", "one@example.com")

	def tearDown(self):
		self.repository.remove()

	def report(self, output_format):
		process = gitinspector_process(subprocess.PIPE, "utf-8", output_format, [self.repository.location])
		(output, errors) = process.communicate()

		self.assertEqual(process.returncode, 0, errors.decode("utf-8", "replace"))
		return output.decode("utf-8")

	def test_the_report_carries_the_stylesheet_and_the_script(self):
		report = self.report("html")

		self.assertIn(".gi-page {", report)
		self.assertIn("gitinspector.theme", report)

	def test_the_report_offers_both_themes_and_the_mode_toggle(self):
		report = self.report("html")

		self.assertIn("data-gi-theme=\"default\"", report)
		self.assertIn("data-gi-theme=\"terminal\"", report)
		self.assertIn("data-gi-mode-toggle=\"true\"", report)

	def test_the_embedded_report_fetches_nothing(self):
		#The embedded format is the one that has to keep working without a network, so it may not
		#link a stylesheet, a script or an image from anywhere.
		report = self.report("htmlembedded")

		self.assertNotIn("<link", report)
		self.assertNotIn("src=\"http", report)
		self.assertNotIn("<script src", report)

	def test_the_linked_report_shows_the_gravatars(self):
		self.assertIn("src=\"https://www.gravatar.com/avatar/", self.report("html"))

	def test_markup_in_an_author_name_is_escaped_everywhere_it_is_shown(self):
		#Git strips the angle brackets of a name itself, so an ampersand and a quote are as much
		#markup as an author can carry. The quote matters: the name is written into the title of
		#its share of the changes, where a bare quote would end the attribute rather than the word.
		self.repository.commit("second", {"b.py": "three\n"}, "a&b\"c", "markup@example.com")
		report = self.report("html")

		self.assertIn("a&amp;b&quot;c", report)
		self.assertNotIn("a&b\"c", report)
