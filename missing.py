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

import os
import system

__checkout_missing__ = False
__missing_files__ =  set()

def add(repo, file_name):
	previous_directory = os.getcwd()
	os.chdir(repo)
	exists = os.path.exists(file_name)
	os.chdir(previous_directory)

	if not exists:
		if __checkout_missing__:
			system.run(repo, "git checkout \"" + file_name.strip() + "\"")
		else:
			__missing_files__.add(file_name)
			return True
	return False

def set_checkout_missing(checkout):
	global __checkout_missing__
	__checkout_missing__ = checkout

def output():
	if __missing_files__:
		print "\nThe following files were missing in the repository and were therefore not"
		print "completely included in the statistical analysis. To include them, you can"
		print "either checkout manually using git or use the -c option in gitinspector:"

		for missing in __missing_files__:
			print missing
