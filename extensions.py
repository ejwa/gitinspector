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

__default_extensions__ = ["java", "c", "cpp", "h", "hpp", "py", "glsl", "rb", "js", "sql"]
extensions = __default_extensions__
located_extensions = set()

def get():
	return extensions

def set(string):
	global extensions
	extensions = string.split(",")

def add_located(string):
	if len(string) > 0:
		global located_extensions
		located_extensions.add(string)

def get_located():
	return located_extensions
