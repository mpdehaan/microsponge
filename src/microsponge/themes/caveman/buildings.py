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

"""The caveman buildings and world wonders."""

from microsponge.engine.kinds.building import Building, Wonder
from microsponge.themes.caveman.resources import Currency, Flint, Food, Stone
from microsponge.themes.caveman.technologies import Agriculture, Discipline, Fire
from microsponge.themes.caveman.terrains import Grassland


class Granary(Building):
    REQUIRES = (Agriculture,)
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 1}
    WORKED_TILE_BONUS = {Grassland: {Food: 1}}
    GROWS_SOONER = 1


class Barracks(Building):
    REQUIRES = (Discipline,)
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 1}
    LEVEL_BONUS = 1


class Harbor(Building):
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 1}
    BESIDE_WATER = True


class Watchtower(Building):
    REQUIRES = (Fire, Flint)
    COST = {Currency: 20}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 1}
    ARMOR_BONUS = 1


class GreatCavePainting(Wonder):
    COST = {Currency: 40}
    BUILD_TURNS = 8
    SUPPORT = {Currency: 1}
    RESEARCH_POINTS = 2


class ArrangementOfRocks(Wonder):
    COST = {Currency: 20, Stone: 50}
    BUILD_TURNS = 10
    SUPPORT = {Currency: 1}
    PRODUCES = {Currency: 2}
    ACTION_POINTS = 1
