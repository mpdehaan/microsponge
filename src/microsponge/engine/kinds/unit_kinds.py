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

"""The bases of a theme's kinds of unit: land, sea, air and space units, and the settler."""

from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.kind import Kind, saved_name
from microsponge.err_messages import ERR_NO_DOMAIN


class UnitKind(Kind):
    """A kind of unit, like a warrior. Each unit on the map is a row of numbers, not an object of this class."""

    # Every kind of unit in a theme defines these three. Hit points are large: about 10 for the weakest unit, up to 500.
    ATTACK = 0
    DEFENSE = 0
    HIT_POINTS = 10
    # The attack points against air units, for a kind whose attack is different against them. None means ATTACK.
    AIR_ATTACK = None
    # Whether a unit of this kind attacks back when it is attacked, and with what percent of its attack points.
    STRIKES_BACK = True
    STRIKE_BACK_PERCENT = 20
    # Which class of unit this kind is: LandUnit, SeaUnit, AirUnit and SpaceUnit each set theirs.
    DOMAIN = None
    # Which classes of unit this kind can hit, attacking or striking back.
    CAN_HIT_LAND = True
    CAN_HIT_SEA = True
    CAN_HIT_AIR = True
    CAN_HIT_SPACE = True
    # The hit points a unit heals each turn, outside a city and inside one. A theme gives its units a default.
    HEAL = 0
    CITY_HEAL = 0
    # The action points a unit of this kind has each turn.
    ACTION_POINTS = 1
    # What it costs to build: each resource with its amount.
    COST = {}
    # What it costs to support each turn: each resource with its amount.
    SUPPORT = {}
    # The turns a city takes to build one.
    BUILD_TURNS = 1
    # The citizens of the city that are used up to build one.
    CITIZENS = 0
    # The improvements a unit of this kind can build on a tile.
    BUILDS = ()
    # Whether a unit of this kind ignores the defense bonus of city walls when attacking a city, like a catapult.
    BYPASSES_WALLS = False
    # Whether a unit of this kind can take a city of another civilization.
    TAKES_CITIES = True
    # The tiles a unit of this kind can be on.
    ON_LAND = True
    ON_WATER = True


class LandUnit(UnitKind):
    """A unit that stays on land, and cannot hit air units. An amphibious kind sets ON_WATER, and a kind that can hit air sets CAN_HIT_AIR."""

    DOMAIN = Domain.LAND
    ON_WATER = False
    CAN_HIT_AIR = False


class SeaUnit(UnitKind):
    """A unit that can only move in water, and cannot hit air units unless its kind sets CAN_HIT_AIR."""

    DOMAIN = Domain.SEA
    ON_LAND = False
    CAN_HIT_AIR = False


class AirUnit(UnitKind):
    """A unit that flies, over land and water alike."""

    DOMAIN = Domain.AIR


class SpaceUnit(UnitKind):
    """A unit that travels in space. Where a space unit can be is not decided yet."""

    DOMAIN = Domain.SPACE


class SettlerUnit(LandUnit):
    """The unit that expends itself to build a city, in every theme.

    A settler costs currency and time like any unit, and also one citizen of the city that
    builds it. A theme's settler has no REQUIRES, which the Catalog checks.
    """

    CITIZENS = 1


def attack_points(*, kind, target):
    """Return the attack points a kind of unit has against another kind: its attack points against air units when the target is one and the kind sets them, or else its attack points."""
    if target.DOMAIN == Domain.AIR and kind.AIR_ATTACK is not None:
        return kind.AIR_ATTACK
    return kind.ATTACK


def can_hit(*, kind, target):
    """Return whether a kind of unit can hit another kind, attacking or striking back, by the class of unit the target is."""
    by_domain = {Domain.LAND: kind.CAN_HIT_LAND, Domain.SEA: kind.CAN_HIT_SEA, Domain.AIR: kind.CAN_HIT_AIR, Domain.SPACE: kind.CAN_HIT_SPACE}
    if target.DOMAIN not in by_domain:
        raise ValueError(ERR_NO_DOMAIN.format(name=saved_name(target)))
    return by_domain[target.DOMAIN]
