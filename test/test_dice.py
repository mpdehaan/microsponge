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

"""The dice a unit's attack is written as."""

import random
import unittest

from microsponge.engine.kinds.dice import NO_DICE, Dice
from microsponge.ui_strings import MSG_DICE, MSG_DICE_PLUS, MSG_FIXED_ROLL

A_SEED = 11
MANY_ROLLS = 200
TWO_D_SIX = Dice(count=2, sides=6)
TWO_D_SIX_PLUS_FOUR = Dice(count=2, sides=6, plus=4)
ONE_D_SIX = Dice(count=1, sides=6)


class TestDice(unittest.TestCase):

    def test_dice_are_a_count_a_number_of_sides_and_a_number_added_which_is_0_unless_given(self):
        self.assertEqual((TWO_D_SIX.count, TWO_D_SIX.sides, TWO_D_SIX.plus), (2, 6, 0))
        self.assertEqual(TWO_D_SIX_PLUS_FOUR.plus, 4)
        self.assertEqual(TWO_D_SIX, Dice(count=2, sides=6, plus=0))

    def test_the_least_the_most_and_the_average_roll(self):
        self.assertEqual((TWO_D_SIX.least(), TWO_D_SIX.most(), TWO_D_SIX.average()), (2, 12, 7))
        self.assertEqual((TWO_D_SIX_PLUS_FOUR.least(), TWO_D_SIX_PLUS_FOUR.most(), TWO_D_SIX_PLUS_FOUR.average()), (6, 16, 11))
        self.assertEqual(ONE_D_SIX.average(), 3.5)
        self.assertEqual((NO_DICE.least(), NO_DICE.most(), NO_DICE.average()), (0, 0, 0))

    def test_a_roll_stays_between_the_least_and_the_most_and_reaches_both(self):
        source = random.Random(A_SEED)
        rolls = [TWO_D_SIX_PLUS_FOUR.roll(random=source) for _ in range(MANY_ROLLS)]
        self.assertTrue(all(TWO_D_SIX_PLUS_FOUR.least() <= roll <= TWO_D_SIX_PLUS_FOUR.most() for roll in rolls))
        self.assertEqual((min(rolls), max(rolls)), (TWO_D_SIX_PLUS_FOUR.least(), TWO_D_SIX_PLUS_FOUR.most()))
        self.assertEqual(NO_DICE.roll(random=source), 0)

    def test_the_same_seed_rolls_the_same_numbers(self):
        first = [TWO_D_SIX.roll(random=random.Random(A_SEED)) for _ in range(1)]
        second = [TWO_D_SIX.roll(random=random.Random(A_SEED)) for _ in range(1)]
        self.assertEqual(first, second)

    def test_extra_dice_and_extra_points_make_new_dice_and_leave_the_old_as_they_were(self):
        self.assertEqual(TWO_D_SIX.with_extra(dice=1), Dice(count=3, sides=6))
        self.assertEqual(TWO_D_SIX.with_extra(plus=4), TWO_D_SIX_PLUS_FOUR)
        self.assertEqual(TWO_D_SIX.with_extra(dice=1, plus=1), Dice(count=3, sides=6, plus=1))
        self.assertEqual(TWO_D_SIX.with_extra(), TWO_D_SIX)
        self.assertEqual(TWO_D_SIX, Dice(count=2, sides=6))

    def test_dice_are_shown_as_people_read_them(self):
        self.assertEqual(TWO_D_SIX.shown(), MSG_DICE.format(count=2, sides=6))
        self.assertEqual(TWO_D_SIX_PLUS_FOUR.shown(), MSG_DICE_PLUS.format(count=2, sides=6, plus=4))
        self.assertEqual(NO_DICE.shown(), MSG_FIXED_ROLL.format(plus=0))
        self.assertEqual(Dice(count=0, sides=0, plus=5).shown(), MSG_FIXED_ROLL.format(plus=5))

    def test_dice_cannot_be_changed_once_made(self):
        with self.assertRaises(AttributeError):
            TWO_D_SIX.count = 3
