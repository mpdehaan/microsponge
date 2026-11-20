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
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.kind import Kind, saved_name
from microsponge.engine.kinds.weight import Versus, Weight
from microsponge.err_messages import ERR_NO_DOMAIN

# The armor class of a unit with no armor, which lets every damage roll land whole.
NO_ARMOR = 10
NO_EXTRA_DICE = 0


class UnitKind(Kind):
    """A kind of unit, like a warrior. Each unit on the map is a row of numbers, not an object of this class."""

    # Every kind of unit in a theme defines these three: the dice an attack rolls, the armor class, where NO_ARMOR is 10 and 0 is the best, and the hit points.
    ATTACK = NO_DICE
    ARMOR_CLASS = NO_ARMOR
    HIT_POINTS = 10
    # The extra dice the kind's melee attack rolls versus a class of unit, a weight class or a unit inside a city, like a slingshot against air units: {Domain.AIR: 1}.
    EXTRA_DICE = {}
    # The kind's ranged attack, a melee attack's twin for a target up to RANGE tiles away, which ends the attacker's turn and never takes a city: its dice, its range, its extra dice, and the classes of unit it can hit.
    RANGED_ATTACK = NO_DICE
    RANGE = 0
    RANGED_EXTRA_DICE = {}
    RANGED_HITS = (Domain.LAND, Domain.SEA)
    # How heavy the kind is, which bonuses can be versus.
    WEIGHT = Weight.LIGHT
    # By how much the kind's armor class is better versus an attacker of a class of unit or a weight class: {Weight.LIGHT: 2}.
    ARMOR_BONUS_AGAINST = {}
    # Whether a unit of this kind can attack the units inside a city.
    ATTACKS_CITIES = True
    # Whether a unit of this kind attacks back when it is attacked, and with what percent of its damage roll.
    STRIKES_BACK = True
    STRIKE_BACK_PERCENT = 50
    # The experience a unit that kills a unit of this kind gains, before the level of the unit killed is added: weaker kinds are worth less.
    EXPERIENCE_WORTH = 1
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
    # The kind of unit that makes this kind obsolete, or None: a city that can build the newer kind cannot build this one, and a unit of this kind can be upgraded to it.
    OBSOLETED_BY = None
    # How far a unit of this kind sees, in tiles in each direction: 5 is the 11 by 11 tiles with the unit in the middle.
    VISION = 5
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


def versus_keys(*, target, in_city=False):
    """Return what a bonus can be versus for a target: its class of unit, its weight class, and being inside a city when it is."""
    return (target.DOMAIN, target.WEIGHT, *((Versus.IN_CITY,) if in_city else ()))


def attack_dice(*, kind, target, in_city=False, ranged=False):
    """Return the dice a kind of unit rolls against another kind, melee or ranged: the attack's dice, with the attack's extra dice versus the other's class of unit, its weight class and being inside a city."""
    dice = kind.RANGED_ATTACK if ranged else kind.ATTACK
    extra = kind.RANGED_EXTRA_DICE if ranged else kind.EXTRA_DICE
    return dice.with_extra(dice=sum(extra.get(key, NO_EXTRA_DICE) for key in versus_keys(target=target, in_city=in_city)))


def armor_against(*, defender, attacker):
    """Return by how much a defending kind's armor class is better versus an attacking kind, by the attacker's class of unit and weight class."""
    return sum(defender.ARMOR_BONUS_AGAINST.get(key, NO_EXTRA_DICE) for key in versus_keys(target=attacker))


def has_melee(kind):
    return kind.ATTACK is not NO_DICE


def has_ranged(kind):
    return kind.RANGED_ATTACK is not NO_DICE and kind.RANGE > 0


def can_hit_ranged(*, kind, target):
    """Return whether a kind of unit's ranged attack can hit another kind, by the class of unit the target is."""
    return has_ranged(kind) and target.DOMAIN in kind.RANGED_HITS


def can_hit(*, kind, target):
    """Return whether a kind of unit can hit another kind, attacking or striking back, by the class of unit the target is."""
    by_domain = {Domain.LAND: kind.CAN_HIT_LAND, Domain.SEA: kind.CAN_HIT_SEA, Domain.AIR: kind.CAN_HIT_AIR, Domain.SPACE: kind.CAN_HIT_SPACE}
    if target.DOMAIN not in by_domain:
        raise ValueError(ERR_NO_DOMAIN.format(name=saved_name(target)))
    return by_domain[target.DOMAIN]
