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
from __future__ import unicode_literals
import json
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal
from .outputable import Outputable

HISTORICAL_INFO_TEXT = N_("The following historical commit information, by author, for this tag:was found")
NO_COMMITED_FILES_TEXT = N_("No commited files with the specified extensions were found")

class Changes_Per_Branch_Output(Outputable):
	def __init__(self, changes, branch):
		self.changes = changes
                self.branch = branch
		Outputable.__init__(self)

	def output_json(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		total_changes = 0.0

		for i in authorinfo_list:
			total_changes += authorinfo_list.get(i).insertions
			total_changes += authorinfo_list.get(i).deletions

		if authorinfo_list:
			message_json = "\t\t\t\"branch\": \"" + self.branch.strip() + "\",\n"
			changes_json = ""

			for i in sorted(authorinfo_list):
				author_email = self.changes.get_latest_email_by_author(i)
				authorinfo = authorinfo_list.get(i)

				percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100
				name_json = "\t\t\t\t\"name\": \"" + i + "\",\n"
				email_json = "\t\t\t\t\"email\": \"" + author_email + "\",\n"
				gravatar_json = "\t\t\t\t\"gravatar\": \"" + gravatar.get_url(author_email) + "\",\n"
				commits_json = "\t\t\t\t\"commits\": " + str(authorinfo.commits) + ",\n"
				insertions_json = "\t\t\t\t\"insertions\": " + str(authorinfo.insertions) + ",\n"
				deletions_json = "\t\t\t\t\"deletions\": " + str(authorinfo.deletions) + ",\n"
				percentage_json = "\t\t\t\t\"percentage_of_changes\": " + "{0:.2f}".format(percentage) + "\n"

				changes_json += ("\t{\n" + name_json + email_json + gravatar_json + commits_json +
				                 insertions_json + deletions_json + percentage_json + "\t\t\t\t}")
				changes_json += ","
			else:
				changes_json = changes_json[:-1]

			print("\t\t\"" + self.branch.strip() + "\": {\n" + message_json + "\t\t\t\"authors\": [\n\t\t\t" + changes_json + "\n\t\t\t]\n", end="")
		else:
			print("\t\t\"exception\": \"" + "No commited files with the specified extensions were found for this branch" + self.branch + "\"")

	def output_text(self):
		authorinfo_list = self.changes.get_authorinfo_list()
		total_changes = 0.0

		for i in authorinfo_list:
			total_changes += authorinfo_list.get(i).insertions
			total_changes += authorinfo_list.get(i).deletions

		if authorinfo_list:
			print(textwrap.fill("The following historical commit information, by author, for this tag:" + self.branch + " was found" + ":", width=terminal.get_size()[0]) + "\n")
			terminal.printb(terminal.ljust(_("Author"), 21) + terminal.rjust(_("Commits"), 13) +
			                terminal.rjust(_("Insertions"), 14) + terminal.rjust(_("Deletions"), 15) +
					terminal.rjust(_("% of changes"), 16))

			for i in sorted(authorinfo_list):
				authorinfo = authorinfo_list.get(i)
				percentage = 0 if total_changes == 0 else (authorinfo.insertions + authorinfo.deletions) / total_changes * 100

				print(terminal.ljust(i, 20)[0:20 - terminal.get_excess_column_count(i)], end=" ")
				print(str(authorinfo.commits).rjust(13), end=" ")
				print(str(authorinfo.insertions).rjust(13), end=" ")
				print(str(authorinfo.deletions).rjust(14), end=" ")
				print("{0:.2f}".format(percentage).rjust(15))
		else:
			print(_(NO_COMMITED_FILES_TEXT) + ".")
