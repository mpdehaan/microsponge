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

"""The rules of visibility: what a civilization sees right now, and what it records in its memory of each world.

A civilization sees the tiles within the vision radius of each of its units, a square with the
unit in the middle (`VISION` of the kind), and the city radius of each of its cities. What it
sees it remembers (`Memory`), as the tiles were when last seen. A technology with
`ENDS_FOG_OF_WAR` lets a civilization see every unit everywhere, but reveals no land.
`Sight.view()` gives the `View` a player or a computer player reads the map through.
"""

from microsponge.engine.cities.city_control import CityControl, on_the_map, square
from microsponge.engine.civilizations.view import View
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.memory import Memory

# The first civilization's id; the civilizations are numbered from 1 in the order they joined.
FIRST_CIVILIZATION = 1


def vision_size(kind):
    """Return the side of the square a kind of unit sees: the vision radius each way and the unit's own tile."""
    return 2 * kind.VISION + 1


class Sight:
    """Static: the rules of visibility, working on the game's units, cities and memories. It is never made into an object."""

    __slots__ = ()

    @staticmethod
    def start(game):
        """Give every civilization a blank memory of every world, or the whole map when the theme starts explored, and let each see what is around it."""
        for civilization, holder in enumerate(game.get_civilizations(), start=FIRST_CIVILIZATION):
            for world in game.get_worlds():
                memory = Memory(width=world.get_width(), height=world.get_height())
                if game.get_theme().LAND_STARTS_EXPLORED:
                    memory.remember_all(world)
                holder.add_memory(memory)
            Sight.refresh(game=game, civilization=civilization)

    @staticmethod
    def refresh(*, game, civilization):
        """Record everything a civilization sees right now, around every unit and in every city radius."""
        for unit in Sight.units_of(game=game, civilization=civilization):
            Sight.look_around_unit(game=game, unit=unit)
        for city in game.get_city_ids():
            if game.get_city(city).get_owner() == civilization:
                Sight.look_around_city(game=game, city=city)

    @staticmethod
    def units_of(*, game, civilization):
        """Return the ids of a civilization's units."""
        units = game.get_units()
        return [unit for unit in units.get_ids() if units.get_value(column=UnitColumn.OWNER, unit=unit) == civilization]

    @staticmethod
    def tiles_around_unit(*, game, unit):
        """Return the tiles a unit sees, as (x, y) on its world."""
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        return on_the_map(tiles=square(x=x, y=y, size=vision_size(UnitControl.kind_of(game=game, unit=unit))), world=game.get_world(world))

    @staticmethod
    def look_around_unit(*, game, unit):
        """Record what a unit's civilization sees around the unit, after the unit has moved."""
        world = UnitControl.tile_of(game=game, unit=unit)[0]
        owner = game.get_units().get_value(column=UnitColumn.OWNER, unit=unit)
        Sight.look(game=game, civilization=owner, world=world, tiles=Sight.tiles_around_unit(game=game, unit=unit))

    @staticmethod
    def look_around_city(*, game, city):
        """Record what a city's civilization sees in the city radius, after the city is founded or changes hands."""
        target = game.get_city(city)
        Sight.look(game=game, civilization=target.get_owner(), world=target.get_world(), tiles=CityControl.radius_tiles(game=game, city=city))

    @staticmethod
    def look(*, game, civilization, world, tiles):
        """Record some tiles of a world in a civilization's memory, with the owner of every city whose radius covers one of them."""
        memory = game.get_civilization(civilization).get_memory(world)
        land = game.get_world(world)
        memory.remember(world=land, tiles=tiles)
        for city in {land.get_value(layer=Layer.CITY, x=x, y=y) for x, y in tiles} - {NOTHING}:
            memory.remember_owner(city=city, owner=game.get_city(city).get_owner())

    @staticmethod
    def vision(*, game, civilization):
        """Return every tile a civilization sees right now, as a set of (world, x, y)."""
        seen = set()
        for unit in Sight.units_of(game=game, civilization=civilization):
            world = UnitControl.tile_of(game=game, unit=unit)[0]
            seen.update((world, x, y) for x, y in Sight.tiles_around_unit(game=game, unit=unit))
        for city in game.get_city_ids():
            target = game.get_city(city)
            if target.get_owner() == civilization:
                seen.update((target.get_world(), x, y) for x, y in CityControl.radius_tiles(game=game, city=city))
        return seen

    @staticmethod
    def sees_every_unit(*, game, civilization):
        """Return whether a civilization knows a technology that ends the fog of war."""
        catalog = game.get_catalog()
        return any(catalog.get_kind(category=Category.TECHNOLOGIES, kind_id=technology).ENDS_FOG_OF_WAR for technology in game.get_civilization(civilization).get_technologies())

    @staticmethod
    def view(*, game, civilization):
        """Return the view a civilization has of the game right now: what it sees, and what it remembers of the rest."""
        return View(game=game, civilization=civilization, vision=Sight.vision(game=game, civilization=civilization), every_unit=Sight.sees_every_unit(game=game, civilization=civilization))
