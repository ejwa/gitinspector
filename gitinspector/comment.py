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
from . import languages

def __get_comment__(extension):
	return languages.get(extension).get("comment", {})

def __has_comment_begining__(extension, string):
	comment = __get_comment__(extension)

	if comment.get("at_line_start"):
		return string.find(comment["block"][0]) == 0
	elif "block" in comment and string.find(comment["block"][1], 2) == -1:
		return string.find(comment["block"][0]) != -1

	return False

def __has_comment_end__(extension, string):
	comment = __get_comment__(extension)

	if comment.get("at_line_start"):
		return string.find(comment["block"][1]) == 0
	elif "block" in comment:
		return string.find(comment["block"][1]) != -1

	return False

def is_comment(extension, string):
	comment = __get_comment__(extension)
	stripped = string.strip()

	if "block" in comment and stripped.startswith(comment["block"][0]):
		return True
	if "block" in comment and stripped.endswith(comment["block"][1]):
		return True
	if "line" in comment and stripped.startswith(comment["line"]):
		return True

	return False

def handle_comment_block(is_inside_comment, extension, content):
	comments = 0

	if is_comment(extension, content):
		comments += 1
	if is_inside_comment:
		if __has_comment_end__(extension, content):
			is_inside_comment = False
		else:
			comments += 1
	elif __has_comment_begining__(extension, content) and not __has_comment_end__(extension, content):
		is_inside_comment = True

	return (comments, is_inside_comment)
