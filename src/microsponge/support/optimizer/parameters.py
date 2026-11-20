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

"""The numbers the optimizer searches, and applying a set of them to a theme for as long as games are played with them.

A theme's numbers are constants on its classes. The optimizer searches a few numbers rather
than every constant: what a unit, a building and a technology cost is a base times a growth
rate for each level of depth in the tech tree, so that later kinds cost more by construction,
beside the income of a citizen, the upkeep of units and buildings, the food a city stores
for each citizen and a scale on the hit points of every unit. Applying a set changes the
theme's classes in the process that plays the games, and puts every constant back after.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from math import exp, log

from microsponge.engine.kinds.building import Wonder
from microsponge.support.optimizer.depth import TreeDepth

LEAST_COST = 1
LEAST_HIT_POINTS = 1
NO_GROWTH = 1.0
# A constant a class did not set itself, but took from a class it inherits from.
MISSING = object()
# The names of the theme's constants the optimizer changes.
COST = 'COST'
SUPPORT = 'SUPPORT'
HIT_POINTS = 'HIT_POINTS'
RESEARCH = 'RESEARCH'
CITIZEN_CURRENCY = 'CITIZEN_CURRENCY'
STORE_FOOD = 'STORE_FOOD'


@dataclass(slots=True, kw_only=True, frozen=True)
class Parameter:
    """One number the optimizer searches: its name, its bounds, and whether it is a whole number."""

    name: str
    low: float
    high: float
    whole: bool = False

    def clipped(self, value):
        """Return a value kept within the bounds, rounded when the number is whole."""
        value = min(max(value, self.low), self.high)
        return round(value) if self.whole else value


class Name:
    """The names of the numbers the optimizer searches."""

    UNIT_COST = 'unit cost base'
    UNIT_GROWTH = 'unit cost growth'
    BUILDING_COST = 'building cost base'
    BUILDING_GROWTH = 'building cost growth'
    WONDER_FACTOR = 'world wonder cost factor'
    RESEARCH = 'research base'
    RESEARCH_GROWTH = 'research growth'
    CITIZEN_CURRENCY = 'currency a citizen'
    UNIT_UPKEEP = 'unit upkeep'
    BUILDING_UPKEEP = 'building upkeep'
    STORE_FOOD = 'food a citizen stores'
    HIT_POINTS_SCALE = 'hit points scale'


PARAMETERS = (
    Parameter(name=Name.UNIT_COST, low=10, high=150),
    Parameter(name=Name.UNIT_GROWTH, low=1.0, high=2.0),
    Parameter(name=Name.BUILDING_COST, low=10, high=200),
    Parameter(name=Name.BUILDING_GROWTH, low=1.0, high=2.0),
    Parameter(name=Name.WONDER_FACTOR, low=1.0, high=5.0),
    Parameter(name=Name.RESEARCH, low=5, high=80),
    Parameter(name=Name.RESEARCH_GROWTH, low=1.0, high=2.5),
    Parameter(name=Name.CITIZEN_CURRENCY, low=1, high=6, whole=True),
    Parameter(name=Name.UNIT_UPKEEP, low=0, high=6, whole=True),
    Parameter(name=Name.BUILDING_UPKEEP, low=0, high=5, whole=True),
    Parameter(name=Name.STORE_FOOD, low=5, high=40, whole=True),
    Parameter(name=Name.HIT_POINTS_SCALE, low=0.5, high=2.0),
)


def scaled(*, base, growth, depth):
    """Return a cost of a base times a growth rate for each level of depth, rounded, never below the least."""
    return max(round(base * growth ** depth), LEAST_COST)


class Tuning:
    """Static: what a set of the optimizer's numbers makes of a theme's constants, and applying them."""

    __slots__ = ()

    @staticmethod
    def currency_cost(*, theme, kind, values):
        """Return the currency a unit, a building or a world wonder costs with a set of numbers."""
        depth = TreeDepth.of_kind(kind)
        if kind in theme.UNITS:
            return scaled(base=values[Name.UNIT_COST], growth=values[Name.UNIT_GROWTH], depth=depth)
        cost = scaled(base=values[Name.BUILDING_COST], growth=values[Name.BUILDING_GROWTH], depth=depth)
        return round(cost * values[Name.WONDER_FACTOR]) if issubclass(kind, Wonder) else cost

    @staticmethod
    def research(*, technology, values):
        return scaled(base=values[Name.RESEARCH], growth=values[Name.RESEARCH_GROWTH], depth=TreeDepth.of_technology(technology))

    @staticmethod
    def hit_points(*, kind, values, original):
        return max(round(original * values[Name.HIT_POINTS_SCALE]), LEAST_HIT_POINTS)

    @staticmethod
    def changes(*, theme, values):
        """Return every constant a set of numbers changes: (the class, the constant's name, the new value), in the theme's order."""
        primary = theme.PRIMARY_RESOURCE
        changes = []
        for kind in (*theme.UNITS, *theme.BUILDINGS):
            cost = dict(kind.COST)
            cost[primary] = Tuning.currency_cost(theme=theme, kind=kind, values=values)
            changes.append((kind, COST, cost))
            upkeep = values[Name.UNIT_UPKEEP] if kind in theme.UNITS else values[Name.BUILDING_UPKEEP]
            changes.append((kind, SUPPORT, {**kind.SUPPORT, primary: upkeep}))
        for kind in theme.UNITS:
            changes.append((kind, HIT_POINTS, Tuning.hit_points(kind=kind, values=values, original=kind.HIT_POINTS)))
        for technology in theme.TECHNOLOGIES:
            changes.append((technology, RESEARCH, Tuning.research(technology=technology, values=values)))
        changes.append((theme.CITY, CITIZEN_CURRENCY, values[Name.CITIZEN_CURRENCY]))
        changes.append((theme.CITY, STORE_FOOD, values[Name.STORE_FOOD]))
        return changes

    @staticmethod
    @contextmanager
    def applied(*, theme, values):
        """Change a theme's constants to what a set of numbers makes of them for as long as the block runs, and put every one back after."""
        changes = Tuning.changes(theme=theme, values=values)
        saved = [(kind, name, kind.__dict__.get(name, MISSING)) for kind, name, _ in changes]
        try:
            for kind, name, value in changes:
                setattr(kind, name, value)
            yield
        finally:
            for kind, name, value in reversed(saved):
                if value is MISSING:
                    delattr(kind, name)
                else:
                    setattr(kind, name, value)

    @staticmethod
    def start(theme):
        """Return a set of numbers that comes close to the theme as it is: each base and growth rate fitted to the theme's costs by depth, and the rest read from the theme."""
        primary = theme.PRIMARY_RESOURCE
        units = [(TreeDepth.of_kind(kind), kind.COST.get(primary, LEAST_COST)) for kind in theme.UNITS]
        buildings = [(TreeDepth.of_kind(kind), kind.COST.get(primary, LEAST_COST)) for kind in theme.BUILDINGS if not issubclass(kind, Wonder)]
        wonders = [kind.COST.get(primary, LEAST_COST) for kind in theme.BUILDINGS if issubclass(kind, Wonder)]
        technologies = [(TreeDepth.of_technology(kind), kind.RESEARCH) for kind in theme.TECHNOLOGIES]
        unit_base, unit_growth = fitted(units)
        building_base, building_growth = fitted(buildings)
        research_base, research_growth = fitted(technologies)
        building_mean = sum(cost for _, cost in buildings) / len(buildings) if buildings else LEAST_COST
        values = {
            Name.UNIT_COST: unit_base, Name.UNIT_GROWTH: unit_growth, Name.BUILDING_COST: building_base, Name.BUILDING_GROWTH: building_growth,
            Name.WONDER_FACTOR: (sum(wonders) / len(wonders) / building_mean) if wonders else 1.0,
            Name.RESEARCH: research_base, Name.RESEARCH_GROWTH: research_growth, Name.CITIZEN_CURRENCY: theme.CITY.CITIZEN_CURRENCY,
            Name.UNIT_UPKEEP: theme.UNITS[0].SUPPORT.get(primary, 0) if theme.UNITS else 0,
            Name.BUILDING_UPKEEP: theme.BUILDINGS[0].SUPPORT.get(primary, 0) if theme.BUILDINGS else 0,
            Name.STORE_FOOD: theme.CITY.STORE_FOOD, Name.HIT_POINTS_SCALE: 1.0,
        }
        return {parameter.name: parameter.clipped(values[parameter.name]) for parameter in PARAMETERS}


def fitted(points):
    """Return (the base, the growth rate) of costs by depth that best fit some (depth, cost) points, on a logarithmic scale; one point or none fits a growth of one."""
    if not points:
        return (LEAST_COST, NO_GROWTH)
    logs = [(depth, log(max(cost, LEAST_COST))) for depth, cost in points]
    count = len(logs)
    mean_depth = sum(depth for depth, _ in logs) / count
    mean_log = sum(value for _, value in logs) / count
    spread = sum((depth - mean_depth) ** 2 for depth, _ in logs)
    slope = sum((depth - mean_depth) * (value - mean_log) for depth, value in logs) / spread if spread else 0
    return (exp(mean_log - slope * mean_depth), exp(slope))
