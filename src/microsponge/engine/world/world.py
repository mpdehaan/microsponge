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

"""One world: a map of tiles that wraps around from east to west."""

from microsponge.engine.kinds.catalog import NOTHING, renumbered
from microsponge.engine.saving.keys import text_keys
from microsponge.engine.world.layer import LAYERS
from microsponge.err_messages import ERR_LAYER_SHAPE, ERR_NO_SUCH_LAYER, ERR_ROW_OFF_THE_MAP, ERR_WORLD_SIZE

# What a saved game calls the parts of a world.
WIDTH_KEY = 'width'
HEIGHT_KEY = 'height'
LAYERS_KEY = 'layers'


def check_size(*, name, value):
    if type(value) is not int or value < 1:
        raise ValueError(ERR_WORLD_SIZE.format(name=name, value=value))
    return value


def rows_of(*, value, width, height):
    """Return a layer with the same value on every tile: a list of rows, each a list of integers."""
    return [[value] * width for _ in range(height)]


def check_rows(*, layer, rows, width, height):
    """Check that a layer read from a saved game is height rows of width tiles."""
    if len(rows) != height or any(len(row) != width for row in rows):
        raise ValueError(ERR_LAYER_SHAPE.format(layer=layer, height=height, width=width))
    return rows


class World:
    """A map of width by height tiles, held as one layer for each fact about a tile.

    Each layer is a list of rows of integers, so a world of 500 by 500 tiles with 10 layers is
    10 arrays of 500 by 500, and nothing is an object per tile. This class is the only code that
    touches the layers. Columns wrap: x is taken around the world, so the tile east of the last
    column is the first. Rows do not: a y off the top or the bottom is refused.
    """

    __slots__ = ('_width', '_height', '_layers')

    def __init__(self, *, width, height):
        self._width = check_size(name=WIDTH_KEY, value=width)
        self._height = check_size(name=HEIGHT_KEY, value=height)
        self._layers = {layer: rows_of(value=NOTHING, width=width, height=height) for layer in LAYERS}

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def column(self, x):
        """Return the column x lands on once it has gone around the world."""
        return x % self._width

    def columns_apart(self, *, first, second):
        """Return how many columns apart two columns are, going around the world the shorter way."""
        apart = abs(self.column(first) - self.column(second))
        return min(apart, self._width - apart)

    def row(self, y):
        """Return y, which has to be a row of the map, since the top and the bottom are edges."""
        if type(y) is not int or not 0 <= y < self._height:
            raise ValueError(ERR_ROW_OFF_THE_MAP.format(last=self._height - 1, value=y))
        return y

    def _rows(self, layer):
        try:
            return self._layers[layer]
        except (KeyError, TypeError):
            raise ValueError(ERR_NO_SUCH_LAYER.format(layer=layer)) from None

    def get_value(self, *, layer, x, y):
        """Return what a layer holds for the tile at x, y."""
        return self._rows(layer)[self.row(y)][x % self._width]

    def set_value(self, *, layer, x, y, value):
        self._rows(layer)[self.row(y)][x % self._width] = value

    def fill(self, *, layer, value):
        """Give every tile the same value in a layer."""
        self._rows(layer)
        self._layers[layer] = rows_of(value=value, width=self._width, height=self._height)

    def renumber(self, *, layer, numbers):
        """Replace each id in a layer with its number in numbers, after loading a game saved with other ids."""
        self._layers[layer] = [renumbered(values=row, numbers=numbers) for row in self._rows(layer)]

    def to_data(self):
        """Return the world as a saved game holds it. The layers are the world's own rows, not copies."""
        return {WIDTH_KEY: self._width, HEIGHT_KEY: self._height, LAYERS_KEY: text_keys(self._layers)}

    @classmethod
    def from_data(cls, data):
        """Return the world a saved game holds, taking its rows as the world's own.

        A layer the saved game lacks, because the layer was added later, has NOTHING on every
        tile. A layer the saved game holds that is not in LAYERS, because it was retired, is
        left behind.
        """
        world = cls(width=data[WIDTH_KEY], height=data[HEIGHT_KEY])
        saved = data[LAYERS_KEY]
        for layer in LAYERS:
            if str(layer) in saved:
                world._layers[layer] = check_rows(layer=layer, rows=saved[str(layer)], width=world._width, height=world._height)
        return world
