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
import blame
import terminal

class ResponsibiltyEntry:
	blames = {}

class Responsibilities:
	@staticmethod
	def get(hard, author_name):
		author_blames = {}

		for i in blame.get(hard).blames.items():
			if (author_name == i[0][0]):
				total_rows = i[1].rows - i[1].comments
				if total_rows > 0:
					author_blames[i[0][1]] = total_rows

		return sorted(author_blames.items())

def output(hard):
	print("\nThe following repsonsibilties, by author, were found in the current")
	print("revision of the repository (comments are exluded from the line count,")
	print("if possible):")

	for i in sorted(set(i[0] for i in blame.get(hard).blames)):
		print("\n" + i, "is mostly responsible for:")
		responsibilities = sorted(((i[1], i[0]) for i in Responsibilities.get(hard, i)), reverse=True)

		for j, entry in enumerate(responsibilities):
			(width, _) = terminal.get_size()
			width -= 7

			print(str(entry[0]).rjust(6), end=" ")
			print("...%s" % entry[1][-width+3:] if len(entry[1]) > width else entry[1])

			if j >= 9:
				break
