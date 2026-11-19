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

"""The base of a theme's city spec: the constants that say what a city means in the theme."""

from microsponge.engine.kinds.control_points import Command, Policy
from microsponge.ui_strings import MSG_CITIES, MSG_CITY


class CitySpec:
    """What a city is. A theme subclasses it and sets what differs, and names its class as the theme's CITY."""

    # What a city is called, and several of them. A theme that calls a city something else sets its own words here.
    NAME = MSG_CITY
    NAMES = MSG_CITIES
    # The city center is this many tiles on a side, and the city radius this many, with the center in the middle.
    CENTER_SIZE = 5
    RADIUS_SIZE = 15
    # The fewest tiles of the city center that are land: at least half.
    CENTER_LAND = 13
    # The citizens a new city has, and the most a city grows to.
    STARTING_CITIZENS = 1
    MAX_CITIZENS = 10
    # By how much every city makes the armor class of every unit inside better when the city is attacked, with no building.
    ARMOR_BONUS = 0
    # A city stores this much food for each of its citizens, and grows a citizen when the store is full.
    STORE_FOOD = 10
    # The food each citizen eats each turn.
    CITIZEN_FOOD = 1
    # The currency each working citizen generates each turn.
    CITIZEN_CURRENCY = 1
    # The control points a city adds to its civilization each turn: Policy and Command, each with its number.
    CONTROL_POINTS = {}
    # The control points a city that is building nothing adds on top of those each turn.
    IDLE_CONTROL_POINTS = {Policy: 1, Command: 1}
    # The research points a city adds to its civilization's pool each turn.
    RESEARCH_POINTS = 0
    # The most units a city holds inside itself.
    MOST_UNITS = 3
    # The resources a city produces each turn by default: each resource with its amount.
    PRODUCES = {}
    # The percent of the value of its buildings that disbanding a city returns.
    DISBAND_PERCENT = 10
    # The percent of a unit's value that disbanding the unit inside a city returns. Outside a city nothing is returned.
    UNIT_DISBAND_PERCENT = 20
