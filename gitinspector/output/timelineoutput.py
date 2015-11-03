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
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal, timeline
from .outputable import Outputable

TIMELINE_INFO_TEXT = N_("The following history timeline has been gathered from the repository")
MODIFIED_ROWS_TEXT = N_("Modified Rows:")

def __output_row__text__(timeline_data, periods, names):
	print("\n" + terminal.__bold__ + terminal.ljust(_("Author"), 20), end=" ")

	for period in periods:
		print(terminal.rjust(period, 10), end=" ")

	print(terminal.__normal__)

	for name in names:
		if timeline_data.is_author_in_periods(periods, name[0]):
			print(terminal.ljust(name[0], 20)[0:20 - terminal.get_excess_column_count(name[0])], end=" ")

			for period in periods:
				multiplier = timeline_data.get_multiplier(period, 9)
				signs = timeline_data.get_author_signs_in_period(name[0], period, multiplier)
				signs_str = (signs[1] * "-" + signs[0] * "+")
				print (("." if timeline_data.is_author_in_period(period, name[0]) and
				               len(signs_str) == 0 else signs_str).rjust(10), end=" ")
			print("")

	print(terminal.__bold__  + terminal.ljust(_(MODIFIED_ROWS_TEXT), 20) + terminal.__normal__, end=" ")

	for period in periods:
		total_changes = str(timeline_data.get_total_changes_in_period(period)[2])

		if hasattr(total_changes, 'decode'):
			total_changes = total_changes.decode("utf-8", "replace")

		print(terminal.rjust(total_changes, 10), end=" ")

	print("")

def __output_row__html__(timeline_data, periods, names):
	timeline_xml = "<table class=\"git full\"><thead><tr><th>" + _("Author") + "</th>"

	for period in periods:
		timeline_xml += "<th>" + str(period) + "</th>"

	timeline_xml += "</tr></thead><tbody>"
	i = 0

	for name in names:
		if timeline_data.is_author_in_periods(periods, name[0]):
			timeline_xml += "<tr" + (" class=\"odd\">" if i % 2 == 1 else ">")

			if format.get_selected() == "html":
				timeline_xml += "<td><img src=\"{0}\"/>{1}</td>".format(gravatar.get_url(name[1]), name[0])
			else:
				timeline_xml += "<td>" + name[0] + "</td>"

			for period in periods:
				multiplier = timeline_data.get_multiplier(period, 18)
				signs = timeline_data.get_author_signs_in_period(name[0], period, multiplier)
				signs_str = (signs[1] * "<div class=\"remove\">&nbsp;</div>" + signs[0] * "<div class=\"insert\">&nbsp;</div>")

				timeline_xml += "<td>" + ("." if timeline_data.is_author_in_period(period, name[0]) and len(signs_str) == 0 else signs_str)
				timeline_xml += "</td>"
			timeline_xml += "</tr>"
			i = i + 1

	timeline_xml += "<tfoot><tr><td><strong>" + _(MODIFIED_ROWS_TEXT) + "</strong></td>"

	for period in periods:
		total_changes = timeline_data.get_total_changes_in_period(period)
		timeline_xml += "<td>" + str(total_changes[2]) + "</td>"

	timeline_xml += "</tr></tfoot></tbody></table>"
	print(timeline_xml)

