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

"""Counting the marked tiles of a world inside a square, quickly, for code that asks about very many squares."""

from microsponge.engine.cities.city_control import span


class SquareCount:
    """How many of some marked tiles of a world are inside any square, from a running count along each row.

    The map generator asks about a square around every possible starting site, so each row
    keeps how many marked tiles lie west of each column, and a square is then two lookups for
    each of its rows. Columns go around the world, and rows off the world hold nothing.
    """

    __slots__ = ('_world', '_running')

    def __init__(self, *, world, marked):
        """Count the marked tiles of a world, given as (x, y) with each tile once."""
        self._world = world
        rows = [[0] * (world.get_width() + 1) for _ in range(world.get_height())]
        for x, y in marked:
            rows[y][x + 1] = 1
        for row in rows:
            for column in range(1, len(row)):
                row[column] += row[column - 1]
        self._running = rows

    def in_square(self, *, x, y, size):
        """Return how many marked tiles are in the square of a size that has a tile in its middle."""
        height = self._world.get_height()
        return sum(self._in_row(row=row, x=x, size=size) for row in span(middle=y, size=size) if 0 <= row < height)

    def _in_row(self, *, row, x, size):
        """Return how many marked tiles of one row are in the columns of a square, which may go around the world."""
        running = self._running[row]
        width = self._world.get_width()
        if size >= width:
            return running[width]
        start = self._world.column(x - size // 2)
        end = start + size
        if end <= width:
            return running[end] - running[start]
        return running[width] - running[start] + running[end - width]
