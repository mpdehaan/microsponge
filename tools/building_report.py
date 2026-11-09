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

"""Show every building of a theme with its properties, to help balance the theme.

Run from the top folder, naming a theme:

    .venv/bin/python tools/building_report.py caveman

The report is a table, one row for each kind and one column for each property, and a column
that no kind of the theme sets is left out and named below the table (`support/kind_reports.py`).
"""

import sys

from microsponge.support.kind_reports import buildings_report
from microsponge.support.theme_tools import run_theme_tool

if __name__ == '__main__':
    sys.exit(run_theme_tool(arguments=sys.argv[1:], report=buildings_report))
