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

"""The caveman theme."""

from microsponge.engine.kinds.theme import Theme
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.buildings import ArrangementOfRocks, Barracks, Granary, GreatCavePainting, Harbor, Watchtower
from microsponge.themes.caveman.improvements import Clearing, Farm
from microsponge.themes.caveman.resources import Currency, Flint, Food, Stone, Wood
from microsponge.themes.caveman.technologies import Agriculture, Clubs, Discipline, Fire
from microsponge.themes.caveman.terrain_bonuses import Bison, Elephants
from microsponge.themes.caveman.terrains import Forest, Grassland, Mountains, Tarpit, Water
from microsponge.themes.caveman.units import AngryBird, CaptainCaveman, Raft, Settler, SlingshotCaveman, Warrior, Worker


class Caveman(Theme):
    PRIMARY_RESOURCE = Currency
    FOOD = Food
    STARTS_WITH = {Currency: 50}
    ACTION_POINTS = 4
    CITY = Village
    TERRAINS = (Grassland, Mountains, Water, Forest, Tarpit)
    RESOURCES = (Currency, Food, Stone, Wood, Flint)
    TECHNOLOGIES = (Clubs, Agriculture, Discipline, Fire)
    UNITS = (Settler, Warrior, Worker, CaptainCaveman, SlingshotCaveman, Raft, AngryBird)
    BUILDINGS = (Granary, GreatCavePainting, ArrangementOfRocks, Barracks, Harbor, Watchtower)
    IMPROVEMENTS = (Farm, Clearing)
    TERRAIN_BONUSES = (Bison, Elephants)
