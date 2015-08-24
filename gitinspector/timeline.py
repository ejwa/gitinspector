# coding: utf-8
#
# Copyright © 2012-2014 Ejwa Software. All rights reserved.
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
from localization import N_
from outputable import Outputable
import datetime
import format
import gravatar
import terminal
import textwrap

class TimelineData:
	def __init__(self, changes, useweeks):
		authordateinfo_list = sorted(changes.get_authordateinfo_list().items())
		self.changes = changes
		self.entries = {}
		self.total_changes_by_period = {}
		self.useweeks = useweeks

		for i in authordateinfo_list:
			key = None

			if useweeks:
				yearweek = datetime.date(int(i[0][0][0:4]), int(i[0][0][5:7]), int(i[0][0][8:10])).isocalendar()
				key = (i[0][1], str(yearweek[0]) + "W" + "{0:02d}".format(yearweek[1]))
			else:
				key = (i[0][1], i[0][0][0:7])

			if self.entries.get(key, None) == None:
				self.entries[key] = i[1]
			else:
				self.entries[key].insertions += i[1].insertions
				self.entries[key].deletions += i[1].deletions

		for period in self.get_periods():
			total_insertions = 0
			total_deletions = 0

			for author in self.get_authors():
				entry = self.entries.get((author[0], period), None)
				if entry != None:
					total_insertions += entry.insertions
					total_deletions += entry.deletions

			self.total_changes_by_period[period] = (total_insertions, total_deletions,
			                                        total_insertions + total_deletions)

	def get_periods(self):
		return sorted(set([i[1] for i in self.entries]))

	def get_total_changes_in_period(self, period):
		return self.total_changes_by_period[period]

	def get_authors(self):
		return sorted(set([(i[0][0], self.changes.get_latest_email_by_author(i[0][0])) for i in self.entries.items()]))

	def get_author_signs_in_period(self, author, period, multiplier):
		authorinfo = self.entries.get((author, period), None)
		total = float(self.total_changes_by_period[period][2])

		if authorinfo:
			i = multiplier * (self.entries[(author, period)].insertions / total)
			j = multiplier * (self.entries[(author, period)].deletions / total)
			return (int(i), int(j))
		else:
			return (0, 0)

	def get_multiplier(self, period, max_width):
		multiplier = 0

		while True:
			for i in self.entries:
				entry = self.entries.get(i)

				if period == i[1]:
					changes_in_period = float(self.total_changes_by_period[i[1]][2])
					if multiplier * (entry.insertions + entry.deletions) / changes_in_period > max_width:
						return multiplier

					multiplier += 0.25

	def is_author_in_period(self, period, author):
		return self.entries.get((author, period), None) != None

	def is_author_in_periods(self, periods, author):
		for period in periods:
			if self.is_author_in_period(period, author):
				return True
		return False


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

class Timeline(Outputable):
	def __init__(self, changes, useweeks):
		self.changes = changes
		self.useweeks = useweeks
		Outputable.__init__(self)

	def output_text(self):
		if self.changes.get_commits():
			print("\n" + textwrap.fill(_(TIMELINE_INFO_TEXT) + ":", width=terminal.get_size()[0]))

			timeline_data = TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()
			(width, _unused) = terminal.get_size()
			max_periods_per_row = int((width - 21) / 11)

			for i in range(0, len(periods), max_periods_per_row):
				__output_row__text__(timeline_data, periods[i:i+max_periods_per_row], names)

	def output_html(self):
		if self.changes.get_commits():
			timeline_data = TimelineData(self.changes, self.useweeks)
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

	def output_xml(self):
		if self.changes.get_commits():
			message_xml = "\t\t<message>" + _(TIMELINE_INFO_TEXT) + "</message>\n"
			timeline_xml = ""
			periods_xml = "\t\t<periods length=\"{0}\">\n".format("week" if self.useweeks else "month")

			timeline_data = TimelineData(self.changes, self.useweeks)
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
