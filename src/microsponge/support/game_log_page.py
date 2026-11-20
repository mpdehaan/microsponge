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

"""The page of a game's log: one HTML file with tabs of charts of everything the log counted turn by turn, the timeline of each civilization and the tables of the report.

The page is the file `game_log_page.html` beside this module with the data of one game put
in. The charts are drawn in the browser by Chart.js, which the page loads from the internet;
with no internet the page still shows the timelines and the tables. Nothing here fetches
anything: only the browser does.
"""

import json
import webbrowser
from pathlib import Path

from microsponge.support.game_log import Key, Series
from microsponge.support.game_log_report import built_table, civilization_ids, fighting_table, forces_table, losses_table, winner_line, made_table, name_of, orders_table, series_of, tables, timelines, title_of
from microsponge.ui_strings import (
    MSG_PAGE_CHART_BUILDINGS, MSG_PAGE_CHART_CITIES, MSG_PAGE_CHART_CITIZENS, MSG_PAGE_CHART_COMMAND, MSG_PAGE_CHART_COMMAND_TAKEN, MSG_PAGE_CHART_DEVELOPMENT_SCORE, MSG_PAGE_CHART_FOOD_STORED, MSG_PAGE_CHART_HIT_POINTS,
    MSG_PAGE_CHART_IMPROVEMENTS_OF_KIND, MSG_PAGE_CHART_INSIDE, MSG_PAGE_CHART_LOST_ATTACKING_CITY, MSG_PAGE_CHART_LOST_ATTACKING_FIELD, MSG_PAGE_CHART_LOST_DEFENDING_CITY, MSG_PAGE_CHART_LOST_DEFENDING_FIELD, MSG_PAGE_CHART_LEVEL, MSG_PAGE_CHART_MILITARY_SCORE, MSG_PAGE_CHART_POLICY, MSG_PAGE_CHART_POLICY_TAKEN,
    MSG_PAGE_CHART_POPULATION_SCORE, MSG_PAGE_CHART_SCIENCE_SCORE, MSG_PAGE_CHART_SCORE, MSG_PAGE_CHART_STRENGTH, MSG_PAGE_CHART_TECHNOLOGIES, MSG_PAGE_CHART_UNITS, MSG_PAGE_CHART_UNITS_OF_KIND, MSG_PAGE_CHART_WARS,
    MSG_PAGE_CHART_BANK_OF, MSG_PAGE_CHART_ORDERS_OF_KIND, MSG_PAGE_NO_CHARTS, MSG_PAGE_TAB_BUILDINGS, MSG_PAGE_TAB_ORDERS, MSG_PAGE_TURNS_FROM_TO, MSG_PAGE_NO_IMPROVEMENTS, MSG_PAGE_TAB_CITIES, MSG_PAGE_TAB_CONTROL_POINTS, MSG_PAGE_TAB_IMPROVEMENTS, MSG_PAGE_TAB_SCORE, MSG_PAGE_TAB_TABLES,
    MSG_PAGE_TAB_TIMELINES, MSG_PAGE_TAB_UNITS, MSG_PAGE_TURN,
)

