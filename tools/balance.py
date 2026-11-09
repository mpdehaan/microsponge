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

"""Show how the units of a theme stand against each other in a fight, to help balance the theme.

Run from the top folder, naming a theme, with --markdown for the guide of the theme:

    .venv/bin/python tools/balance.py caveman

What the report holds is explained in `src/microsponge/support/balance_report.py`.
"""

import sys

from microsponge.support.balance_report import report
from microsponge.support.theme_tools import run_theme_tool

if __name__ == '__main__':
    sys.exit(run_theme_tool(arguments=sys.argv[1:], report=report))
