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

"""The classic theme."""

from microsponge.engine.kinds.theme import Theme
from microsponge.themes.classic.city import ClassicCity
from microsponge.themes.classic.buildings import (
    Bank, CityWalls, College, Library, ResearchCenter, TheColossusOfRhodes, TheGreatWall, TheHangingGardensOfBabylon, TheLibraryOfAlexandria,
    TheLighthouseOfAlexandria, TheManhattanProject, TheMausoleumAtHalicarnassus, ThePyramids, TheStatueOfZeusAtOlympia, TheTempleOfArtemisAtEphesus,
)
from microsponge.themes.classic.improvements import Mine
from microsponge.themes.classic.resources import Currency, Food, Gold, Iron, Metal, Silk, Stone, Uranium, Wood
from microsponge.themes.classic.terrain_bonuses import MetalDeposit
from microsponge.themes.classic.technologies import BronzeWorking, Computers, Fortification, Industrialization, IronWorking, Irrigation, Literacy, Sanitation, TheInternet
from microsponge.themes.classic.terrains import Desert, Grassland, Lake, Mountains, Ocean, River
from microsponge.themes.classic.units import (
    AntiAirPlatform, AntiMissilePlatform, Bomber, Cannon, Catapult, CruiseMissile, Drone, FighterPlane, Howitzer,
    Infantry, Knights, Legion, Musketeer, NuclearMissile, Phalanx, Scout, Settler, StealthBomber, Warrior,
)


class Classic(Theme):
    PRIMARY_RESOURCE = Currency
    FOOD = Food
    CITY = ClassicCity
    TERRAINS = (Grassland, Desert, Mountains, River, Lake, Ocean)
    RESOURCES = (Currency, Food, Wood, Stone, Metal, Iron, Gold, Uranium, Silk)
    TECHNOLOGIES = (BronzeWorking, IronWorking, Irrigation, Literacy, Sanitation, Fortification, Industrialization, Computers, TheInternet)
    UNITS = (
        Settler, Scout, Warrior, Phalanx, Legion, Catapult, Knights, Cannon, Howitzer, Musketeer, Infantry, FighterPlane, Bomber, StealthBomber,
        CruiseMissile, NuclearMissile, Drone, AntiMissilePlatform, AntiAirPlatform,
    )
    IMPROVEMENTS = (Mine,)
    TERRAIN_BONUSES = (MetalDeposit,)
    BUILDINGS = (
        Library, College, ResearchCenter, Bank, CityWalls,
        ThePyramids, TheGreatWall, TheLibraryOfAlexandria, TheHangingGardensOfBabylon, TheStatueOfZeusAtOlympia,
        TheTempleOfArtemisAtEphesus, TheMausoleumAtHalicarnassus, TheColossusOfRhodes, TheLighthouseOfAlexandria, TheManhattanProject,
    )