TEMPLATE = Path(__file__).with_name('game_log_page.html')
# Where the data of a game goes in the template.
PLACEHOLDER = '/*PAGE*/'
PAGE_SUFFIX = '.html'
FILE_ENCODING = 'utf-8'
# What would end a script element inside the data, and what is written instead.
CLOSING_TAG = '</'
ESCAPED_CLOSING_TAG = '<\\/'
# The two charts at the top of the score tab, drawn large: the rise and fall, and what may decide a winner.
MAIN_CHARTS = (
    (Series.STRENGTH, MSG_PAGE_CHART_STRENGTH),
    (Series.SCORE, MSG_PAGE_CHART_SCORE),
    (Series.WARS, MSG_PAGE_CHART_WARS),
)
SCORE_PART_CHARTS = (
    (Series.MILITARY_SCORE, MSG_PAGE_CHART_MILITARY_SCORE),
    (Series.SCIENCE_SCORE, MSG_PAGE_CHART_SCIENCE_SCORE),
    (Series.POPULATION_SCORE, MSG_PAGE_CHART_POPULATION_SCORE),
    (Series.DEVELOPMENT_SCORE, MSG_PAGE_CHART_DEVELOPMENT_SCORE),
)
CITY_CHARTS = (
    (Series.CITIES, MSG_PAGE_CHART_CITIES),
    (Series.CITIZENS, MSG_PAGE_CHART_CITIZENS),
    (Series.TECHNOLOGIES, MSG_PAGE_CHART_TECHNOLOGIES),
    (Series.FOOD_STORED, MSG_PAGE_CHART_FOOD_STORED),
)
BUILDING_CHARTS = ((Series.BUILDINGS, MSG_PAGE_CHART_BUILDINGS),)
# The orders tab counts the orders each civilization gave in each span of this many turns.
ORDER_SPAN_TURNS = 10
# The units tab has the units in all, then a chart for each kind of unit, then these.
ALL_UNITS_CHARTS = ((Series.UNITS, MSG_PAGE_CHART_UNITS),)
MILITARY_CHARTS = (
    (Series.LOST_ATTACKING_CITY, MSG_PAGE_CHART_LOST_ATTACKING_CITY),
    (Series.LOST_ATTACKING_FIELD, MSG_PAGE_CHART_LOST_ATTACKING_FIELD),
    (Series.LOST_DEFENDING_CITY, MSG_PAGE_CHART_LOST_DEFENDING_CITY),
    (Series.LOST_DEFENDING_FIELD, MSG_PAGE_CHART_LOST_DEFENDING_FIELD),
    (Series.HIT_POINTS, MSG_PAGE_CHART_HIT_POINTS),
    (Series.INSIDE, MSG_PAGE_CHART_INSIDE),
    (Series.LEVEL, MSG_PAGE_CHART_LEVEL),
)
CONTROL_POINT_CHARTS = (
    (Series.POLICY, MSG_PAGE_CHART_POLICY),
    (Series.POLICY_TAKEN, MSG_PAGE_CHART_POLICY_TAKEN),
    (Series.COMMAND, MSG_PAGE_CHART_COMMAND),
    (Series.COMMAND_TAKEN, MSG_PAGE_CHART_COMMAND_TAKEN),
)
# Counts that change by whole steps are drawn as steps, and totals that grow every turn as lines.
SMOOTH = (Series.LOST_ATTACKING_CITY, Series.LOST_ATTACKING_FIELD, Series.LOST_DEFENDING_CITY, Series.LOST_DEFENDING_FIELD, Series.FOOD_STORED, Series.SCORE, Series.MILITARY_SCORE, Series.SCIENCE_SCORE, Series.POPULATION_SCORE, Series.DEVELOPMENT_SCORE, Series.WEALTH, Series.STRENGTH, Series.HIT_POINTS, Series.LEVEL)


class PageKey:
    """The names the page's script reads."""

    TITLE = 'title'
    TABS = 'tabs'
    WINNER = 'winner'
    ID = 'id'
    NAME = 'name'
    CONTENT = 'content'
    CHARTS = 'charts'
    NOTE = 'note'
    TIMELINES = 'timelines'
    TABLES = 'tables'
    NO_CHARTS = 'noCharts'
    TURN_LABEL = 'turnLabel'
    SERIES = 'series'
    VALUES = 'values'
    STEPPED = 'stepped'
    WIDE = 'wide'
    MOST = 'most'
    BARS = 'bars'
    LABELS = 'labels'
    LINES = 'lines'
    HEADING = 'heading'
    ROWS = 'rows'


