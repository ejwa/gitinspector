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
import os
import subprocess
import terminal

__checkout_missing__ = False
__missing_files__ =  set()

def add(file_name):
	if not os.path.exists(file_name):
		if __checkout_missing__:
			subprocess.call("git checkout \"" + file_name.strip() + "\"", shell=True)
		else:
			__missing_files__.add(file_name)
			return True
	return False

def set_checkout_missing(checkout):
	global __checkout_missing__
	__checkout_missing__ = checkout

def output():
	if __missing_files__:
		print("\nThe following files were missing in the repository and were therefore not")
		print("completely included in the statistical analysis. To include them, you can")
		print("either checkout manually using git or use the -c option in gitinspector:")

		for missing in __missing_files__:
			(width, _) = terminal.get_size()
			print("...%s" % missing[-width+3:] if len(missing) > width else missing)
