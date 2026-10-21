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
import re
import subprocess
from .changes import FileDiff
from . import comment, filtering, git, interval, languages, workers

METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD = 50
METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD = 0.75
METRIC_COGNITIVE_COMPLEXITY_THRESHOLD = 45

class MetricsThread(workers.Worker):
	def __init__(self, metrics, filename):
		workers.Worker.__init__(self)

		self.metrics = metrics
		self.filename = filename

	def work(self):
		file_r = workers.lines_of(["git", "show", interval.get_ref() + ":{0}".format(self.filename)])
		self.metrics.measure(self.filename, MetricsLogic.decode_lines(file_r))

class MetricsLogic(object):
	def __init__(self):
		self.eloc = {}
		self.cyclomatic_complexity = {}
		self.cyclomatic_complexity_density = {}
		self.cognitive_complexity = {}

		ls_tree_p = subprocess.Popen(["git", "ls-tree", "--name-only", "-r", "-z", interval.get_ref()],
		                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		lines = [entry for entry in ls_tree_p.communicate()[0].split(b"\0") if entry]

		if ls_tree_p.returncode == 0:
			for i in lines:
				i = git.decode(i)

				if FileDiff.is_valid_extension(i) and not filtering.set_filtered(FileDiff.get_filename(i)):
					MetricsThread(self, i).start()

			workers.join()

	def measure(self, filename, file_lines):
		extension = FileDiff.get_extension(filename)
		code_lines = MetricsLogic.get_code_lines(file_lines, extension)
		eloc = len(code_lines)
		cycc = MetricsLogic.get_cyclomatic_complexity(code_lines, extension)
		cogc = MetricsLogic.get_cognitive_complexity(file_lines, extension)
		filename = filename.strip()

		eloc_threshold = languages.get(extension).get("eloc")

		if eloc_threshold is not None and eloc_threshold < eloc:
			self.eloc[filename] = eloc

		if METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD < cycc:
			self.cyclomatic_complexity[filename] = cycc

		if eloc > 0 and METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD < cycc / float(eloc):
			self.cyclomatic_complexity_density[filename] = cycc / float(eloc)

		if METRIC_COGNITIVE_COMPLEXITY_THRESHOLD < cogc:
			self.cognitive_complexity[filename] = cogc

	def __iadd__(self, other):
		try:
			self.eloc.update(other.eloc)
			self.cyclomatic_complexity.update(other.cyclomatic_complexity)
			self.cyclomatic_complexity_density.update(other.cyclomatic_complexity_density)
			self.cognitive_complexity.update(other.cognitive_complexity)
			return self
		except AttributeError:
			return other

	@staticmethod
	def decode_lines(file_r):
		return [i.decode("utf-8", "replace") for i in file_r]

	@staticmethod
	def get_code_lines(file_lines, extension):
		is_inside_comment = False
		code_lines = []

		for i in file_lines:
			(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, i)

			if not is_inside_comment and not comment.is_comment(extension, i):
				code_lines.append(i)

		return code_lines

	@staticmethod
	def get_cyclomatic_complexity(code_lines, extension):
		cc_counter = 0

		cyclomatic = languages.get(extension).get("cyclomatic", {})
		entry_tokens = cyclomatic.get("branches")
		exit_tokens = cyclomatic.get("exits")

		if entry_tokens or exit_tokens:
			for i in code_lines:
				for j in entry_tokens:
					if re.search(j, i, re.DOTALL):
						cc_counter += 2
				for j in exit_tokens:
					if re.search(j, i, re.DOTALL):
						cc_counter += 1
			return cc_counter

		return -1

	@staticmethod
	def get_cognitive_complexity(file_lines, extension):
		is_inside_comment = False
		cognitive_counter = 0
		open_structures = []

		#Cognitive complexity charges a structure for how deeply it is nested, so the nesting tokens open a
		#nested structure while the continuation tokens merely continue one that has already been counted.
		cognitive = languages.get(extension).get("cognitive", {})
		nesting_tokens = cognitive.get("nesting")
		continuation_tokens = cognitive.get("continuation")

		if not nesting_tokens:
			return -1

		for i in file_lines:
			i = i.expandtabs()
			(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, i)

			if is_inside_comment or comment.is_comment(extension, i) or not i.strip():
				continue

			indentation = len(i) - len(i.lstrip())

			#A brace alone on its line belongs to the structure above it and must not close it.
			if i.strip() != "{":
				while open_structures and indentation <= open_structures[-1]:
					open_structures.pop()

			continues = any(re.search(j, i) for j in continuation_tokens)
			nests = 0 if continues else len([j for j in nesting_tokens if re.search(j, i)])

			if continues:
				cognitive_counter += 1
			else:
				cognitive_counter += nests * (1 + len(open_structures))

			if continues or nests:
				open_structures.append(indentation)

		return cognitive_counter
