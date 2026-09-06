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
import subprocess

__escapes__ ={"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\", "\"": "\""}
__octal__ = re.compile("[0-7]{1,3}")

def decode(output):
	# Git hands over names and paths as the bytes they were committed with, which predate UTF-8 in old repositories.
	try:
		return output.decode("utf-8")
	except UnicodeDecodeError:
		return output.decode("latin-1")

def __output_of__(command, location):
	with open(os.devnull, "w") as devnull:
		process = subprocess.Popen(command, cwd=location, stdout=subprocess.PIPE, stderr=devnull)
		return decode(process.communicate()[0]).strip()

def get_branch(location):
	branch = __output_of__(["git", "symbolic-ref", "--short", "-q", "HEAD"], location)

	if branch:
		return branch

	return __output_of__(["git", "rev-parse", "--short", "HEAD"], location)

def unquote(path):
	if len(path) < 2 or path[0] != "\"" or path[-1] != "\"":
		return path

	quoted = path[1:-1]
	unquoted = bytearray()
	position = 0

	while position < len(quoted):
		if quoted[position] == "\\" and position + 1 < len(quoted):
			octal = __octal__.match(quoted, position + 1)

			if octal:
				unquoted.append(int(octal.group(0), 8))
				position = octal.end()
			else:
				unquoted.extend(__escapes__.get(quoted[position + 1], quoted[position + 1]).encode("utf-8"))
				position += 2
		else:
			unquoted.extend(quoted[position].encode("utf-8"))
			position += 1

	return decode(bytes(unquoted))
