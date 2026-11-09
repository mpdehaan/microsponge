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

"""The base of a theme's terrains: what a tile of the map is."""

from microsponge.engine.kinds.kind import Kind


class Terrain(Kind):
    """What a tile is, like grassland or mountains."""

    # Land, or else water.
    LAND = True
    # Water that is not salt, which a tile next to it can be watered from.
    FRESH_WATER = False
    # The action points it costs a unit to move onto a tile of this terrain.
    MOVE_COST = 1
    # What a tile of this terrain gives the citizen who works it each turn: each resource with its amount. A tile never runs out.
    GIVES = {}
    # The strategic resources a tile of this terrain can have. Several terrains can list the same one.
    CAN_HAVE = ()
    # Whether land units can be on a tile of this terrain. A tar pit sets this False.
    CROSSED_BY_LAND_UNITS = True
    # Whether anything can be built on a tile of this terrain: a city center over it, an improvement, or work that changes the terrain.
    BUILDABLE = True
