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

"""Refresh the generated appendix of every theme's guide, GUIDE_<THEME>.md, from the code.

Run from the top folder:

    .venv/bin/python tools/theme_guides.py            # rewrite every appendix that is out of date
    .venv/bin/python tools/theme_guides.py --check    # say which are out of date, and fail if any is

The words of a guide are written by hand and never touched; only the tables between the two
marker comments change (`src/microsponge/support/guides.py`).
"""

import sys
from pathlib import Path

from microsponge.support.guides import guide_path, is_current, refresh
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes import THEMES
from microsponge.ui_strings import MSG_GUIDE_CURRENT, MSG_GUIDE_MISSING, MSG_GUIDE_REFRESHED, MSG_GUIDE_STALE

ROOT = Path(__file__).resolve().parents[1]
CHECK_FLAG = '--check'


def main(arguments):
    check = CHECK_FLAG in arguments
    failed = False
    for theme in THEMES:
        path = guide_path(root=ROOT, theme=theme)
        if not path.exists():
            print(MSG_GUIDE_MISSING.format(path=path.name))
            failed = True
        elif check:
            current = is_current(path=path, theme=theme)
            print((MSG_GUIDE_CURRENT if current else MSG_GUIDE_STALE).format(path=path.name))
            failed = failed or not current
        else:
            print((MSG_GUIDE_REFRESHED if refresh(path=path, theme=theme) else MSG_GUIDE_CURRENT).format(path=path.name))
    return FAILED if failed else SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
