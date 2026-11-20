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

"""The caveman units."""

from microsponge.engine.kinds.dice import Dice
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.weight import Versus, Weight
from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit, SeaUnit, SettlerUnit, UnitKind
from microsponge.themes.caveman.buildings import Barracks, Harbor
from microsponge.themes.caveman.improvements import Clearing, Farm
from microsponge.themes.caveman.resources import Currency, Poppies, Wood
from microsponge.themes.caveman.technologies import Agriculture, Carpentry, ChurchOfTheCaveBear, Clubs


class CavemanUnit(UnitKind):
    SUPPORT = {Currency: 2}
    ACTION_POINTS = 2
    HEAL = 1
    CITY_HEAL = 3


class Settler(CavemanUnit, SettlerUnit):
    COST = {Currency: 45}
    BUILD_TURNS = 6
    HIT_POINTS = 5


class CaptainCaveman(CavemanUnit, LandUnit):
    REQUIRES = (Barracks,)
    WEIGHT = Weight.HEAVY
    COST = {Currency: 180}
    BUILD_TURNS = 6
    ATTACK = Dice(count=5, sides=6)
    ARMOR_CLASS = 8
    HIT_POINTS = 20
    EXPERIENCE_WORTH = 5


class Clubber(CavemanUnit, LandUnit):
    REQUIRES = (Clubs,)
    OBSOLETED_BY = CaptainCaveman
    COST = {Currency: 45}
    BUILD_TURNS = 3
    ATTACK = Dice(count=2, sides=6)
    ARMOR_CLASS = 8
    HIT_POINTS = 10
    EXPERIENCE_WORTH = 2


class SlingshotCaveman(CavemanUnit, LandUnit):
    REQUIRES = (Clubs,)
    COST = {Currency: 60}
    BUILD_TURNS = 3
    ATTACK = Dice(count=2, sides=4)
    EXTRA_DICE = {Domain.AIR: 2}
    CAN_HIT_AIR = True
    ARMOR_CLASS = 8
    HIT_POINTS = 8
    EXPERIENCE_WORTH = 2


class WildClubber(CavemanUnit, LandUnit):
    REQUIRES = (ChurchOfTheCaveBear, Poppies)
    WEIGHT = Weight.MEDIUM
    COST = {Currency: 60}
    BUILD_TURNS = 5
    ATTACK = Dice(count=3, sides=6)
    ARMOR_CLASS = 8
    HIT_POINTS = 13
    EXPERIENCE_WORTH = 3


class Worker(CavemanUnit, LandUnit):
    REQUIRES = (Agriculture,)
    BUILDS = (Farm, Clearing)
    COST = {Currency: 45}
    BUILD_TURNS = 3
    HIT_POINTS = 5


class Raft(CavemanUnit, SeaUnit):
    REQUIRES = (Harbor,)
    COST = {Currency: 45, Wood: 10}
    BUILD_TURNS = 4
    ATTACK = Dice(count=2, sides=4)
    ARMOR_CLASS = 9
    HIT_POINTS = 8


class AngryBird(CavemanUnit, AirUnit):
    COST = {Currency: 45}
    BUILD_TURNS = 2
    ATTACK = Dice(count=2, sides=4)
    HIT_POINTS = 6
    TAKES_CITIES = False
    ATTACKS_CITIES = False
    ACTION_POINTS = 6
    VISION = 7


class MammothCatapult(CavemanUnit, LandUnit):
    REQUIRES = (Carpentry,)
    WEIGHT = Weight.HEAVY
    COST = {Currency: 120, Wood: 20}
    BUILD_TURNS = 5
    RANGED_ATTACK = Dice(count=4, sides=6)
    RANGE = 3
    RANGED_EXTRA_DICE = {Versus.IN_CITY: 2}
    ARMOR_CLASS = 10
    HIT_POINTS = 8
    EXPERIENCE_WORTH = 3
    STRIKES_BACK = False
    TAKES_CITIES = False
    BYPASSES_WALLS = True
