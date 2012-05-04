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

import platform

bold =  "\033[1m"
normal =  "\033[0;0m"

def __get_size_windows__():
	res=None
	try:
		from ctypes import windll, create_string_buffer

		h = windll.kernel32.GetStdHandle(-12) # stderr
		csbi = create_string_buffer(22)
		res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
	except:
		return None

	if res:
		import struct
		(bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
		sizex = right - left + 1
		sizey = bottom - top + 1
		return sizex, sizey
	else:
		return None

def __get_size_tput__():
	try:
		import subprocess
		proc=subprocess.Popen(["tput", "cols"], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
		output = proc.communicate(input = None)
		cols = int(output[0])
		proc = subprocess.Popen(["tput", "lines"], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
		output = proc.communicate(input = None)
		rows = int(output[0])
		return (cols, rows)
	except:
		return None

def __get_size_linux__():
	def ioctl_GWINSZ(fd):
		try:
			import fcntl, termios, struct, os
			cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
		except:
			return None

		return cr

	cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)

	if not cr:
		try:
			fd = os.open(os.ctermid(), os.O_RDONLY)
			cr = ioctl_GWINSZ(fd)
			os.close(fd)
		except:
			pass
	if not cr:
		try:
			cr = (env['LINES'], env['COLUMNS'])
		except:
			return None

	return int(cr[1]), int(cr[0])

def skip_escapes(skip):
	if skip:
		global bold
		global normal
		bold = ""
		normal = ""

def printb(string):
	print bold + string + normal

def get_size():
	current_os = platform.system()
	tuple_xy = None

	if current_os == 'Windows':
		tuple_xy = __get_size_windows__()
	if tuple_xy is None:
		tuple_xy = __get_size_tput__()
	if current_os == 'Linux' or current_os == 'Darwin' or  current_os.startswith('CYGWIN'):
		tuple_xy = __get_size_linux__()
	if tuple_xy is None:
		tuple_xy = (80, 25)

	return tuple_xy
