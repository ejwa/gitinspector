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

from __future__ import print_function
import datetime
import terminal
import textwrap

class TimelineData:
	def __init__(self, changes, useweeks):
		authordateinfo_list = sorted(changes.get_authordateinfo_list().items())
		self.entries = {}
		self.total_changes_by_period = {}
		self.useweeks = useweeks

		for i in authordateinfo_list:
			key = None

			if useweeks:
				yearweek = datetime.date(int(i[0][0][0:4]), int(i[0][0][5:7]), int(i[0][0][8:10])).isocalendar()
				key = (i[0][1], str(yearweek[0]) + "W" + str(yearweek[1]))
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
				entry = self.entries.get((author, period), None)
				if entry != None:
					total_insertions += entry.insertions
					total_deletions += entry.deletions

			self.total_changes_by_period[period] = (total_insertions, total_deletions,
			                                        total_insertions + total_deletions)

	def get_periods(self):
		return sorted(set([i[1] for i in self.entries]))

	def get_authors(self):
		return sorted(set([i[0] for i in self.entries]))

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

__timeline_info_text__ = "The following history timeline has been gathered from the repository"

def output_html(changes, useweeks):
	print("HTML output not yet supported.")

def __output_row__text__(timeline_data, periods, names):
	print("\n" + terminal.__bold__ + "Author".ljust(20), end=" ")
	
	for period in periods:
		print(period.rjust(10), end=" ")

	print(terminal.__normal__)

	for name in names:
		print(name.ljust(20)[0:20], end=" ")
		for period in periods:
			multiplier = timeline_data.get_multiplier(period, 9)
			signs = timeline_data.get_author_signs_in_period(name, period, multiplier)
			signs_str = (signs[1] * "-" + signs[0] * "+")
			print (("." if timeline_data.is_author_in_period(period, name) and
			               len(signs_str) == 0 else signs_str).rjust(10), end=" ")
		print("")

def output_text(changes, useweeks):
	if changes.get_commits():
		print("\n" + textwrap.fill(__timeline_info_text__ + ":", width=terminal.get_size()[0]))

		timeline_data = TimelineData(changes, useweeks)
		periods = timeline_data.get_periods()
		names = timeline_data.get_authors()
		(width, _) = terminal.get_size()
		max_periods_per_row = int((width - 21) / 11)

		for i in range(0, len(periods), max_periods_per_row):
			__output_row__text__(timeline_data, periods[i:i+max_periods_per_row], names)

def output_xml(changes, useweeks):
	if changes.get_commits():
		message_xml = "\t\t<message>" + __timeline_info_text__ + "</message>\n"
		timeline_xml = ""
		periods_xml = "\t\t<periods length=\"{0}\">\n".format("week" if useweeks else "month")

		timeline_data = TimelineData(changes, useweeks)
		periods = timeline_data.get_periods()
		names = timeline_data.get_authors()

		for period in periods:
			name_xml = "\t\t\t\t<name>" + str(period) + "</name>\n"
			authors_xml = ""

			for name in names:
				authors_xml += "\t\t\t\t<authors>\n"
				multiplier = timeline_data.get_multiplier(period, 24)
				signs = timeline_data.get_author_signs_in_period(name, period, multiplier)
				signs_str = (signs[1] * "-" + signs[0] * "+")

				if not len(signs_str) == 0:
					authors_xml += "\t\t\t\t\t<author>\n\t\t\t\t\t\t<name>" + name + "</name>\n"
					authors_xml += "\t\t\t\t\t\t<work>" + signs_str + "</work>\n\t\t\t\t\t</author>\n"

				authors_xml += "\t\t\t\t</authors>\n"

			timeline_xml += "\t\t\t<period>\n" + name_xml + authors_xml + "\t\t\t</period>\n"

		print("\t<timeline>\n" + message_xml + periods_xml + timeline_xml + "\t\t</periods>\n\t</timeline>")
