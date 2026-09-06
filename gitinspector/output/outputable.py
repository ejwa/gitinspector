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
from xml.sax.saxutils import escape
from .. import format

class Outputable(object):
	def output_html(self):
		raise NotImplementedError(_("HTML output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

	def output_json(self):
		raise NotImplementedError(_("JSON output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

	def output_text(self):
		raise NotImplementedError(_("Text output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

	def output_xml(self):
		raise NotImplementedError(_("XML output not yet supported in") + " \"" + self.__class__.__name__ + "\".")

#The twelve author colours of the report stylesheet; an author keeps the same colour in every
#section because the index comes from its place in the sorted list of names.
AUTHOR_COLORS = 12

#Authors below this share of the work are gathered into a single entry in the legends, which would
#otherwise grow longer than the chart they explain in a repository with many contributors.
MINOR_AUTHOR_PERCENTAGE = 1.00

def author_indices(names):
	return dict((name, index) for (index, name) in enumerate(sorted(names)))

def author_color(index):
	return "var(--a{0})".format(index % AUTHOR_COLORS)

def percentage(part, whole):
	return 0.0 if not whole else 100.0 * part / whole

def attribute(value):
	"""escape() leaves the quote alone, which is fine in an element but not in an attribute."""
	return escape(value, {"\"": "&quot;"})

def html_avatar(name, index, url=None):
	content = "<img src=\"{0}\" alt=\"\" />".format(attribute(url)) if url else escape(name.strip()[0:1]) or "?"
	return "<span class=\"gi-avatar\" style=\"--gi-c:{0}\">{1}</span>".format(author_color(index), content)

def html_author_cell(name, index, url=None):
	return ("<td class=\"gi-author\"><div>{0}<span>{1}</span></div></td>".format(
	        html_avatar(name, index, url), escape(name)))

def html_header_cell(label, numeric=False):
	return "<th data-gi-sort=\"true\"{0}>{1} <span class=\"gi-arrow\"></span></th>".format(
	       " class=\"gi-num\"" if numeric else "", escape(label))

def html_number_cell(label, value):
	return "<td class=\"gi-num\" data-label=\"{0}\" data-gi-value=\"{1}\">{1}</td>".format(attribute(label), value)

def html_meter_cell(label, part, color=None):
	return ("<td data-label=\"{0}\" data-gi-value=\"{1:.2f}\"><div class=\"gi-meter\"><div class=\"gi-track\" "
	        "style=\"--gi-c:{2}\"><div style=\"width:{1:.2f}%\"></div></div><span>{1:.2f}</span></div></td>".format(
	        attribute(label), part, color if color else "var(--accent)"))

def html_diverging_header(left_label, right_label):
	return ("<th class=\"gi-diverge\"><div>"
	        "<span class=\"gi-del-num\" data-gi-sort=\"del\">{0} <span class=\"gi-arrow\"></span></span>"
	        "<span class=\"gi-spacer\"></span>"
	        "<span class=\"gi-ins-num\" data-gi-sort=\"ins\">{1} <span class=\"gi-arrow\"></span></span>"
	        "</div></th>".format(escape(left_label), escape(right_label)))

def html_diverging_cell(deletions, insertions, widest):
	return ("<td class=\"gi-diverge\" data-gi-del=\"{0}\" data-gi-ins=\"{1}\"><div>"
	        "<span class=\"gi-del-num\">−{0}</span>"
	        "<div class=\"gi-bars\"><div class=\"gi-left\"><div style=\"width:{2:.2f}%\"></div></div>"
	        "<div class=\"gi-mid\"></div>"
	        "<div class=\"gi-right\"><div style=\"width:{3:.2f}%\"></div></div></div>"
	        "<span class=\"gi-ins-num\">+{1}</span>"
	        "</div></td>".format(deletions, insertions, percentage(deletions, widest), percentage(insertions, widest)))

def html_stats(entries):
	stats = "".join("<div class=\"gi-stat\"><div class=\"gi-stat-label\">{0}</div>"
	                "<div class=\"gi-stat-num\">{1}</div></div>".format(escape(label), value)
	                for (label, value) in entries)
	return "<section class=\"gi-stats\">" + stats + "</section>"

def html_card(title, body, subtitle=None, pad=False):
	return ("<section class=\"gi-card{0}\"><div class=\"gi-card-head\"><h2>{1}</h2>{2}</div>{3}</section>".format(
	        " gi-pad" if pad else "", escape(title),
	        "<div class=\"gi-sub\">" + escape(subtitle) + "</div>" if subtitle else "", body))

def html_file_row(path, value, part, widest, color=None):
	return ("<div class=\"gi-file\" data-gi-searchable=\"files\" style=\"--gi-c:{0}\">"
	        "<div class=\"gi-path\">{1}</div><div class=\"gi-value\">{2}</div>"
	        "<div class=\"gi-rail\"><div style=\"width:{3:.0f}%\"></div></div></div>".format(
	        color if color else "var(--a4)", escape(path), escape("{0}".format(value)), percentage(part, widest)))

def html_files(rows):
	return "<div class=\"gi-files\">" + "".join(rows) + "</div>"

def html_cards(cards):
	return "<section class=\"gi-cards\">" + "".join(cards) + "</section>"

def html_table(identifier, body):
	return "<div class=\"gi-scroll\"><table id=\"{0}\" class=\"gi-table\">{1}</table></div>".format(identifier, body)

def html_share(entries, minor_text):
	"""Turn (label, percentage, colour) triples into the coloured bar and the legend below it."""
	minor = sum(entry[1] for entry in entries if entry[1] < MINOR_AUTHOR_PERCENTAGE)
	shown = [entry for entry in entries if entry[1] >= MINOR_AUTHOR_PERCENTAGE]

	if minor:
		shown.append((minor_text, minor, "var(--muted)"))

	bar = "".join("<div style=\"width:{0:.2f}%;background:{1}\" title=\"{2}\"></div>".format(
	              part, color, attribute(label)) for (label, part, color) in shown)
	legend = "".join("<div><span class=\"gi-key\" style=\"background:{0}\"></span>{1} {2:.2f}%</div>".format(
	                 color, escape(label), part) for (label, part, color) in shown)

	return ("<div class=\"gi-share\"><div class=\"gi-share-bar\">" + bar + "</div>"
	        "<div class=\"gi-legend\">" + legend + "</div></div>")

def output(outputable):
	if format.get_selected() == "html" or format.get_selected() == "htmlembedded":
		outputable.output_html()
	elif format.get_selected() == "json":
		outputable.output_json()
	elif format.get_selected() == "text":
		outputable.output_text()
	else:
		outputable.output_xml()
