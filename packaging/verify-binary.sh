#!/bin/sh
#
# Analyzes a repository with a built gitinspector executable and checks what came out of it. A
# bundle that lost its data files still starts and still prints a version, so it is the reports
# that prove the html templates, the logo and the compiled catalogs came along with the
# interpreter. The repository is given as a clone url by default, which puts the cloning of a
# remote repository through the same run.
#
# Usage: packaging/verify-binary.sh <executable> [repository or clone url]

set -e

binary=$1
repository=${2:-https://github.com/psf/requests.git}
reports=${TMPDIR:-/tmp}/gitinspector-verify-$$
options="--timeline --metrics --responsibilities --list-file-types"

mkdir -p "$reports"

analyze() {
	echo "--- $1"
	LANGUAGE=C "$binary" --format="$1" $options "$repository" > "$reports/report.$1"
}

expect() {
	grep -q "$2" "$reports/report.$1" || { echo "the $1 report carries no $2" >&2; exit 1; }
}

refuse() {
	if grep -q "$2" "$reports/report.$1"; then
		echo "the $1 report carries $2" >&2
		exit 1
	fi
}

LANGUAGE=C "$binary" --version | grep -q "^gitinspector "
LANGUAGE=sv "$binary" --version | grep -q "Skrivet av"
LANGUAGE=C "$binary" --help | grep -q -- "--responsibilities"

analyze text
expect text "% of changes"

analyze html
expect html "gi-page"
expect html "border-radius"
expect html "gitinspector.theme"
expect html "fonts.googleapis"

analyze htmlembedded
expect htmlembedded "data:image/png;base64,"
refuse htmlembedded "fonts.googleapis"

analyze json
expect json "\"responsibilities\""

analyze xml
expect xml "</gitinspector>"

# The stricter parse only runs where an interpreter happens to be installed. The executables are
# tested where none is as well, that being the whole point of them.
if command -v python3 > /dev/null 2>&1; then
	python3 -c "import io, json, sys; json.load(io.open(sys.argv[1], encoding='utf-8'))" "$reports/report.json"
fi

if LANGUAGE=C "$binary" --nonsense "$repository" > /dev/null 2>&1; then
	echo "an unknown option was accepted" >&2
	exit 1
fi

rm -rf "$reports"
echo "$binary reported on $repository in every format"
