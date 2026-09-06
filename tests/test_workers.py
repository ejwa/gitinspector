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
import errno
import subprocess
import threading
import time

try:
	import unittest2 as unittest
except ImportError:
	import unittest

from gitinspector import workers
from .harness import Repository, analyze_blame, analyze_changes

OUTPUT = b"line one\nline two\n"
PATIENCE = 10.0

class FakeProcess(object):
	def __init__(self, system):
		self.system = system

	def communicate(self):
		self.system.finished.wait()
		self.system.stop()
		return (self.system.output, None)

class ExhaustedSystem(object):
	def __init__(self, capacity, recovers_after=None, error_number=errno.ENOMEM, output=OUTPUT):
		self.capacity = capacity
		self.recovers_after = recovers_after
		self.error_number = error_number
		self.output = output
		self.running = 0
		self.refusals = 0
		self.commands = []
		self.lock = threading.Lock()
		self.finished = threading.Event()
		self.finished.set()

	def __call__(self, command, **options):
		with self.lock:
			self.commands.append(list(command))

			if self.running >= self.capacity and self.refusals != self.recovers_after:
				self.refusals += 1
				raise OSError(self.error_number, "refused")

			self.running += 1
			return FakeProcess(self)

	def stop(self):
		with self.lock:
			self.running -= 1

class RefusingGit(object):
	def __init__(self, subcommand, limit=1):
		self.popen = subprocess.Popen
		self.subcommand = subcommand
		self.limit = limit
		self.refusals = 0

	def __call__(self, command, **options):
		command = list(command)

		if command[:2] == ["git", self.subcommand] and self.refusals != self.limit:
			self.refusals += 1
			raise OSError(errno.ENOMEM, "Cannot allocate memory")

		return self.popen(command, **options)

class Reader(workers.Worker):
	def __init__(self):
		workers.Worker.__init__(self)
		self.output = None

	def work(self):
		self.output = workers.output_of(["git", "log"])

class Broken(workers.Worker):
	def work(self):
		raise ValueError("broken")

class WorkersTest(unittest.TestCase):
	def setUp(self):
		self.popen = subprocess.Popen
		self.num_threads = workers.NUM_THREADS
		self.retry_delay = workers.RETRY_DELAY
		workers.RETRY_DELAY = 0.01

	def tearDown(self):
		subprocess.Popen = self.popen
		workers.NUM_THREADS = self.num_threads
		workers.RETRY_DELAY = self.retry_delay

	def wait_until(self, condition):
		deadline = time.time() + PATIENCE

		while not condition():
			self.assertTrue(time.time() < deadline, "Timed out waiting for the workers")
			time.sleep(0.01)

class StartTest(WorkersTest):
	def test_a_refused_start_is_retried(self):
		for error_number in (errno.ENOMEM, errno.EAGAIN):
			system = ExhaustedSystem(0, recovers_after=1, error_number=error_number)
			subprocess.Popen = system

			self.assertEqual(workers.output_of(["git", "log"]), OUTPUT)
			self.assertEqual(system.refusals, 1)

	def test_the_command_survives_the_retry_even_when_given_as_an_iterator(self):
		system = ExhaustedSystem(0, recovers_after=1)
		subprocess.Popen = system

		self.assertEqual(workers.output_of(filter(None, ["git", "", "log"])), OUTPUT)
		self.assertEqual(system.commands, [["git", "log"], ["git", "log"]])

	def test_other_errors_are_not_retried(self):
		system = ExhaustedSystem(0, error_number=errno.ENOENT)
		subprocess.Popen = system

		self.assertRaises(OSError, workers.output_of, ["git", "log"])
		self.assertEqual(system.refusals, 1)

	def test_the_start_is_given_up_when_no_git_of_ours_can_free_resources(self):
		system = ExhaustedSystem(0)
		subprocess.Popen = system

		self.assertRaises(workers.OutOfResourcesError, workers.output_of, ["git", "log"])
		self.assertEqual(system.refusals, workers.ATTEMPTS_WITHOUT_RUNNING_GIT)

	def test_lines_are_only_split_at_line_feeds(self):
		subprocess.Popen = ExhaustedSystem(1, output=b"one\rtwo\nthree\n")

		self.assertEqual(workers.lines_of(["git", "log"]), [b"one\rtwo\n", b"three\n"])

	def test_a_thread_that_cannot_be_started_is_retried(self):
		original_start = threading.Thread.start
		attempts = []

		def refusing_start(thread):
			attempts.append(thread)

			if len(attempts) == 1:
				raise threading.ThreadError("can't start new thread")
			original_start(thread)

		subprocess.Popen = ExhaustedSystem(1)
		threading.Thread.start = refusing_start
		reader = Reader()

		try:
			reader.start()
			workers.join()
		finally:
			threading.Thread.start = original_start

		self.assertEqual(reader.output, OUTPUT)
		self.assertEqual(len(attempts), 2)

