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

"""The optimizer's report: how the theme as it is and the best numbers found fare against each criterion, on the seeds searched and on seeds held out, the numbers themselves, and every constant of the theme the best numbers would change."""

from microsponge.engine.kinds.kind import shown_name
from microsponge.support.optimizer.criteria import Criterion, Weights, score
from microsponge.support.optimizer.parameters import PARAMETERS, Tuning
from microsponge.support.tables import shown_amounts, table_lines
from microsponge.ui_strings import (
    MSG_OPTIMIZER_CHANGES_HEADING, MSG_OPTIMIZER_CHANGES_TITLE, MSG_OPTIMIZER_CRITERIA_HEADING, MSG_OPTIMIZER_CRITERIA_TITLE,
    MSG_OPTIMIZER_NUMBERS_HEADING, MSG_OPTIMIZER_NUMBERS_TITLE, MSG_OPTIMIZER_SCORE, MSG_OPTIMIZER_SUMMARY,
)

DECIMALS = '{:.2f}'
SECONDS_A_MINUTE = 60


def shown_decimal(number):
    return DECIMALS.format(number)


def shown_value(value):
    """Return a constant's value as a cell: amounts keyed by kinds as a cost is, and anything else as it is."""
    return shown_amounts(value) if isinstance(value, dict) else str(value)


def criteria_table(*, found, markdown):
    """Return the table of each criterion's weight and badness: the theme as it is and the best numbers, on the seeds searched and on the seeds held out, and the score of each column last."""
    columns = (found.now_searched, found.best_searched, found.now_held_out, found.best_held_out)
    rows = [[criterion, shown_decimal(Weights.WEIGHTS[criterion]), *(shown_decimal(column[criterion]) for column in columns)] for criterion in Criterion.ALL]
    rows.append([MSG_OPTIMIZER_SCORE, '', *(shown_decimal(score(column)) for column in columns)])
    return table_lines(title=MSG_OPTIMIZER_CRITERIA_TITLE, heading=MSG_OPTIMIZER_CRITERIA_HEADING, rows=rows, markdown=markdown)


def numbers_table(*, start, best, markdown):
    """Return the table of the numbers searched: the ones that fit the theme as it is, and the best found."""
    rows = [[parameter.name, shown_decimal(start[parameter.name]), shown_decimal(best[parameter.name])] for parameter in PARAMETERS]
    return table_lines(title=MSG_OPTIMIZER_NUMBERS_TITLE, heading=MSG_OPTIMIZER_NUMBERS_HEADING, rows=rows, markdown=markdown)


def changed_constants(*, theme, values):
    """Return (the kind, the constant, the value now, the value suggested) for every constant of a theme a set of numbers would change, in the theme's order."""
    changed = []
    for kind, name, value in Tuning.changes(theme=theme, values=values):
        now = getattr(kind, name)
        if now != value:
            changed.append((kind, name, now, value))
    return changed


def changes_table(*, theme, values, markdown):
    rows = [[shown_name(kind), name, shown_value(now), shown_value(value)] for kind, name, now, value in changed_constants(theme=theme, values=values)]
    return table_lines(title=MSG_OPTIMIZER_CHANGES_TITLE, heading=MSG_OPTIMIZER_CHANGES_HEADING, rows=rows, markdown=markdown)


def report_lines(*, theme, found, markdown=False):
    """Return the optimizer's report on what a search found, as lines."""
    result = found.result
    lines = [MSG_OPTIMIZER_SUMMARY.format(theme=shown_name(theme), steps=len(result.steps), restarts=result.restarts, games=found.games, minutes=round(found.seconds / SECONDS_A_MINUTE)), '']
    lines += criteria_table(found=found, markdown=markdown) + ['']
    lines += numbers_table(start=result.start, best=result.best, markdown=markdown) + ['']
    lines += changes_table(theme=theme, values=result.best, markdown=markdown)
    return lines
