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

"""The base of a theme's map spec: the constants that say how the map generator makes a world for the theme."""


class MapSpec:
    """How a world of the theme is made. A theme subclasses it and sets what differs, and names its class as the theme's MAP.

    The generator fills the world with BASE_TERRAIN, then grows patches of each terrain in
    TERRAIN_PERCENT until each covers its percent of the tiles, then scatters the strategic
    resources and the terrain bonuses. A theme with no BASE_TERRAIN cannot have its worlds made yet.
    """

    # The terrain every tile starts as, or None for a theme whose maps cannot be made yet.
    BASE_TERRAIN = None
    # The other terrains, each with the percent of the tiles it covers.
    TERRAIN_PERCENT = {}
    # About how many tiles one patch of a terrain grows to.
    PATCH_SIZE = 12
    # The percent of the tiles that can have a strategic resource that are given one.
    STRATEGIC_PERCENT = 10
    # The percent of the tiles that a terrain bonus can be on that are given one, for each terrain bonus.
    TERRAIN_BONUS_PERCENT = 2
    # The size of a world the generator makes when asked for none in particular, in tiles.
    WIDTH = 80
    HEIGHT = 40
