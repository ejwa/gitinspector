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

import os
import sys
from gitinspector.version import __version__
from glob import glob
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name = "gitinspector",
	version = __version__,
	author = "Ejwa Software",
	author_email = "gitinspector@ejwa.se",
	description = ("A statistical analysis tool for git repositories."),
	license = "GNU GPL v3",
	keywords = "analysis analyzer git python statistics stats vc vcs timeline",
	url = "https://github.com/ejwa/gitinspector",
	long_description = read("DESCRIPTION.txt"),
	classifiers = [
		"Development Status :: 4 - Beta",
		"Environment :: Console",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
		"Topic :: Software Development :: Version Control",
		"Topic :: Utilities"
	],
	packages = find_packages(exclude = ['tests']),
	package_data = {"": ["html/*", "translations/*"]},
	data_files = [("share/doc/gitinspector", glob("*.txt"))],
	entry_points = {"console_scripts": ["gitinspector = gitinspector.gitinspector:main"]},
	zip_safe = False
)