class Tab:
    """The tabs of the page, by the name each has in the address of the page, in the order the page shows them."""

    SCORE = 'score'
    CITIES = 'cities'
    UNITS = 'units'
    BUILDINGS = 'buildings'
    IMPROVEMENTS = 'improvements'
    ORDERS = 'orders'
    CONTROL_POINTS = 'control-points'
    TIMELINES = 'timelines'
    TABLES = 'tables'

    ORDER = (SCORE, CITIES, UNITS, BUILDINGS, IMPROVEMENTS, ORDERS, CONTROL_POINTS, TIMELINES, TABLES)


class Content:
    """What a tab of the page shows."""

    CHARTS = 'charts'
    TIMELINES = 'timelines'
    TABLES = 'tables'


def lines_of(*, data, counted):
    """Return a line for each civilization of a log: its name, and what counted(civilization) gives for it turn by turn."""
    return [{PageKey.NAME: name_of(data=data, civilization=civilization), PageKey.VALUES: counted(civilization)} for civilization in civilization_ids(data)]


def chart_of(*, data, series, title, wide=False):
    """Return one chart of the page: a line for each civilization of what the log counted of one series. The chart of wars runs from none to every other civilization of the game."""
    lines = lines_of(data=data, counted=lambda civilization: series_of(data=data, civilization=civilization, series=series))
    chart = {PageKey.TITLE: title, PageKey.SERIES: lines, PageKey.STEPPED: series not in SMOOTH, PageKey.WIDE: wide}
    if series == Series.WARS:
        chart[PageKey.MOST] = len(data[Key.CIVILIZATIONS]) - 1
    return chart


def charts_of(*, data, charts, wide=False):
    return [chart_of(data=data, series=series, title=title, wide=wide) for series, title in charts]


def kinds_ever_had(*, data, key):
    """Return the kinds a log counted under a key, like the kinds of unit, that some civilization had at least one of on some turn, in the theme's order."""
    return [kind for kind, counts in data[key].items() if any(any(turns) for turns in counts.values())]


def kind_chart(*, data, key, kind, title, stepped=True):
    """Return one chart of the page: a line for each civilization of how many of one kind, counted under a key, the civilization had."""
    lines = lines_of(data=data, counted=lambda civilization: data[key][kind][str(civilization)])
    return {PageKey.TITLE: title.format(kind=kind, city=data[Key.CITY_WORD]), PageKey.SERIES: lines, PageKey.STEPPED: stepped, PageKey.WIDE: False}


def kind_charts(*, data, key, title, stepped=True):
    """Return a chart for each kind counted under a key that some civilization ever had."""
    return [kind_chart(data=data, key=key, kind=kind, title=title, stepped=stepped) for kind in kinds_ever_had(data=data, key=key)]


def spans_of(data):
    """Return the label of each span of turns the orders tab counts orders in, from the first turn of the game to the last."""
    return [MSG_PAGE_TURNS_FROM_TO.format(first=first, last=min(first + ORDER_SPAN_TURNS, data[Key.TURNS]) - 1) for first in range(0, data[Key.TURNS], ORDER_SPAN_TURNS)]


