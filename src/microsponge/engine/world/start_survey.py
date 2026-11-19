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

"""A survey of a world for the map generator: how good each tile is as the place a civilization starts."""

from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.world.land import Land
from microsponge.engine.world.square_count import SquareCount

WHOLE = 100
# A square that reaches a number of steps each way from its middle tile is this many tiles wide for each step, plus the middle tile.
SIDES_OF_A_REACH = 2
MIDDLE_TILE = 1


def square_size(reach):
    """Return the width of the square that reaches a number of steps each way from its middle tile."""
    return reach * SIDES_OF_A_REACH + MIDDLE_TILE


class StartSurvey:
    """What the map generator knows about a world when it chooses where civilizations start, read once from the world as the world is when the survey is made.

    A starting site is judged by what the theme's MAP spec asks of one: room, which is enough
    of the tiles around the site that the starting unit can walk to; the resources the first
    city radius must give; and the strategic resources that must be near. The survey names no
    kind of any theme.
    """

    __slots__ = ('_game', '_land', '_giving', '_holding')

    def __init__(self, *, game, world_id, kind):
        """Survey a world for a kind of unit, the one each civilization starts with."""
        spec = game.get_theme().MAP
        world = game.get_world(world_id)
        self._game = game
        self._land = Land(game=game, world_id=world_id, kind=kind)
        giving = {resource: [] for resource in spec.START_NEEDS}
        holding = {resource: [] for resource in spec.START_STRATEGIC}
        for y in range(world.get_height()):
            for x in range(world.get_width()):
                for resource in Harvest.tile_gives(game=game, world=world_id, x=x, y=y):
                    if resource in giving:
                        giving[resource].append((x, y))
                held = Strategic.resource_at(game=game, world=world_id, x=x, y=y)
                if held in holding:
                    holding[held].append((x, y))
        self._giving = {resource: SquareCount(world=world, marked=tiles) for resource, tiles in giving.items()}
        self._holding = {resource: SquareCount(world=world, marked=tiles) for resource, tiles in holding.items()}

    def has_room(self, *, x, y):
        """Return whether enough of the tiles within the theme's START_REACH steps of a tile can be walked to from the tile. Tiles off the world count as tiles that cannot."""
        spec = self._game.get_theme().MAP
        size = square_size(spec.START_REACH)
        return self._land.reachable_in(x=x, y=y, size=size) * WHOLE >= spec.START_REACHABLE_PERCENT * size * size

    def radius_gives(self, *, x, y):
        """Return, for each resource a first city radius must give, how many tiles of the radius of a city founded on a tile give the resource, outside the city center."""
        city = self._game.get_theme().CITY
        return {resource: count.in_square(x=x, y=y, size=city.RADIUS_SIZE) - count.in_square(x=x, y=y, size=city.CENTER_SIZE) for resource, count in self._giving.items()}

    def lacks(self, *, x, y):
        """Return the resources the radius of a city founded on a tile gives on too few tiles, each with how many tiles it is short."""
        needs = self._game.get_theme().MAP.START_NEEDS
        return {resource: needs[resource] - tiles for resource, tiles in self.radius_gives(x=x, y=y).items() if tiles < needs[resource]}

    def misses(self, *, x, y):
        """Return the strategic resources that must be near a start and are not within the theme's START_STRATEGIC_DISTANCE of the radius of a city founded on a tile."""
        size = strategic_square_size(self._game.get_theme())
        return [resource for resource, count in self._holding.items() if count.in_square(x=x, y=y, size=size) == 0]

    def is_ready(self, *, x, y):
        """Return whether a tile is a good starting site as the world is: room, and nothing lacking or missing."""
        return self.has_room(x=x, y=y) and not self.lacks(x=x, y=y) and not self.misses(x=x, y=y)


def strategic_square_size(theme):
    """Return the width of the square around a starting site in which the strategic resources of a start must be: the first city radius and the theme's START_STRATEGIC_DISTANCE past each side."""
    return theme.CITY.RADIUS_SIZE + theme.MAP.START_STRATEGIC_DISTANCE * SIDES_OF_A_REACH
