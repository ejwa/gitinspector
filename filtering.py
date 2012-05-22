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

__filters__ = []
__filtered_files__ = set()

def get():
	return __filters__

def add(string):
	__filters__.append(string)

def get_filered():
	return __filtered_files__

def set_filtered(file_name):
	string = file_name.strip()

	if len(string) > 0:
		for i in __filters__:
			if string.find(i) != -1:
				__filtered_files__.add(string)
				return True
	return False

def output():
	if __filtered_files__:
		print  "\nThe following files were excluded from the statistics due to the"
		print "specified exclusion patterns:"

		for i in __filtered_files__:
			print i