def given_in_spans(*, turns, spans):
    """Return how many of some turns an order was given on fall in each span of turns."""
    counts = [0] * spans
    for turn in turns:
        counts[min(turn // ORDER_SPAN_TURNS, spans - 1)] += 1
    return counts


def order_chart(*, data, kind):
    """Return the chart of how many orders of one kind each civilization gave in each span of turns, drawn as bars."""
    labels = spans_of(data)
    given = {record[Key.CIVILIZATION]: record[Key.GIVEN] for record in data[Key.ORDERS] if record[Key.KIND] == kind}
    lines = lines_of(data=data, counted=lambda civilization: given_in_spans(turns=given.get(civilization, []), spans=len(labels)))
    title = MSG_PAGE_CHART_ORDERS_OF_KIND.format(kind=kind, turns=ORDER_SPAN_TURNS)
    return {PageKey.TITLE: title, PageKey.SERIES: lines, PageKey.STEPPED: False, PageKey.WIDE: False, PageKey.BARS: True, PageKey.LABELS: labels}


def order_charts(data):
    """Return a chart for each kind of order some civilization gave."""
    kinds = list(dict.fromkeys(record[Key.KIND] for record in data[Key.ORDERS] if record[Key.GIVEN]))
    return [order_chart(data=data, kind=kind) for kind in kinds]


def table_data(table):
    return {PageKey.TITLE: table.title, PageKey.HEADING: table.heading, PageKey.ROWS: table.rows}


def tab_of(*, tab, name, content=Content.CHARTS, charts=(), note=None, tab_tables=()):
    """Return one tab of the page: what it shows, its charts, a note when it has nothing to chart, and the tables it shows above its charts."""
    return {PageKey.ID: tab, PageKey.NAME: name, PageKey.CONTENT: content, PageKey.CHARTS: list(charts), PageKey.NOTE: note, PageKey.TABLES: [table_data(table) for table in tab_tables]}


def tabs_of(data):
    """Return the tabs of the page of a log, in order, each with its charts."""
    units = [*charts_of(data=data, charts=ALL_UNITS_CHARTS), *kind_charts(data=data, key=Key.UNIT_KINDS, title=MSG_PAGE_CHART_UNITS_OF_KIND), *charts_of(data=data, charts=MILITARY_CHARTS)]
    improvements = kind_charts(data=data, key=Key.IMPROVEMENTS, title=MSG_PAGE_CHART_IMPROVEMENTS_OF_KIND)
    return [
        tab_of(tab=Tab.SCORE, name=MSG_PAGE_TAB_SCORE, charts=(*charts_of(data=data, charts=MAIN_CHARTS, wide=True), *charts_of(data=data, charts=SCORE_PART_CHARTS))),
        tab_of(tab=Tab.CITIES, name=MSG_PAGE_TAB_CITIES, charts=(*charts_of(data=data, charts=CITY_CHARTS), *kind_charts(data=data, key=Key.BANKS, title=MSG_PAGE_CHART_BANK_OF, stepped=False))),
        tab_of(tab=Tab.UNITS, name=MSG_PAGE_TAB_UNITS, charts=units, tab_tables=(made_table(data), fighting_table(data), losses_table(data), forces_table(data))),
        tab_of(tab=Tab.BUILDINGS, name=MSG_PAGE_TAB_BUILDINGS, charts=charts_of(data=data, charts=BUILDING_CHARTS), tab_tables=(built_table(data),)),
        tab_of(tab=Tab.IMPROVEMENTS, name=MSG_PAGE_TAB_IMPROVEMENTS, charts=improvements, note=None if improvements else MSG_PAGE_NO_IMPROVEMENTS.format(city=data[Key.CITY_WORD])),
        tab_of(tab=Tab.ORDERS, name=MSG_PAGE_TAB_ORDERS, charts=order_charts(data), tab_tables=(orders_table(data),)),
        tab_of(tab=Tab.CONTROL_POINTS, name=MSG_PAGE_TAB_CONTROL_POINTS, charts=charts_of(data=data, charts=CONTROL_POINT_CHARTS)),
        tab_of(tab=Tab.TIMELINES, name=MSG_PAGE_TAB_TIMELINES, content=Content.TIMELINES),
        tab_of(tab=Tab.TABLES, name=MSG_PAGE_TAB_TABLES, content=Content.TABLES),
    ]


def page_data(data):
    """Return everything the page's script reads, worked out from the data of a log."""
    return {
        PageKey.TITLE: title_of(data),
        PageKey.WINNER: winner_line(data),
        PageKey.TABS: tabs_of(data),
        PageKey.TIMELINES: [{PageKey.TITLE: timeline.title, PageKey.LINES: timeline.lines} for timeline in timelines(data)],
        PageKey.TABLES: [table_data(table) for table in tables(data)],
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
