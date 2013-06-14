# coding: utf-8
#
# Copyright © 2012-2013 Ejwa Software. All rights reserved.
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
import codecs
import os
import platform
import sys

__bold__ =  "\033[1m"
__normal__ =  "\033[0;0m"

def __get_size_windows__():
	res = None
	try:
		from ctypes import windll, create_string_buffer

		handler = windll.kernel32.GetStdHandle(-12) # stderr
		csbi = create_string_buffer(22)
		res = windll.kernel32.GetConsoleScreenBufferInfo(handler, csbi)
	except:
		return None

	if res:
		import struct
		(_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
		sizex = right - left + 1
		sizey = bottom - top + 1
		return sizex, sizey
	else:
		return None

def __get_size_linux__():
	def ioctl_get_window_size(file_descriptor):
		try:
			import fcntl, termios, struct
			size = struct.unpack('hh', fcntl.ioctl(file_descriptor, termios.TIOCGWINSZ, '1234'))
		except:
			return None

		return size

	size = ioctl_get_window_size(0) or ioctl_get_window_size(1) or ioctl_get_window_size(2)

	if not size:
		try:
			file_descriptor = os.open(os.ctermid(), os.O_RDONLY)
			size = ioctl_get_window_size(file_descriptor)
			os.close(file_descriptor)
		except:
			pass
	if not size:
		try:
			size = (os.environ["LINES"], os.environ["COLUMNS"])
		except:
			return None

	return int(size[1]), int(size[0])

def clear_row():
	print("\b" * 200, end="")

def skip_escapes(skip):
	if skip:
		global __bold__
		global __normal__
		__bold__ = ""
		__normal__ = ""

def printb(string):
	print(__bold__ + string + __normal__)

def get_size():
	width = 0
	height = 0

	if sys.stdout.isatty():
		current_os = platform.system()

		if current_os == 'Windows':
			(width, height) = __get_size_windows__()
		elif current_os == 'Linux' or current_os == 'Darwin' or  current_os.startswith('CYGWIN'):
			(width, height) = __get_size_linux__()

	if width > 0:
		return (width, height)

	return (80, 25)

def set_stdout_encoding():
	if not sys.stdout.isatty() and sys.version_info < (3,):
		sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
