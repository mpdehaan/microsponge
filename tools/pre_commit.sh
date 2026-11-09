#!/bin/sh
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
#
# The git pre-commit hook: no commit goes in unless the whole test suite passes, as the user
# requires, so that a broken import or a missing constant can never reach a commit.
# `make hooks` installs it by linking .git/hooks/pre-commit to this file, and git runs it before
# every commit. .claude/TESTING.md says that it stays installed and is never bypassed.

set -e
# Git runs the hook through its link in .git/hooks, so the repository is asked for its top folder.
cd "$(git rev-parse --show-toplevel)"
echo 'pre-commit: running every test first'
./run_tests.sh
