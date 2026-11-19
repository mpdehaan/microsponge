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

"""How a caveman world is made."""

from microsponge.engine.kinds.map_spec import MapSpec
from microsponge.themes.caveman.terrains import Forest, Grassland, Mountains, Tarpit, Water


class CavemanMap(MapSpec):
    BASE_TERRAIN = Grassland
    TERRAIN_PERCENT = {Water: 15, Forest: 15, Mountains: 8, Tarpit: 1}
