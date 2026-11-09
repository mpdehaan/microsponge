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

"""The bases of what a city builds inside itself: buildings and world wonders."""

from microsponge.engine.kinds.kind import Kind


class Building(Kind):
    """Something a city builds and keeps."""

    # What it costs to build: each resource with its amount.
    COST = {}
    # The turns a city takes to build it.
    BUILD_TURNS = 1
    # What it costs to support each turn: each resource with its amount. Every building of a theme defines it.
    SUPPORT = {}
    # The action points it adds to its civilization's pool each turn.
    ACTION_POINTS = 0
    # The research points it adds to its civilization's pool each turn.
    RESEARCH_POINTS = 0
    # What it produces each turn, whatever else happens: each resource with its amount.
    PRODUCES = {}
    # The percent it adds to the currency its city brings in each turn.
    INCOME_BONUS = 0
    # What it adds to each worked tile of a terrain: each terrain with each resource and its amount.
    WORKED_TILE_BONUS = {}
    # The turns sooner its city grows a citizen.
    GROWS_SOONER = 0
    # The percent it adds to the defense of every unit inside its city when the city is attacked, like a watchtower.
    DEFENSE_BONUS = 0
    # Whether it is city walls, whose defense bonus a unit that bypasses walls, like a catapult, ignores.
    WALLS = False
    # Whether only a city with a water tile next to its city center can build it, like a harbor.
    BESIDE_WATER = False


class Wonder(Building):
    """A world wonder: only one civilization can build it, and it is captured with its city."""
