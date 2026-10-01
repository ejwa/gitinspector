#!/usr/bin/env bash
#
# Cuts a release: sets the version in every file that carries it, runs the tests, records the release
# in a commit and a tag, and opens the next development version.
#
# Run ./create-release.sh --help for what it takes.
#
# Nothing is pushed. The commits and the tag stay local until they are sent.

set -euo pipefail

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION_PY="gitinspector/version.py"
readonly MAN_PAGE="docs/gitinspector.txt"
readonly PACKAGE_JSON="package.json"
readonly TRANSLATIONS="gitinspector/translations"

python="${PYTHON:-python3}"

die() { printf '%s\n' "$*" >&2; exit 1; }
step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

usage() {
	cat <<'USAGE'
Cuts a release: sets the version, runs the tests, records the release in a
commit and a tag, and opens the next development version. Nothing is pushed.

  ./create-release.sh [options]

The version released is the one gitinspector/version.py is already working
towards, with the dev suffix dropped: 0.5.2dev releases 0.5.2. It is shown and
confirmed before anything changes. What is opened afterwards is up to --bump.

  --bump=revrevision  raise the third number, and the default: 0.5.2 opens
                      0.5.3dev.
  --bump=revision     raise the second, zeroing the third: 0.5.2 opens 0.6.0dev.
  --bump=version      raise the first, zeroing the rest: 0.5.2 opens 1.0.0dev.

  --skip-tests        do not run the tests. Nothing is verified: for a release
                      you have already tested.
  --help, -h          this.

Needs a clean working tree and msgfmt from the gettext tools. PYTHON picks the
interpreter that runs the tests.
USAGE
}

tests="run"
bump="revrevision"
for argument in "$@"; do
	case "$argument" in
		--help|-h) usage; exit 0 ;;
		--skip-tests) tests="skip" ;;
		--bump=version|--bump=revision|--bump=revrevision) bump="${argument#--bump=}" ;;
		--bump=*) die "Bump one of version, revision or revrevision, not '${argument#--bump=}'." ;;
		*) usage >&2; die "
Takes no version: $VERSION_PY already says which one comes next.
Unexpected argument '$argument'." ;;
	esac
done

is_dev_version() { [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+dev$ ]]; }

current_version() { sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$VERSION_PY"; }

# The next development version: the named level one higher, everything under it back to zero, so a
# release opens a version rather than an odd corner of one.
bumped() {
	local major="${1%%.*}" rest="${1#*.}"
	local minor="${rest%%.*}" patch="${rest#*.}"
	case "$2" in
		version) printf '%s.0.0' "$(( major + 1 ))" ;;
		revision) printf '%s.%s.0' "$major" "$(( minor + 1 ))" ;;
		*) printf '%s.%s.%s' "$major" "$minor" "$(( patch + 1 ))" ;;
	esac
}

expect() { grep -qF -- "$2" "$1" || die "$1 did not take the version."; }

# BSD sed insists on a backup suffix after -i and GNU sed accepts one, so one is always given.
rewrite() {
	sed -i.orig "$2" "$1"
	rm -f "$1.orig"
}

# Rewrites the version in every file that carries it, then reads each one back, so a pattern that
# matched nothing is caught rather than committed. The compiled catalogs follow their sources.
set_version() {
	local version="$1" package="$2" catalog

	rewrite "$VERSION_PY" "s/^__version__ = \".*\"/__version__ = \"$version\"/"
	expect "$VERSION_PY" "__version__ = \"$version\""

	rewrite "$MAN_PAGE" "s/^:man version: .*/:man version: $version/"
	expect "$MAN_PAGE" ":man version: $version"

	rewrite "$PACKAGE_JSON" "s/^\(  \"version\": \"\)[^\"]*/\1$package/"
	expect "$PACKAGE_JSON" "\"version\": \"$package\""

	for catalog in "$TRANSLATIONS"/messages.pot "$TRANSLATIONS"/messages_*.po; do
		rewrite "$catalog" 's/\(Project-Id-Version: gitinspector \)[^\]*/\1'"$version"'/'
		expect "$catalog" "Project-Id-Version: gitinspector $version"'\n"'
	done

	for catalog in "$TRANSLATIONS"/messages_*.po; do
		msgfmt -o "${catalog%.po}.mo" "$catalog"
	done
}

cd "$ROOT"

git rev-parse --git-dir >/dev/null 2>&1 || die "Not a git repository."
command -v msgfmt >/dev/null 2>&1 || die "msgfmt is needed to compile the translations; install the gettext tools."

dirty="$(git status --porcelain)"
[ -z "$dirty" ] || die "Working tree is not clean; commit or stash first:
$dirty"

current="$(current_version)"
is_dev_version "$current" \
	|| die "$VERSION_PY reads '$current', which is not a development version.
Set it to a major.minor.patchdev version first, such as 0.5.2dev."
version="${current%dev}"
next="$(bumped "$version" "$bump")dev"
next_package="${next%dev}-dev-1"

tag="v$version"
git rev-parse -q --verify "refs/tags/$tag" >/dev/null \
	&& die "Tag $tag already exists; that release has been cut."

printf 'Release %s, then open %s?' "$version" "$next"
if [ -t 0 ]; then
	printf ' [Y/n] '
	read -r answer
	case "$answer" in
		""|y|Y|yes) ;;
		*) die "Nothing released." ;;
	esac
else
	printf '\n'
fi

# Whatever fails from here on, the tree, the branch and the tags end up as they were found. The tree
# was clean and on $start when this began, so a hard reset is safe, and the tag is only deleted when
# this run made it. The trap comes after the checks above so that a refusal never touches what
# somebody else was editing.
start="$(git rev-parse HEAD)"
tagged="no"
finished="no"
roll_back() {
	[ "$finished" = yes ] && return
	git reset -q --hard "$start"
	if [ "$tagged" = yes ]; then git tag -d "$tag" >/dev/null; fi
	printf '\nThe release failed; everything it did has been taken back.\n' >&2
}
trap roll_back EXIT

step "Setting the version to $version"
set_version "$version" "$version"

case "$tests" in
	run)
		step "Running the tests"
		LC_ALL=C.UTF-8 LANGUAGE=C PYTHONIOENCODING=utf-8 "$python" -m unittest discover
		;;
	skip)
		step "Skipping the tests; nothing is verified"
		;;
esac

step "Recording the release"
git add -u
git commit -q -m "Bump the version number to $version"
git tag "$tag"
tagged="yes"

step "Opening the next development version"
set_version "$next" "$next_package"
git add -u
git commit -q -m "Bump the version number to $next"
finished="yes"

printf '\n\033[1mReleased %s\033[0m\n' "$version"
printf '  tag    %s\n' "$tag"
printf '  next   %s\n' "$next"
printf '\nNothing was pushed. When you are ready:\n'
printf '  git push && git push origin %s\n' "$tag"
