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

"""The base of a theme's terrain bonuses: a special tile that gives more when it is worked."""

from microsponge.engine.kinds.kind import Kind


class TerrainBonus(Kind):
    """Something on a tile that adds to what the tile gives the citizen who works it, like cows on grassland. It is not a strategic resource.

    A bonus has a list of compatible terrains, usually one. When the tile's terrain changes
    to one that is not compatible, the bonus is gone for good.
    """

    # The terrains a tile with this bonus can be, usually one.
    ON = ()
    # What it adds to what its tile gives: each resource with its amount.
    GIVES = {}
