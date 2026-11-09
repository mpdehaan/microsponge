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

"""The units of fantasy. Which are psychic, and what each can do, is not decided."""

from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit, SettlerUnit


class Settler(SettlerUnit):
    pass


class Worker(LandUnit):
    pass


class Scout(LandUnit):
    pass


class Soldier(LandUnit):
    pass


class Knight(LandUnit):
    pass


class Ranger(LandUnit):
    pass


class Monk(LandUnit):
    pass


class Cleric(LandUnit):
    pass


class Sorcerer(LandUnit):
    pass


class Wizard(LandUnit):
    pass


class Elemental(LandUnit):
    pass


class Ogre(LandUnit):
    pass


class Goblin(LandUnit):
    pass


class Dragon(AirUnit):
    pass


class Wyvern(AirUnit):
    pass


class Blimp(AirUnit):
    pass
