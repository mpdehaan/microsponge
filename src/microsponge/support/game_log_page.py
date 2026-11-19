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

"""The page of a game's log: one HTML file with a chart of everything the log counted turn by turn, the timeline of each civilization and the tables of the report.

The page is the file `game_log_page.html` beside this module with the data of one game put
in. The charts are drawn in the browser by Chart.js, which the page loads from the internet;
with no internet the page still shows the timelines and the tables. Nothing here fetches
anything: only the browser does.
"""

import json
import webbrowser
from pathlib import Path

from microsponge.support.game_log import Series
from microsponge.support.game_log_report import civilization_ids, name_of, series_of, tables, timelines, title_of
from microsponge.ui_strings import (
    MSG_PAGE_CHART_BUILDINGS, MSG_PAGE_CHART_CITIES, MSG_PAGE_CHART_CITIZENS, MSG_PAGE_CHART_COMMAND, MSG_PAGE_CHART_COMMAND_TAKEN, MSG_PAGE_CHART_DEVELOPMENT_SCORE, MSG_PAGE_CHART_HIT_POINTS,
    MSG_PAGE_CHART_INSIDE, MSG_PAGE_CHART_LEVEL, MSG_PAGE_CHART_MILITARY_SCORE, MSG_PAGE_CHART_POLICY, MSG_PAGE_CHART_POLICY_TAKEN, MSG_PAGE_CHART_POPULATION_SCORE, MSG_PAGE_CHART_SCIENCE_SCORE,
    MSG_PAGE_CHART_SCORE, MSG_PAGE_CHART_STRENGTH, MSG_PAGE_CHART_TECHNOLOGIES, MSG_PAGE_CHART_UNITS, MSG_PAGE_CHART_WEALTH, MSG_PAGE_CHARTS_HEADING, MSG_PAGE_NO_CHARTS, MSG_PAGE_TABLES_HEADING,
    MSG_PAGE_TIMELINES_HEADING, MSG_PAGE_TURN,
)

TEMPLATE = Path(__file__).with_name('game_log_page.html')
# Where the data of a game goes in the template.
PLACEHOLDER = '/*PAGE*/'
PAGE_SUFFIX = '.html'
FILE_ENCODING = 'utf-8'
# What would end a script element inside the data, and what is written instead.
CLOSING_TAG = '</'
ESCAPED_CLOSING_TAG = '<\\/'
# The two charts at the top of the page, drawn large: the rise and fall, and what may decide a winner.
MAIN_CHARTS = (
    (Series.STRENGTH, MSG_PAGE_CHART_STRENGTH),
    (Series.SCORE, MSG_PAGE_CHART_SCORE),
)
CHARTS = (
    (Series.MILITARY_SCORE, MSG_PAGE_CHART_MILITARY_SCORE),
    (Series.SCIENCE_SCORE, MSG_PAGE_CHART_SCIENCE_SCORE),
    (Series.POPULATION_SCORE, MSG_PAGE_CHART_POPULATION_SCORE),
    (Series.DEVELOPMENT_SCORE, MSG_PAGE_CHART_DEVELOPMENT_SCORE),
    (Series.CITIES, MSG_PAGE_CHART_CITIES),
    (Series.CITIZENS, MSG_PAGE_CHART_CITIZENS),
    (Series.UNITS, MSG_PAGE_CHART_UNITS),
    (Series.HIT_POINTS, MSG_PAGE_CHART_HIT_POINTS),
    (Series.INSIDE, MSG_PAGE_CHART_INSIDE),
    (Series.LEVEL, MSG_PAGE_CHART_LEVEL),
    (Series.POLICY, MSG_PAGE_CHART_POLICY),
    (Series.POLICY_TAKEN, MSG_PAGE_CHART_POLICY_TAKEN),
    (Series.COMMAND, MSG_PAGE_CHART_COMMAND),
    (Series.COMMAND_TAKEN, MSG_PAGE_CHART_COMMAND_TAKEN),
    (Series.WEALTH, MSG_PAGE_CHART_WEALTH),
    (Series.TECHNOLOGIES, MSG_PAGE_CHART_TECHNOLOGIES),
    (Series.BUILDINGS, MSG_PAGE_CHART_BUILDINGS),
)
# Counts that change by whole steps are drawn as steps, and totals that grow every turn as lines.
SMOOTH = (Series.SCORE, Series.MILITARY_SCORE, Series.SCIENCE_SCORE, Series.POPULATION_SCORE, Series.DEVELOPMENT_SCORE, Series.WEALTH, Series.STRENGTH, Series.HIT_POINTS, Series.LEVEL)


class PageKey:
    """The names the page's script reads."""

    TITLE = 'title'
    MAIN_CHARTS = 'mainCharts'
    CHARTS = 'charts'
    TIMELINES = 'timelines'
    TABLES = 'tables'
    TIMELINES_HEADING = 'timelinesHeading'
    CHARTS_HEADING = 'chartsHeading'
    TABLES_HEADING = 'tablesHeading'
    NO_CHARTS = 'noCharts'
    TURN_LABEL = 'turnLabel'
    SERIES = 'series'
    NAME = 'name'
    VALUES = 'values'
    STEPPED = 'stepped'
    LINES = 'lines'
    HEADING = 'heading'
    ROWS = 'rows'


def chart_of(*, data, series, title):
    """Return one chart of the page: a line for each civilization of what the log counted of one thing."""
    lines = [{PageKey.NAME: name_of(data=data, civilization=civilization), PageKey.VALUES: series_of(data=data, civilization=civilization, series=series)} for civilization in civilization_ids(data)]
    return {PageKey.TITLE: title, PageKey.SERIES: lines, PageKey.STEPPED: series not in SMOOTH}


def charts_of(*, data, charts):
    return [chart_of(data=data, series=series, title=title) for series, title in charts]


def page_data(data):
    """Return everything the page's script reads, worked out from the data of a log."""
    return {
        PageKey.TITLE: title_of(data),
        PageKey.MAIN_CHARTS: charts_of(data=data, charts=MAIN_CHARTS),
        PageKey.CHARTS: charts_of(data=data, charts=CHARTS),
        PageKey.TIMELINES: [{PageKey.TITLE: timeline.title, PageKey.LINES: timeline.lines} for timeline in timelines(data)],
        PageKey.TABLES: [{PageKey.TITLE: table.title, PageKey.HEADING: table.heading, PageKey.ROWS: table.rows} for table in tables(data)],
        PageKey.TIMELINES_HEADING: MSG_PAGE_TIMELINES_HEADING,
        PageKey.CHARTS_HEADING: MSG_PAGE_CHARTS_HEADING,
        PageKey.TABLES_HEADING: MSG_PAGE_TABLES_HEADING,
        PageKey.NO_CHARTS: MSG_PAGE_NO_CHARTS,
        PageKey.TURN_LABEL: MSG_PAGE_TURN,
    }


def page_text(data):
    """Return the HTML of the page of a log."""
    inside = json.dumps(page_data(data)).replace(CLOSING_TAG, ESCAPED_CLOSING_TAG)
    return TEMPLATE.read_text(encoding=FILE_ENCODING).replace(PLACEHOLDER, inside)


def page_path(log_path):
    """Return where the page of a log file is written: beside the log file."""
    return log_path.with_suffix(PAGE_SUFFIX)


def write_page(*, data, path):
    path.write_text(page_text(data), encoding=FILE_ENCODING)


def open_page(path):
    """Open a page in the default browser."""
    webbrowser.open(path.resolve().as_uri())