class ConcurrencyTest(WorkersTest):
	def test_the_thread_count_drops_to_what_the_system_could_start(self):
		system = ExhaustedSystem(2)
		system.finished.clear()
		subprocess.Popen = system
		workers.NUM_THREADS = 3
		readers = [Reader(), Reader(), Reader()]

		for reader in readers:
			reader.start()

		self.wait_until(lambda: system.refusals > 0)
		system.finished.set()
		workers.join()

		self.assertEqual([reader.output for reader in readers], [OUTPUT] * 3)
		self.assertEqual(workers.NUM_THREADS, 2)

	def test_a_broken_thread_is_reported_instead_of_hanging(self):
		Broken().start()
		self.assertRaises(ValueError, workers.join)
		workers.join()

		subprocess.Popen = ExhaustedSystem(1)
		reader = Reader()
		reader.start()
		workers.join()
		self.assertEqual(reader.output, OUTPUT)

	def test_no_thread_is_started_after_a_failure(self):
		subprocess.Popen = ExhaustedSystem(1)
		broken = Broken()
		broken.start()
		broken.join()
		reader = Reader()
		reader.start()

		self.assertRaises(ValueError, workers.join)
		self.assertEqual(reader.output, None)

class AnalysisTest(WorkersTest):
	def setUp(self):
		WorkersTest.setUp(self)
		self.repository = Repository()
		self.repository.commit("first", {"a.py": "x = 1\n"}, "First Author", "first@example.com")
		self.repository.commit("second", {"b.py": "y = 2\ny = 3\n"}, "Second Author", "second@example.com")

	def tearDown(self):
		WorkersTest.tearDown(self)
		self.repository.remove()

	def test_the_changes_are_complete_after_a_refused_git_log(self):
		subprocess.Popen = RefusingGit("log")
		result = analyze_changes(self.repository)

		self.assertEqual(subprocess.Popen.refusals, 1)
		self.assertEqual([commit.author for commit in result.get_commits()], ["First Author", "Second Author"])

	def test_the_blame_is_complete_after_a_refused_git_blame(self):
		analyzed_changes = analyze_changes(self.repository)
		subprocess.Popen = RefusingGit("blame")
		result = analyze_blame(self.repository, analyzed_changes)

		self.assertEqual(subprocess.Popen.refusals, 1)
		self.assertEqual(dict((key, entry.lines) for (key, entry) in result.blames.items()),
		                 {("First Author", "a.py"): 1, ("Second Author", "b.py"): 2})

	def test_a_refused_git_show_in_the_message_filter_is_retried(self):
		subprocess.Popen = RefusingGit("show")
		result = analyze_changes(self.repository, exclude="message:second")

		self.assertEqual(subprocess.Popen.refusals, 1)
		self.assertEqual([commit.author for commit in result.get_commits()], ["First Author"])

	def test_the_analysis_fails_cleanly_when_git_can_never_be_started(self):
		subprocess.Popen = RefusingGit("log", limit=None)

		self.assertRaises(workers.OutOfResourcesError, analyze_changes, self.repository)
		self.assertEqual(subprocess.Popen.refusals, workers.ATTEMPTS_WITHOUT_RUNNING_GIT)

		subprocess.Popen = self.popen
		self.assertEqual([commit.author for commit in analyze_changes(self.repository).get_commits()],
		                 ["First Author", "Second Author"])
