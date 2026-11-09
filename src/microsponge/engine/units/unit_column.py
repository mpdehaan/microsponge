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

"""The columns of the units, each with a number of its own that never changes."""

from microsponge.engine.kinds.category import Category


class UnitColumn:
    """One fact about every unit. A saved game calls a column by its number, so a number is never reused.

    A column is retired the way a Layer is: it moves from UNIT_COLUMNS to RETIRED_UNIT_COLUMNS.
    """

    # The id of the unit's kind, in the catalog's units, or NOTHING for a unit that is gone.
    KIND = 1
    # The id of the civilization the unit belongs to.
    OWNER = 2
    # Which world of the game the unit is in, and the tile there. A unit inside a city has the tile in the middle of the city.
    WORLD = 3
    X = 4
    Y = 5
    HIT_POINTS = 6
    # The id of the city the unit is inside, or NOTHING for a unit on a tile of its own.
    CITY = 7
    # The action points the unit has left this turn.
    ACTION_POINTS = 8
    # The id of the improvement the unit is building, in the catalog's improvements, or NOTHING, and the turns the building still takes.
    IMPROVEMENT = 9
    BUILD_TURNS = 10


UNIT_COLUMNS = (
    UnitColumn.KIND, UnitColumn.OWNER, UnitColumn.WORLD, UnitColumn.X, UnitColumn.Y, UnitColumn.HIT_POINTS, UnitColumn.CITY, UnitColumn.ACTION_POINTS,
    UnitColumn.IMPROVEMENT, UnitColumn.BUILD_TURNS,
)
RETIRED_UNIT_COLUMNS = ()
# The columns that hold ids of a theme's kinds, which loading a saved game may have to renumber.
COLUMN_CATEGORIES = {UnitColumn.KIND: Category.UNITS, UnitColumn.IMPROVEMENT: Category.IMPROVEMENTS}
