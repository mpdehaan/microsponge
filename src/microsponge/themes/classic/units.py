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

"""The units of classic."""

from microsponge.engine.kinds.dice import Dice
from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit, SettlerUnit, UnitKind
from microsponge.themes.classic.buildings import TheManhattanProject
from microsponge.themes.classic.resources import Iron


class Settler(SettlerUnit):
    pass


class Scout(LandUnit):
    pass


class Warrior(LandUnit):
    pass


class Phalanx(LandUnit):
    pass


class Legion(LandUnit):
    REQUIRES = (Iron,)


class Catapult(LandUnit):
    STRIKES_BACK = False
    BYPASSES_WALLS = True
    ATTACK = Dice(count=2, sides=6)
    HIT_POINTS = 1


class Knights(LandUnit):
    pass


class Cannon(LandUnit):
    STRIKES_BACK = False
    BYPASSES_WALLS = True
    ATTACK = Catapult.ATTACK.with_extra(dice=Catapult.ATTACK.count * 2)
    HIT_POINTS = 1


class Howitzer(LandUnit):
    STRIKES_BACK = False
    BYPASSES_WALLS = True
    ATTACK = Cannon.ATTACK.with_extra(dice=Cannon.ATTACK.count * 2)
    HIT_POINTS = 1


class Musketeer(LandUnit):
    pass


class Infantry(LandUnit):
    pass


class FighterPlane(AirUnit):
    pass


class Bomber(AirUnit):
    pass


class StealthBomber(AirUnit):
    pass


class CruiseMissile(UnitKind):
    pass


class NuclearMissile(UnitKind):
    REQUIRES = (TheManhattanProject,)


class Drone(UnitKind):
    pass


class AntiMissilePlatform(UnitKind):
    NAME = 'anti-missile platform'


class AntiAirPlatform(UnitKind):
    NAME = 'anti-air platform'
