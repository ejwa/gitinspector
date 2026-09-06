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
import io
import multiprocessing
import subprocess
import threading

NUM_THREADS = multiprocessing.cpu_count()
RETRY_DELAY = 1.0
ATTEMPTS_WITHOUT_RUNNING_GIT = 3

__condition__ = threading.Condition()
__failure__ = None
__processes__ = 0
__running__ = 0

class OutOfResourcesError(Exception):
	def __init__(self):
		msg = _("Unable to start git: the system is out of memory or cannot create more processes.")
		super(OutOfResourcesError, self).__init__(msg)
		self.msg = msg

def __is_out_of_resources__(error):
	# Thread.start reports an exhausted system through a ThreadError, which carries no errno.
	return not isinstance(error, OSError) or error.errno in (errno.EAGAIN, errno.ENOMEM)

def __keep_trying__(start):
	global NUM_THREADS
	attempts_without_running_git = 0

	while True:
		try:
			return start()
		except (OSError, threading.ThreadError) as error:
			if not __is_out_of_resources__(error):
				raise

			NUM_THREADS = max(1, min(NUM_THREADS, __processes__))

			if __processes__ == 0:
				attempts_without_running_git += 1

				if attempts_without_running_git == ATTEMPTS_WITHOUT_RUNNING_GIT:
					raise OutOfResourcesError()

			__condition__.wait(RETRY_DELAY)

def output_of(command):
	global __processes__
	command = list(command)

	with __condition__:
		process = __keep_trying__(lambda: subprocess.Popen(command, stdout=subprocess.PIPE))
		__processes__ += 1

	output = process.communicate()[0]

	with __condition__:
		__processes__ -= 1
		__condition__.notify_all()

	return output

def lines_of(command):
	# The lines exactly as git delimited them; splitlines() would also break them at carriage returns.
	return io.BytesIO(output_of(command)).readlines()

def __fail__(error):
	global __failure__

	with __condition__:
		if __failure__ is None:
			__failure__ = error

def __release__():
	global __running__

	with __condition__:
		__running__ -= 1
		__condition__.notify_all()

def join():
	global __failure__

	with __condition__:
		while __running__ > 0:
			__condition__.wait()

		(failure, __failure__) = (__failure__, None)

	if failure is not None:
		raise failure

class Worker(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True

	def start(self):
		global __running__

		with __condition__:
			if __failure__ is not None:
				return

			while __running__ >= NUM_THREADS:
				__condition__.wait()

			__keep_trying__(lambda: threading.Thread.start(self))
			__running__ += 1

	def run(self):
		try:
			self.work()
		except Exception as error:
			__fail__(error)
		finally:
			__release__()

	def work(self):
		raise NotImplementedError()
