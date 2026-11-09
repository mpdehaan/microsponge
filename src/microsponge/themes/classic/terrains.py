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

"""The terrains of classic."""

from microsponge.engine.kinds.terrain import Terrain
from microsponge.themes.classic.resources import Gold, Iron, Uranium


class Grassland(Terrain):
    pass


class Desert(Terrain):
    pass


class Mountains(Terrain):
    CAN_HAVE = (Iron, Gold, Uranium)


class River(Terrain):
    LAND = False
    FRESH_WATER = True


class Lake(Terrain):
    LAND = False
    FRESH_WATER = True


class Ocean(Terrain):
    LAND = False
