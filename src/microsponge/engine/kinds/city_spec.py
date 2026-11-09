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
    # The turns in a row with enough food that a city needs to grow, by its size: the first number is for a city
    # of 1 citizen, the next for 2, and the last number goes for every larger size.
    GROWTH_TURNS = (5, 10)
    # A turn has enough food when the civilization holds this much food for each citizen of the city.
    GROWTH_FOOD = 0
    # The food each citizen eats each turn.
    CITIZEN_FOOD = 1
    # The currency each working citizen generates each turn.
    CITIZEN_CURRENCY = 1
    # The action points a city adds to its civilization's pool each turn.
    ACTION_POINTS = 0
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
