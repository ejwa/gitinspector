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

from __future__ import print_function
from __future__ import unicode_literals

class ResponsibiltyEntry(object):
	blames = {}

class Responsibilities(object):
	@staticmethod
	def get(blame, author_name):
		author_blames = {}

		for i in blame.blames.items():
			if author_name == i[0][0]:
				total_rows = i[1].rows - i[1].comments
				if total_rows > 0:
					author_blames[i[0][1]] = total_rows

		return sorted(author_blames.items())
