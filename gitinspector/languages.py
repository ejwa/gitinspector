# coding: utf-8
#
# Copyright © 2026 Ejwa Hosting AB. All rights reserved.
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
import json
import os
from . import basedir

__value_keys__ = ("comment", "eloc", "cyclomatic", "cognitive")
__definition_keys__ = __value_keys__ + ("extensions", "overrides", "note")
__token_keys__ = {"cyclomatic": ["branches", "exits"], "cognitive": ["continuation", "nesting"]}

def __json_files__(directory):
	names = sorted(os.listdir(directory)) if os.path.isdir(directory) else []
	files = [os.path.join(directory, name) for name in names if name.endswith(".json")]

	if not files:
		raise ValueError("No language definitions in \"{0}\".".format(directory))

	return files

def __check_keys__(keys, allowed, name):
	for key in keys:
		if key not in allowed:
			raise ValueError("Unknown key \"{0}\" in \"{1}\".".format(key, name))

def __flatten__(definition, extension, name):
	flattened = dict((key, definition[key]) for key in __value_keys__ if key in definition)

	for key, value in definition.get("overrides", {}).get(extension, {}).items():
		if value is None:
			flattened.pop(key, None)
		else:
			flattened[key] = value

	#The metrics iterate both token lists of a block, so a missing one would only fail inside a worker thread.
	for key, tokens in __token_keys__.items():
		if key in flattened and sorted(flattened[key]) != tokens:
			raise ValueError("\"{0}\" of \"{1}\" in \"{2}\" needs exactly {3}.".format(key, extension, name, tokens))

	return flattened

def __load_file__(path):
	name = os.path.basename(path)

	try:
		with open(path, "rb") as definition_file:
			definition = json.loads(definition_file.read().decode("utf-8"))
	except ValueError as error:
		raise ValueError("Invalid language definition in \"{0}\": {1}".format(name, error))

	if not isinstance(definition, dict) or not isinstance(definition.get("extensions"), list) or \
	   not isinstance(definition.get("overrides", {}), dict):
		raise ValueError("\"{0}\" needs a list of extensions and its overrides as an object.".format(name))

	__check_keys__(definition, __definition_keys__, name)

	for extension, override in definition.get("overrides", {}).items():
		if extension not in definition["extensions"] or not isinstance(override, dict):
			raise ValueError("Invalid override for \"{0}\" in \"{1}\".".format(extension, name))

		__check_keys__(override, __value_keys__, name)

	return dict((extension, __flatten__(definition, extension, name)) for extension in definition["extensions"])

def load(directory):
	definitions = {}
	sources = {}

	for path in __json_files__(directory):
		name = os.path.basename(path)

		for extension, definition in __load_file__(path).items():
			if extension in definitions:
				raise ValueError("Extension \"{0}\" is defined in both \"{1}\" and \"{2}\".".format(
				                 extension, sources[extension], name))

			definitions[extension] = definition
			sources[extension] = name

	return definitions

#Worker threads read the definitions concurrently, so they are loaded before any of them starts.
__definitions__ = load(os.path.join(basedir.get_basedir(), "languages"))

def get(extension):
	return __definitions__.get(extension, {})
