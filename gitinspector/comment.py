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

__comment_begining__ = {"java": "/*", "c": "/*", "cc": "/*", "cpp": "/*", "cs": "/*", "h": "/*", "hh": "/*", "hpp": "/*",
                        "hs": "{-", "html": "<!--", "php": "/*", "py": "\"\"\"", "glsl": "/*", "rb": "=begin", "js": "/*",
                        "jspx": "<!--", "scala": "/*", "sql": "/*", "tex": "\\begin{comment}", "xhtml": "<!--",
                        "xml": "<!--", "ml": "(*", "mli": "(*", "go": "/*", "ly": "%{", "ily": "%{"}

__comment_end__ = {"java": "*/", "c": "*/", "cc": "*/", "cpp": "*/", "cs": "*/", "h": "*/", "hh": "*/", "hpp": "*/", "hs": "-}",
                   "html": "-->", "php": "*/", "py": "\"\"\"", "glsl": "*/", "rb": "=end", "js": "*/", "jspx": "-->",
                   "scala": "*/", "sql": "*/", "tex": "\\end{comment}", "xhtml": "-->", "xml": "-->", "ml": "*)", "mli": "*)",
                   "go": "*/", "ly": "%}", "ily": "%}"}

__comment__ = {"java": "//", "c": "//", "cc": "//", "cpp": "//", "cs": "//", "h": "//", "hh": "//", "hpp": "//", "hs": "--",
               "pl": "#", "php": "//", "py": "#", "glsl": "//", "rb": "#", "robot": "#", "rs": "//", "rlib": "//", "js": "//",
               "scala": "//", "sql": "--", "tex": "%", "ada": "--", "ads": "--", "adb": "--", "pot": "#", "po": "#", "go": "//",
               "ly": "%", "ily": "%"}

__comment_markers_must_be_at_begining__ = {"tex": True}

def __has_comment_begining__(extension, string):
	if __comment_markers_must_be_at_begining__.get(extension, None) == True:
		return string.find(__comment_begining__[extension]) == 0
	elif __comment_begining__.get(extension, None) != None and string.find(__comment_end__[extension], 2) == -1:
		return string.find(__comment_begining__[extension]) != -1

	return False

def __has_comment_end__(extension, string):
	if __comment_markers_must_be_at_begining__.get(extension, None) == True:
		return string.find(__comment_end__[extension]) == 0
	elif __comment_end__.get(extension, None) != None:
		return string.find(__comment_end__[extension]) != -1

	return False

def is_comment(extension, string):
	if __comment_begining__.get(extension, None) != None and string.strip().startswith(__comment_begining__[extension]):
		return True
	if __comment_end__.get(extension, None) != None and string.strip().endswith(__comment_end__[extension]):
		return True
	if __comment__.get(extension, None) != None and string.strip().startswith(__comment__[extension]):
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
