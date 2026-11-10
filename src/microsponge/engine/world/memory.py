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

"""What a civilization remembers of one world: every tile as the civilization last saw it, and who owned each city it has seen.

A memory is a map like the world itself, with the same layers but the units, since the fog of
war hides units and a civilization remembers none. A tile the civilization has never seen has
NOTHING for its terrain, which no real tile has. The owner of each city the civilization has
seen is kept beside the layers, as the owner was when the city was last seen, so that a
civilization that comes back may find a city in other hands, or gone.
"""

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.saving.keys import number_keys, text_keys
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.world import World

# The layers a memory holds: every layer of a world but the units.
REMEMBERED_LAYERS = (Layer.TERRAIN, Layer.CITY, Layer.CITY_CENTER, Layer.IMPROVEMENT, Layer.STRATEGIC_RESOURCE, Layer.TERRAIN_BONUS)
# What a saved game calls the owners of the cities a memory has seen.
OWNERS_KEY = 'owners'


class Memory(World):
    """One civilization's memory of one world."""

    __slots__ = ('_owners',)
    HELD_LAYERS = REMEMBERED_LAYERS

    def __init__(self, *, width, height):
        super().__init__(width=width, height=height)
        self._owners = {}

    def has_seen(self, *, x, y):
        """Return whether the civilization has ever seen a tile."""
        return self.get_value(layer=Layer.TERRAIN, x=x, y=y) != NOTHING

    def remember(self, *, world, tiles):
        """Record what a world holds on some tiles, in every remembered layer, as what the civilization last saw there."""
        for layer in REMEMBERED_LAYERS:
            for x, y in tiles:
                self.set_value(layer=layer, x=x, y=y, value=world.get_value(layer=layer, x=x, y=y))

    def remember_all(self, world):
        """Record every tile of a world, for a theme whose land starts explored."""
        self.remember(world=world, tiles=[(x, y) for y in range(self.get_height()) for x in range(self.get_width())])

    def remember_owner(self, *, city, owner):
        self._owners[city] = owner

    def get_owner(self, city):
        """Return who owned a city when the civilization last saw it, or NOTHING for a city never seen."""
        return self._owners.get(city, NOTHING)

    def to_data(self):
        return {**super().to_data(), OWNERS_KEY: text_keys(self._owners)}

    @classmethod
    def from_data(cls, data):
        memory = super().from_data(data)
        memory._owners = number_keys(data[OWNERS_KEY])
        return memory
