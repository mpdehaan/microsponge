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

"""The base of a theme's improvements: what a unit builds on a tile."""

from microsponge.engine.kinds.kind import Kind


class Improvement(Kind):
    """Something a unit builds on a tile, like a farm, which an enemy unit can destroy, or work that changes the tile's terrain, like cutting trees."""

    # The terrains it can be built on.
    ON = ()
    # The turns a unit takes to build it, during which the unit cannot move.
    BUILD_TURNS = 1
    # What it adds to what its tile gives: each resource with its amount.
    TILE_BONUS = {}
    # The terrain its tile becomes when the work is done, for work that changes the land and leaves nothing on the tile. None for an improvement that stays.
    BECOMES = None
