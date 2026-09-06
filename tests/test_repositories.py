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
import json
import os
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import metrics
from . import reference

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CACHE = os.getenv("GITINSPECTOR_TEST_REPOSITORIES") or os.path.join(tempfile.gettempdir(),
                                                                    "gitinspector-test-repositories")
REPORT_OPTIONS = ["--timeline", "--metrics", "--responsibilities", "--list-file-types"]

class Repository(object):
	def __init__(self, name, file_types, url=None, tag=None):
		self.name = name
		self.file_types = file_types
		self.url = url
		self.tag = tag

	def prepare(self):
		if self.url is None:
			return PROJECT_ROOT

		location = os.path.join(CACHE, self.name)

		if not os.path.isdir(location):
			self.__clone__(location)
		elif reference.git(location, "rev-parse", "HEAD") != reference.git(location, "rev-parse", self.tag + "^{commit}"):
			reference.git(location, "checkout", "-q", self.tag)

		return location

	def __clone__(self, location):
		try:
			reference.git(PROJECT_ROOT, "clone", "-q", "--branch", self.tag, self.url, location)
		except (subprocess.CalledProcessError, OSError):
			shutil.rmtree(location, ignore_errors=True)
			raise unittest.SkipTest("{0} could not be cloned from {1}".format(self.name, self.url))

GITINSPECTOR = Repository("gitinspector", "**")
REQUESTS = Repository("requests", "py", "https://github.com/psf/requests.git", "v2.32.3")
JQ = Repository("jq", "c,h", "https://github.com/jqlang/jq.git", "jq-1.7.1")
COBRA = Repository("cobra", "go", "https://github.com/spf13/cobra.git", "v1.8.1")

