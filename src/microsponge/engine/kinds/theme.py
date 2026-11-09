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

"""The base of a theme: the kind of game being played, as lists of its kinds."""

from microsponge.engine.kinds.city_spec import CitySpec

# The least currency any unit or building costs to build, in every theme.
LEAST_COST = 10


class Theme:
    """A theme lists its kinds, each list in the order the theme wants them shown.

    A theme is never made into an object. The order of a list can change between versions and
    kinds can be added, because a saved game records each kind by name.
    """

    # The theme's currency: what units and buildings cost, and what supporting them is paid in.
    PRIMARY_RESOURCE = None
    # The resource that citizens collect unless told otherwise, and that cities grow on.
    FOOD = None
    # What each civilization holds when a game starts: each resource with its amount.
    STARTS_WITH = {}
    # The action points a civilization has each turn before its cities add theirs.
    ACTION_POINTS = 0
    # The action points it costs a unit to do something that is neither a move nor an attack, like building a city.
    ACTION_COST_BASE = 1
    # A civilization whose currency is at 0 is bankrupt: it collects this percent less of every resource,
    # and after this many turns in a row of it, the game ends.
    BANKRUPTCY_HARVEST_PENALTY = 50
    BANKRUPTCY_TURNS = 50
    # The percent of what a city has paid for a build that comes back when the city switches to another build, or to nothing.
    SWITCH_REFUND_PERCENT = 20
    # How much currency each research point becomes while a civilization has nothing left to research.
    RESEARCH_TO_CURRENCY = 1
    # What a city means in the theme.
    CITY = CitySpec
    # The fewest and the most worlds a game has. A theme with planets raises the most, and the player chooses.
    MIN_WORLDS = 1
    MAX_WORLDS = 1
    # The action points moving one tile costs before the terrain is counted, straight and diagonally, and the same for attacking.
    STRAIGHT_MOVE_COST_BASE = 1
    DIAGONAL_MOVE_COST_BASE = 1
    STRAIGHT_ATTACK_COST_BASE = 1
    DIAGONAL_ATTACK_COST_BASE = 1
    TERRAINS = ()
    RESOURCES = ()
    TECHNOLOGIES = ()
    UNITS = ()
    BUILDINGS = ()
    IMPROVEMENTS = ()
    TERRAIN_BONUSES = ()


def underpriced(theme):
    """Return the units and buildings of a theme that cost less currency than every one must."""
    return [kind for kind in theme.UNITS + theme.BUILDINGS if kind.COST.get(theme.PRIMARY_RESOURCE, 0) < LEAST_COST]
