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

"""Print a world the map generator makes for a theme, as a plain grid of letters with a legend, to talk about the generator.

Run from the top folder, naming a theme, and optionally a seed and how many civilizations start:

    .venv/bin/python tools/map_preview.py caveman
    .venv/bin/python tools/map_preview.py caveman 7 3

The same seed always makes the same world (`src/microsponge/support/map_preview.py`).
"""

import sys

from microsponge.support.map_preview import CIVILIZATIONS, preview_lines, previewed_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED, number_at, theme_called, theme_names
from microsponge.ui_strings import MSG_MAP_USAGE

DEFAULT_SEED = 1
# Where each argument is on the command line.
THEME_ARGUMENT = 0
SEED_ARGUMENT = 1
CIVILIZATIONS_ARGUMENT = 2


def main(arguments):
    theme = theme_called(arguments[THEME_ARGUMENT]) if arguments else None
    seed = number_at(arguments=arguments, place=SEED_ARGUMENT, default=DEFAULT_SEED)
    civilizations = number_at(arguments=arguments, place=CIVILIZATIONS_ARGUMENT, default=CIVILIZATIONS)
    if theme is None or seed is None or not civilizations or len(arguments) > CIVILIZATIONS_ARGUMENT + 1:
        print(MSG_MAP_USAGE.format(themes=theme_names()))
        return FAILED
    try:
        game, world = previewed_game(theme=theme, seed=seed, civilizations=civilizations)
    except ValueError as problem:
        print(problem)
        return FAILED
    for line in preview_lines(game=game, world_id=world, seed=seed):
        print(line)
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
