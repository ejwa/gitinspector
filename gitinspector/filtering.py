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
from . import git, workers

__filters__ ={"file": [set(), set()], "author": [set(), set()], "email": [set(), set()], "revision": [set(), set()],
               "message" : [set(), None]}

class InvalidRegExpError(ValueError):
	def __init__(self, msg):
		super(InvalidRegExpError, self).__init__(msg)
		self.msg = msg

def get():
	return __filters__

#Compiled once, when a rule is added, so that an invalid rule is reported before any analysis starts.
__patterns__ = {}

def __add_rule__(filter_type, rule):
	try:
		__patterns__[rule] = re.compile(rule)
	except re.error:
		raise InvalidRegExpError(_("invalid regular expression specified"))

	__filters__[filter_type][0].add(rule)

def __add_one__(string):
	for i in __filters__:
		if (i + ":").lower() == string[0:len(i) + 1].lower():
			__add_rule__(i, string[len(i) + 1:])
			return
	__add_rule__("file", string)

def add(string):
	rules = string.split(",")
	for rule in rules:
		__add_one__(rule)

def clear():
	for i in __filters__:
		__filters__[i][0] = set()
		if __filters__[i][1] is not None:
			__filters__[i][1] = set()

def get_filered(filter_type="file"):
	return __filters__[filter_type][1]

def has_filtered():
	for i in __filters__:
		if __filters__[i][1]:
			return True
	return False

def __find_commit_message__(sha):
	return git.decode(workers.output_of(["git", "show", "-s", "--pretty=%B", "-w", sha]).strip())

def set_filtered(string, filter_type="file"):
	string = string.strip()

	if len(string) > 0:
		#A matching message adds a revision rule while other threads may be going through the rules.
		rules = list(__filters__[filter_type][0])
		search_for = __find_commit_message__(string) if rules and filter_type == "message" else string

		for i in rules:
			if __patterns__[i].search(search_for):
				if filter_type == "message":
					__add_rule__("revision", string)
				else:
					__filters__[filter_type][1].add(string)
				return True
	return False
