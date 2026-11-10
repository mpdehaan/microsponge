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

"""The traits of a computer-played civilization: eight numbers from 0 to 100 that make its personality (the model, "Traits").

The traits are dealt as points: of the 800 points the eight traits could hold together, a
civilization gets between 40 and 60 percent, spread at random over its traits with no trait
above 100. The named tendencies, like campaigner, are settings of the eight numbers that are
then nudged a little at random, so that two campaigners are not the same player.
"""

from microsponge.err_messages import ERR_NO_SUCH_TRAIT, ERR_TRAIT_VALUE
from microsponge.ui_strings import (
    MSG_TRAIT_AGGRESSIVE_HYPERFOCUS, MSG_TRAIT_BOLDNESS, MSG_TRAIT_CONQUEST, MSG_TRAIT_ECONOMICS, MSG_TRAIT_EXPANSION, MSG_TRAIT_GRUDGE, MSG_TRAIT_PEACE,
    MSG_TRAIT_SCIENCE,
)

# The traits, by the names the screens and the saved game use.
EXPANSION = MSG_TRAIT_EXPANSION
BOLDNESS = MSG_TRAIT_BOLDNESS
GRUDGE = MSG_TRAIT_GRUDGE
AGGRESSIVE_HYPERFOCUS = MSG_TRAIT_AGGRESSIVE_HYPERFOCUS
SCIENCE = MSG_TRAIT_SCIENCE
PEACE = MSG_TRAIT_PEACE
CONQUEST = MSG_TRAIT_CONQUEST
ECONOMICS = MSG_TRAIT_ECONOMICS
TRAITS = (EXPANSION, BOLDNESS, GRUDGE, AGGRESSIVE_HYPERFOCUS, SCIENCE, PEACE, CONQUEST, ECONOMICS)
LEAST = 0
MOST = 100
MIDDLE = 50
# The share of all the points the traits could hold that a civilization is dealt, at least and at most, in percent.
LEAST_DEALT_PERCENT = 40
MOST_DEALT_PERCENT = 60
WHOLE = 100
# How far a named tendency's numbers are nudged each way.
NUDGE = 10

# The named tendencies: what the model calls logical and strategic, campaigner and peaceful builder. Claude chose the numbers.
LOGICAL = {**{trait: MIDDLE for trait in TRAITS}, SCIENCE: 70}
CAMPAIGNER = {**{trait: MIDDLE for trait in TRAITS}, BOLDNESS: 80, AGGRESSIVE_HYPERFOCUS: 90, PEACE: 10}
PEACEFUL_BUILDER = {**{trait: MIDDLE for trait in TRAITS}, EXPANSION: 80, PEACE: 90, BOLDNESS: 20}
TENDENCIES = (LOGICAL, CAMPAIGNER, PEACEFUL_BUILDER)


def check_trait(trait):
    if trait not in TRAITS:
        raise ValueError(ERR_NO_SUCH_TRAIT.format(trait=trait))
    return trait


def check_value(value):
    if type(value) is not int or not LEAST <= value <= MOST:
        raise ValueError(ERR_TRAIT_VALUE.format(least=LEAST, most=MOST, value=value))
    return value


def clamped(value):
    return max(LEAST, min(MOST, value))


class Traits:
    """The personality of one computer-played civilization, as a number for each trait."""

    __slots__ = ('_values',)

    def __init__(self, values):
        self._values = {trait: LEAST for trait in TRAITS}
        for trait, value in values.items():
            self.set(trait=trait, value=value)

    def get(self, trait):
        return self._values[check_trait(trait)]

    def set(self, *, trait, value):
        self._values[check_trait(trait)] = check_value(value)

    def get_values(self):
        """Return every trait with its value, in the traits' order."""
        return dict(self._values)

    def total(self):
        return sum(self._values.values())

    def favors(self, *, trait, random):
        """Return whether a trait wins a draw: a trait of 70 wins 70 times in 100, so that the trait tips a decision without deciding it every time."""
        return random.randrange(WHOLE) < self._values[trait]

    @classmethod
    def dealt(cls, random):
        """Return traits dealt at random: 40 to 60 percent of all the points there could be, spread one at a time over the traits, no trait above MOST."""
        could_hold = MOST * len(TRAITS)
        points = random.randint(could_hold * LEAST_DEALT_PERCENT // WHOLE, could_hold * MOST_DEALT_PERCENT // WHOLE)
        values = {trait: LEAST for trait in TRAITS}
        while points > 0:
            trait = random.choice([trait for trait in TRAITS if values[trait] < MOST])
            values[trait] += 1
            points -= 1
        return cls(values)

    @classmethod
    def tending_to(cls, *, tendency, random):
        """Return the traits of a named tendency, each number nudged up to NUDGE each way at random."""
        return cls({trait: clamped(value + random.randint(-NUDGE, NUDGE)) for trait, value in tendency.items()})

    def to_data(self):
        return dict(self._values)

    @classmethod
    def from_data(cls, data):
        return cls(data)
