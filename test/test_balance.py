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

"""Tests for the report that shows how the units of a theme stand against each other in a fight, and the tool that prints it."""

import contextlib
import io
import re
import subprocess
import sys
import unittest
from pathlib import Path

from later_caveman import later_caveman
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.dice import Dice
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit
from microsponge.engine.units.levels import FIRST_LEVEL, LAST_LEVEL
from microsponge.engine.units.unit_control import UnitControl
from microsponge.support import balance_report
from microsponge.support.theme_tools import FAILED, MARKDOWN_FLAG, SUCCEEDED, run_theme_tool, theme_names
from microsponge.ui_strings import (
    MSG_BALANCE_ATTACKS_CORNER, MSG_BALANCE_ATTACKS_TITLE, MSG_BALANCE_KINDS_HEADING, MSG_BALANCE_KINDS_TITLE, MSG_BALANCE_LEVELS_HEADING, MSG_BALANCE_LEVELS_TITLE,
    MSG_BALANCE_NO_CLASS, MSG_BALANCE_NO_FIGHTERS, MSG_BALANCE_NOTHING_OUTSIDE, MSG_BALANCE_ONE_ATTACK_NOTE, MSG_BALANCE_OUTSIDE_HEADING, MSG_BALANCE_OUTSIDE_TITLE,
    MSG_BALANCE_SLOW_NOTE, MSG_LIST_SEPARATOR, MSG_MARKDOWN_ROW, MSG_NAME_ONE_THEME,
)
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Warrior
from microsponge.themes.classic import units as classic_units
from microsponge.themes.classic.theme import Classic
from microsponge.themes.scifi.theme import SciFi

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / 'tools' / 'balance.py'
NO_SUCH_THEME = 'atlantis'
TWO_OR_MORE_SPACES = r' {2,}'
A_TITLE = 'a table'
A_WORD = 'ox'
A_LONGER_WORD = 'mammoth'
A_NUMBER = '7'
A_LONGER_NUMBER = '123'


class Mouse(LandUnit):
    """A unit whose attack is chip damage against everything."""

    ATTACK = Dice(count=0, sides=0, plus=1)
    HIT_POINTS = 10


class Mammoth(LandUnit):
    """A unit that finishes a mouse at once, and takes a mouse a great many attacks."""

    ATTACK = Dice(count=0, sides=0, plus=50)
    HIT_POINTS = 100


class Sparrow(AirUnit):
    """An air unit with no attack dice, which no land unit can hit."""


class Rabbit(LandUnit):
    """A unit with no attack dice, which is fair game for a mouse."""

    HIT_POINTS = 5


SMALL_THEME = later_caveman({Category.UNITS: (Mouse, Mammoth, Sparrow, Rabbit)})
EVEN_THEME = later_caveman({Category.UNITS: (Mouse, Rabbit)})


def cells(line):
    """Return the cells of a line of a table, with the padding taken off: the cells are two or more spaces apart, and a word has single spaces inside it."""
    return [cell for cell in re.split(TWO_OR_MORE_SPACES, line.strip()) if cell]


