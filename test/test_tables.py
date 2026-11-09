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

"""Tables of text with lined-up columns, plain and as Markdown."""

import unittest

from microsponge.engine.kinds.dice import Dice
from microsponge.support.tables import LEAST_COLUMN_WIDTH, is_number, shown_amounts, shown_amounts_by_kind, shown_flag, shown_kinds, shown_number, table_lines
from microsponge.themes.caveman.resources import Currency, Wood
from microsponge.themes.caveman.terrains import Grassland
from microsponge.ui_strings import MSG_AMOUNT, MSG_AMOUNTS_OF, MSG_COLUMN_GAP, MSG_LIST_SEPARATOR, MSG_MARKDOWN_CELL_GAP, MSG_MARKDOWN_ROW, MSG_NONE_MARK, MSG_YES_MARK

A_TITLE = 'a table'
A_WORD = 'oxen'
A_SHORT_HEADING = 'hp'
A_LONGER_WORD = 'mammoth'
A_NUMBER = '7'
A_LONGER_NUMBER = '1234'
HEADING = (A_WORD, A_WORD)
ROWS = [[A_LONGER_WORD, A_NUMBER], [A_WORD, A_LONGER_NUMBER]]


class TestTables(unittest.TestCase):

    def test_a_plain_table_is_its_title_the_heading_and_each_row_with_words_at_the_left_and_numbers_at_the_right(self):
        lines = table_lines(title=A_TITLE, heading=HEADING, rows=ROWS)
        self.assertEqual(lines[0], A_TITLE)
        self.assertEqual(lines[1], A_WORD.ljust(len(A_LONGER_WORD)) + MSG_COLUMN_GAP + A_WORD)
        self.assertEqual(lines[2], A_LONGER_WORD + MSG_COLUMN_GAP + A_NUMBER.rjust(len(A_LONGER_NUMBER)))
        self.assertEqual(lines[3], A_WORD.ljust(len(A_LONGER_WORD)) + MSG_COLUMN_GAP + A_LONGER_NUMBER)

    def test_a_column_with_a_word_in_any_row_is_lined_up_at_the_left_and_the_none_mark_counts_as_a_number(self):
        lines = table_lines(title=A_TITLE, heading=HEADING, rows=[[A_WORD, A_NUMBER], [A_WORD, A_LONGER_WORD]])
        self.assertTrue(lines[2].endswith(A_NUMBER.ljust(len(A_LONGER_WORD)).rstrip()))
        self.assertTrue(is_number(MSG_NONE_MARK))
        self.assertTrue(is_number(A_NUMBER))
        self.assertFalse(is_number(A_WORD))
        lines = table_lines(title=A_TITLE, heading=HEADING, rows=[[A_WORD, A_NUMBER], [A_WORD, MSG_NONE_MARK]])
        self.assertEqual(lines[3], A_WORD + MSG_COLUMN_GAP + MSG_NONE_MARK.rjust(len(A_WORD)))

    def test_a_markdown_table_has_a_blank_line_under_the_title_a_rule_that_marks_numeric_columns_and_every_column_at_least_three_wide(self):
        lines = table_lines(title=A_TITLE, heading=HEADING, rows=ROWS, markdown=True)
        self.assertEqual(lines[:2], [A_TITLE, ''])
        self.assertEqual(lines[2], MSG_MARKDOWN_ROW.format(cells=MSG_MARKDOWN_CELL_GAP.join([A_WORD.ljust(len(A_LONGER_WORD)), A_WORD.rjust(len(A_LONGER_NUMBER))])))
        self.assertEqual(lines[3], MSG_MARKDOWN_ROW.format(cells=MSG_MARKDOWN_CELL_GAP.join(['-' * len(A_LONGER_WORD), '-' * (len(A_LONGER_NUMBER) - 1) + ':'])))
        self.assertEqual(lines[4], MSG_MARKDOWN_ROW.format(cells=MSG_MARKDOWN_CELL_GAP.join([A_LONGER_WORD, A_NUMBER.rjust(len(A_LONGER_NUMBER))])))
        narrow = table_lines(title=A_TITLE, heading=(A_SHORT_HEADING,), rows=[[A_NUMBER]], markdown=True)
        self.assertEqual(narrow[3], MSG_MARKDOWN_ROW.format(cells='-' * (LEAST_COLUMN_WIDTH - 1) + ':'))

    def test_cells_are_shown_as_people_read_them_with_a_mark_for_none(self):
        self.assertEqual((shown_number(0), shown_number(3)), (MSG_NONE_MARK, '3'))
        self.assertEqual((shown_flag(True), shown_flag(False)), (MSG_YES_MARK, MSG_NONE_MARK))
        self.assertEqual(shown_kinds(()), MSG_NONE_MARK)
        self.assertEqual(shown_kinds((Currency, Wood)), MSG_LIST_SEPARATOR.join(['currency', 'wood']))
        self.assertEqual(shown_amounts({}), MSG_NONE_MARK)
        self.assertEqual(shown_amounts({Currency: 10, Wood: 5}), MSG_LIST_SEPARATOR.join([MSG_AMOUNT.format(amount=10, name='currency'), MSG_AMOUNT.format(amount=5, name='wood')]))
        self.assertEqual(shown_amounts_by_kind({Grassland: {Wood: 1}}), MSG_AMOUNTS_OF.format(name='grassland', amounts=MSG_AMOUNT.format(amount=1, name='wood')))
        self.assertEqual(shown_amounts_by_kind({}), MSG_NONE_MARK)
        self.assertEqual(Dice(count=2, sides=6).shown(), '2d6')
