# coding: utf-8
#
# Copyright © 2013 Ejwa Software. All rights reserved.
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
import getopt

class InvalidOptionArgument(Exception):
	def __init__(self, msg):
		super(InvalidOptionArgument, self).__init__(msg)
		self.msg = msg

def __find_arg_in_options__(arg, options):
	for opt in options:
		if opt[0].find(arg) == 0:
			return opt

	return None

def __find_options_to_extend__(long_options):
	options_to_extend = []

	for num, arg in enumerate(long_options):
		arg = arg.split(":")
		if len(arg) == 2:
			long_options[num] = arg[0] + "="
			options_to_extend.append(("--" + arg[0], arg[1]))

	return options_to_extend

# This is a duplicate of gnu_getopt, but with support for optional arguments in long options, in the form; "arg:default_value".

def gnu_getopt(args, options, long_options):
	options_to_extend = __find_options_to_extend__(long_options)

	for num, arg in enumerate(args):
		opt = __find_arg_in_options__(arg, options_to_extend)
		if opt:
			args[num] = arg + "=" + opt[1]

	return getopt.gnu_getopt(args, options, long_options)

def get_boolean_argument(arg):
	if isinstance(arg, bool):
		return arg
	elif arg == None or arg.lower() == "false" or arg.lower() == "f" or arg == "0":
		return False
	elif arg.lower() == "true" or arg.lower() == "t" or arg == "1":
		return True

	raise InvalidOptionArgument(_("The given option argument is not a valid boolean."))