class TestBalance(unittest.TestCase):

    tool = balance_report

    def printed_by(self, arguments):
        """Run the tool's command line and return (what it returned, the lines it printed)."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            returned = run_theme_tool(arguments=arguments, report=balance_report.report)
        return returned, output.getvalue().splitlines()

    def test_the_units_that_attack_are_the_ones_with_attack_points(self):
        self.assertEqual(self.tool.fighters(SMALL_THEME), [Mouse, Mammoth])
        self.assertEqual(self.tool.fighters(Classic), [classic_units.Catapult, classic_units.Cannon, classic_units.Howitzer])
        self.assertEqual(self.tool.fighters(SciFi), [])

    def test_a_kind_of_unit_with_no_class_of_unit_yet_is_left_out_of_the_table_and_named_below_it(self):
        unclassed = self.tool.unclassed(Classic)
        self.assertIn(classic_units.CruiseMissile, unclassed)
        self.assertFalse(set(unclassed) & set(self.tool.classed(Classic)))
        self.assertEqual(set(unclassed) | set(self.tool.classed(Classic)), set(Classic.UNITS))
        table = self.tool.attacks_table(Classic)
        self.assertFalse({defender for _, defender in table} & set(unclassed))
        returned, lines = self.printed_by([shown_name(Classic)])
        self.assertEqual(returned, SUCCEEDED)
        self.assertEqual(lines[-1], MSG_BALANCE_NO_CLASS.format(units=MSG_LIST_SEPARATOR.join(shown_name(unit) for unit in unclassed)))
        self.assertEqual(self.tool.unclassed(Caveman), [])

    def test_a_unit_with_extra_dice_against_air_units_attacks(self):
        slingers = [unit for unit in Caveman.UNITS if unit.EXTRA_DICE]
        self.assertTrue(slingers)
        self.assertLessEqual(set(slingers), set(self.tool.fighters(Caveman)))

    def test_the_table_holds_the_attacks_each_attacker_needs_against_every_unit_and_none_where_it_cannot_hit(self):
        table = self.tool.attacks_table(SMALL_THEME)
        self.assertEqual(set(table), {(attacker, defender) for attacker in (Mouse, Mammoth) for defender in SMALL_THEME.UNITS})
        for (attacker, defender), attacks in table.items():
            with self.subTest(attacker=attacker, defender=defender):
                self.assertEqual(attacks, UnitControl.attacks_to_kill(theme=SMALL_THEME, attacker=attacker, defender=defender))
        self.assertIsNone(table[(Mouse, Sparrow)])
        self.assertEqual(table[(Mouse, Mammoth)], Mammoth.HIT_POINTS)

    def test_the_pairs_outside_what_the_user_wants_are_one_attack_and_more_than_the_most_attacks(self):
        self.assertEqual(self.tool.one_attack_kills(SMALL_THEME), [(Mammoth, Mouse), (Mammoth, Rabbit)])
        self.assertEqual(self.tool.slow_kills(SMALL_THEME), [(Mouse, Mammoth, Mammoth.HIT_POINTS)])
        self.assertGreater(Mammoth.HIT_POINTS, self.tool.MOST_ATTACKS)
        self.assertEqual(self.tool.slow_kills(EVEN_THEME), [])
        self.assertEqual(self.tool.one_attack_kills(EVEN_THEME), [])

    def test_the_report_names_every_unit_and_every_pair_outside_what_the_user_wants(self):
        lines = self.tool.report(SMALL_THEME)
        self.assertEqual(lines[0], MSG_BALANCE_KINDS_TITLE.format(theme=shown_name(SMALL_THEME)))
        self.assertEqual(cells(lines[1]), list(MSG_BALANCE_KINDS_HEADING))
        self.assertEqual(cells(lines[2]), [shown_name(Mouse), Mouse.ATTACK.shown(), str(Mouse.ARMOR_CLASS), str(Mouse.HIT_POINTS), str(Mouse.EXPERIENCE_WORTH)])
        self.assertEqual(lines[5], MSG_BALANCE_ATTACKS_TITLE.format(cannot=self.tool.CANNOT_HIT))
        self.assertEqual(cells(lines[6]), [MSG_BALANCE_ATTACKS_CORNER] + [shown_name(unit) for unit in SMALL_THEME.UNITS])
        self.assertEqual(cells(lines[7]), [shown_name(Mouse), str(Mouse.HIT_POINTS), str(Mammoth.HIT_POINTS), self.tool.CANNOT_HIT, str(Rabbit.HIT_POINTS)])
        self.assertEqual(lines[10], MSG_BALANCE_OUTSIDE_TITLE.format(most=self.tool.MOST_ATTACKS))
        self.assertEqual(cells(lines[11]), list(MSG_BALANCE_OUTSIDE_HEADING))
        self.assertEqual(cells(lines[12]), [shown_name(Mammoth), shown_name(Mouse), str(self.tool.ONE_ATTACK), MSG_BALANCE_ONE_ATTACK_NOTE])
        self.assertEqual(cells(lines[14]), [shown_name(Mouse), shown_name(Mammoth), str(Mammoth.HIT_POINTS), MSG_BALANCE_SLOW_NOTE.format(most=self.tool.MOST_ATTACKS)])
        self.assertEqual(lines[16], MSG_BALANCE_LEVELS_TITLE.format(last=LAST_LEVEL, first=FIRST_LEVEL))
        self.assertEqual(cells(lines[17]), [column.format(last=LAST_LEVEL, first=FIRST_LEVEL) for column in MSG_BALANCE_LEVELS_HEADING])

    def test_a_theme_with_nothing_outside_what_the_user_wants_says_so(self):
        expected = MSG_BALANCE_NOTHING_OUTSIDE.format(least=self.tool.ONE_ATTACK + 1, most=self.tool.MOST_ATTACKS)
        self.assertIn(expected, self.tool.report(EVEN_THEME))

    def test_the_report_says_how_a_unit_at_the_last_level_stands_against_one_at_the_first(self):
        rows = self.tool.level_rows(Caveman)
        self.assertEqual(len(rows), len(self.tool.fighters(Caveman)))
        veteran = UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Warrior, attacker_level=LAST_LEVEL)
        recruit = UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Warrior, defender_level=LAST_LEVEL)
        self.assertLess(veteran, recruit)
        self.assertEqual(rows[0], [shown_name(Warrior), str(veteran), str(recruit)])
        expected = [[shown_name(unit), str(UnitControl.attacks_to_kill(theme=SMALL_THEME, attacker=unit, defender=unit, attacker_level=LAST_LEVEL)), str(UnitControl.attacks_to_kill(theme=SMALL_THEME, attacker=unit, defender=unit, defender_level=LAST_LEVEL))] for unit in (Mouse, Mammoth)]
        self.assertEqual(self.tool.level_rows(SMALL_THEME), expected)

    def test_the_report_comes_as_markdown_when_asked_with_every_table_a_markdown_table(self):
        plain = self.tool.report(SMALL_THEME)
        marked = self.tool.report(SMALL_THEME, markdown=True)
        self.assertNotEqual(plain, marked)
        self.assertTrue(any(line.startswith(MSG_MARKDOWN_ROW[0]) for line in marked))
        self.assertFalse(any(line.startswith(MSG_MARKDOWN_ROW[0]) for line in plain))
        self.assertIn(MSG_BALANCE_KINDS_TITLE.format(theme=shown_name(SMALL_THEME)), marked[0])
        returned, lines = self.printed_by([shown_name(Caveman), MARKDOWN_FLAG])
        self.assertEqual((returned, lines), (SUCCEEDED, self.tool.report(Caveman, markdown=True)))

    def test_the_script_prints_the_report_of_the_theme_named(self):
        run = subprocess.run([sys.executable, str(TOOL_PATH), shown_name(Caveman)], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(run.returncode, SUCCEEDED)
        self.assertEqual(run.stdout.splitlines(), self.tool.report(Caveman))

    def test_the_tool_reports_on_the_theme_it_is_given(self):
        returned, lines = self.printed_by([shown_name(Caveman)])
        self.assertEqual(returned, SUCCEEDED)
        self.assertEqual(lines, self.tool.report(Caveman))
        self.assertEqual(lines[0], MSG_BALANCE_KINDS_TITLE.format(theme=shown_name(Caveman)))

    def test_a_theme_whose_units_have_no_attack_points_yet_says_so(self):
        returned, lines = self.printed_by([shown_name(SciFi)])
        self.assertEqual(returned, SUCCEEDED)
        self.assertEqual(lines, [MSG_BALANCE_NO_FIGHTERS.format(theme=shown_name(SciFi))])

    def test_no_theme_or_a_theme_that_does_not_exist_lists_the_themes(self):
        for arguments in ([], [NO_SUCH_THEME], [shown_name(Caveman), shown_name(Classic)]):
            with self.subTest(arguments=arguments):
                returned, lines = self.printed_by(arguments)
                self.assertEqual(returned, FAILED)
                self.assertEqual(lines, [MSG_NAME_ONE_THEME.format(themes=theme_names(), flag=MARKDOWN_FLAG)])
