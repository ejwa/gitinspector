# coding: utf-8
#
# Copyright © 2012-2026 Ejwa Hosting AB. All rights reserved.
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
import base64
import json
import os
import textwrap
import time
from xml.sax.saxutils import escape, quoteattr
from .localization import N_
from . import basedir, localization, terminal, version

__available_formats__ = ["html", "htmlembedded", "json", "text", "xml"]

DEFAULT_FORMAT = __available_formats__[3]

__selected_format__ = DEFAULT_FORMAT

class InvalidFormatError(Exception):
	def __init__(self, msg):
		super(InvalidFormatError, self).__init__(msg)
		self.msg = msg

def select(format):
	global __selected_format__
	__selected_format__ = format

	return format in __available_formats__

def get_selected():
	return __selected_format__

def is_interactive_format():
	return __selected_format__ == "text"

def __output_html_template__(name):
	template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
	file_r = open(template_path, "rb")
	template = file_r.read().decode("utf-8", "replace")

	file_r.close()
	return template

REPOSITORY_STATISTICS_TEXT = N_("repository statistics")
DEFAULT_THEME_TEXT = N_("Default")
TERMINAL_THEME_TEXT = N_("Terminal")
MODE_TEXT = N_("Toggle light and dark")
DARK_TEXT = N_("Dark")
LIGHT_TEXT = N_("Light")
SEARCH_TEXT = N_("Search")
AUTHORS_TEXT = N_("Authors")
FILES_TEXT = N_("Files")

INFO_ONE_REPOSITORY = N_("Statistical information for the repository '{0}' was gathered on {1}.")
INFO_MANY_REPOSITORIES = N_("Statistical information for the repositories '{0}' was gathered on {1}.")
INFO_ONE_BRANCH = N_("The analyzed branch was '{0}'.")
INFO_MANY_BRANCHES = N_("The analyzed branches were {0}.")
BRANCH_IN_REPOSITORY = N_("'{0}' in {1}")

def __info_text__(repos):
	repos_string = ", ".join([repo.name for repo in repos])

	if len(repos) <= 1:
		return _(INFO_ONE_REPOSITORY).format(repos_string, localization.get_date()) + " " + \
		       _(INFO_ONE_BRANCH).format(repos[0].branch)

	branches = ", ".join([_(BRANCH_IN_REPOSITORY).format(repo.branch, repo.name) for repo in repos])
	return _(INFO_MANY_REPOSITORIES).format(repos_string, localization.get_date()) + " " + \
	       _(INFO_MANY_BRANCHES).format(branches)

def output_header(repos):
	repos_string = ", ".join([repo.name for repo in repos])

	if __selected_format__ == "html" or __selected_format__ == "htmlembedded":
		base = basedir.get_basedir()
		html_header = __output_html_template__(base + "/html/html.header")

		logo_file = open(base + "/html/gitinspector_piclet.png", "rb")
		logo = logo_file.read()
		logo_file.close()
		logo = base64.b64encode(logo)

		# The terminal theme asks for a font that only the linked format can fetch; the embedded one
		# falls back to whatever monospaced face the reader has.
		if __selected_format__ == "htmlembedded":
			fonts = ""
		else:
			fonts = "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />\n\t\t" + \
			        "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?" + \
			        "family=JetBrains+Mono:wght@400;500;600&display=swap\" />"

		print(html_header.format(title=_("Repository statistics for '{0}'").format(escape(repos_string)),
		                         fonts=fonts,
		                         stylesheet=__output_html_template__(base + "/html/report.css"),
		                         logo=logo.decode("utf-8", "replace"),
		                         version=version.__version__,
		                         statistics_text=_(REPOSITORY_STATISTICS_TEXT),
		                         repo_title=escape(repos_string),
		                         repo_text=escape(__info_text__(repos)),
		                         default_text=_(DEFAULT_THEME_TEXT),
		                         terminal_text=_(TERMINAL_THEME_TEXT),
		                         mode_text=_(MODE_TEXT),
		                         dark_text=_(DARK_TEXT),
		                         light_text=_(LIGHT_TEXT),
		                         search_text=_(SEARCH_TEXT),
		                         authors_text=_(AUTHORS_TEXT),
		                         files_text=_(FILES_TEXT)))
	elif __selected_format__ == "json":
		print("{\n\t\"gitinspector\": {")
		print("\t\t\"version\": \"" + version.__version__ + "\",")

		if len(repos) <= 1:
			print("\t\t\"repository\": " + json.dumps(repos_string) + ",")
			print("\t\t\"branch\": " + json.dumps(repos[0].branch) + ",")
		else:
			print("\t\t\"repositories\": [ " + ", ".join([json.dumps(repo.name) for repo in repos]) + " ],")
			print("\t\t\"branches\": [ " + ", ".join([json.dumps(repo.branch) for repo in repos]) + " ],")

		print("\t\t\"report_date\": \"" + time.strftime("%Y/%m/%d") + "\",")

	elif __selected_format__ == "xml":
		print("<gitinspector>")
		print("\t<version>" + version.__version__ + "</version>")

		if len(repos) <= 1:
			print("\t<repository branch=" + quoteattr(repos[0].branch) + ">" + escape(repos_string) + "</repository>")
		else:
			print("\t<repositories>")

			for repo in repos:
				print("\t\t<repository branch=" + quoteattr(repo.branch) + ">" + escape(repo.name) + "</repository>")

			print("\t</repositories>")

		print("\t<report-date>" + time.strftime("%Y/%m/%d") + "</report-date>")
	else:
		print(textwrap.fill(__info_text__(repos), width=terminal.get_size()[0]))

def output_footer():
	if __selected_format__ == "html" or __selected_format__ == "htmlembedded":
		base = basedir.get_basedir()
		html_footer = __output_html_template__(base + "/html/html.footer")
		print(html_footer.format(script=__output_html_template__(base + "/html/report.js"),
		                         logo_text=_("The output has been generated by {0} {1}. The statistical analysis tool"
		                                     " for git repositories.").format(
		                                     "<a href=\"https://github.com/ejwa/gitinspector\">gitinspector</a>",
		                                     version.__version__)))
	elif __selected_format__ == "json":
		print("\n\t}\n}")
	elif __selected_format__ == "xml":
		print("</gitinspector>")
