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
import math
import textwrap
from xml.sax.saxutils import escape
from ..localization import N_
from .. import format, gravatar, terminal, timeline
from .outputable import Outputable, attribute, author_indices, html_avatar, html_card, percentage

TIMELINE_INFO_TEXT_M = N_("The following monthly history timeline has been gathered from the repository")
TIMELINE_INFO_TEXT_W = N_("The following weekly history timeline has been gathered from the repository")
MODIFIED_LINES_TEXT = N_("Modified Lines:")

#Enough periods to show a trend, few enough that a cell stays wide enough to read on a phone.
PERIODS_PER_BAND = 10

def __output_line__text__(timeline_data, periods, names):
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

	print(terminal.__bold__  + terminal.ljust(_(MODIFIED_LINES_TEXT), 20) + terminal.__normal__, end=" ")

	for period in periods:
		total_changes = str(timeline_data.get_total_changes_in_period(period)[2])

		if hasattr(total_changes, 'decode'):
			total_changes = total_changes.decode("utf-8", "replace")

		print(terminal.rjust(total_changes, 10), end=" ")

	print("")

def __compact__(number):
	if number >= 10000:
		return "{0:.0f}k".format(number / 1000.0)
	if number >= 1000:
		return "{0:.1f}k".format(number / 1000.0)
	return "{0}".format(number)

def __changes_title__(label, insertions, deletions):
	return attribute("{0}: +{1} / −{2}".format(label, insertions, deletions))

def __html_cell__(title, insertions, deletions, busiest):
	"""A cell is a green to red gradient split by the share of insertions, deepened by the amount."""
	changes = insertions + deletions

	if not changes:
		return "<div class=\"gi-cell\"></div>"

	weight = 18 + 82 * math.sqrt(percentage(changes, busiest) / 100.0)
	split = percentage(insertions, changes)

	return ("<div class=\"gi-cell\" title=\"{3}\" style=\"background:linear-gradient(90deg,"
	        "color-mix(in oklch, var(--add) {0:.0f}%, var(--surface)) 0 {1:.0f}%,"
	        "color-mix(in oklch, var(--del) {0:.0f}%, var(--surface)) {1:.0f}% 100%);color:{2}\">{4}</div>".format(
	        weight, split, "var(--surface)" if weight > 70 else "var(--text)", title, __compact__(changes)))

def __output_band__html__(timeline_data, periods, names, indices, busiest):
	#Every band keeps the full number of columns, so that a short last band is not blown up.
	columns = " style=\"--gi-cols:{0}\"".format(PERIODS_PER_BAND)
	tallest = max([timeline_data.get_total_changes_in_period(period)[2] for period in periods])
	bars = "<div class=\"gi-grid\"" + columns + "><div></div>"
	totals = ""
	axis = "<div class=\"gi-grid gi-axis\"" + columns + "><div class=\"gi-range\">{0}–{1}</div>".format(
	       escape(periods[0]), escape(periods[-1]))
	changed = 0

	for period in periods:
		(insertions, deletions, total) = timeline_data.get_total_changes_in_period(period)
		title = __changes_title__(period, insertions, deletions)
		changed += total

		bars += ("<div class=\"gi-week\" title=\"{0}\"><div class=\"gi-up\"><div style=\"height:{1:.0f}%\"></div></div>"
		         "<div class=\"gi-down\"><div style=\"height:{2:.0f}%\"></div></div></div>".format(
		         title, percentage(insertions, tallest), percentage(deletions, tallest)))
		totals += "<div class=\"gi-week-total\" title=\"{0}\">{1}</div>".format(title, __compact__(total))
		axis += "<div>" + escape(period) + "</div>"

	bars += ("<div class=\"gi-band-total\">" + _(MODIFIED_LINES_TEXT) + " <strong>" + __compact__(changed) +
	         "</strong></div>" + totals + "</div>")
	axis += "</div>"
	heat = ""

	for name in names:
		if not timeline_data.is_author_in_periods(periods, name[0]):
			continue

		index = indices.get(name[0], 0)
		url = gravatar.get_url(name[1], size=18) if format.get_selected() == "html" else None
		heat += "<div class=\"gi-grid\" data-gi-searchable=\"authors\"" + columns + ">"
		heat += "<div class=\"gi-heat\">{0}<span>{1}</span></div>".format(html_avatar(name[0], index, url), escape(name[0]))

		for period in periods:
			(insertions, deletions) = timeline_data.get_author_changes_in_period(name[0], period)
			heat += __html_cell__(__changes_title__(name[0] + ", " + period, insertions, deletions),
			                      insertions, deletions, busiest)

		heat += "</div>"

	return "<div class=\"gi-band\">" + bars + axis + heat + "</div>"

