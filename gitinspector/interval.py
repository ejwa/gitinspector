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

from __future__ import unicode_literals
from . import git, optval

try:
	from shlex import quote
except ImportError:
	from pipes import quote

REVISION_PREFIX = "rev:"

__since__ = ""

__until__ = ""

__ref__ = "HEAD"

__branch__ = "HEAD"

def clear():
	global __since__
	global __until__
	global __ref__
	global __branch__
	__since__ = ""
	__until__ = ""
	__ref__ = "HEAD"
	__branch__ = "HEAD"

def has_interval():
	return __since__ + __until__ != ""

def get_since():
	return __since__

def set_since(since):
	global __since__
	__since__ = since

def get_until():
	return __until__

def set_until(until):
	global __until__
	__until__ = until

def __revision_of__(bound):
	return bound[len(REVISION_PREFIX):] if bound.startswith(REVISION_PREFIX) else None

def __date_argument__(option, bound):
	return [option + "=" + quote(bound)] if bound and __revision_of__(bound) is None else []

#Leaving out the parents of the revision, rather than the revision itself, keeps it inside the interval.
def __since_arguments__():
	revision = __revision_of__(__since__)
	return __date_argument__("--since", __since__) if revision is None else ["^" + revision + "^@"]

def get_rev_list_arguments():
	until_revision = __revision_of__(__until__)
	return __since_arguments__() + __date_argument__("--until", __until__) + [until_revision or __branch__]

def get_blame_arguments():
	return __since_arguments__() + [__ref__]

def __time_of__(option, bound, repository):
	revision = __revision_of__(bound)

	if not bound:
		return None
	elif revision is None:
		return git.get_date_time(__date_argument__(option, bound)[0])

	#git would take a name starting with a dash for an option, and cannot create such a branch anyway.
	time = None if revision.startswith("-") else git.get_commit_time(revision)

	if time is None:
		raise optval.InvalidOptionArgument(_("revision {0} was not found in {1}.").format(revision, repository))

	return time

def __check_branch_exists__(repository):
	if __branch__.startswith("-") or git.get_commit_time(__branch__) is None:
		raise optval.InvalidOptionArgument(_("branch {0} was not found in {1}.").format(__branch__, repository))

def __check_bounds_on_branch__(repository):
	for bound in (__since__, __until__):
		revision = __revision_of__(bound)

		if revision is not None and not git.is_ancestor(revision, __branch__):
			raise optval.InvalidOptionArgument(
				_("revision {0} is not on branch {1} of {2}.").format(revision, __branch__, repository))

#A revision bound is only held to the branch when one was asked for, as it otherwise replaces HEAD as the tip.
def check(repository):
	has_branch = __branch__ != "HEAD"

	if has_branch:
		__check_branch_exists__(repository)

	since_time = __time_of__("--since", __since__, repository)
	until_time = __time_of__("--until", __until__, repository)

	if since_time is not None and until_time is not None and since_time > until_time:
		raise optval.InvalidOptionArgument(_("the --since bound lies after the --until bound."))

	if has_branch:
		__check_bounds_on_branch__(repository)

def get_branch():
	return __branch__

def set_branch(branch):
	global __branch__
	__branch__ = branch

def get_ref():
	return __ref__

def set_ref(ref):
	global __ref__
	__ref__ = ref
