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

"""Charts drawn in plain characters: how a number of each civilization went over the turns of a game."""

from string import digits

from microsponge.ui_strings import MSG_CHART_AXIS_CORNER, MSG_CHART_AXIS_LINE, MSG_CHART_BLANK, MSG_CHART_LEGEND_ITEM, MSG_CHART_LEGEND_SEPARATOR, MSG_CHART_ROW, MSG_CHART_SHARED, MSG_CHART_SHARED_LEGEND, MSG_CHART_TURNS

# The most columns and the rows a chart is drawn in.
CHART_WIDTH = 64
CHART_HEIGHT = 8
FIRST_SERIES = 1
# The top of a chart whose every number is 0, so that the chart still has a scale.
LEAST_TOP = 1


def mark_of(number):
    """Return the character a series is drawn with: the digit of its number, counted from 1."""
    return digits[number % len(digits)]


def sampled(*, column, columns, turns):
    """Return the turn a column of a chart shows, when columns columns are spread evenly over turns turns."""
    return column * (turns - 1) // max(columns - 1, 1)


def row_of(*, value, top, height):
    """Return the row a value is drawn on, 0 at the bottom and height - 1 for the top value."""
    return round(value * (height - 1) / top)


def chart_grid(*, series, columns, height, top):
    """Return the cells of a chart, top row first: each series drawn with its mark, and the shared mark where two series meet."""
    turns = max(len(values) for values in series)
    grid = [[MSG_CHART_BLANK] * columns for _ in range(height)]
    for number, values in enumerate(series, start=FIRST_SERIES):
        for column in range(columns):
            turn = sampled(column=column, columns=columns, turns=turns)
            if turn < len(values):
                row = height - 1 - row_of(value=values[turn], top=top, height=height)
                grid[row][column] = mark_of(number) if grid[row][column] == MSG_CHART_BLANK else MSG_CHART_SHARED
    return grid


def chart_lines(*, title, series, names, width=CHART_WIDTH, height=CHART_HEIGHT):
    """Return a chart as lines: the title, the rows with the number each row stands for, the axis of turns, and a legend.

    series holds one list of numbers for each name, a number for each turn from the first; a
    series that stops early, like that of a civilization that was defeated, is drawn up to
    where it stops. A game longer than the chart is wide is sampled evenly.
    """
    turns = max((len(values) for values in series), default=0)
    if turns == 0:
        return [title]
    columns = min(width, turns)
    top = max(LEAST_TOP, max(max(values, default=0) for values in series))
    grid = chart_grid(series=series, columns=columns, height=height, top=top)
    label_width = len(str(top))
    lines = [title]
    for place, cells in enumerate(grid):
        label = round(top * (height - 1 - place) / (height - 1))
        lines.append(MSG_CHART_ROW.format(label=str(label).rjust(label_width), cells=''.join(cells)).rstrip())
    lines.append(MSG_CHART_BLANK * label_width + MSG_CHART_AXIS_CORNER + MSG_CHART_AXIS_LINE * columns)
    lines.append(MSG_CHART_TURNS.format(indent=MSG_CHART_BLANK * label_width, last=str(turns - 1).rjust(columns - 1)))
    legend = [MSG_CHART_LEGEND_ITEM.format(mark=mark_of(number), name=name) for number, name in enumerate(names, start=FIRST_SERIES)]
    lines.append(MSG_CHART_LEGEND_SEPARATOR.join([*legend, MSG_CHART_SHARED_LEGEND.format(mark=MSG_CHART_SHARED)]))
    return lines