class TimelineOutput(Outputable):
	def __init__(self, changes, useweeks):
		self.changes = changes
		self.useweeks = useweeks
		Outputable.__init__(self)

	def get_tinfo_txt(self):
		if self.useweeks:
			return _(TIMELINE_INFO_TEXT_W)
		return _(TIMELINE_INFO_TEXT_M)

	def output_text(self):
		if self.changes.get_commits():
			print("\n" + textwrap.fill(self.get_tinfo_txt() + ":", width=terminal.get_size()[0]))

			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()
			(width, _unused) = terminal.get_size()
			max_periods_per_line = int((width - 21) / 11)

			for i in range(0, len(periods), max_periods_per_line):
				__output_line__text__(timeline_data, periods[i:i+max_periods_per_line], names)

	def output_html(self):
		if self.changes.get_commits():
			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()
			indices = author_indices(self.changes.get_authorinfo_list())
			#One scale for every cell in the report, so that a quiet week stays visibly quiet.
			busiest = max([sum(timeline_data.get_author_changes_in_period(name[0], period))
			               for name in names for period in periods])
			bands = ""

			for i in range(0, len(periods), PERIODS_PER_BAND):
				bands += __output_band__html__(timeline_data, periods[i:i+PERIODS_PER_BAND], names, indices, busiest)

			print(html_card(self.get_tinfo_txt(), "<div class=\"gi-scroll\">" + bands + "</div>", pad=True))

	def output_json(self):
		if self.changes.get_commits():
			message_json = "\t\t\t\"message\": \"" + self.get_tinfo_txt() + "\",\n"
			timeline_json = ""
			periods_json = "\t\t\t\"period_length\": \"{0}\",\n".format("week" if self.useweeks else "month")
			periods_json += "\t\t\t\"periods\": [\n\t\t\t"

			timeline_data = timeline.TimelineData(self.changes, self.useweeks)
			periods = timeline_data.get_periods()
			names = timeline_data.get_authors()

			for period in periods:
				name_json = "\t\t\t\t\"name\": \"" + str(period) + "\",\n"
				authors_json = "\t\t\t\t\"authors\": [\n\t\t\t\t"

				for name in names:
					if timeline_data.is_author_in_period(period, name[0]):
						multiplier = timeline_data.get_multiplier(period, 24)
						signs = timeline_data.get_author_signs_in_period(name[0], period, multiplier)
						signs_str = (signs[1] * "-" + signs[0] * "+")

						if len(signs_str) == 0:
							signs_str = "."

						authors_json += "{\n\t\t\t\t\t\"name\": \"" + name[0] + "\",\n"
						authors_json += "\t\t\t\t\t\"email\": \"" + name[1] + "\",\n"
						authors_json += "\t\t\t\t\t\"gravatar\": \"" + gravatar.get_url(name[1]) + "\",\n"
						authors_json += "\t\t\t\t\t\"work\": \"" + signs_str + "\"\n\t\t\t\t},"
				else:
					authors_json = authors_json[:-1]

				authors_json += "],\n"
				modified_lines_json = "\t\t\t\t\"modified_lines\": " + \
				                    str(timeline_data.get_total_changes_in_period(period)[2]) + "\n"
				timeline_json += "{\n" + name_json + authors_json + modified_lines_json + "\t\t\t},"
			else:
				timeline_json = timeline_json[:-1]

			print(",\n\t\t\"timeline\": {\n" + message_json + periods_json + timeline_json + "]\n\t\t}", end="")

	def output_xml(self):
		if self.changes.get_commits():
			message_xml = "\t\t<message>" + self.get_tinfo_txt() + "</message>\n"
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
						authors_xml += "\t\t\t\t\t\t<email>" + name[1] + "</email>\n"
						authors_xml += "\t\t\t\t\t\t<gravatar>" + gravatar.get_url(name[1]) + "</gravatar>\n"
						authors_xml += "\t\t\t\t\t\t<work>" + signs_str + "</work>\n\t\t\t\t\t</author>\n"

				authors_xml += "\t\t\t\t</authors>\n"
				modified_lines_xml = "\t\t\t\t<modified_lines>" + \
				                    str(timeline_data.get_total_changes_in_period(period)[2]) + "</modified_lines>\n"
				timeline_xml += "\t\t\t<period>\n" + name_xml + authors_xml + modified_lines_xml + "\t\t\t</period>\n"

			print("\t<timeline>\n" + message_xml + periods_xml + timeline_xml + "\t\t</periods>\n\t</timeline>")
