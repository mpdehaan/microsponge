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

"""The pieces of a world that a kind of unit can walk around in, and how much of a piece is near a tile."""

from microsponge.engine.kinds.category import Category
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.square_count import SquareCount

# The eight tiles around a tile, as (dx, dy): a unit moves to any of them.
NEIGHBORS = tuple((dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0))
# The piece of a tile that the kind of unit cannot be on.
NO_PIECE = 0
FIRST_PIECE = 1


class Land:
    """The tiles of a world a kind of unit can be on, split into pieces: a unit walks from a tile to every other tile of the same piece, and to no tile of another.

    The pieces are found once, from the terrain alone, when the object is made. A change of
    terrain afterwards is not followed.
    """

    __slots__ = ('_world', '_pieces', '_tiles', '_counts')

    def __init__(self, *, game, world_id, kind):
        self._world = game.get_world(world_id)
        self._pieces = [[NO_PIECE] * self._world.get_width() for _ in range(self._world.get_height())]
        self._tiles = {}
        self._counts = {}
        walkable = Land.walkable_terrains(game=game, kind=kind)
        piece = FIRST_PIECE
        for y in range(self._world.get_height()):
            for x in range(self._world.get_width()):
                if self._pieces[y][x] == NO_PIECE and self._world.get_value(layer=Layer.TERRAIN, x=x, y=y) in walkable:
                    self._tiles[piece] = self._spread(piece=piece, x=x, y=y, walkable=walkable)
                    piece += 1

    @staticmethod
    def walkable_terrains(*, game, kind):
        """Return the ids of the terrains a kind of unit can be on."""
        catalog = game.get_catalog()
        return {catalog.get_id(category=Category.TERRAINS, kind=terrain) for terrain in game.get_theme().TERRAINS if UnitControl.can_be_on(kind=kind, terrain=terrain)}

    def _spread(self, *, piece, x, y, walkable):
        """Mark every tile a unit can walk to from a tile as one piece, and return the tiles."""
        self._pieces[y][x] = piece
        found = [(x, y)]
        for from_x, from_y in found:
            for dx, dy in NEIGHBORS:
                to_x = self._world.column(from_x + dx)
                to_y = from_y + dy
                if 0 <= to_y < self._world.get_height() and self._pieces[to_y][to_x] == NO_PIECE and self._world.get_value(layer=Layer.TERRAIN, x=to_x, y=to_y) in walkable:
                    self._pieces[to_y][to_x] = piece
                    found.append((to_x, to_y))
        return found

    def get_piece(self, *, x, y):
        """Return the piece a tile belongs to, or NO_PIECE for a tile the kind of unit cannot be on."""
        return self._pieces[y][self._world.column(x)]

    def reachable_in(self, *, x, y, size):
        """Return how many tiles of the square of a size around a tile a unit standing on the tile can walk to, the tile itself included."""
        piece = self.get_piece(x=x, y=y)
        if piece == NO_PIECE:
            return 0
        if piece not in self._counts:
            self._counts[piece] = SquareCount(world=self._world, marked=self._tiles[piece])
        return self._counts[piece].in_square(x=x, y=y, size=size)
