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

"""The levels of units: what experience a level takes and what a level adds."""

from microsponge.support.numbers import divided_rounding_up

FIRST_LEVEL = 1
LAST_LEVEL = 20
NO_EXPERIENCE = 0
# The experience a level takes is EXPERIENCE_STEP times the triangular number of the levels gained: 10, 30, 60 and so on.
EXPERIENCE_STEP = 10
TRIANGLE_HALVES = 2
# Every DAMAGE_EVERY levels a unit adds 1 to each damage roll, and interlaced with that, every ARMOR_EVERY levels from ARMOR_FROM its armor class gets 1 better: rare, so that a unit at the last level is only about half again as strong.
DAMAGE_EVERY = 10
ARMOR_EVERY = 10
ARMOR_FROM = 5
ONE_POINT = 1
WHOLE = 100


class Levels:
    """The rules for the levels of units, as static methods over a kind, a level and a theme. It is never made into an object."""

    __slots__ = ()

    @staticmethod
    def experience_for(*, level):
        """Return the experience a unit needs to be at a level: 0 for the first level, 10 for the second, 30 for the third."""
        gained = level - FIRST_LEVEL
        return EXPERIENCE_STEP * gained * (gained + 1) // TRIANGLE_HALVES

    @staticmethod
    def level_for(*, experience):
        """Return the level a unit with some experience has reached, never past the last level."""
        level = FIRST_LEVEL
        while level < LAST_LEVEL and experience >= Levels.experience_for(level=level + ONE_POINT):
            level += ONE_POINT
        return level

    @staticmethod
    def damage_bonus(*, level):
        """Return what a level adds to each damage roll: 1 at level 10 and 2 at level 20."""
        return level // DAMAGE_EVERY

    @staticmethod
    def armor_bonus(*, level):
        """Return by how much a level makes the armor class better: 1 at level 5 and 2 at level 15."""
        return max(level - ARMOR_FROM, -ONE_POINT) // ARMOR_EVERY + ONE_POINT if level >= ARMOR_FROM else 0

    @staticmethod
    def extra_hit_points(*, theme, kind, level):
        """Return the hit points a level adds to a kind's: the theme's percent of the kind's hit points for each level gained, rounded down over all of them."""
        return kind.HIT_POINTS * theme.LEVEL_HIT_POINTS_PERCENT * (level - FIRST_LEVEL) // WHOLE

    @staticmethod
    def hit_points(*, theme, kind, level):
        """Return the hit points a whole unit of a kind has at a level."""
        return kind.HIT_POINTS + Levels.extra_hit_points(theme=theme, kind=kind, level=level)

    @staticmethod
    def kill_experience(*, killed, level):
        """Return the experience a kill gives: the worth of the kind killed plus the level of the unit killed."""
        return killed.EXPERIENCE_WORTH + level

    @staticmethod
    def attacks_to_kill(*, hit_points, damage):
        return divided_rounding_up(amount=hit_points, by=damage)
