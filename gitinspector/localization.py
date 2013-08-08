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
import basedir
import gettext
import locale
import os

__installed__ = False
__translation__ = None

#Dummy function used to handle string constants
def N_(message):
	return message

def init():
	global __installed__
	global __translation__

	if not __installed__:
		try:
			locale.setlocale(locale.LC_ALL, "")
		except locale.Error:
			__translation__ = gettext.NullTranslations()
		else:
			lang = locale.getlocale()

			#Fix for non-POSIX-compliant systems (Windows et al.).
			if os.getenv('LANG') is None:
				lang = locale.getdefaultlocale()
				os.environ['LANG'] = lang[0]

			filename = basedir.get_basedir() + "/translations/messages_%s.mo" % lang[0][0:2]

			try:
				__translation__ = gettext.GNUTranslations(open(filename, "rb"))
			except IOError:
				__translation__ = gettext.NullTranslations()

		__installed__ = True
		__translation__.install(True)

def enable():
	if __installed__ and type(__translation__) is not gettext.GNUTranslations:
		__translation__.install(True)

def disable():
	if __installed__:
		gettext.NullTranslations().install(True)
