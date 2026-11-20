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

"""Print the effectiveness report of a theme: what does nothing or too little, from the theme and from the logs of games the computer players played.

Run from the top folder, naming a theme, and optionally the logs to read; with none, every log
of the theme in logs/ is read. Write logs first with make game-log:

    .venv/bin/python tools/effectiveness_report.py caveman
    .venv/bin/python tools/effectiveness_report.py caveman logs/caveman_seed1.json --markdown

`DEV_TOOLS.md` says how to read it.
"""

import sys
from pathlib import Path

from microsponge.engine.kinds.kind import shown_name
from microsponge.support.effectiveness import report_lines
from microsponge.support.game_log import read_log
from microsponge.support.theme_tools import FAILED, MARKDOWN_FLAG, SUCCEEDED, theme_called, theme_names
from microsponge.ui_strings import MSG_EFFECTIVENESS_NO_LOGS, MSG_EFFECTIVENESS_USAGE

LOG_FOLDER = Path('logs')
LOG_PATTERN = '{theme}_seed*.json'


def log_paths(*, theme, named):
    """Return the logs named, or every log of the theme in logs/ when none is named."""
    return [Path(name) for name in named] if named else sorted(LOG_FOLDER.glob(LOG_PATTERN.format(theme=shown_name(theme))))


def main(arguments):
    markdown = MARKDOWN_FLAG in arguments
    names = [argument for argument in arguments if argument != MARKDOWN_FLAG]
    theme = theme_called(names[0]) if names else None
    if theme is None:
        print(MSG_EFFECTIVENESS_USAGE.format(themes=theme_names()))
        return FAILED
    paths = log_paths(theme=theme, named=names[1:])
    if not paths:
        print(MSG_EFFECTIVENESS_NO_LOGS.format(theme=shown_name(theme)))
        return FAILED
    try:
        logs = [read_log(path) for path in paths]
    except (OSError, ValueError) as problem:
        print(problem)
        return FAILED
    for line in report_lines(theme=theme, logs=logs, markdown=markdown):
        print(line)
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
