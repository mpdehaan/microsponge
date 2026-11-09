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

"""What can be done with units: so far, putting one on the map, taking one off, and working out the damage of an attack through armor."""

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import NO_ARMOR, attack_dice, can_hit
from microsponge.engine.units.levels import FIRST_LEVEL, Levels
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.world.layer import Layer
from microsponge.support.numbers import divided_rounding_up
from microsponge.err_messages import ERR_CANNOT_BE_ON, ERR_TILE_HAS_A_UNIT, ERR_TILE_IN_A_CITY_CENTER

# The least damage an attack deals, however good the armor.
CHIP_DAMAGE = 1
# What a unit that does not strike back deals.
NO_DAMAGE = 0
WHOLE = 100
# The armor bonus of a unit outside a city.
NO_BONUS = 0
# Every point of armor class below NO_ARMOR takes this percent off a damage roll, and an armor class of 0 lets only chip damage through.
PERCENT_PER_ARMOR_POINT = 10
WORST_ARMOR_CLASS = NO_ARMOR
BEST_ARMOR_CLASS = 0


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
    def mitigated(*, roll, armor_class):
        """Return the damage a roll deals through an armor class: 10 percent less for every point of armor class below 10, rounded up, and never less than chip damage.

        An armor class of 10 is no armor and lets the roll land whole; 0, or better, lets only
        the chip damage through.
        """
        through = min(max(armor_class, BEST_ARMOR_CLASS), WORST_ARMOR_CLASS) * PERCENT_PER_ARMOR_POINT
        return max(divided_rounding_up(amount=roll * through, by=WHOLE), CHIP_DAMAGE)

    @staticmethod
    def armor_class(*, kind, level=FIRST_LEVEL, bonus=NO_BONUS):
        """Return the armor class a unit of a kind defends with: the kind's, made better by its level and by a city's buildings."""
        return kind.ARMOR_CLASS - Levels.armor_bonus(level=level) - bonus

    @staticmethod
    def average_roll(*, attacker, defender, level=FIRST_LEVEL):
        """Return what a kind of unit rolls against another on average, rounded down, with its level's bonus."""
        return int(attack_dice(kind=attacker, target=defender).average()) + Levels.damage_bonus(level=level)

    @staticmethod
    def damage(*, attacker, defender, armor_bonus=NO_BONUS, attacker_level=FIRST_LEVEL, defender_level=FIRST_LEVEL):
        """Return the hit points a kind of unit takes off another on an average roll, through the other's armor class, for balancing and for screens that say what to expect."""
        roll = UnitControl.average_roll(attacker=attacker, defender=defender, level=attacker_level)
        return UnitControl.mitigated(roll=roll, armor_class=UnitControl.armor_class(kind=defender, level=defender_level, bonus=armor_bonus))

    @staticmethod
    def strike_back_roll(*, attacker, defender, roll):
        """Return what a unit that was attacked strikes back with from its own roll: its kind's percent of the roll, rounded down, or None when its kind does not strike back or cannot hit the attacker's class of unit."""
        if not defender.STRIKES_BACK or not can_hit(kind=defender, target=attacker):
            return None
        return roll * defender.STRIKE_BACK_PERCENT // WHOLE

    @staticmethod
    def strike_back_damage(*, attacker, defender):
        """Return the hit points a kind of unit that was attacked takes off its attacker by striking back on an average roll, through the attacker's armor class, or nothing when its kind does not strike back at the attacker."""
        roll = UnitControl.strike_back_roll(attacker=attacker, defender=defender, roll=UnitControl.average_roll(attacker=defender, defender=attacker))
        if roll is None:
            return NO_DAMAGE
        return UnitControl.mitigated(roll=roll, armor_class=UnitControl.armor_class(kind=attacker))

    @staticmethod
    def attacks_to_kill(*, theme, attacker, defender, attacker_level=FIRST_LEVEL, defender_level=FIRST_LEVEL):
        """Return how many attacks a kind of unit needs, on average rolls, to take every hit point off a whole unit of another kind, or None when the kind cannot hit the other.

        Nothing the other unit heals between the attacks is counted.
        """
        if not can_hit(kind=attacker, target=defender):
            return None
        damage = UnitControl.damage(attacker=attacker, defender=defender, attacker_level=attacker_level, defender_level=defender_level)
        return Levels.attacks_to_kill(hit_points=Levels.hit_points(theme=theme, kind=defender, level=defender_level), damage=damage)

    @staticmethod
    def level_of(*, game, unit):
        return game.get_units().get_value(column=UnitColumn.LEVEL, unit=unit)

    @staticmethod
    def max_hit_points(*, game, unit):
        """Return the hit points a unit has when whole: its kind's, plus what its level adds."""
        return Levels.hit_points(theme=game.get_theme(), kind=UnitControl.kind_of(game=game, unit=unit), level=UnitControl.level_of(game=game, unit=unit))

    @staticmethod
    def armor_class_of(*, game, unit, bonus=NO_BONUS):
        """Return the armor class a unit defends with, at its level, with what a city's buildings add."""
        return UnitControl.armor_class(kind=UnitControl.kind_of(game=game, unit=unit), level=UnitControl.level_of(game=game, unit=unit), bonus=bonus)

    @staticmethod
    def roll_against(*, game, unit, target):
        """Return a unit's damage roll against another unit: its kind's dice against the other's class of unit, plus its level's bonus, drawn from the game's random source."""
        dice = attack_dice(kind=UnitControl.kind_of(game=game, unit=unit), target=UnitControl.kind_of(game=game, unit=target))
        return dice.roll(random=game.get_random()) + Levels.damage_bonus(level=UnitControl.level_of(game=game, unit=unit))

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
    def place(*, game, kind, owner, world, x, y, level=FIRST_LEVEL):
        """Put a new unit of a kind on a tile for a civilization, and return the unit's id.

        Only one unit may be on a tile, the tile's terrain has to be one the kind can be on, and
        no unit stands on a tile of a city center: a unit there is inside the city.
        """
        UnitControl.check_tile(game=game, kind=kind, world=world, x=x, y=y)
        unit = UnitControl.create(game=game, kind=kind, owner=owner, world=world, x=x, y=y, city=NOTHING, level=level)
        game.get_world(world).set_value(layer=Layer.UNIT, x=x, y=y, value=unit)
        return unit

    @staticmethod
    def create(*, game, kind, owner, world, x, y, city, level=FIRST_LEVEL):
        """Add a new unit of a kind to the units, whole at its level and with all its action points, and return the unit's id.

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
            UnitColumn.HIT_POINTS: Levels.hit_points(theme=game.get_theme(), kind=kind, level=level),
            UnitColumn.ACTION_POINTS: kind.ACTION_POINTS,
            UnitColumn.CITY: city,
            UnitColumn.LEVEL: level,
            UnitColumn.EXPERIENCE: Levels.experience_for(level=level),
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
