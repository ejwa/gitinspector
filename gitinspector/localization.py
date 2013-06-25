#!/usr/bin/python
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

import gettext
import locale
import os

def init():
	locale.setlocale(locale.LC_ALL, '')
	lang = locale.getlocale()

	#Fix for non-POSIX-compliant systems (Windows et al.).
	if os.getenv('LANG') is None:
		lang, _ = locale.getdefaultlocale()
		os.environ['LANG'] = lang

	filename = "translations/messages_%s.mo" % lang[0][0:2]

	try:
		translation = gettext.GNUTranslations(open( filename, "rb" ) )
	except IOError:
		translation = gettext.NullTranslations()

	translation.install()
