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

"""The rules for cities: where one can be built, which tiles it covers, and how units get inside and out."""

from microsponge.engine.cities.city import City
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.units.levels import FIRST_LEVEL, LAST_LEVEL
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_CANNOT_TAKE_CITIES, ERR_CITY_COVERS_A_UNIT, ERR_CITY_COVERS_TERRAIN, ERR_CITY_DEFENDED, ERR_CITY_FULL, ERR_CITY_NEEDS_LAND, ERR_CITY_OFF_THE_MAP, ERR_CITY_TOO_CLOSE, ERR_NOT_A_SETTLER,
    ERR_NOT_AT_WAR, ERR_NOT_NEXT_TO_CENTER, ERR_NOT_NEXT_TO_CITY, ERR_UNIT_IN_A_CITY, ERR_UNIT_NOT_IN_A_CITY,
)

# The tiles next to the city center make a square this much wider than the center, with the center cut out.
RING_WIDTH = 2


def span(*, middle, size):
    """Return the columns, or the rows, of a square of a size that has middle in its middle."""
    half = size // 2
    return range(middle - half, middle + half + 1)


def square(*, x, y, size):
    """Return every tile of a square as (x, y), row by row. The tiles may be off the map."""
    return [(column, row) for row in span(middle=y, size=size) for column in span(middle=x, size=size)]


def reaches_off_the_map(*, tiles, world):
    """Return whether any tile is past the top or the bottom of a world."""
    return any(not 0 <= row < world.get_height() for _, row in tiles)


def on_the_map(*, tiles, world):
    """Return the tiles that are on a world, each with its column taken around the world."""
    return [(world.column(column), row) for column, row in tiles if 0 <= row < world.get_height()]


