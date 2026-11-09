# microsponge: a strategy game
# Copyright (C) 2026  Michael DeHaan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# The everyday things, so that nobody has to remember how each one is launched.
# `make` on its own lists them. Everything runs from the virtual environment in .venv,
# which `make setup` creates.

PYTHON = .venv/bin/python
NAME ?=

.PHONY: help setup run test test-one pyflakes pep8 loose-strings balance unit-report building-report wonder-report tech-report guides hooks clean

help:
	@echo "make setup          make .venv and install microsponge into it"
	@echo "make run            start the game"
	@echo "make test           run every test, in parallel: the unit tests, the rule tests and pyflakes"
	@echo "make test-one       the tests matching a name (make test-one NAME=test_version)"
	@echo "make pyflakes       unused imports, undefined names and names defined twice (the test suite runs this too)"
	@echo "make pep8           what pycodestyle says, less what setup.cfg ignores: a look, not a rule, see .claude/STYLE.md"
	@echo "make loose-strings  string literals inside functions under src/, which should be constants"
	@echo "make balance        how the units of a theme stand against each other: THEME=caveman, or classic, SciFi, fantasy or PlanetWars"
	@echo "make unit-report    every unit of a theme with its properties: THEME=caveman; add FORMAT=--markdown to any report for the guides"
	@echo "make building-report  every building of a theme with its properties: THEME=caveman"
	@echo "make wonder-report  every world wonder of a theme with its properties: THEME=caveman"
	@echo "make tech-report    the tech tree of a theme with its properties: THEME=caveman"
	@echo "make guides         refresh the generated appendix of every theme guide, GUIDE_<THEME>.md"
	@echo "make hooks          install the git pre-commit hook, which runs every test before a commit goes in"
	@echo "make clean          remove Python caches"

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -e .

run:
	$(PYTHON) -m microsponge

test:
	./run_tests.sh

test-one:
	./run_tests.sh $(NAME)

pyflakes:
	$(PYTHON) -m pyflakes src test tools

pep8:
	$(PYTHON) -m pycodestyle src test tools

loose-strings:
	$(PYTHON) tools/loose_strings.py src

balance:
	$(PYTHON) tools/balance.py $(THEME) $(FORMAT)

unit-report:
	$(PYTHON) tools/unit_report.py $(THEME) $(FORMAT)

building-report:
	$(PYTHON) tools/building_report.py $(THEME) $(FORMAT)

wonder-report:
	$(PYTHON) tools/wonder_report.py $(THEME) $(FORMAT)

tech-report:
	$(PYTHON) tools/tech_report.py $(THEME) $(FORMAT)

guides:
	$(PYTHON) tools/theme_guides.py

hooks:
	ln -sf ../../tools/pre_commit.sh .git/hooks/pre-commit

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
