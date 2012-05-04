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

import datetime
import terminal

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

		for p in self.get_periods():
			total_insertions = 0
			total_deletions = 0

			for a in self.get_authors():
				e = self.entries.get((a, p), None)
				if e != None:
					total_insertions += e.insertions
					total_deletions += e.deletions

			self.total_changes_by_period[p] = (total_insertions, total_deletions, total_insertions + total_deletions)

	def get_periods(self):
		return sorted(set([i[1] for i in self.entries]))

	def get_authors(self):
		return sorted(set([i[0] for i in self.entries]))

	def get_author_signs_in_period(self, author, period, multiplier):
		authorinfo = self.entries.get((author, period), None)
		insertions = float(self.total_changes_by_period[period][0])
		deletions = float(self.total_changes_by_period[period][1])
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
				e = self.entries.get(i)

				if period == i[1]:
					deletions = e.deletions / float(self.total_changes_by_period[i[1]][2])
					if multiplier * (e.insertions + e.deletions) / float(self.total_changes_by_period[i[1]][2]) > max_width:
						return multiplier

					multiplier += 0.25

	def is_author_in_period(self, period, author):
		return self.entries.get((author, period), None) != None

def __output_row__(changes, timeline_data, periods, names):
	print "\n" + terminal.bold + "Author".ljust(20),
	
	for p in periods:
		print p.rjust(10),

	print terminal.normal

	for n in names:
		print n.ljust(20)[0:20],
		for p in periods:
			multiplier = timeline_data.get_multiplier(p, 9)
			signs = timeline_data.get_author_signs_in_period(n, p, multiplier)
			signs_str = (signs[1] * "-" + signs[0] * "+")
			print ("." if timeline_data.is_author_in_period(p, n) and len(signs_str) == 0 else signs_str).rjust(10),
		print ""

def output(changes, useweeks):
	if changes.get_commits():
		print "\nThe following history timeline has been gathered from the repository:"

		timeline_data = TimelineData(changes, useweeks)
		periods = timeline_data.get_periods()
		names = timeline_data.get_authors()
		(width, _) = terminal.get_size()
		max_periods_per_row = (width - 21) / 11

		for i in range(0, len(periods), max_periods_per_row):
			__output_row__(changes, timeline_data, periods[i:i+max_periods_per_row], names)
