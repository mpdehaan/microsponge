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

"""The things that give and receive orders, each named by its type and its id."""

from dataclasses import dataclass
from enum import Enum


class ThingType(Enum):
    CIVILIZATION = 1
    PLANET = 2
    CITY = 3
    ARMY = 4
    DIVISION = 5
    UNIT = 6


@dataclass(slots=True, kw_only=True, frozen=True)
class Thing:
    """One thing in a game that gives or receives orders: a civilization, a planet, a city, an army, a division or a unit."""

    type: ThingType
    id: int


def civilization_thing(civilization):
    return Thing(type=ThingType.CIVILIZATION, id=civilization)


def city_thing(city):
    return Thing(type=ThingType.CITY, id=city)


def army_thing(army):
    return Thing(type=ThingType.ARMY, id=army)


def division_thing(division):
    return Thing(type=ThingType.DIVISION, id=division)


def unit_thing(unit):
    return Thing(type=ThingType.UNIT, id=unit)
