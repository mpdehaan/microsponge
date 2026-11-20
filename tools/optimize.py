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

"""Search for better numbers for a theme, judged by games the computer players play, and print a report of suggestions. The theme is never changed.

Run from the top folder, naming a theme, and optionally how many minutes to search, how many
seeds to search with, how many seeds to hold out, how many civilizations play and how many
turns a game may run:

    .venv/bin/python tools/optimize.py caveman
    .venv/bin/python tools/optimize.py caveman 60 6 3 3 200
    .venv/bin/python tools/optimize.py caveman 60 6 3 3 200 12345

With no search seed, the tool picks one at random, so each run tries different numbers; the
report names the seed, and giving it again repeats the run on an unchanged theme.

The report is printed and written to logs/<theme>_optimizer.md. `DEV_TOOLS.md` says how to read it.
"""

import os
import sys
from pathlib import Path
from random import SystemRandom

from microsponge.engine.kinds.kind import shown_name
from microsponge.support.optimizer.report import report_lines, shown_decimal
from microsponge.support.optimizer.run import optimize
from microsponge.support.theme_tools import FAILED, SUCCEEDED, number_at, theme_called, theme_names
from microsponge.ui_strings import MSG_LOG_WRITTEN, MSG_OPTIMIZER_BEST_MARK, MSG_OPTIMIZER_STEP, MSG_OPTIMIZER_USAGE

THEME_ARGUMENT = 0
MINUTES_ARGUMENT = 1
SEARCHED_ARGUMENT = 2
HELD_OUT_ARGUMENT = 3
CIVILIZATIONS_ARGUMENT = 4
TURNS_ARGUMENT = 5
SEED_ARGUMENT = 6
DEFAULT_MINUTES = 10
DEFAULT_SEARCHED = 6
DEFAULT_HELD_OUT = 3
DEFAULT_CIVILIZATIONS = 3
DEFAULT_TURNS = 200
SECONDS_A_MINUTE = 60
# The search seeds picked at random are below this.
MOST_SEEDS = 1000000
LEAST_PROCESSES = 1
REPORT_FOLDER = Path('logs')
REPORT_NAME = '{theme}_optimizer.md'
NO_MARK = ''
LINE_END = '\n'


def show_step(step):
    print(MSG_OPTIMIZER_STEP.format(number=step.number, score=shown_decimal(step.score), mark=MSG_OPTIMIZER_BEST_MARK if step.best else NO_MARK), flush=True)


def main(arguments):
    theme = theme_called(arguments[THEME_ARGUMENT]) if arguments else None
    numbers = [number_at(arguments=arguments, place=place, default=default) for place, default in (
        (MINUTES_ARGUMENT, DEFAULT_MINUTES), (SEARCHED_ARGUMENT, DEFAULT_SEARCHED), (HELD_OUT_ARGUMENT, DEFAULT_HELD_OUT),
        (CIVILIZATIONS_ARGUMENT, DEFAULT_CIVILIZATIONS), (TURNS_ARGUMENT, DEFAULT_TURNS))]
    random_seed = number_at(arguments=arguments, place=SEED_ARGUMENT, default=SystemRandom().randrange(MOST_SEEDS))
    if theme is None or not all(numbers) or random_seed is None or len(arguments) > SEED_ARGUMENT + 1:
        print(MSG_OPTIMIZER_USAGE.format(themes=theme_names()))
        return FAILED
    minutes, searched, held_out, civilizations, turns = numbers
    processes = max(min(os.cpu_count() or LEAST_PROCESSES, searched), LEAST_PROCESSES)
    try:
        found = optimize(theme=theme, seconds=minutes * SECONDS_A_MINUTE, searched=searched, held_out=held_out, civilizations=civilizations, turns=turns, processes=processes, random_seed=random_seed, on_step=show_step)
    except ValueError as problem:
        print(problem)
        return FAILED
    lines = report_lines(theme=theme, found=found)
    for line in lines:
        print(line)
    path = REPORT_FOLDER / REPORT_NAME.format(theme=shown_name(theme))
    path.parent.mkdir(exist_ok=True)
    path.write_text(LINE_END.join(report_lines(theme=theme, found=found, markdown=True)) + LINE_END)
    print(MSG_LOG_WRITTEN.format(path=path))
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
