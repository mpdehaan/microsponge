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

"""Charts drawn in plain characters."""

import unittest

from microsponge.support.charts import CHART_HEIGHT, CHART_WIDTH, chart_lines, mark_of, row_of, sampled
from microsponge.ui_strings import MSG_CHART_AXIS_LINE, MSG_CHART_LEGEND_ITEM, MSG_CHART_SHARED, MSG_CHART_SHARED_LEGEND

A_TITLE = 'Citizens:'
NAMES = ['Ugg', 'Grok']
RISING = [0, 1, 2, 3, 4, 5, 6, 7]
FALLING = [7, 6, 5, 4]
LONG = 200
FIRST = '1'
SECOND = '2'
# The lines of a chart around its rows: the title above, and the axis, the turns and the legend below.
TITLE_LINES = 1
LINES_BELOW = 3


def rows_of(lines):
    """Return the cells of each row of a chart, top row first, without the label at the left."""
    return [line.split('|', 1)[1] if '|' in line else '' for line in lines[TITLE_LINES:-LINES_BELOW]]


class TestCharts(unittest.TestCase):

    def test_a_chart_is_a_title_a_row_for_each_step_of_the_scale_an_axis_the_turns_and_a_legend(self):
        lines = chart_lines(title=A_TITLE, series=[RISING, FALLING], names=NAMES)
        self.assertEqual(lines[0], A_TITLE)
        self.assertEqual(len(lines), TITLE_LINES + CHART_HEIGHT + LINES_BELOW)
        self.assertTrue(lines[TITLE_LINES].startswith(str(max(RISING))))
        self.assertTrue(lines[CHART_HEIGHT].startswith(str(min(RISING))))
        self.assertEqual(lines[-LINES_BELOW].count(MSG_CHART_AXIS_LINE), len(RISING))
        self.assertTrue(lines[-2].rstrip().endswith(str(len(RISING) - 1)))
        for number, name in enumerate(NAMES, start=1):
            self.assertIn(MSG_CHART_LEGEND_ITEM.format(mark=mark_of(number), name=name), lines[-1])
        self.assertIn(MSG_CHART_SHARED_LEGEND.format(mark=MSG_CHART_SHARED), lines[-1])

    def test_each_series_is_drawn_with_its_own_mark_at_the_height_of_its_number_on_each_turn(self):
        rows = rows_of(chart_lines(title=A_TITLE, series=[RISING, FALLING], names=NAMES))
        for turn, value in enumerate(RISING):
            self.assertIn(rows[CHART_HEIGHT - 1 - value].ljust(len(RISING))[turn], (FIRST, MSG_CHART_SHARED))
        self.assertEqual(rows[0].ljust(len(RISING))[0], SECOND)
        self.assertEqual(rows[1].ljust(len(RISING))[1], SECOND)

    def test_two_series_on_the_same_cell_show_the_shared_mark_and_a_series_that_stops_early_is_drawn_no_further(self):
        rows = rows_of(chart_lines(title=A_TITLE, series=[RISING, RISING[:3]], names=NAMES))
        drawn = ''.join(rows)
        self.assertEqual(drawn.count(MSG_CHART_SHARED), 3)
        self.assertEqual(drawn.count(FIRST), len(RISING) - 3)
        self.assertEqual(drawn.count(SECOND), 0)

    def test_a_game_longer_than_the_chart_is_wide_is_sampled_evenly_from_its_first_turn_to_its_last(self):
        lines = chart_lines(title=A_TITLE, series=[list(range(LONG))], names=NAMES[:1])
        self.assertEqual(lines[-LINES_BELOW].count(MSG_CHART_AXIS_LINE), CHART_WIDTH)
        self.assertTrue(lines[-2].rstrip().endswith(str(LONG - 1)))
        self.assertEqual(sampled(column=0, columns=CHART_WIDTH, turns=LONG), 0)
        self.assertEqual(sampled(column=CHART_WIDTH - 1, columns=CHART_WIDTH, turns=LONG), LONG - 1)
        rows = rows_of(lines)
        self.assertEqual(rows[0].rstrip()[-1], FIRST)
        self.assertEqual(rows[-1][0], FIRST)

    def test_a_chart_of_nothing_is_only_its_title_and_a_chart_of_zeros_still_has_a_scale(self):
        self.assertEqual(chart_lines(title=A_TITLE, series=[[], []], names=NAMES), [A_TITLE])
        self.assertEqual(chart_lines(title=A_TITLE, series=[], names=[]), [A_TITLE])
        lines = chart_lines(title=A_TITLE, series=[[0, 0, 0]], names=NAMES[:1])
        self.assertEqual(rows_of(lines)[-1], FIRST * 3)
        self.assertEqual(row_of(value=0, top=1, height=CHART_HEIGHT), 0)
