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

"""Strategic resources: where they are on the map, and which a civilization has within its borders."""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import StrategicResource
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_NOT_STRATEGIC, ERR_RESOURCE_NOT_ON


def each_once(kinds):
    """Return some kinds with every repeat left out, in the order each first comes."""
    return list(dict.fromkeys(kinds))


class Strategic:
    """The rules for strategic resources, as static methods over a game. It is never made into an object.

    A strategic resource is on a tile and is never collected or used up. A civilization has
    the resource while a tile with the resource is within the borders of the civilization: the
    city limits of its cities, whether or not a citizen works the tile.
    """

    __slots__ = ()

    @staticmethod
    def resource_at(*, game, world, x, y):
        """Return the strategic resource on a tile, as the theme's class, or None."""
        resource = game.get_world(world).get_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y)
        return None if resource == NOTHING else game.get_catalog().get_kind(category=Category.RESOURCES, kind_id=resource)

    @staticmethod
    def problem_placing(*, game, world, x, y, resource):
        """Return why a resource cannot be put on a tile, as an error message, or None when it can: the resource has to be strategic, and the tile of a terrain that can have it."""
        if not issubclass(resource, StrategicResource):
            return ERR_NOT_STRATEGIC.format(resource=shown_name(resource))
        terrain = game.get_terrain(world=world, x=x, y=y)
        if resource not in terrain.CAN_HAVE:
            return ERR_RESOURCE_NOT_ON.format(resource=shown_name(resource), terrain=shown_name(terrain))
        return None

    @staticmethod
    def place(*, game, world, x, y, resource):
        """Put a strategic resource on a tile, in place of any the tile had."""
        problem = Strategic.problem_placing(game=game, world=world, x=x, y=y, resource=resource)
        if problem is not None:
            raise ValueError(problem)
        resource_id = game.get_catalog().get_id(category=Category.RESOURCES, kind=resource)
        game.get_world(world).set_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y, value=resource_id)

    @staticmethod
    def remove(*, game, world, x, y):
        """Take the strategic resource off a tile, for good."""
        game.get_world(world).set_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y, value=NOTHING)

    @staticmethod
    def terrain_changed(*, game, world, x, y):
        """Take the strategic resource off a tile whose terrain has changed to one that cannot have the resource."""
        resource = Strategic.resource_at(game=game, world=world, x=x, y=y)
        if resource is not None and resource not in game.get_terrain(world=world, x=x, y=y).CAN_HAVE:
            Strategic.remove(game=game, world=world, x=x, y=y)

    @staticmethod
    def of_city(*, game, city):
        """Return the strategic resources on the tiles that belong to a city, as the theme's classes, one for each tile that has one."""
        world = game.get_city(city).get_world()
        found = [Strategic.resource_at(game=game, world=world, x=x, y=y) for x, y in CityControl.radius_tiles(game=game, city=city)]
        return [resource for resource in found if resource is not None]

    @staticmethod
    def held(*, game, civilization):
        """Return the strategic resources within the borders of a civilization, as the theme's classes, each once."""
        found = []
        for city in game.get_cities_of(civilization):
            found += Strategic.of_city(game=game, city=city)
        return each_once(found)
