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
from microsponge.engine.kinds.control_points import Command, Policy
from microsponge.themes.caveman.resources import Currency, Flint, Food, Ivory, Stone, Wood
from microsponge.themes.caveman.technologies import Astrology, Barter, Carpentry, ChurchOfTheCaveBear, Discipline, Fire, Leadership, Sewing
from microsponge.themes.caveman.terrains import Grassland


class Granary(Building):
    REQUIRES = (Sewing,)
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 2}
    WORKED_TILE_BONUS = {Grassland: {Food: 1}}
    GROWS_SOONER = 2


class Barracks(Building):
    REQUIRES = (Discipline,)
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 2}
    LEVEL_BONUS = 1


class Harbor(Building):
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 2}
    BESIDE_WATER = True


class Watchtower(Building):
    REQUIRES = (Fire, Flint)
    COST = {Currency: 20}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 2}
    ARMOR_BONUS = 2
    CONTROL_POINTS = {Command: 5}


class ChieftainsHut(Building):
    NAME = "chieftain's hut"
    REQUIRES = (Leadership,)
    COST = {Currency: 20}
    BUILD_TURNS = 4
    SUPPORT = {Currency: 2}
    CONTROL_POINTS = {Policy: 2}


class CityWalls(Building):
    REQUIRES = (Carpentry,)
    COST = {Currency: 20, Wood: 20, Stone: 30}
    BUILD_TURNS = 6
    SUPPORT = {Currency: 2}
    ARMOR_BONUS = 1
    WALLS = True


class CaveBearShrine(Building):
    REQUIRES = (ChurchOfTheCaveBear,)
    COST = {Currency: 30, Stone: 10}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 2}
    RESEARCH_POINTS = 2


class TradingPost(Building):
    REQUIRES = (Barter, Ivory)
    COST = {Currency: 30}
    BUILD_TURNS = 5
    SUPPORT = {Currency: 2}
    INCOME_BONUS = 10


class GreatCavePainting(Wonder):
    COST = {Currency: 120}
    BUILD_TURNS = 16
    SUPPORT = {Currency: 2}
    RESEARCH_POINTS = 4
    CONTROL_POINTS = {Policy: 2}
    INCOME_BONUS = 10


class ArrangementOfRocks(Wonder):
    REQUIRES = (Astrology,)
    COST = {Currency: 60, Stone: 30}
    BUILD_TURNS = 16
    SUPPORT = {Currency: 2}
    PRODUCES = {Currency: 2}
    CONTROL_POINTS = {Policy: 3, Command: 3}
    ARMOR_BONUS = 1
    UNIT_SUPPORT_DISCOUNT = {Currency: 1}
