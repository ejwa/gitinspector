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

from __future__ import print_function
from __future__ import unicode_literals
import gettext
import locale
import os
import re
import sys
import time
from . import basedir

__enabled__ = False
__installed__ = False
__translation__ = None

#Dummy function used to handle string constants
def N_(message):
	return message

def __install_translation__(translation):
	# Python 2 wants a flag asking for unicode strings, which Python 3 replaced with a list of names.
	if sys.version_info[0] < 3:
		translation.install(True)
	else:
		translation.install()

LANGUAGE_VARIABLES = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
WINDOWS_LOCALE_NAME_MAX_LENGTH = 85

def __get_windows_language__():
	import ctypes
	name = ctypes.create_unicode_buffer(WINDOWS_LOCALE_NAME_MAX_LENGTH)

	try:
		if ctypes.windll.kernel32.GetUserDefaultLocaleName(name, len(name)):
			return name.value[0:2]
	except (AttributeError, OSError):
		pass

	return None

def __get_language__():
	for variable in LANGUAGE_VARIABLES:
		value = os.getenv(variable)

		if value:
			return value.split(":")[0][0:2]

	return __get_windows_language__() if sys.platform == "win32" else None

def __load_translation__(language):
	if language is None:
		print("WARNING: Localization disabled because the system language could not be determined.", file=sys.stderr)
		return gettext.NullTranslations()

	try:
		with open(basedir.get_basedir() + "/translations/messages_%s.mo" % language, "rb") as catalog:
			return gettext.GNUTranslations(catalog)
	except IOError:
		return gettext.NullTranslations()

def init():
	global __enabled__
	global __installed__
	global __translation__

	if not __installed__:
		try:
			locale.setlocale(locale.LC_ALL, "")
		except locale.Error:
			__translation__ = gettext.NullTranslations()
		else:
			__translation__ = __load_translation__(__get_language__())

		__enabled__ = True
		__installed__ = True
		__install_translation__(__translation__)

def check_compatibility(version):
	if isinstance(__translation__, gettext.GNUTranslations):
		header_pattern = re.compile("^([^:\n]+): *(.*?) *$", re.MULTILINE)
		header_entries = dict(header_pattern.findall(_("")))

		if header_entries["Project-Id-Version"] != "gitinspector {0}".format(version):
			print("WARNING: The translation for your system locale is not up to date with the current gitinspector "
			      "version. The current maintainer of this locale is {0}.".format(header_entries["Last-Translator"]),
			      file=sys.stderr)

def get_date():
	if __enabled__ and isinstance(__translation__, gettext.GNUTranslations):
		date = time.strftime("%x")

		if hasattr(date, 'decode'):
			date = date.decode("utf-8", "replace")

		return date
	else:
		return time.strftime("%Y/%m/%d")

def enable():
	if isinstance(__translation__, gettext.GNUTranslations):
		__install_translation__(__translation__)

		global __enabled__
		__enabled__ = True

def disable():
	global __enabled__
	__enabled__ = False

	if __installed__:
		__install_translation__(gettext.NullTranslations())