def report(output_format, file_types, locations, *options):
	env = dict(os.environ)
	env["PYTHONIOENCODING"] = "utf-8"
	command = [sys.executable, "-m", "gitinspector.gitinspector", "-F", output_format, "-f", file_types]
	process = subprocess.Popen(command + REPORT_OPTIONS + list(options) + locations, cwd=PROJECT_ROOT, env=env,
	                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(output, errors) = process.communicate()

	if process.returncode != 0:
		raise AssertionError("gitinspector failed with {0}: {1}".format(process.returncode, errors.decode("utf-8", "replace")))

	return output.decode("utf-8")

def json_report(file_types, locations, *options):
	return json.loads(report("json", file_types, locations, *options))["gitinspector"]

def reported_changes(json_report):
	return dict((author["name"], author) for author in json_report["changes"]["authors"])

def reported_blame(json_report):
	return dict((author["name"], author["lines"]) for author in json_report["blame"]["authors"])

def assert_changes_agree(test, json_report, expected):
	reported = reported_changes(json_report)
	contributors = expected.contributors()
	test.assertEqual(sorted(reported), sorted(contributors))

	for (name, author) in contributors.items():
		test.assertEqual((reported[name]["commits"], reported[name]["insertions"], reported[name]["deletions"]),
		                 (author.commits, author.insertions, author.deletions), name)
		test.assertIn(reported[name]["email"], author.emails, name)

def assert_blame_agrees(test, json_report, expected):
	reported = reported_blame(json_report)
	test.assertEqual(sum(reported.values()), expected.blamed_lines())
	expected_by_name = expected.blamed_lines_by_name()

	for name in (set(reported) | set(expected_by_name)) - expected.ambiguous_names():
		test.assertEqual(reported.get(name, 0), expected_by_name.get(name, 0), name)

class ReportChecks(object):
	repository = None

	@classmethod
	def setUpClass(cls):
		cls.location = cls.repository.prepare()
		cls.json = json_report(cls.repository.file_types, [cls.location])
		cls.xml = ElementTree.fromstring(report("xml", cls.repository.file_types, [cls.location]).encode("utf-8"))
		cls.text = report("text", cls.repository.file_types, [cls.location])
		cls.html = report("html", cls.repository.file_types, [cls.location])
		cls.expected = reference.Statistics(cls.location, cls.repository.file_types)

	def test_header_names_the_repository_and_its_branch(self):
		self.assertEqual(self.json["repository"], os.path.basename(self.location))
		self.assertEqual(self.json["branch"], reference.branch_of(self.location))

	def test_changes_agree_with_git_log(self):
		assert_changes_agree(self, self.json, self.expected)

	def test_blame_agrees_with_git_blame(self):
		assert_blame_agrees(self, self.json, self.expected)

	def test_file_type_listing_agrees_with_git_log(self):
		located = self.expected.located
		self.assertEqual(self.json["extensions"]["used"], sorted(e for e in located if self.expected.wants(e)))
		self.assertEqual(self.json["extensions"]["unused"], sorted(e for e in located if not self.expected.wants(e)))

	def test_timeline_agrees_with_git_log(self):
		periods = self.json["timeline"]["periods"]
		self.assertEqual(self.json["timeline"]["period_length"], "month")
		self.assertEqual([period["name"] for period in periods], sorted(self.expected.modified_lines_by_period))

		for period in periods:
			self.assertEqual(period["modified_lines"], self.expected.modified_lines_by_period[period["name"]], period["name"])
			self.assertEqual(sorted(author["name"] for author in period["authors"]),
			                 sorted(self.expected.authors_by_period[period["name"]]), period["name"])

	def test_responsibilities_are_backed_by_blame(self):
		expected = self.expected.blamed_lines_by_name_and_file()

		for author in self.json["responsibilities"]["authors"]:
			lines = [entry["lines"] for entry in author["files"]]
			self.assertTrue(len(lines) <= 10 and lines == sorted(lines, reverse=True), author["name"])

			if author["name"] not in self.expected.ambiguous_names():
				for entry in author["files"]:
					blamed = expected.get((author["name"], entry["name"]), 0)
					self.assertTrue(0 < entry["lines"] <= blamed, "{0}: {1}".format(author["name"], entry["name"]))

	def test_metrics_name_files_over_the_thresholds(self):
		files = set(reference.git(self.location, "ls-tree", "-r", "--name-only", "-z", "HEAD").split("\0"))

		for violation in self.json["metrics"]["violations"]:
			self.assertIn(violation["file_name"], files)

			if violation["type"] == "estimated-lines-of-code":
				threshold = metrics.__metric_eloc__[reference.extension_of(violation["file_name"])]
			elif violation["type"] == "cyclomatic-complexity":
				threshold = metrics.METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD
			elif violation["type"] == "cognitive-complexity":
				threshold = metrics.METRIC_COGNITIVE_COMPLEXITY_THRESHOLD
			else:
				threshold = metrics.METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD

			self.assertGreater(violation["value"], threshold, violation["file_name"])

	def test_xml_report_agrees_with_json_report(self):
		self.assertEqual(self.xml.find("repository").text, self.json["repository"])
		self.assertEqual(self.xml.find("repository").get("branch"), self.json["branch"])
		changes = reported_changes(self.json)
		authors = list(self.xml.find("changes").find("authors"))
		self.assertEqual(sorted(author.findtext("name") for author in authors), sorted(changes))

		for author in authors:
			reported = changes[author.findtext("name")]
			self.assertEqual([int(author.findtext(key)) for key in ("commits", "insertions", "deletions")],
			                 [reported[key] for key in ("commits", "insertions", "deletions")])

		blame = reported_blame(self.json)
		authors = list(self.xml.find("blame").find("authors"))
		self.assertEqual(dict((author.findtext("name"), int(author.findtext("lines"))) for author in authors), blame)

	def test_text_and_html_reports_name_every_author(self):
		for name in reported_changes(self.json):
			self.assertIn(name[0:10], self.text)
			self.assertIn(name, self.html)

		self.assertTrue(self.html.rstrip().endswith("</html>"))

class GitinspectorReportTest(ReportChecks, unittest.TestCase):
	repository = GITINSPECTOR

class RequestsReportTest(ReportChecks, unittest.TestCase):
	repository = REQUESTS

class JqReportTest(ReportChecks, unittest.TestCase):
	repository = JQ

class CobraReportTest(ReportChecks, unittest.TestCase):
	repository = COBRA

class IntervalTest(unittest.TestCase):
	SINCE = "2016-01-01"
	UNTIL = "2017-12-31"

	@classmethod
	def setUpClass(cls):
		cls.location = REQUESTS.prepare()
		cls.json = json_report("py", [cls.location], "--since=" + cls.SINCE, "--until=" + cls.UNTIL)
		cls.expected = reference.Statistics(cls.location, "py", cls.SINCE, cls.UNTIL)

	def test_changes_are_limited_to_the_interval(self):
		assert_changes_agree(self, self.json, self.expected)
		self.assertTrue(all(cls_period >= self.SINCE[0:7] and cls_period <= self.UNTIL[0:7]
		                    for cls_period in (period["name"] for period in self.json["timeline"]["periods"])))

	def test_blame_is_limited_to_the_interval(self):
		assert_blame_agrees(self, self.json, self.expected)

class SeveralRepositoriesTest(unittest.TestCase):
	FILE_TYPES = "py,c,h"

	@classmethod
	def setUpClass(cls):
		cls.locations = [REQUESTS.prepare(), JQ.prepare()]
		cls.json = json_report(cls.FILE_TYPES, cls.locations)
		cls.expected = [reference.Statistics(location, cls.FILE_TYPES) for location in cls.locations]

	def test_header_names_every_repository(self):
		self.assertEqual(self.json["repositories"], [os.path.basename(location) for location in self.locations])
		self.assertEqual(self.json["branches"], [reference.branch_of(location) for location in self.locations])

	def test_changes_are_summed_over_the_repositories(self):
		reported = reported_changes(self.json)
		expected = {}

		for statistics in self.expected:
			for (name, author) in statistics.contributors().items():
				totals = expected.setdefault(name, [0, 0, 0])
				totals[0] += author.commits
				totals[1] += author.insertions
				totals[2] += author.deletions

		self.assertEqual(sorted(reported), sorted(expected))

		for (name, totals) in expected.items():
			self.assertEqual([reported[name]["commits"], reported[name]["insertions"], reported[name]["deletions"]], totals, name)

	def test_blame_is_summed_over_the_repositories(self):
		reported = reported_blame(self.json)
		self.assertEqual(sum(reported.values()), sum(statistics.blamed_lines() for statistics in self.expected))
		ambiguous = set().union(*[statistics.ambiguous_names() for statistics in self.expected])
		expected = {}

		for statistics in self.expected:
			for (name, lines) in statistics.blamed_lines_by_name().items():
				expected[name] = expected.get(name, 0) + lines

		for name in (set(reported) | set(expected)) - ambiguous:
			self.assertEqual(reported.get(name, 0), expected.get(name, 0), name)
