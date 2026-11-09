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

"""Dice, which a kind of unit's attack is written as, like 2d6 or 2d6+4."""

from dataclasses import dataclass

from microsponge.ui_strings import MSG_DICE, MSG_DICE_PLUS, MSG_FIXED_ROLL

# The least a die shows.
LOWEST_FACE = 1
# A die's average is half of one more than its sides.
HALVES = 2


@dataclass(slots=True, kw_only=True, frozen=True)
class Dice:
    """A count of dice of one kind, plus a number added to the roll: 2d6+4 is count 2, sides 6 and plus 4.

    Stored as three numbers rather than as text, so that code can edit a kind's dice: add a die
    for a bonus against a class of unit, or add to the roll for a level.
    """

    count: int
    sides: int
    plus: int = 0

    def roll(self, *, random):
        """Return one roll of the dice, drawn from a game's random source."""
        return sum(random.randint(LOWEST_FACE, self.sides) for _ in range(self.count)) + self.plus

    def least(self):
        return self.count * LOWEST_FACE + self.plus

    def most(self):
        return self.count * self.sides + self.plus

    def average(self):
        """Return the average roll, which can end in a half: 1d6 averages 3.5."""
        return self.count * (self.sides + LOWEST_FACE) / HALVES + self.plus

    def with_extra(self, *, dice=0, plus=0):
        """Return these dice with more dice of the same kind, or more added to the roll, or both."""
        return Dice(count=self.count + dice, sides=self.sides, plus=self.plus + plus)

    def shown(self):
        """Return the dice as people read them: 2d6, 2d6+4, or just the number when there are no dice."""
        if self.count == 0:
            return MSG_FIXED_ROLL.format(plus=self.plus)
        if self.plus == 0:
            return MSG_DICE.format(count=self.count, sides=self.sides)
        return MSG_DICE_PLUS.format(count=self.count, sides=self.sides, plus=self.plus)


# What a kind of unit that cannot attack rolls: nothing.
NO_DICE = Dice(count=0, sides=0)
