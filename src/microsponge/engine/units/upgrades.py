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

"""Obsolete units, and upgrading a unit to the unit that made its kind obsolete."""

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import StrategicResource
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_NOT_OBSOLETE, ERR_UPGRADE_NOT_BUILDABLE, ERR_UPGRADE_OUTSIDE_BORDERS, ERR_UPGRADE_PRICE

WHOLE = 100
# A unit upgraded keeps at least this many hit points.
LEAST_HIT_POINTS = 1


class Upgrades:
    """Static: which units are obsolete where, and upgrading a unit.

    A theme names, for a kind of unit, the kind that makes it obsolete (OBSOLETED_BY). A city
    cannot build the older kind once the city can build the newer one, and a newer kind that
    requires a strategic resource makes nothing obsolete. A unit of an obsolete kind can be
    upgraded to the newer kind anywhere within its civilization's borders, for the theme's
    percent of what the newer kind costs, and keeps its level, its experience and its share of
    hit points.
    """

    __slots__ = ()

    @staticmethod
    def newer_of(kind):
        """Return the kind that makes a kind of unit obsolete, or None: a kind that requires a strategic resource never makes another obsolete."""
        newer = kind.OBSOLETED_BY
        if newer is None or any(issubclass(required, StrategicResource) for required in newer.REQUIRES):
            return None
        return newer

    @staticmethod
    def is_obsolete_in(*, game, city, kind, problem_building):
        """Return whether a kind of unit is obsolete in a city: the city can build the newer kind. problem_building is how a city's ability to build a kind is checked."""
        newer = Upgrades.newer_of(kind)
        return newer is not None and problem_building(game=game, city=city, kind=newer) is None

    @staticmethod
    def price(*, game, kind):
        """Return what upgrading to a kind costs: the theme's percent of each resource the kind costs, rounded down."""
        percent = game.get_theme().UPGRADE_PERCENT
        return {resource: amount * percent // WHOLE for resource, amount in kind.COST.items()}

    @staticmethod
    def is_within_borders(*, game, unit):
        """Return whether a unit is inside a city of its civilization or on a tile of the radius of one."""
        units = game.get_units()
        owner = units.get_value(column=UnitColumn.OWNER, unit=unit)
        city = units.get_value(column=UnitColumn.CITY, unit=unit)
        if city == NOTHING:
            world, x, y = UnitControl.tile_of(game=game, unit=unit)
            city = game.get_world(world).get_value(layer=Layer.CITY, x=x, y=y)
        return city != NOTHING and game.get_city(city).get_owner() == owner

    @staticmethod
    def problem_upgrading(*, game, unit, problem_building):
        """Return why a unit cannot be upgraded now, as an error message, or None when it can: its kind has a newer kind, some city of its civilization can build the newer kind, it is within its civilization's borders, and the civilization holds the price."""
        kind = UnitControl.kind_of(game=game, unit=unit)
        newer = Upgrades.newer_of(kind)
        if newer is None:
            return ERR_NOT_OBSOLETE.format(unit=shown_name(kind))
        owner = game.get_units().get_value(column=UnitColumn.OWNER, unit=unit)
        if not any(problem_building(game=game, city=city, kind=newer) is None for city in game.get_cities_of(owner)):
            return ERR_UPGRADE_NOT_BUILDABLE.format(unit=shown_name(kind), newer=shown_name(newer))
        if not Upgrades.is_within_borders(game=game, unit=unit):
            return ERR_UPGRADE_OUTSIDE_BORDERS.format(unit=shown_name(kind))
        holder = game.get_civilization(owner)
        catalog = game.get_catalog()
        for resource, amount in Upgrades.price(game=game, kind=newer).items():
            if holder.get_amount(catalog.get_id(category=Category.RESOURCES, kind=resource)) < amount:
                return ERR_UPGRADE_PRICE.format(unit=shown_name(kind), newer=shown_name(newer))
        return None

    @staticmethod
    def upgrade(*, game, unit, problem_building):
        """Upgrade a unit to the newer kind and charge the price, keeping its level, its experience and its share of hit points, rounded down and never below one."""
        problem = Upgrades.problem_upgrading(game=game, unit=unit, problem_building=problem_building)
        if problem is not None:
            raise ValueError(problem)
        units = game.get_units()
        newer = Upgrades.newer_of(UnitControl.kind_of(game=game, unit=unit))
        holder = game.get_civilization(units.get_value(column=UnitColumn.OWNER, unit=unit))
        catalog = game.get_catalog()
        for resource, amount in Upgrades.price(game=game, kind=newer).items():
            holder.pay(resource=catalog.get_id(category=Category.RESOURCES, kind=resource), amount=amount)
        hit_points = units.get_value(column=UnitColumn.HIT_POINTS, unit=unit)
        whole = UnitControl.max_hit_points(game=game, unit=unit)
        units.set_value(column=UnitColumn.KIND, unit=unit, value=catalog.get_id(category=Category.UNITS, kind=newer))
        units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=max(hit_points * UnitControl.max_hit_points(game=game, unit=unit) // whole, LEAST_HIT_POINTS))