class CityControl:
    """The rules for cities, as static methods over a game. It is never made into an object.

    It keeps the two layers that say what a city covers: the city layer, which says whose city
    radius a tile belongs to, and the city center layer, which says whose city center covers a
    tile. City radii never overlap, so a tile belongs to one city at most.
    """

    __slots__ = ()

    @staticmethod
    def center_tiles(*, game, city):
        """Return the tiles of a city's center, as (x, y)."""
        return CityControl._tiles(game=game, city=city, size=game.get_theme().CITY.CENTER_SIZE)

    @staticmethod
    def radius_tiles(*, game, city):
        """Return the tiles of a city's radius, as (x, y)."""
        return CityControl._tiles(game=game, city=city, size=game.get_theme().CITY.RADIUS_SIZE)

    @staticmethod
    def ring_tiles(*, game, city):
        """Return the tiles next to a city's center, as (x, y): where a unit enters the city from, and leaves it to."""
        center = set(CityControl.center_tiles(game=game, city=city))
        around = CityControl._tiles(game=game, city=city, size=game.get_theme().CITY.CENTER_SIZE + RING_WIDTH)
        return [tile for tile in around if tile not in center]

    @staticmethod
    def _tiles(*, game, city, size):
        """Return the tiles on the map of a square of a size around the middle of a city."""
        target = game.get_city(city)
        return on_the_map(tiles=square(x=target.get_x(), y=target.get_y(), size=size), world=game.get_world(target.get_world()))

    @staticmethod
    def problem_founding(*, game, settler):
        """Return why a unit cannot build a city where it stands, as an error message, or None when it can.

        The unit has to be a settler on a tile of its own. The whole city center has to be on
        the map, covering no other unit and no terrain that nothing can be built on, with enough
        land, and the city radius has to be outside every other city radius.
        """
        units = game.get_units()
        spec = game.get_theme().CITY
        kind = UnitControl.kind_of(game=game, unit=settler)
        if not issubclass(kind, SettlerUnit):
            return ERR_NOT_A_SETTLER.format(unit=shown_name(kind), city=spec.NAME)
        if units.get_value(column=UnitColumn.CITY, unit=settler) != NOTHING:
            return ERR_UNIT_IN_A_CITY.format(unit=settler, city=spec.NAME)
        world_id, x, y = UnitControl.tile_of(game=game, unit=settler)
        world = game.get_world(world_id)
        center = square(x=x, y=y, size=spec.CENTER_SIZE)
        if reaches_off_the_map(tiles=center, world=world):
            return ERR_CITY_OFF_THE_MAP.format(city=spec.NAME)
        for tile_x, tile_y in on_the_map(tiles=square(x=x, y=y, size=spec.RADIUS_SIZE), world=world):
            neighbor = world.get_value(layer=Layer.CITY, x=tile_x, y=tile_y)
            if neighbor != NOTHING:
                return ERR_CITY_TOO_CLOSE.format(city=spec.NAME, name=game.get_city(neighbor).get_name())
        land = 0
        for tile_x, tile_y in center:
            if world.get_value(layer=Layer.UNIT, x=tile_x, y=tile_y) not in (NOTHING, settler):
                return ERR_CITY_COVERS_A_UNIT.format(city=spec.NAME, x=world.column(tile_x), y=tile_y)
            terrain = game.get_terrain(world=world_id, x=tile_x, y=tile_y)
            if not terrain.BUILDABLE:
                return ERR_CITY_COVERS_TERRAIN.format(city=spec.NAME, terrain=shown_name(terrain), x=world.column(tile_x), y=tile_y)
            land += terrain.LAND
        if land < spec.CENTER_LAND:
            return ERR_CITY_NEEDS_LAND.format(city=spec.NAME, least=spec.CENTER_LAND, land=land)
        return None

    @staticmethod
    def found(*, game, settler, name):
        """Build a city where a settler stands, and return the city's id. The settler expends itself: it is gone."""
        problem = CityControl.problem_founding(game=game, settler=settler)
        if problem is not None:
            raise ValueError(problem)
        world_id, x, y = UnitControl.tile_of(game=game, unit=settler)
        owner = game.get_units().get_value(column=UnitColumn.OWNER, unit=settler)
        city = City(name=name, owner=owner, world=world_id, x=x, y=y, founded=game.get_turn(), citizens=game.get_theme().CITY.STARTING_CITIZENS)
        UnitControl.remove(game=game, unit=settler)
        city_id = game.add_city(city)
        game.get_civilization(owner).count_founded_city()
        world = game.get_world(world_id)
        for tile_x, tile_y in CityControl.radius_tiles(game=game, city=city_id):
            if world.get_value(layer=Layer.CITY, x=tile_x, y=tile_y) == NOTHING:
                world.set_value(layer=Layer.CITY, x=tile_x, y=tile_y, value=city_id)
        for tile_x, tile_y in CityControl.center_tiles(game=game, city=city_id):
            world.set_value(layer=Layer.CITY_CENTER, x=tile_x, y=tile_y, value=city_id)
        return city_id

    @staticmethod
    def buildings_of(*, game, city):
        """Return the buildings a city has, as the theme's classes."""
        catalog = game.get_catalog()
        return [catalog.get_kind(category=Category.BUILDINGS, kind_id=building) for building in game.get_city(city).get_buildings()]

    @staticmethod
    def has_room(*, game, city):
        """Return whether a city can hold one more unit."""
        return len(game.get_city(city).get_units()) < game.get_theme().CITY.MOST_UNITS

    @staticmethod
    def is_beside_water(*, game, city):
        """Return whether any tile next to a city's center is water."""
        world = game.get_city(city).get_world()
        return any(not game.get_terrain(world=world, x=x, y=y).LAND for x, y in CityControl.ring_tiles(game=game, city=city))

    @staticmethod
    def free_ring_tiles(*, game, city, kind):
        """Return the tiles next to a city's center that a unit of a kind can stand on, as (x, y)."""
        world = game.get_city(city).get_world()
        return [(x, y) for x, y in CityControl.ring_tiles(game=game, city=city) if UnitControl.problem_standing(game=game, kind=kind, world=world, x=x, y=y) is None]

    @staticmethod
    def muster(*, game, city, kind):
        """Make a new unit of a kind that a city has finished, and return the unit's id, or None when there is nowhere to put the unit.

        The unit goes inside the city. When the city is full of units, the unit goes on a tile
        next to the city center that it can stand on, chosen at random. The unit starts at the
        level the city's buildings give, like a barracks that starts units at level 2.
        """
        target = game.get_city(city)
        level = CityControl.starting_level(game=game, city=city)
        if CityControl.has_room(game=game, city=city):
            unit = UnitControl.create(game=game, kind=kind, owner=target.get_owner(), world=target.get_world(), x=target.get_x(), y=target.get_y(), city=city, level=level)
            target.add_unit(unit)
            return unit
        free = CityControl.free_ring_tiles(game=game, city=city, kind=kind)
        if not free:
            return None
        x, y = game.get_random().choice(free)
        return UnitControl.place(game=game, kind=kind, owner=target.get_owner(), world=target.get_world(), x=x, y=y, level=level)

    @staticmethod
    def starting_level(*, game, city):
        """Return the level a unit built in a city starts at: the first, plus what each of the city's buildings adds, never past the last level."""
        return min(FIRST_LEVEL + sum(building.LEVEL_BONUS for building in CityControl.buildings_of(game=game, city=city)), LAST_LEVEL)

    @staticmethod
    def armor_bonus(*, game, city, against):
        """Return by how much a city's buildings make the armor class of every unit inside better against a kind of unit, like a watchtower's. City walls add nothing against a kind that bypasses walls."""
        buildings = CityControl.buildings_of(game=game, city=city)
        return sum(building.ARMOR_BONUS for building in buildings if not (building.WALLS and against.BYPASSES_WALLS))

    @staticmethod
    def capture(*, game, city, by):
        """Give a city with no units inside to another civilization, with its buildings and its priorities as they are. Everything the city was building ends, with no refund."""
        target = game.get_city(city)
        target.set_owner(by)
        target.clear_queue()
        target.set_builds_nothing(False)

    @staticmethod
    def problem_taking(*, game, unit, city):
        """Return why a unit cannot take a city of another civilization by going inside, as an error message, or None when it can.

        The unit's civilization has to be at war with the city's, no unit can be inside the
        city, and the unit's kind has to be one that takes cities.
        """
        units = game.get_units()
        spec = game.get_theme().CITY
        target = game.get_city(city)
        owner = units.get_value(column=UnitColumn.OWNER, unit=unit)
        if not game.get_civilization(owner).is_at_war_with(target.get_owner()):
            return ERR_NOT_AT_WAR.format(name=game.get_civilization(target.get_owner()).get_name())
        if target.get_units():
            return ERR_CITY_DEFENDED.format(name=target.get_name())
        kind = UnitControl.kind_of(game=game, unit=unit)
        if not kind.TAKES_CITIES:
            return ERR_CANNOT_TAKE_CITIES.format(unit=shown_name(kind), city=spec.NAME)
        return None

    @staticmethod
    def enter(*, game, unit, city):
        """Move a unit from a tile next to the center of a city into the city, which holds only so many units. A city of another civilization with no unit inside is taken."""
        units = game.get_units()
        spec = game.get_theme().CITY
        target = game.get_city(city)
        if units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING:
            raise ValueError(ERR_UNIT_IN_A_CITY.format(unit=unit, city=spec.NAME))
        owner = units.get_value(column=UnitColumn.OWNER, unit=unit)
        taking = owner != target.get_owner()
        if taking:
            problem = CityControl.problem_taking(game=game, unit=unit, city=city)
            if problem is not None:
                raise ValueError(problem)
        world_id, x, y = UnitControl.tile_of(game=game, unit=unit)
        if world_id != target.get_world() or (x, y) not in CityControl.ring_tiles(game=game, city=city):
            raise ValueError(ERR_NOT_NEXT_TO_CITY.format(unit=unit, city=spec.NAME, name=target.get_name()))
        if not CityControl.has_room(game=game, city=city):
            raise ValueError(ERR_CITY_FULL.format(city=spec.NAME, name=target.get_name(), most=spec.MOST_UNITS))
        game.get_world(world_id).set_value(layer=Layer.UNIT, x=x, y=y, value=NOTHING)
        units.set_value(column=UnitColumn.X, unit=unit, value=target.get_x())
        units.set_value(column=UnitColumn.Y, unit=unit, value=target.get_y())
        units.set_value(column=UnitColumn.CITY, unit=unit, value=city)
        target.add_unit(unit)
        if taking:
            CityControl.capture(game=game, city=city, by=owner)

    @staticmethod
    def leave(*, game, unit, x, y):
        """Move a unit out of the city it is inside, onto an empty tile next to the city center that its kind can be on."""
        units = game.get_units()
        spec = game.get_theme().CITY
        city = units.get_value(column=UnitColumn.CITY, unit=unit)
        if city == NOTHING:
            raise ValueError(ERR_UNIT_NOT_IN_A_CITY.format(unit=unit, city=spec.NAME))
        target = game.get_city(city)
        world = game.get_world(target.get_world())
        if type(y) is not int or (world.column(x), y) not in CityControl.ring_tiles(game=game, city=city):
            raise ValueError(ERR_NOT_NEXT_TO_CENTER.format(x=x, y=y, city=spec.NAME, name=target.get_name()))
        UnitControl.check_tile(game=game, kind=UnitControl.kind_of(game=game, unit=unit), world=target.get_world(), x=x, y=y)
        target.remove_unit(unit)
        units.set_value(column=UnitColumn.X, unit=unit, value=world.column(x))
        units.set_value(column=UnitColumn.Y, unit=unit, value=y)
        units.set_value(column=UnitColumn.CITY, unit=unit, value=NOTHING)
        world.set_value(layer=Layer.UNIT, x=x, y=y, value=unit)
