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
from . import comment, filtering, git, interval, workers

__metric_eloc__ = {"java": 500, "c": 500, "cpp": 500, "cs": 500, "h": 300, "hpp": 300, "php": 500, "py": 500, "glsl": 1000,
                   "rb": 500, "js": 500, "sql": 1000, "xml": 1000, "go": 500, "swift": 500, "ts": 500, "tsx": 500,
                   "rs": 500}

__metric_cc_tokens__ = [[["java", "js", "c", "cc", "cpp", "ts", "tsx"], ["else", r"for\s+\(.*\)", r"if\s+\(.*\)",
                                                                   r"case\s+\w+:", "default:", r"while\s+\(.*\)"],
                                                                  ["assert", "break", "continue", "return"]],
                       [["cs"], ["else", r"for\s+\(.*\)", r"foreach\s+\(.*\)", r"goto\s+\w+:", r"if\s+\(.*\)", r"case\s+\w+:",
                                 "default:", r"while\s+\(.*\)"],
                                ["assert", "break", "continue", "return"]],
                       [["py"], [r"^\s+elif .*:$", r"^\s+else:$", r"^\s+for .*:", r"^\s+if .*:$", r"^\s+while .*:$"],
                                [r"^\s+assert", "break", "continue", "return"]],
                       [["go"], ["else", r"for\s+.*\{", r"if\s+.*\{", r"case\s+\w+:", "default:", r"goto\s+\w+"],
                                ["break", "continue", "return"]],
                       [["swift"], [r"\belse\b", r"\bfor\s+.*\{", r"\bif\s+.*\{", r"\bcase\s+.*:", r"\bdefault\s*:", r"\bwhile\s+"],
                                   ["assert", "break", "continue", "return"]],
                       [["php"], [r"\belse\b", r"\belseif\s*\(.*\)", r"\bfor\s*\(.*\)", r"\bforeach\s*\(.*\)", r"\bif\s*\(.*\)",
                                  r"\bcase\s+.*:", r"\bdefault\s*:", r"\bwhile\s*\(.*\)"],
                                 ["assert", "break", "continue", "return"]],
                       #Rust branches on the arms of a match rather than on case labels, hence the fat arrow.
                       [["rs"], [r"\belse\b", r"\bfor\s+.*\{", r"\bif\s+.*\{", r"\bwhile\s+.*\{", r"\bloop\s*\{", "=>"],
                                [r"\bassert", r"\bbreak\b", r"\bcontinue\b", r"\breturn\b"]]]

#Cognitive complexity charges a structure for how deeply it is nested, so the tokens are split into
#the ones that open a nested structure and the ones that merely continue an already counted one.
__metric_cognitive_tokens__ = [[["java", "js", "c", "cc", "cpp", "ts", "tsx", "cs"],
                                [r"\bif\s*\(", r"\bfor\s*\(", r"\bforeach\s*\(", r"\bwhile\s*\(", r"\bswitch\s*\(",
                                 r"\bcatch\s*\(", r"\bdo\s*\{"],
                                [r"\belse\b"]],
                               [["py"], [r"\bif\s+.*:", r"\bfor\s+.*:", r"\bwhile\s+.*:", r"\bexcept\b"],
                                        [r"\belif\b", r"\belse\b"]],
                               [["go"], [r"\bif\s+.*\{", r"\bfor\b.*\{", r"\bswitch\b.*\{", r"\bselect\s*\{"],
                                        [r"\belse\b"]],
                               [["swift"], [r"\bif\s+.*\{", r"\bfor\s+.*\{", r"\bwhile\s+.*\{", r"\bswitch\s+.*\{",
                                            r"\brepeat\s*\{", r"\bguard\s+.*\{", r"\bcatch\b"],
                                           [r"\belse\b"]],
                               [["php"], [r"\bif\s*\(", r"\bfor\s*\(", r"\bforeach\s*\(", r"\bwhile\s*\(", r"\bswitch\s*\(",
                                          r"\bcatch\s*\("],
                                         [r"\belseif\b", r"\belse\b"]],
                               [["rs"], [r"\bif\s+.*\{", r"\bfor\s+.*\{", r"\bwhile\s+.*\{", r"\bloop\s*\{",
                                         r"\bmatch\s+.*\{"],
                                        [r"\belse\b"]]]

METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD = 50
METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD = 0.75
METRIC_COGNITIVE_COMPLEXITY_THRESHOLD = 45

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
					file_r = workers.lines_of(["git", "show", interval.get_ref() + ":{0}".format(i)])

					extension = FileDiff.get_extension(i)
					lines = MetricsLogic.get_eloc(file_r, extension)
					cycc = MetricsLogic.get_cyclomatic_complexity(file_r, extension)
					cogc = MetricsLogic.get_cognitive_complexity(file_r, extension)

					if __metric_eloc__.get(extension, None) != None and __metric_eloc__[extension] < lines:
						self.eloc[i.strip()] = lines

					if METRIC_CYCLOMATIC_COMPLEXITY_THRESHOLD < cycc:
						self.cyclomatic_complexity[i.strip()] = cycc

					if lines > 0 and METRIC_CYCLOMATIC_COMPLEXITY_DENSITY_THRESHOLD < cycc / float(lines):
						self.cyclomatic_complexity_density[i.strip()] = cycc / float(lines)

					if METRIC_COGNITIVE_COMPLEXITY_THRESHOLD < cogc:
						self.cognitive_complexity[i.strip()] = cogc

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
	def get_cyclomatic_complexity(file_r, extension):
		is_inside_comment = False
		cc_counter = 0

		entry_tokens = None
		exit_tokens = None

		for i in __metric_cc_tokens__:
			if extension in i[0]:
				entry_tokens = i[1]
				exit_tokens = i[2]

		if entry_tokens or exit_tokens:
			for i in file_r:
				i = i.decode("utf-8", "replace")
				(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, i)

				if not is_inside_comment and not comment.is_comment(extension, i):
					for j in entry_tokens:
						if re.search(j, i, re.DOTALL):
							cc_counter += 2
					for j in exit_tokens:
						if re.search(j, i, re.DOTALL):
							cc_counter += 1
			return cc_counter

		return -1

	@staticmethod
	def get_cognitive_complexity(file_r, extension):
		is_inside_comment = False
		cognitive_counter = 0
		open_structures = []

		nesting_tokens = None
		continuation_tokens = None

		for i in __metric_cognitive_tokens__:
			if extension in i[0]:
				nesting_tokens = i[1]
				continuation_tokens = i[2]

		if not nesting_tokens:
			return -1

		for i in file_r:
			i = i.decode("utf-8", "replace").expandtabs()
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

	@staticmethod
	def get_eloc(file_r, extension):
		is_inside_comment = False
		eloc_counter = 0

		for i in file_r:
			i = i.decode("utf-8", "replace")
			(_, is_inside_comment) = comment.handle_comment_block(is_inside_comment, extension, i)

			if not is_inside_comment and not comment.is_comment(extension, i):
				eloc_counter += 1

		return eloc_counter
