.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@poetry run python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr .pytest_cache

lint: ## check style with flake8 and pylint
	# stop the build if there are Python syntax errors or undefined names
	poetry run flake8 gitinspector tests --count --select=E9,F63,F7,F82 --show-source --statistics --builtins="_"
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	poetry run flake8 gitinspector tests --count --ignore=E203,E722,W503,E401,C901 --exit-zero --max-complexity=10 --max-line-length=127 --statistics --builtins="_"
	poetry run pylint --rcfile=.pylintrc gitinspector

test: ## run tests quickly with the default Python
	poetry run pytest

test-coverage: ## check code coverage quickly with the default Python
	poetry run coverage run --source gitinspector -m pytest
	poetry run coverage report -m

release: dist ## package and upload a release
	poetry publish

tag-version:
	@export VERSION_TAG=`poetry run python3 -c "from gitinspector.version import __version__; print(__version__)"` \
	&& git tag v$$VERSION_TAG

untag-version:
	@export VERSION_TAG=`poetry run python3 -c "from gitinspector.version import __version__; print(__version__)"` \
	&& git tag -d v$$VERSION_TAG

push-tagged-version: tag-version
	@export VERSION_TAG=`poetry run python3 -c "from gitinspector.version import __version__; print(__version__)"` \
	&& git push origin v$$VERSION_TAG

dist: clean ## builds source and wheel package
	poetry build
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	poetry install

format: ## format code with black and isort
	poetry run black gitinspector tests
	poetry run isort gitinspector tests

type-check: ## run type checking with mypy
	poetry run mypy gitinspector

dev-install: ## install development dependencies
	poetry install --with dev

update-deps: ## update dependencies
	poetry update