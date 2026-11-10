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

"""The view a civilization has of the game: the map as the civilization sees it right now where it has vision, and as it remembers it elsewhere.

A screen and a computer player both read the map through a view, made by `Sight.view()` for
one civilization at one moment, and never through the world itself, so that neither sees
through the fog of war. A view is read and then dropped: it holds the tiles in vision as a set,
worked out once.
"""

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.world.layer import Layer


class View:
    """What one civilization can see and remembers, at one moment."""

    __slots__ = ('_game', '_civilization', '_vision', '_every_unit')

    def __init__(self, *, game, civilization, vision, every_unit):
        self._game = game
        self._civilization = civilization
        self._vision = vision
        self._every_unit = every_unit

    def get_civilization(self):
        return self._civilization

    def can_see(self, *, world, x, y):
        """Return whether a tile is within the civilization's vision right now."""
        return (world, self._game.get_world(world).column(x), y) in self._vision

    def has_seen(self, *, world, x, y):
        """Return whether the civilization has ever seen a tile, so that the tile is drawn at all."""
        return self.can_see(world=world, x=x, y=y) or self._game.get_civilization(self._civilization).get_memory(world).has_seen(x=x, y=y)

    def remembered(self, *, world, layer, x, y):
        """Return what a layer holds on a tile as the civilization knows it: as it is where the tile is in vision, as last seen elsewhere, and NOTHING on a tile never seen."""
        if self.can_see(world=world, x=x, y=y):
            return self._game.get_world(world).get_value(layer=layer, x=x, y=y)
        return self._game.get_civilization(self._civilization).get_memory(world).get_value(layer=layer, x=x, y=y)

    def owner_of(self, city):
        """Return who owns a city as the civilization knows it: the owner now when the city center is in vision, else the owner when last seen, and NOTHING for a city never seen."""
        target = self._game.get_city(city)
        if self.can_see(world=target.get_world(), x=target.get_x(), y=target.get_y()):
            return target.get_owner()
        return self._game.get_civilization(self._civilization).get_memory(target.get_world()).get_owner(city)

    def units_seen(self):
        """Return the ids of the other civilizations' units the civilization sees: every unit on a tile in vision, or every unit on any tile once the fog of war has ended. A unit inside a city is on no tile and is not seen."""
        units = self._game.get_units()
        seen = []
        for unit in units.get_ids():
            if units.get_value(column=UnitColumn.OWNER, unit=unit) in (NOTHING, self._civilization) or units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING:
                continue
            world = units.get_value(column=UnitColumn.WORLD, unit=unit)
            if self._every_unit or self.can_see(world=world, x=units.get_value(column=UnitColumn.X, unit=unit), y=units.get_value(column=UnitColumn.Y, unit=unit)):
                seen.append(unit)
        return seen

    def unit_on(self, *, world, x, y):
        """Return the unit the civilization sees on a tile, or NOTHING: its own units always, another civilization's only in vision or once the fog of war has ended."""
        unit = self._game.get_world(world).get_value(layer=Layer.UNIT, x=x, y=y)
        if unit == NOTHING or self._game.get_units().get_value(column=UnitColumn.OWNER, unit=unit) == self._civilization:
            return unit
        return unit if self._every_unit or self.can_see(world=world, x=x, y=y) else NOTHING
