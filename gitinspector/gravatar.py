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

import format
import hashlib
import urllib

def get_url(email):
	md5hash = hashlib.md5(email.lower().strip()).hexdigest()
	base_url = "http://www.gravatar.com/avatar/" + md5hash
	params = None

	if format.get_selected() == "html":
		params = {"default": "identicon", "size": 20}
	elif format.get_selected() == "xml":
		params = {"default": "identicon"}

	return base_url + "?" + urllib.urlencode(params)
