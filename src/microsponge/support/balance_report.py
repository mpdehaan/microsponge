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

"""How the units of a theme stand against each other in a fight, as the report `tools/balance.py` prints and the guide of a theme shows.

The report is four tables, each with a title that says what it holds and a heading row that
names every column. The first lists each unit that can attack, with its dice, its armor class, its
hit points and its experience worth. The second is the attacks table: each row is an attacker,
each column is a defender, and the number is how many attacks the attacker needs, on average
rolls, to take every hit point off a whole level 1 unit of the defender's kind; a dash says that
the attacker cannot hit that kind at all. Nothing healed between the attacks is counted, and
neither is striking back. The third lists the pairs outside what the user wants of a theme, a
defender gone after one attack or still standing after 10, with a note saying which. The fourth
says, for each attacker, how a level 20 unit stands against a level 1 unit of the same kind,
which the user wants to be only about half again as strong. A kind of unit whose class of unit,
land, sea, air or space, is not decided yet is left out of the tables and named at the end,
since what can hit it is unknown.
"""

from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.units.levels import FIRST_LEVEL, LAST_LEVEL
from microsponge.engine.units.unit_control import UnitControl
from microsponge.support.tables import shown_kinds, table_lines
from microsponge.ui_strings import (
    MSG_BALANCE_ATTACKS_CORNER, MSG_BALANCE_ATTACKS_TITLE, MSG_BALANCE_KINDS_HEADING, MSG_BALANCE_KINDS_TITLE, MSG_BALANCE_LEVELS_HEADING, MSG_BALANCE_LEVELS_TITLE,
    MSG_BALANCE_NO_CLASS, MSG_BALANCE_NO_FIGHTERS, MSG_BALANCE_NOTHING_OUTSIDE, MSG_BALANCE_ONE_ATTACK_NOTE, MSG_BALANCE_OUTSIDE_HEADING, MSG_BALANCE_OUTSIDE_TITLE,
    MSG_BALANCE_SLOW_NOTE, MSG_NONE_MARK,
)

# Most units should be gone after at most this many attacks by any unit that can hit them, and none after just this many.
MOST_ATTACKS = 10
ONE_ATTACK = 1
NO_ATTACK_POINTS = 0
CANNOT_HIT = MSG_NONE_MARK
BLANK_LINE = ''


def classed(theme):
    """Return the kinds of unit of a theme whose class of unit is decided."""
    return [unit for unit in theme.UNITS if unit.DOMAIN is not None]


def unclassed(theme):
    """Return the kinds of unit of a theme whose class of unit is not decided yet."""
    return [unit for unit in theme.UNITS if unit.DOMAIN is None]


def fighters(theme):
    """Return the kinds of unit of a theme that have attack dice, against every unit or only against some class of unit, and a class of unit."""
    return [unit for unit in classed(theme) if unit.ATTACK.most() > NO_ATTACK_POINTS or unit.EXTRA_DICE]


def attacks_table(theme):
    """Return the attacks each fighter of a theme needs against each classed kind of unit: {(attacker, defender): attacks}, with None where the attacker cannot hit."""
    return {(attacker, defender): UnitControl.attacks_to_kill(theme=theme, attacker=attacker, defender=defender) for attacker in fighters(theme) for defender in classed(theme)}


def kind_rows(theme):
    """Return a row for each fighter of a theme: its name, its dice, its armor class, its hit points and its experience worth."""
    return [[shown_name(unit), unit.ATTACK.shown(), str(unit.ARMOR_CLASS), str(unit.HIT_POINTS), str(unit.EXPERIENCE_WORTH)] for unit in fighters(theme)]


def level_rows(theme):
    """Return a row for each fighter of a theme that can hit its own kind: its name, the attacks a unit at the last level needs against one at the first, and the other way round."""
    rows = []
    for unit in fighters(theme):
        veteran = UnitControl.attacks_to_kill(theme=theme, attacker=unit, defender=unit, attacker_level=LAST_LEVEL)
        recruit = UnitControl.attacks_to_kill(theme=theme, attacker=unit, defender=unit, defender_level=LAST_LEVEL)
        if veteran is not None:
            rows.append([shown_name(unit), str(veteran), str(recruit)])
    return rows


def one_attack_kills(theme):
    """Return each (attacker, defender) of a theme where one attack is enough."""
    return [pair for pair, attacks in attacks_table(theme).items() if attacks == ONE_ATTACK]


def slow_kills(theme):
    """Return each (attacker, defender, attacks) of a theme where the attacker needs more attacks than the user wants."""
    return [(attacker, defender, attacks) for (attacker, defender), attacks in attacks_table(theme).items() if attacks is not None and attacks > MOST_ATTACKS]


def shown_attacks(attacks):
    return CANNOT_HIT if attacks is None else str(attacks)


def attack_rows(theme):
    """Return a row for each attacker of a theme: its name, then the attacks it needs against each classed kind, or a dash."""
    table = attacks_table(theme)
    return [[shown_name(attacker)] + [shown_attacks(table[(attacker, defender)]) for defender in classed(theme)] for attacker in fighters(theme)]


def outside_rows(theme):
    """Return a row for each pair of a theme outside what the user wants: the attacker, the defender, the attacks and a note saying which way the pair is outside."""
    rows = [[shown_name(attacker), shown_name(defender), str(ONE_ATTACK), MSG_BALANCE_ONE_ATTACK_NOTE] for attacker, defender in one_attack_kills(theme)]
    for attacker, defender, attacks in slow_kills(theme):
        rows.append([shown_name(attacker), shown_name(defender), str(attacks), MSG_BALANCE_SLOW_NOTE.format(most=MOST_ATTACKS)])
    return rows


def report(theme, *, markdown=False):
    """Return everything the tool says about a theme, as lines of text or of Markdown: the four tables, and the kinds left out."""
    if not fighters(theme):
        return [MSG_BALANCE_NO_FIGHTERS.format(theme=shown_name(theme))]
    outside = outside_rows(theme)
    lines = table_lines(title=MSG_BALANCE_KINDS_TITLE.format(theme=shown_name(theme)), heading=MSG_BALANCE_KINDS_HEADING, rows=kind_rows(theme), markdown=markdown)
    lines += [BLANK_LINE, *table_lines(title=MSG_BALANCE_ATTACKS_TITLE.format(cannot=CANNOT_HIT), heading=[MSG_BALANCE_ATTACKS_CORNER] + [shown_name(defender) for defender in classed(theme)], rows=attack_rows(theme), markdown=markdown)]
    if outside:
        lines += [BLANK_LINE, *table_lines(title=MSG_BALANCE_OUTSIDE_TITLE.format(most=MOST_ATTACKS), heading=MSG_BALANCE_OUTSIDE_HEADING, rows=outside, markdown=markdown)]
    else:
        lines += [BLANK_LINE, MSG_BALANCE_OUTSIDE_TITLE.format(most=MOST_ATTACKS), MSG_BALANCE_NOTHING_OUTSIDE.format(least=ONE_ATTACK + 1, most=MOST_ATTACKS)]
    levels_heading = [column.format(last=LAST_LEVEL, first=FIRST_LEVEL) for column in MSG_BALANCE_LEVELS_HEADING]
    lines += [BLANK_LINE, *table_lines(title=MSG_BALANCE_LEVELS_TITLE.format(last=LAST_LEVEL, first=FIRST_LEVEL), heading=levels_heading, rows=level_rows(theme), markdown=markdown)]
    if unclassed(theme):
        lines += [BLANK_LINE, MSG_BALANCE_NO_CLASS.format(units=shown_kinds(unclassed(theme)))]
    return lines

