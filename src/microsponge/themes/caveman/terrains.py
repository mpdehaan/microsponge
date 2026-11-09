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

"""What the caveman world is made of."""

from microsponge.engine.kinds.terrain import Terrain
from microsponge.themes.caveman.resources import Flint, Food, Stone, Wood


class Grassland(Terrain):
    GIVES = {Food: 2}


class Mountains(Terrain):
    MOVE_COST = 2
    GIVES = {Stone: 1}
    CAN_HAVE = (Flint,)


class Forest(Terrain):
    MOVE_COST = 2
    GIVES = {Wood: 1}


class Water(Terrain):
    LAND = False
    GIVES = {Food: 1}


class Tarpit(Terrain):
    CROSSED_BY_LAND_UNITS = False
    BUILDABLE = False
