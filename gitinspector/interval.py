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

from __future__ import unicode_literals

try:
	from shlex import quote
except ImportError:
	from pipes import quote

__since__ = ""

__until__ = ""

__ref__ = "HEAD"

def has_interval():
	return __since__ + __until__ != ""

def get_since():
	return __since__

def set_since(since):
	global __since__
	__since__ = "--since=" + quote(since)

def get_until():
	return __until__

def set_until(until):
	global __until__
	__until__ = "--until=" + quote(until)

def get_ref():
	return __ref__

def set_ref(ref):
	global __ref__
	__ref__ = ref
