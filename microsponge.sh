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

# Runs the microsponge command from the project folder, which starts the game:
#     ./microsponge.sh

set -e

# The program has to run from the top folder of the project.
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo '.venv is missing, so please set it up first:'
    echo '    python3 -m venv .venv'
    echo '    .venv/bin/python -m pip install -e .'
    exit 1
fi

if ! .venv/bin/python -c 'import microsponge' 2>/dev/null; then
    echo 'microsponge is not installed in .venv, so please install it first:'
    echo '    .venv/bin/python -m pip install -e .'
    exit 1
fi

exec .venv/bin/python -m microsponge "$@"
