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

from __future__ import print_function
import codecs
import os
import platform
import sys
import unicodedata

__bold__ = "\033[1m"
__normal__ = "\033[0;0m"

DEFAULT_TERMINAL_SIZE = (80, 25)

def __get_size_windows__():
	res = None
	try:
		from ctypes import windll, create_string_buffer

		handler = windll.kernel32.GetStdHandle(-12) # stderr
		csbi = create_string_buffer(22)
		res = windll.kernel32.GetConsoleScreenBufferInfo(handler, csbi)
	except:
		return DEFAULT_TERMINAL_SIZE

	if res:
		import struct
		(_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
		sizex = right - left + 1
		sizey = bottom - top + 1
		return sizex, sizey
	else:
		return DEFAULT_TERMINAL_SIZE

def __get_size_linux__():
	def ioctl_get_window_size(file_descriptor):
		try:
			import fcntl, termios, struct
			size = struct.unpack('hh', fcntl.ioctl(file_descriptor, termios.TIOCGWINSZ, "1234"))
		except:
			return DEFAULT_TERMINAL_SIZE

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
			return DEFAULT_TERMINAL_SIZE

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

		if current_os == "Windows":
			(width, height) = __get_size_windows__()
		elif current_os == "Linux" or current_os == "Darwin" or  current_os.startswith("CYGWIN"):
			(width, height) = __get_size_linux__()

	if width > 0:
		return (width, height)

	return DEFAULT_TERMINAL_SIZE

def set_stdout_encoding():
	if not sys.stdout.isatty() and sys.version_info < (3,):
		sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

def set_stdin_encoding():
	if not sys.stdin.isatty() and sys.version_info < (3,):
		sys.stdin = codecs.getreader("utf-8")(sys.stdin)

def convert_command_line_to_utf8():
	try:
		argv = []

		for arg in sys.argv:
			argv.append(arg.decode(sys.stdin.encoding, "replace"))

		return argv
	except AttributeError:
		return sys.argv

def check_terminal_encoding():
	if sys.stdout.isatty() and (sys.stdout.encoding == None or sys.stdin.encoding == None):
		print(_("WARNING: The terminal encoding is not correctly configured. gitinspector might malfunction. "
		        "The encoding can be configured with the environment variable 'PYTHONIOENCODING'."), file=sys.stderr)

def get_excess_column_count(string):
	width_mapping = {'F': 2, 'H': 1, 'W': 2, 'Na': 1, 'N': 1, 'A': 1}
	result = 0

	for i in string:
		width = unicodedata.east_asian_width(i)
		result += width_mapping[width]

	return result - len(string)

def ljust(string, pad):
	return string.ljust(pad - get_excess_column_count(string))

def rjust(string, pad):
	return string.rjust(pad - get_excess_column_count(string))

def output_progress(text, pos, length):
	if sys.stdout.isatty():
		(width, _unused) = get_size()
		progress_text = text.format(100 * pos / length)

		if len(progress_text) > width:
			progress_text = "...%s" % progress_text[-width+3:]

		print("\r{0}\r{1}".format(" " * width, progress_text), end="")
		sys.stdout.flush()
