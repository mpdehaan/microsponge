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

"""Show how the units of a theme stand against each other in a fight, to help balance the theme.

Run from the top folder, naming a theme:

    .venv/bin/python tools/balance.py caveman

Each row of the table is a kind of unit that has attack points, and each column is a kind of
unit being attacked. A number says how many attacks the unit of the row needs to take every hit
point off a whole unit of the column, and a dash says that the unit of the row cannot hit that
unit at all. Nothing healed between the attacks is counted, and neither is striking back. A
kind of unit whose class of unit, land, sea, air or space, is not decided yet is left out of
the table and named below it, since what can hit it is unknown.

Below the table are the pairs that fall outside what the user wants of a theme: a unit that is
gone after one attack, and a unit that takes more than 10 attacks. Not every pair listed is
wrong, since a strong unit may well finish a settler at once, so it is a list to read, not a
rule to enforce.
"""

import sys

from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.units.unit_control import UnitControl
from microsponge.themes import THEMES

SUCCEEDED = 0
FAILED = 1
# Most units should be gone after at most this many attacks by any unit that can hit them, and none after just this many.
MOST_ATTACKS = 10
ONE_ATTACK = 1
NO_ATTACK_POINTS = 0
CANNOT_HIT = '-'
CORNER = ''
COLUMN_GAP = '  '
NAME_SEPARATOR = ', '
USAGE_LINE = 'name one theme: {themes}'
NO_FIGHTERS_LINE = 'no unit of {theme} has attack points yet'
NO_CLASS_LINE = 'left out, with no class of unit yet: {units}'
TITLE_LINE = 'attacks a unit of {theme} needs, each row against each column:'
ONE_ATTACK_LINE = 'gone after one attack: {defender}, attacked by {attacker}'
SLOW_LINE = 'takes more than {most} attacks: {defender}, attacked by {attacker} ({attacks} attacks)'
NOTHING_OUTSIDE_LINE = 'every unit is gone after {least} to {most} attacks by every unit that can hit it'
BLANK_LINE = ''


def theme_called(name):
    """Return the theme whose name as people read it is name, or None."""
    for theme in THEMES:
        if shown_name(theme) == name:
            return theme
    return None


def theme_names():
    return NAME_SEPARATOR.join(shown_name(theme) for theme in THEMES)


def classed(theme):
    """Return the kinds of unit of a theme whose class of unit is decided."""
    return [unit for unit in theme.UNITS if unit.DOMAIN is not None]


def unclassed(theme):
    """Return the kinds of unit of a theme whose class of unit is not decided yet."""
    return [unit for unit in theme.UNITS if unit.DOMAIN is None]


def fighters(theme):
    """Return the kinds of unit of a theme that have attack points, against air units or against the rest, and a class of unit."""
    return [unit for unit in classed(theme) if unit.ATTACK > NO_ATTACK_POINTS or unit.AIR_ATTACK]


def attacks_table(theme):
    """Return the attacks each fighter of a theme needs against each classed kind of unit: {(attacker, defender): attacks}, with None where the attacker cannot hit."""
    return {(attacker, defender): UnitControl.attacks_to_kill(attacker=attacker, defender=defender) for attacker in fighters(theme) for defender in classed(theme)}


def one_attack_kills(theme):
    """Return each (attacker, defender) of a theme where one attack is enough."""
    return [pair for pair, attacks in attacks_table(theme).items() if attacks == ONE_ATTACK]


def slow_kills(theme):
    """Return each (attacker, defender, attacks) of a theme where the attacker needs more attacks than the user wants."""
    return [(attacker, defender, attacks) for (attacker, defender), attacks in attacks_table(theme).items() if attacks is not None and attacks > MOST_ATTACKS]


def shown_attacks(attacks):
    return CANNOT_HIT if attacks is None else str(attacks)


def table_lines(theme):
    """Return the table of a theme as lines of text, with the columns lined up."""
    table = attacks_table(theme)
    heading = [CORNER] + [shown_name(defender) for defender in classed(theme)]
    rows = [[shown_name(attacker)] + [shown_attacks(table[(attacker, defender)]) for defender in classed(theme)] for attacker in fighters(theme)]
    widths = [max(len(row[column]) for row in [heading] + rows) for column in range(len(heading))]
    return [lined_up(cells=row, widths=widths) for row in [heading] + rows]


def lined_up(*, cells, widths):
    """Return one row of the table: the name at the left, and each number at the right of its column."""
    name = cells[0].ljust(widths[0])
    numbers = [cell.rjust(width) for cell, width in zip(cells[1:], widths[1:])]
    return COLUMN_GAP.join([name] + numbers)


def outside_lines(theme):
    """Return a line for each pair of a theme outside what the user wants, or one line saying there is none."""
    lines = [ONE_ATTACK_LINE.format(attacker=shown_name(attacker), defender=shown_name(defender)) for attacker, defender in one_attack_kills(theme)]
    for attacker, defender, attacks in slow_kills(theme):
        lines.append(SLOW_LINE.format(most=MOST_ATTACKS, attacker=shown_name(attacker), defender=shown_name(defender), attacks=attacks))
    return lines or [NOTHING_OUTSIDE_LINE.format(least=ONE_ATTACK + 1, most=MOST_ATTACKS)]


def report(theme):
    """Return everything the tool says about a theme, as lines of text."""
    if not fighters(theme):
        return [NO_FIGHTERS_LINE.format(theme=shown_name(theme))]
    lines = [TITLE_LINE.format(theme=shown_name(theme)), BLANK_LINE, *table_lines(theme), BLANK_LINE, *outside_lines(theme)]
    if unclassed(theme):
        lines += [BLANK_LINE, NO_CLASS_LINE.format(units=NAME_SEPARATOR.join(shown_name(unit) for unit in unclassed(theme)))]
    return lines


def main(arguments):
    theme = theme_called(arguments[0]) if len(arguments) == 1 else None
    if theme is None:
        print(USAGE_LINE.format(themes=theme_names()))
        return FAILED
    for line in report(theme):
        print(line)
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
