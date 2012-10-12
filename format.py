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

from __future__ import print_function
import terminal

__available_formats__ = ["html", "text", "xml"]
__default_format__ = __available_formats__[1]
__selected_format__ = __default_format__

class InvalidFormatError(Exception):
	pass

def select(format):
	global __selected_format__
	__selected_format__ = format

	return format in __available_formats__

def output():
	print("Currently nothing")
