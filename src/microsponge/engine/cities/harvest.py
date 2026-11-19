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

"""What the citizens of a city collect each turn, and which tile each citizen takes."""

from dataclasses import dataclass

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl

NOTHING_GIVEN = 0
WHOLE = 100


@dataclass(slots=True, kw_only=True)
class WorkableTile:
    """A tile a citizen can work, and what it gives the citizen each turn: each resource with its amount."""

    x: int
    y: int
    gives: dict

    def amount_of(self, resource):
        return self.gives.get(resource, NOTHING_GIVEN)

    def amount_of_everything(self):
        return sum(self.gives.values())


def added(*, totals, amounts):
    """Add amounts of resources to running totals of them."""
    for resource, amount in amounts.items():
        totals[resource] = totals.get(resource, NOTHING_GIVEN) + amount


def most_of(*, tiles, resource):
    """Return the tile that gives the most of a resource, or None when no tile gives any.

    The tiles come nearest the middle of the city first, and of several tiles that give the
    same, the first is returned, so the nearest wins.
    """
    giving = [tile for tile in tiles if tile.amount_of(resource) > NOTHING_GIVEN]
    return max(giving, key=lambda tile: tile.amount_of(resource), default=None)


def most_of_anything(tiles):
    """Return the tile that gives the most of all resources together, the nearest of several, or None when no tile gives anything."""
    giving = [tile for tile in tiles if tile.amount_of_everything() > NOTHING_GIVEN]
    return max(giving, key=WorkableTile.amount_of_everything, default=None)


class Harvest:
    """How a city's citizens collect resources, as static methods over a game. It is never made into an object.

    Citizens are never managed by hand. Each working citizen takes one tile of the city, and no
    two share a tile. A citizen the city's settings give a priority looks for that resource
    first. Every citizen falls back to food, and when no tile gives food, to the tile that
    delivers the most of anything.
    """

    __slots__ = ()

    @staticmethod
    def tile_gives(*, game, world, x, y):
        """Return what a tile gives the citizen who works it each turn: each resource with its amount, from its terrain, its terrain bonus and its improvement."""
        catalog = game.get_catalog()
        tiles = game.get_world(world)
        gives = dict(game.get_terrain(world=world, x=x, y=y).GIVES)
        added(totals=gives, amounts=TerrainBonusControl.gives(game=game, world=world, x=x, y=y))
        improvement = tiles.get_value(layer=Layer.IMPROVEMENT, x=x, y=y)
        if improvement != NOTHING:
            added(totals=gives, amounts=catalog.get_kind(category=Category.IMPROVEMENTS, kind_id=improvement).TILE_BONUS)
        return gives

    @staticmethod
    def city_tile_gives(*, game, city, x, y):
        """Return what a tile gives a citizen of a city who works it: what the tile gives, and what the city's buildings add to a worked tile of its terrain."""
        world = game.get_city(city).get_world()
        gives = Harvest.tile_gives(game=game, world=world, x=x, y=y)
        terrain = game.get_terrain(world=world, x=x, y=y)
        for building in CityControl.buildings_of(game=game, city=city):
            added(totals=gives, amounts=building.WORKED_TILE_BONUS.get(terrain, {}))
        return gives

    @staticmethod
    def workable_tiles(*, game, city):
        """Return the tiles a city's citizens can work, nearest the middle of the city first.

        They are the tiles of the city radius that belong to the city, outside its city center.
        """
        target = game.get_city(city)
        world = game.get_world(target.get_world())

        def steps_away(tile):
            x, y = tile
            return max(world.columns_apart(first=x, second=target.get_x()), abs(y - target.get_y()))

        def is_workable(tile):
            x, y = tile
            return world.get_value(layer=Layer.CITY, x=x, y=y) == city and world.get_value(layer=Layer.CITY_CENTER, x=x, y=y) == NOTHING

        own = sorted(filter(is_workable, CityControl.radius_tiles(game=game, city=city)), key=steps_away)
        return [WorkableTile(x=x, y=y, gives=Harvest.city_tile_gives(game=game, city=city, x=x, y=y)) for x, y in own]

    @staticmethod
    def wanted(*, game, city):
        """Return the resource each citizen of a city looks for first, the citizens with a priority first. None is a citizen with no priority."""
        target = game.get_city(city)
        catalog = game.get_catalog()
        first = []
        for resource, citizens in sorted(target.get_priorities().items()):
            first += [catalog.get_kind(category=Category.RESOURCES, kind_id=resource)] * citizens
        first = first[:target.get_citizens()]
        return first + [None] * (target.get_citizens() - len(first))

    @staticmethod
    def assignments(*, game, city):
        """Return the tile each working citizen of a city takes, in the order the citizens choose. A citizen with no tile left does not work."""
        food = game.get_theme().FOOD
        free = Harvest.workable_tiles(game=game, city=city)
        taken = []
        for resource in Harvest.wanted(game=game, city=city):
            tile = most_of(tiles=free, resource=resource) or most_of(tiles=free, resource=food) or most_of_anything(free)
            if tile is None:
                break
            free.remove(tile)
            taken.append(tile)
        return taken

    @staticmethod
    def of_city(*, game, city):
        """Return what a city collects in a turn: each resource with its amount.

        That is what its working citizens' tiles give, the currency each working citizen
        generates, and what the city and each of its buildings produce by themselves. A
        building can then add a percent to the currency, rounded down.
        """
        theme = game.get_theme()
        buildings = CityControl.buildings_of(game=game, city=city)
        totals = {}
        worked = Harvest.assignments(game=game, city=city)
        for tile in worked:
            added(totals=totals, amounts=tile.gives)
        for producer in [theme.CITY, *buildings]:
            added(totals=totals, amounts=producer.PRODUCES)
        added(totals=totals, amounts={theme.PRIMARY_RESOURCE: theme.CITY.CITIZEN_CURRENCY * len(worked)})
        income_percent = WHOLE + sum(building.INCOME_BONUS for building in buildings)
        totals[theme.PRIMARY_RESOURCE] = totals[theme.PRIMARY_RESOURCE] * income_percent // WHOLE
        return totals
