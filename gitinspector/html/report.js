/*
 * The behaviour of the HTML reports: the theme and light/dark switches, sortable tables, the search
 * box and the collapsible responsibilities. Inlined into the report as it is, so it is never run
 * through str.format. Written without a framework and without any network access, so that a report
 * saved to disk keeps working.
 */
(function () {
	"use strict";

	var STORE_THEME = "gitinspector.theme";
	var STORE_MODE = "gitinspector.mode";

	function remember(key, value) {
		try { window.localStorage.setItem(key, value); } catch (e) { /* private mode, never mind */ }
	}

	function recall(key) {
		try { return window.localStorage.getItem(key); } catch (e) { return null; }
	}

	function preferredMode() {
		var stored = recall(STORE_MODE);

		if (stored) {
			return stored;
		}
		return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
	}

	function apply(theme, mode) {
		var root = document.documentElement;
		root.setAttribute("data-theme", theme);
		root.setAttribute("data-mode", mode);

		each(document.querySelectorAll("[data-gi-theme]"), function (button) {
			button.setAttribute("aria-pressed", button.getAttribute("data-gi-theme") === theme ? "true" : "false");
		});

		var label = document.querySelector("[data-gi-mode-label]");

		if (label) {
			label.textContent = label.getAttribute(mode === "dark" ? "data-gi-light-text" : "data-gi-dark-text");
		}
	}

	function each(list, callback) {
		for (var i = 0; i < list.length; i++) {
			callback(list[i], i);
		}
	}

	/* Sorting ------------------------------------------------------------------------------- */

	function ancestor(element, tag) {
		while (element && element.tagName !== tag) {
			element = element.parentNode;
		}
		return element;
	}

	function cellValue(row, index, key) {
		var cell = row.children[index];

		if (!cell) {
			return "";
		}

		var value = cell.getAttribute(key ? "data-gi-" + key : "data-gi-value");
		return value === null ? cell.textContent.trim() : value;
	}

	function comparator(index, key, descending) {
		return function (first, second) {
			var a = cellValue(first, index, key);
			var b = cellValue(second, index, key);
			var na = parseFloat(a);
			var nb = parseFloat(b);
			var result;

			if (!isNaN(na) && !isNaN(nb)) {
				result = na - nb;
			} else {
				result = String(a).toLowerCase().localeCompare(String(b).toLowerCase());
			}
			return descending ? -result : result;
		};
	}

	/* The handle is the clickable element, which is the header cell itself except in the diverging
	   column, where deletions and insertions share one header and sort on a key of their own. */
	function sortTable(table, handle) {
		var cell = ancestor(handle, "TH");
		var index = 0;

		each(table.querySelectorAll("thead th"), function (candidate, position) {
			if (candidate === cell) {
				index = position;
			}
		});

		var key = handle.getAttribute("data-gi-sort");
		var descending = handle.getAttribute("data-gi-order") !== "descending";
		var body = table.tBodies[0];
		var rows = [];

		each(body.rows, function (row) { rows.push(row); });
		rows.sort(comparator(index, key === "true" ? null : key, descending));

		each(table.querySelectorAll("[data-gi-sort]"), function (candidate) {
			candidate.removeAttribute("data-gi-order");
			var arrow = candidate.querySelector(".gi-arrow");

			if (arrow) {
				arrow.textContent = "";
			}
		});

		handle.setAttribute("data-gi-order", descending ? "descending" : "ascending");
		var arrow = handle.querySelector(".gi-arrow");

		if (arrow) {
			arrow.textContent = descending ? "↓" : "↑";
		}

		each(rows, function (row) { body.appendChild(row); });
	}

	/* Searching ----------------------------------------------------------------------------- */

	function filter() {
		var box = document.querySelector("[data-gi-query]");

		if (!box) {
			return;
		}

		var scopeBox = document.querySelector("[data-gi-scope]");
		var scope = scopeBox ? scopeBox.value : "authors";
		var needle = box.value.trim().toLowerCase();

		each(document.querySelectorAll("[data-gi-searchable]"), function (element) {
			var kind = element.getAttribute("data-gi-searchable");
			var matches = !needle || (kind === scope && element.textContent.toLowerCase().indexOf(needle) !== -1);

			if (!needle || kind !== scope) {
				element.classList.remove("gi-hidden");
			} else {
				element.classList.toggle("gi-hidden", !matches);
			}
		});
	}

	/* Wiring -------------------------------------------------------------------------------- */

	function ready() {
		apply(recall(STORE_THEME) || "default", preferredMode());

		each(document.querySelectorAll("[data-gi-theme]"), function (button) {
			button.addEventListener("click", function () {
				var theme = button.getAttribute("data-gi-theme");
				remember(STORE_THEME, theme);
				apply(theme, document.documentElement.getAttribute("data-mode"));
			});
		});

		var toggle = document.querySelector("[data-gi-mode-toggle]");

		if (toggle) {
			toggle.addEventListener("click", function () {
				var mode = document.documentElement.getAttribute("data-mode") === "dark" ? "light" : "dark";
				remember(STORE_MODE, mode);
				apply(document.documentElement.getAttribute("data-theme"), mode);
			});
		}

		each(document.querySelectorAll("table.gi-table [data-gi-sort]"), function (handle) {
			handle.addEventListener("click", function () {
				sortTable(ancestor(handle, "TABLE"), handle);
			});
		});

		each(document.querySelectorAll("[data-gi-query], [data-gi-scope]"), function (element) {
			element.addEventListener("input", filter);
			element.addEventListener("change", filter);
		});

		each(document.querySelectorAll("[data-gi-toggle]"), function (button) {
			button.addEventListener("click", function () {
				var panel = document.getElementById(button.getAttribute("data-gi-toggle"));
				var chevron = button.querySelector(".gi-chev");

				if (!panel) {
					return;
				}

				var hidden = panel.classList.toggle("gi-hidden");

				button.setAttribute("aria-expanded", hidden ? "false" : "true");

				if (chevron) {
					chevron.textContent = hidden ? "▸" : "▾";
				}
			});
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", ready);
	} else {
		ready();
	}
})();
