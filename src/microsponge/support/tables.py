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

"""Tables of text with lined-up columns, for the tools' reports and for anything else that prints a table.

A table comes in two forms: plain text for a terminal, and Markdown, to be pasted into the guide
for a theme. Both line the columns up, numbers at the right and words at the left.
"""

from microsponge.engine.kinds.kind import shown_name

# A Markdown rule needs three characters, so no column is narrower.
LEAST_COLUMN_WIDTH = 3
# A Markdown table needs a blank line before it.
BLANK_LINE = ''
from microsponge.ui_strings import (
    MSG_AMOUNT, MSG_AMOUNTS_OF, MSG_COLUMN_GAP, MSG_LIST_SEPARATOR, MSG_MARKDOWN_CELL_GAP, MSG_MARKDOWN_RIGHT_MARK, MSG_MARKDOWN_ROW, MSG_MARKDOWN_RULE,
    MSG_NONE_MARK, MSG_YES_MARK,
)


def is_number(cell):
    """Return whether a cell is a number, or the mark that stands for none, which goes where a number would."""
    return cell.isdigit() or cell == MSG_NONE_MARK


def is_numeric_column(*, rows, column):
    """Return whether every cell of a column is a number or the mark for none, so that the column is lined up at the right."""
    return all(is_number(row[column]) for row in rows)


def lined_up(*, cells, widths, numeric):
    """Return one row of a table: each cell at the right of its column when the column is numeric, and at the left otherwise."""
    return MSG_COLUMN_GAP.join(cell.rjust(width) if right else cell.ljust(width) for cell, width, right in zip(cells, widths, numeric)).rstrip()


def markdown_row(*, cells, widths, numeric):
    """Return one row of a Markdown table, padded the same way as a plain row so that the source reads as a table too."""
    return MSG_MARKDOWN_ROW.format(cells=MSG_MARKDOWN_CELL_GAP.join(cell.rjust(width) if right else cell.ljust(width) for cell, width, right in zip(cells, widths, numeric)))


def markdown_rule(*, widths, numeric):
    """Return the line under a Markdown table's heading, as wide as each column, which says that numeric columns line up at the right."""
    rules = [MSG_MARKDOWN_RULE * (width - len(MSG_MARKDOWN_RIGHT_MARK)) + MSG_MARKDOWN_RIGHT_MARK if right else MSG_MARKDOWN_RULE * width for width, right in zip(widths, numeric)]
    return MSG_MARKDOWN_ROW.format(cells=MSG_MARKDOWN_CELL_GAP.join(rules))


def table_lines(*, title, heading, rows, markdown=False):
    """Return a titled table as lines: the title, the heading row and each row, with the columns lined up, numbers at the right and words at the left, as plain text or as Markdown."""
    cells = [list(heading)] + rows
    widths = [max(LEAST_COLUMN_WIDTH, *(len(row[column]) for row in cells)) for column in range(len(heading))]
    numeric = [is_numeric_column(rows=rows, column=column) for column in range(len(heading))]
    if markdown:
        body = [markdown_row(cells=cells[0], widths=widths, numeric=numeric), markdown_rule(widths=widths, numeric=numeric)]
        body += [markdown_row(cells=row, widths=widths, numeric=numeric) for row in rows]
        return [title, BLANK_LINE, *body]
    return [title, *[lined_up(cells=row, widths=widths, numeric=numeric) for row in cells]]


def shown_number(number):
    """Return a number as a cell: the mark for none when it is 0."""
    return str(number) if number else MSG_NONE_MARK


def shown_flag(flag):
    """Return a yes-or-no property as a cell: a mark for yes, and the mark for none for no."""
    return MSG_YES_MARK if flag else MSG_NONE_MARK


def shown_kinds(kinds):
    """Return kinds as a cell: their names as people read them, or the mark for none."""
    return MSG_LIST_SEPARATOR.join(shown_name(kind) for kind in kinds) or MSG_NONE_MARK


def shown_amounts(amounts):
    """Return amounts keyed by kinds, like a cost, as a cell: 10 currency, 10 wood, or the mark for none."""
    return MSG_LIST_SEPARATOR.join(MSG_AMOUNT.format(amount=amount, name=shown_name(kind)) for kind, amount in amounts.items()) or MSG_NONE_MARK


def shown_amounts_by_kind(nested):
    """Return amounts keyed by a kind and then by kinds, like a bonus for each terrain, as a cell: grassland: 1 food, or the mark for none."""
    return MSG_LIST_SEPARATOR.join(MSG_AMOUNTS_OF.format(name=shown_name(kind), amounts=shown_amounts(amounts)) for kind, amounts in nested.items()) or MSG_NONE_MARK
