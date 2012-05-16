# coding: utf-8
#
# Copyright © 2012 Ejwa Software. All rights reserved.
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

import terminal

__default_extensions__ = ["java", "c", "cpp", "h", "hpp", "py", "glsl", "rb", "js", "sql"]
__extensions__ = __default_extensions__
__located_extensions__ = set()

def get():
	return __extensions__

def define(string):
	global __extensions__
	__extensions__ = string.split(",")

def add_located(string):
	if len(string) > 0:
		__located_extensions__.add(string)

def output():
	if __located_extensions__:
		print "\nThe extensions below were found in the repository history"
		print "(extensions used during statistical analysis are marked):"

		for i in __located_extensions__:
			if i in __extensions__:
				print "[" + terminal.__bold__ + i + terminal.__normal__ + "]",
			else:
				print i,
