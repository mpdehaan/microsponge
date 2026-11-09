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

"""What can be done with units: so far, putting one on the map, taking one off, and working out the damage of an attack."""

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import attack_points, can_hit
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.world.layer import Layer
from microsponge.support.numbers import divided_rounding_up
from microsponge.err_messages import ERR_CANNOT_BE_ON, ERR_TILE_HAS_A_UNIT, ERR_TILE_IN_A_CITY_CENTER

# The least damage an attack deals, however strong the defense.
CHIP_DAMAGE = 1
# What a unit that does not strike back deals.
NO_DAMAGE = 0
WHOLE = 100
# The defense bonus of a unit outside a city.
NO_BONUS = 0


class UnitControl:
    """The rules for units, as static methods over a game's worlds and units. It is never made into an object.

    It keeps the two records of where a unit is in step: the unit layer of the world, which says
    which unit is on a tile, and the columns of the units, which say which tile a unit is on.
    """

    __slots__ = ()

    @staticmethod
    def can_be_on(*, kind, terrain):
        """Return whether a kind of unit can be on a terrain: land units on land, naval units in water, and no land unit on land that land units cannot cross."""
        if not terrain.LAND:
            return kind.ON_WATER
        return kind.ON_LAND and (terrain.CROSSED_BY_LAND_UNITS or kind.DOMAIN != Domain.LAND)

    @staticmethod
    def damage(*, attacker, defender, defense_bonus=NO_BONUS):
        """Return the hit points a kind of unit takes off another by attacking: its attack against that unit less the other's defense, boosted by a percent inside a city and rounded up, and never less than chip damage."""
        defense = divided_rounding_up(amount=defender.DEFENSE * (WHOLE + defense_bonus), by=WHOLE)
        return max(attack_points(kind=attacker, target=defender) - defense, CHIP_DAMAGE)

    @staticmethod
    def strike_back_damage(*, attacker, defender):
        """Return the hit points a kind of unit that was attacked takes off its attacker by striking back.

        The unit strikes back with a percent of its attack points, rounded down, and deals no
        damage at all when its kind does not strike back or cannot hit the attacker's class of unit.
        """
        if not defender.STRIKES_BACK or not can_hit(kind=defender, target=attacker):
            return NO_DAMAGE
        return max(attack_points(kind=defender, target=attacker) * defender.STRIKE_BACK_PERCENT // WHOLE - attacker.DEFENSE, CHIP_DAMAGE)

    @staticmethod
    def attacks_to_kill(*, attacker, defender):
        """Return how many attacks a kind of unit needs to take every hit point off a whole unit of another kind, or None when the kind cannot hit the other.

        Nothing the other unit heals between the attacks is counted.
        """
        if not can_hit(kind=attacker, target=defender):
            return None
        return divided_rounding_up(amount=defender.HIT_POINTS, by=UnitControl.damage(attacker=attacker, defender=defender))

    @staticmethod
    def problem_standing(*, game, kind, world, x, y):
        """Return why a unit of a kind cannot stand on a tile, as an error message, or None when it can.

        The tile has to be empty, outside every city center, and of a terrain the kind can be on.
        """
        tiles = game.get_world(world)
        if tiles.get_value(layer=Layer.UNIT, x=x, y=y) != NOTHING:
            return ERR_TILE_HAS_A_UNIT.format(x=tiles.column(x), y=y)
        if tiles.get_value(layer=Layer.CITY_CENTER, x=x, y=y) != NOTHING:
            return ERR_TILE_IN_A_CITY_CENTER.format(city=game.get_theme().CITY.NAME, x=tiles.column(x), y=y)
        terrain = game.get_terrain(world=world, x=x, y=y)
        if not UnitControl.can_be_on(kind=kind, terrain=terrain):
            return ERR_CANNOT_BE_ON.format(unit=shown_name(kind), terrain=shown_name(terrain))
        return None

    @staticmethod
    def check_tile(*, game, kind, world, x, y):
        """Check that a unit of a kind can stand on a tile."""
        problem = UnitControl.problem_standing(game=game, kind=kind, world=world, x=x, y=y)
        if problem is not None:
            raise ValueError(problem)

    @staticmethod
    def place(*, game, kind, owner, world, x, y):
        """Put a new unit of a kind on a tile for a civilization, and return the unit's id.

        Only one unit may be on a tile, the tile's terrain has to be one the kind can be on, and
        no unit stands on a tile of a city center: a unit there is inside the city.
        """
        UnitControl.check_tile(game=game, kind=kind, world=world, x=x, y=y)
        unit = UnitControl.create(game=game, kind=kind, owner=owner, world=world, x=x, y=y, city=NOTHING)
        game.get_world(world).set_value(layer=Layer.UNIT, x=x, y=y, value=unit)
        return unit

    @staticmethod
    def create(*, game, kind, owner, world, x, y, city):
        """Add a new unit of a kind to the units, whole and with all its action points, and return the unit's id.

        The caller says where the unit is and puts the unit there: place() on a tile, and
        CityControl inside a city.
        """
        game.get_civilization(owner)
        return game.get_units().add({
            UnitColumn.KIND: game.get_catalog().get_id(category=Category.UNITS, kind=kind),
            UnitColumn.OWNER: owner,
            UnitColumn.WORLD: world,
            UnitColumn.X: game.get_world(world).column(x),
            UnitColumn.Y: y,
            UnitColumn.HIT_POINTS: kind.HIT_POINTS,
            UnitColumn.ACTION_POINTS: kind.ACTION_POINTS,
            UnitColumn.CITY: city,
        })

    @staticmethod
    def remove(*, game, unit):
        """Take a unit out of the game for good, from its tile or from the city it is inside."""
        units = game.get_units()
        city = units.get_value(column=UnitColumn.CITY, unit=unit)
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        if city != NOTHING:
            game.get_city(city).remove_unit(unit)
        else:
            game.get_world(world).set_value(layer=Layer.UNIT, x=x, y=y, value=NOTHING)
        units.remove(unit)

    @staticmethod
    def move_to(*, game, unit, x, y):
        """Take a unit that stands on a tile of its own to another tile of its world that it can stand on."""
        units = game.get_units()
        world, from_x, from_y = UnitControl.tile_of(game=game, unit=unit)
        tiles = game.get_world(world)
        UnitControl.check_tile(game=game, kind=UnitControl.kind_of(game=game, unit=unit), world=world, x=x, y=y)
        tiles.set_value(layer=Layer.UNIT, x=from_x, y=from_y, value=NOTHING)
        tiles.set_value(layer=Layer.UNIT, x=x, y=y, value=unit)
        units.set_value(column=UnitColumn.X, unit=unit, value=tiles.column(x))
        units.set_value(column=UnitColumn.Y, unit=unit, value=y)

    @staticmethod
    def units_of(*, game, civilization):
        """Return the ids of the units that belong to a civilization."""
        units = game.get_units()
        return [unit for unit in units.get_ids() if units.get_value(column=UnitColumn.OWNER, unit=unit) == civilization]

    @staticmethod
    def tile_of(*, game, unit):
        """Return where a unit is, as (world, x, y). A unit inside a city is at the middle of the city."""
        units = game.get_units()
        return (units.get_value(column=UnitColumn.WORLD, unit=unit), units.get_value(column=UnitColumn.X, unit=unit), units.get_value(column=UnitColumn.Y, unit=unit))

    @staticmethod
    def kind_of(*, game, unit):
        """Return the kind of a unit, as the theme's class."""
        kind_id = game.get_units().get_value(column=UnitColumn.KIND, unit=unit)
        return game.get_catalog().get_kind(category=Category.UNITS, kind_id=kind_id)
