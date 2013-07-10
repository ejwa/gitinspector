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

from __future__ import unicode_literals

import optparse
import sys

class InvalidOptionArgument(Exception):
	pass

class OptionParsingError(RuntimeError):
	pass

def __handle_boolean_argument__(option, __opt_str__, value, parser, *__args__, **kwargs):
	if isinstance(value, bool):
		return value
	elif value == None or value.lower() == "false" or value.lower() == "f" or value == "0":
		value = False
	elif value.lower() == "true" or value.lower() == "t" or value == "1":
		value = True
	else:
		raise InvalidOptionArgument("The given option argument is not a valid boolean.")

	if "multidest" in kwargs:
		for dest in kwargs["multidest"]:
			setattr(parser.values, dest, value)

	setattr(parser.values, option.dest, value)

# Originaly taken from here (and modified):
# http://stackoverflow.com/questions/1229146/parsing-empty-options-in-python

def add_option(parser, *args, **kwargs):
	if "multidest" in kwargs:
		multidest = kwargs.pop("multidest")
		kwargs["callback_kwargs"] = {"multidest": multidest}
	if "boolean" in kwargs and kwargs["boolean"] == True:
		boolean = kwargs.pop("boolean")
		kwargs["type"] = "string"
		kwargs["action"] = "callback"
		kwargs["callback"] = __handle_boolean_argument__
		kwargs["default"] = not boolean

		for i in range(len(sys.argv) - 1, 0, -1):
			arg = sys.argv[i]
			if arg in args:
				sys.argv.insert(i + 1, "true")

		parser.add_option(*args, **kwargs)

class OptionParser(optparse.OptionParser):
	def error(self, msg):
		if msg.find("requires") != -1:
			variable = msg.split()[0]
			raise OptionParsingError(_("option '{0}' requires an argument").format(variable))
		else:
			variable = msg.split()[-1]
			if variable[1] == "-":
				raise OptionParsingError("unrecognized option '{0}'".format(variable))
			else:
				raise OptionParsingError("invalid option -- '{0}'".format(variable[1:]))

		raise OptionParsingError("invalid command-line options")
