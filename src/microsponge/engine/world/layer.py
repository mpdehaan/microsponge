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

"""The layers of a world, each with a number of its own that never changes."""

from microsponge.engine.kinds.category import Category


class Layer:
    """One fact about every tile. A saved game calls a layer by its number, so a number is never reused.

    When a feature is taken out, its layer's number is retired: it moves from LAYERS to
    RETIRED_LAYERS and is never given to another layer.
    """

    # The id of each tile's terrain, in the catalog's terrains.
    TERRAIN = 1
    # The id of the unit on each tile, or NOTHING.
    UNIT = 2
    # The id of the city whose city radius each tile belongs to, or NOTHING.
    CITY = 3
    # The id of the city whose city center covers each tile, or NOTHING.
    CITY_CENTER = 4
    # The id of the improvement built on each tile, in the catalog's improvements, or NOTHING.
    IMPROVEMENT = 5
    # The id of the strategic resource on each tile, in the catalog's resources, or NOTHING.
    STRATEGIC_RESOURCE = 6
    # The id of the terrain bonus on each tile, in the catalog's terrain bonuses, or NOTHING.
    TERRAIN_BONUS = 7


LAYERS = (Layer.TERRAIN, Layer.UNIT, Layer.CITY, Layer.CITY_CENTER, Layer.IMPROVEMENT, Layer.STRATEGIC_RESOURCE, Layer.TERRAIN_BONUS)
RETIRED_LAYERS = ()
# The layers that hold ids of a theme's kinds, which loading a saved game may have to renumber.
LAYER_CATEGORIES = {Layer.TERRAIN: Category.TERRAINS, Layer.IMPROVEMENT: Category.IMPROVEMENTS, Layer.STRATEGIC_RESOURCE: Category.RESOURCES, Layer.TERRAIN_BONUS: Category.TERRAIN_BONUSES}
