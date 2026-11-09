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

"""Tests for the tool that shows how the units of a theme stand against each other in a fight."""

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

from later_caveman import later_caveman
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit
from microsponge.engine.units.unit_control import UnitControl
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.classic import units as classic_units
from microsponge.themes.classic.theme import Classic
from microsponge.themes.scifi.theme import SciFi

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / 'tools' / 'balance.py'
TOOL_NAME = 'balance'
NO_SUCH_THEME = 'atlantis'


class Mouse(LandUnit):
    """A unit whose attack is chip damage against everything."""

    ATTACK = 1
    HIT_POINTS = 10


class Mammoth(LandUnit):
    """A unit that finishes a mouse at once, and takes a mouse a great many attacks."""

    ATTACK = 50
    HIT_POINTS = 100


class Sparrow(AirUnit):
    """An air unit with no attack points, which no land unit can hit."""


class Rabbit(LandUnit):
    """A unit with no attack points, which is fair game for a mouse."""

    HIT_POINTS = 5


SMALL_THEME = later_caveman({Category.UNITS: (Mouse, Mammoth, Sparrow, Rabbit)})
EVEN_THEME = later_caveman({Category.UNITS: (Mouse, Rabbit)})


def load_tool():
    """Return the tool as a module. The tools are scripts, not a package, so the tool is loaded from its file."""
    spec = importlib.util.spec_from_file_location(TOOL_NAME, TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBalance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def printed_by(self, arguments):
        """Run the tool and return (what it returned, the lines it printed)."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            returned = self.tool.main(arguments)
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
        self.assertEqual(returned, self.tool.SUCCEEDED)
        self.assertEqual(lines[-1], self.tool.NO_CLASS_LINE.format(units=self.tool.NAME_SEPARATOR.join(shown_name(unit) for unit in unclassed)))
        self.assertEqual(self.tool.unclassed(Caveman), [])

    def test_a_unit_with_attack_points_only_against_air_units_attacks(self):
        slingers = [unit for unit in Caveman.UNITS if unit.AIR_ATTACK]
        self.assertTrue(slingers)
        self.assertLessEqual(set(slingers), set(self.tool.fighters(Caveman)))

    def test_the_table_holds_the_attacks_each_attacker_needs_against_every_unit_and_none_where_it_cannot_hit(self):
        table = self.tool.attacks_table(SMALL_THEME)
        self.assertEqual(set(table), {(attacker, defender) for attacker in (Mouse, Mammoth) for defender in SMALL_THEME.UNITS})
        for (attacker, defender), attacks in table.items():
            with self.subTest(attacker=attacker, defender=defender):
                self.assertEqual(attacks, UnitControl.attacks_to_kill(attacker=attacker, defender=defender))
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
        heading = lines[2]
        for unit in SMALL_THEME.UNITS:
            self.assertIn(shown_name(unit), heading)
        mouse_row = lines[3].split()
        self.assertEqual(mouse_row, [shown_name(Mouse), str(Mouse.HIT_POINTS), str(Mammoth.HIT_POINTS), self.tool.CANNOT_HIT, str(Rabbit.HIT_POINTS)])
        self.assertIn(self.tool.ONE_ATTACK_LINE.format(attacker=shown_name(Mammoth), defender=shown_name(Mouse)), lines)
        self.assertIn(self.tool.SLOW_LINE.format(most=self.tool.MOST_ATTACKS, attacker=shown_name(Mouse), defender=shown_name(Mammoth), attacks=Mammoth.HIT_POINTS), lines)

    def test_a_theme_with_nothing_outside_what_the_user_wants_says_so(self):
        expected = self.tool.NOTHING_OUTSIDE_LINE.format(least=self.tool.ONE_ATTACK + 1, most=self.tool.MOST_ATTACKS)
        self.assertEqual(self.tool.report(EVEN_THEME)[-1], expected)

    def test_the_tool_reports_on_the_theme_it_is_given(self):
        returned, lines = self.printed_by([shown_name(Caveman)])
        self.assertEqual(returned, self.tool.SUCCEEDED)
        self.assertEqual(lines, self.tool.report(Caveman))
        self.assertEqual(lines[0], self.tool.TITLE_LINE.format(theme=shown_name(Caveman)))

    def test_a_theme_whose_units_have_no_attack_points_yet_says_so(self):
        returned, lines = self.printed_by([shown_name(SciFi)])
        self.assertEqual(returned, self.tool.SUCCEEDED)
        self.assertEqual(lines, [self.tool.NO_FIGHTERS_LINE.format(theme=shown_name(SciFi))])

    def test_no_theme_or_a_theme_that_does_not_exist_lists_the_themes(self):
        for arguments in ([], [NO_SUCH_THEME], [shown_name(Caveman), shown_name(Classic)]):
            with self.subTest(arguments=arguments):
                returned, lines = self.printed_by(arguments)
                self.assertEqual(returned, self.tool.FAILED)
                self.assertEqual(lines, [self.tool.USAGE_LINE.format(themes=self.tool.theme_names())])