class TimelineOutput(Outputable):
	def __init__(self, changes, useweeks):
		self.changes = changes
		self.useweeks = useweeks
		Outputable.__init__(self)

	def output_text(self):
		if self.changes.get_commits():
			print("\n" + textwrap.fill(_(TIMELINE_INFO_TEXT) + ":", width=terminal.get_size()[0]))

			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()
			(width, _unused) = terminal.get_size()
			max_periods_per_row = int((width - 21) / 11)

			for i in range(0, len(periods), max_periods_per_row):
				__output_row__text__(timeline_data, periods[i:i+max_periods_per_row], names)

	def output_html(self):
		if self.changes.get_commits():
			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()
			max_periods_per_row = 8

			timeline_xml = "<div><div id=\"timeline\" class=\"box\">"
			timeline_xml += "<p>" + _(TIMELINE_INFO_TEXT) + ".</p>"
			print(timeline_xml)

			for i in range(0, len(periods), max_periods_per_row):
				__output_row__html__(timeline_data, periods[i:i+max_periods_per_row], names)

			timeline_xml = "</div></div>"
			print(timeline_xml)

	def output_json(self):
		if self.changes.get_commits():
			message_xml = "\t\t\t\"message\": \"" + _(TIMELINE_INFO_TEXT) + "\",\n"
			timeline_xml = ""
			periods_xml = "\t\t\t\"period_length\": \"{0}\",\n".format("week" if self.useweeks else "month")
			periods_xml += "\t\t\t\"periods\": [\n\t\t\t"

			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()

			for period in periods:
				name_xml = "\t\t\t\t\"name\": \"" + str(period) + "\",\n"
				authors_xml = "\t\t\t\t\"authors\": [\n\t\t\t\t"

				for name in names:
					if timeline_data.is_author_in_period(period, name[0]):
						multiplier = timeline_data.get_multiplier(period, 24)
						signs = timeline_data.get_author_signs_in_period(name[0], period, multiplier)
						signs_str = (signs[1] * "-" + signs[0] * "+")

						if len(signs_str) == 0:
							signs_str = "."

						authors_xml += "{\n\t\t\t\t\t\"name\": \"" + name[0] + "\",\n"
						authors_xml += "\t\t\t\t\t\"gravatar\": \"" + gravatar.get_url(name[1]) + "\",\n"
						authors_xml += "\t\t\t\t\t\"work\": \"" + signs_str + "\"\n\t\t\t\t},"
				else:
					authors_xml = authors_xml[:-1]

				authors_xml += "],\n"
				modified_rows_xml = "\t\t\t\t\"modified_rows\": " + \
				                    str(timeline_data.get_total_changes_in_period(period)[2]) + "\n"
				timeline_xml += "{\n" + name_xml + authors_xml + modified_rows_xml + "\t\t\t},"
			else:
				timeline_xml = timeline_xml[:-1]

			print(",\n\t\t\"timeline\": {\n" + message_xml + periods_xml + timeline_xml + "]\n\t\t}", end="")

	def output_xml(self):
		if self.changes.get_commits():
			message_xml = "\t\t<message>" + _(TIMELINE_INFO_TEXT) + "</message>\n"
			timeline_xml = ""
			periods_xml = "\t\t<periods length=\"{0}\">\n".format("week" if self.useweeks else "month")

			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()

			for period in periods:
				name_xml = "\t\t\t\t<name>" + str(period) + "</name>\n"
				authors_xml = "\t\t\t\t<authors>\n"

				for name in names:
					if timeline_data.is_author_in_period(period, name[0]):
						multiplier = timeline_data.get_multiplier(period, 24)
						signs = timeline_data.get_author_signs_in_period(name[0], period, multiplier)
						signs_str = (signs[1] * "-" + signs[0] * "+")

						if len(signs_str) == 0:
							signs_str = "."

						authors_xml += "\t\t\t\t\t<author>\n\t\t\t\t\t\t<name>" + name[0] + "</name>\n"
						authors_xml += "\t\t\t\t\t\t<gravatar>" + gravatar.get_url(name[1]) + "</gravatar>\n"
						authors_xml += "\t\t\t\t\t\t<work>" + signs_str + "</work>\n\t\t\t\t\t</author>\n"

				authors_xml += "\t\t\t\t</authors>\n"
				modified_rows_xml = "\t\t\t\t<modified_rows>" + \
				                    str(timeline_data.get_total_changes_in_period(period)[2]) + "</modified_rows>\n"
				timeline_xml += "\t\t\t<period>\n" + name_xml + authors_xml + modified_rows_xml + "\t\t\t</period>\n"

			print("\t<timeline>\n" + message_xml + periods_xml + timeline_xml + "\t\t</periods>\n\t</timeline>")
