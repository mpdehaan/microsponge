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

"""The buildings of classic."""

from microsponge.engine.kinds.building import Building, Wonder
from microsponge.themes.classic.resources import Stone
from microsponge.themes.classic.technologies import Fortification


class Library(Building):
    pass


class College(Building):
    pass


class ResearchCenter(Building):
    pass


class Bank(Building):
    INCOME_BONUS = 20


class CityWalls(Building):
    REQUIRES = (Fortification,)
    COST = {Stone: 30}
    ARMOR_BONUS = 2
    WALLS = True


class ThePyramids(Wonder):
    pass


class TheGreatWall(Wonder):
    pass


class TheLibraryOfAlexandria(Wonder):
    pass


class TheHangingGardensOfBabylon(Wonder):
    pass


class TheStatueOfZeusAtOlympia(Wonder):
    pass


class TheTempleOfArtemisAtEphesus(Wonder):
    pass


class TheMausoleumAtHalicarnassus(Wonder):
    pass


class TheColossusOfRhodes(Wonder):
    pass


class TheLighthouseOfAlexandria(Wonder):
    pass


class TheManhattanProject(Wonder):
    pass
