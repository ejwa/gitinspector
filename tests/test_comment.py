# coding: utf-8
#
# Copyright © 2013-2015 Ejwa Software. All rights reserved.
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
import sys
import unittest2
import gitinspector.comment

def __test_extension__(commented_file, extension):
	base = os.path.dirname(os.path.realpath(__file__))
	tex_file = open(base + commented_file, "r")
	tex = tex_file.readlines()
	tex_file.close()

	is_inside_comment = False
	comment_counter = 0
	for i in tex:
		i = i.decode("utf-8", "replace")
		(_, is_inside_comment) = gitinspector.comment.handle_comment_block(is_inside_comment, extension, i)
		if is_inside_comment or gitinspector.comment.is_comment(extension, i):
			comment_counter += 1

	return comment_counter

class TexFileTest(unittest2.TestCase):
    def test(self):
	comment_counter = __test_extension__("/resources/commented_file.tex", "tex")
	self.assertEqual(comment_counter, 30)

class CppFileTest(unittest2.TestCase):
    def test(self):
	comment_counter = __test_extension__("/resources/commented_file.cpp", "cpp")
	self.assertEqual(comment_counter, 25)
