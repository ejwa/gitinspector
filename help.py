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

"""Usage: {0} [OPTION]... [DIRECTORY]
List information about the repository in DIRECTORY. If no directory is
specified, the current directory is used. If multiple directories are
given, information will be fetched from the last directory specified.

Mandatory arguments to long options are mandatory for short options too.
  -c, --checkout-missing       try to checkout any missing files
  -f, --file-types=EXTENSIONS  a comma separated list of file extensions to
                                 include when computing statistics. The
                                 default extensions used are:
                                 {1}
  -F, --format=FORMAT          define in which format output should be
                                 generated; the default format is 'text' and
                                 the available formats are: {2}
      --grading                show statistics and information in a way that
                                 is formatted for grading of student projects;
                                 this is the same as supplying -HlmrTw
  -H, --hard                   track rows and look for duplicates harder;
                                 this can be quite slow with big repositories
  -l, --list-file-types        list all the file extensions available in the
                                 current branch of the repository
  -m  --metrics                include checks for certain metrics during the
                                 analysis of commits
  -r  --responsibilities       show which files the different authors seem
                                 most responsible for
      --since=DATE             show statistics for commits more recent than a
                                 specific date
  -T, --timeline               show commit timeline, including author names
      --until=DATE             show  statistics for commits older than a
                                 specific date
  -w                           show all statistical information in weeks
                                 instead of in months
  -x, --exclude=PATTERN        an exclusion pattern describing file names that
                                 should be excluded from the statistics; can
                                 be specified multiple times
  -h, --help                   display this help and exit
      --version                output version information and exit

gitinspector will filter statistics to only include commits that modify,
add or remove one of the specified extensions, see -f or --file-types for
more information.

gitinspector requires that the git executable is available in your PATH.
Report gitinspector bugs to gitinspector@ejwa.se."""

from __future__ import print_function
from extensions import __default_extensions__
from format import __available_formats__
import sys

def output():
	print(__doc__.format(sys.argv[0], ",".join(__default_extensions__), ",".join(__available_formats__)))
