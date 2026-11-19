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

"""Analyze the log of a game: print the timeline of each civilization and the tables of the report, or write the page with the charts.

Run from the top folder, naming a log file that `tools/game_log.py` wrote:

    .venv/bin/python tools/game_report.py logs/caveman_seed1.json             # the report, as text
    .venv/bin/python tools/game_report.py logs/caveman_seed1.json --markdown  # with Markdown tables
    .venv/bin/python tools/game_report.py logs/caveman_seed1.json --html      # write logs/caveman_seed1.html
    .venv/bin/python tools/game_report.py logs/caveman_seed1.json --open      # write the page and open it in the browser

The report is `src/microsponge/support/game_log_report.py` and the page is `game_log_page.py`
beside it. `DEV_TOOLS.md` says more.
"""

import sys
from pathlib import Path

from microsponge.support.game_log import read_log
from microsponge.support.game_log_page import open_page, page_path, write_page
from microsponge.support.game_log_report import report_lines
from microsponge.support.theme_tools import FAILED, MARKDOWN_FLAG, SUCCEEDED
from microsponge.ui_strings import MSG_LOG_REPORT_USAGE, MSG_LOG_WRITTEN

HTML_FLAG = '--html'
OPEN_FLAG = '--open'
FLAGS = (MARKDOWN_FLAG, HTML_FLAG, OPEN_FLAG)
ONE_FILE = 1


def main(arguments):
    files = [argument for argument in arguments if argument not in FLAGS]
    if len(files) != ONE_FILE or not Path(files[0]).is_file():
        print(MSG_LOG_REPORT_USAGE)
        return FAILED
    path = Path(files[0])
    data = read_log(path)
    if HTML_FLAG in arguments or OPEN_FLAG in arguments:
        page = page_path(path)
        write_page(data=data, path=page)
        print(MSG_LOG_WRITTEN.format(path=page))
        if OPEN_FLAG in arguments:
            open_page(page)
        return SUCCEEDED
    for line in report_lines(data=data, markdown=MARKDOWN_FLAG in arguments):
        print(line)
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
