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

"""Have the computer players of a theme play a whole game against each other, and print the report of the game: a story, tables and charts.

Run from the top folder, naming a theme, and optionally a seed, how many civilizations play and
how many turns the game may run:

    .venv/bin/python tools/scripted_game.py caveman
    .venv/bin/python tools/scripted_game.py caveman 7 3 300

The same seed always plays the same game (`src/microsponge/support/scripted_game.py`).
"""

import sys

from microsponge.support.game_story import report_lines
from microsponge.support.map_preview import CIVILIZATIONS
from microsponge.support.scripted_game import TURNS, play, started_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED, number_at, theme_called, theme_names
from microsponge.ui_strings import MSG_GAME_USAGE

DEFAULT_SEED = 1
# Where each argument is on the command line.
THEME_ARGUMENT = 0
SEED_ARGUMENT = 1
CIVILIZATIONS_ARGUMENT = 2
TURNS_ARGUMENT = 3


def main(arguments):
    theme = theme_called(arguments[THEME_ARGUMENT]) if arguments else None
    seed = number_at(arguments=arguments, place=SEED_ARGUMENT, default=DEFAULT_SEED)
    civilizations = number_at(arguments=arguments, place=CIVILIZATIONS_ARGUMENT, default=CIVILIZATIONS)
    turns = number_at(arguments=arguments, place=TURNS_ARGUMENT, default=TURNS)
    if theme is None or seed is None or not civilizations or not turns or len(arguments) > TURNS_ARGUMENT + 1:
        print(MSG_GAME_USAGE.format(themes=theme_names()))
        return FAILED
    try:
        game = started_game(theme=theme, seed=seed, civilizations=civilizations)
    except ValueError as problem:
        print(problem)
        return FAILED
    for line in report_lines(game=game, chronicle=play(game=game, turns=turns), seed=seed):
        print(line)
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
