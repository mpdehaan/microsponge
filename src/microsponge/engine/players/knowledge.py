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

"""What a civilization knows, read only through its view and its memory of the map, for the helper AI and the main AI alike."""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.unit_kinds import SettlerUnit, has_melee, has_ranged
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl


# How far, in moves each way, a computer player looks for a site for a settler, and on every how many tiles.
SITE_REACH = 30
SITE_STEP = 2


def distance(*, world, from_x, from_y, to_x, to_y):
    """Return how many moves apart two tiles are, going around the world the shorter way, since a unit moves diagonally as easily as straight."""
    return max(world.columns_apart(first=from_x, second=to_x), abs(from_y - to_y))


class Knowledge:
    """Static: what a civilization knows of its own units and of the other civilizations. It never looks through the fog of war."""

    __slots__ = ()

    @staticmethod
    def units_of(*, game, civilization):
        return Sight.units_of(game=game, civilization=civilization)

    @staticmethod
    def is_settler(*, game, unit):
        return issubclass(UnitControl.kind_of(game=game, unit=unit), SettlerUnit)

    @staticmethod
    def is_fighter(*, game, unit):
        kind = UnitControl.kind_of(game=game, unit=unit)
        return has_melee(kind) or has_ranged(kind)

    @staticmethod
    def settlers_of(*, game, civilization):
        return [unit for unit in Knowledge.units_of(game=game, civilization=civilization) if Knowledge.is_settler(game=game, unit=unit)]

    @staticmethod
    def city_of(*, game, unit):
        """Return the id of the city a unit is inside, or NOTHING."""
        return game.get_units().get_value(column=UnitColumn.CITY, unit=unit)

    @staticmethod
    def steps_to_city(*, game, unit, city):
        """Return how many moves a unit is from the center of a city on the unit's world."""
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        target = game.get_city(city)
        return distance(world=game.get_world(world), from_x=x, from_y=y, to_x=target.get_x(), to_y=target.get_y())

    @staticmethod
    def nearest_city(*, game, unit, cities):
        """Return the id of the nearest of some cities to a unit on the same world, or NOTHING."""
        world, _, _ = UnitControl.tile_of(game=game, unit=unit)
        same_world = [city for city in cities if game.get_city(city).get_world() == world]
        if not same_world:
            return NOTHING
        return min(same_world, key=lambda city: Knowledge.steps_to_city(game=game, unit=unit, city=city))

    @staticmethod
    def enemies_of(*, game, civilization):
        """Return the ids of the civilizations this one is at war with and that are still playing."""
        holder = game.get_civilization(civilization)
        return [other for other in game.get_still_playing() if holder.is_at_war_with(other)]

    @staticmethod
    def known_cities_of(*, game, civilization, others):
        """Return the cities the civilization knows to belong to any of some other civilizations, as last seen."""
        view = Sight.view(game=game, civilization=civilization)
        return [city for city in game.get_city_ids() if view.owner_of(city) in others]

    @staticmethod
    def known_civilizations(*, game, civilization):
        """Return the other civilizations this one has met: whose unit it sees or whose city it has seen."""
        view = Sight.view(game=game, civilization=civilization)
        units = game.get_units()
        met = {units.get_value(column=UnitColumn.OWNER, unit=unit) for unit in view.units_seen()}
        met.update(view.owner_of(city) for city in game.get_city_ids())
        return sorted(other for other in met - {NOTHING, civilization} if not game.get_civilization(other).has_lost())

    @staticmethod
    def foreign_cities(*, game, civilization, world):
        """Return the cities of other civilizations on a world that the civilization knows of."""
        memory = game.get_civilization(civilization).get_memory(world)
        return [game.get_city(city) for city in game.get_city_ids() if memory.get_owner(city) not in (NOTHING, civilization) and game.get_city(city).get_world() == world]

    @staticmethod
    def is_in_foreign_land(*, game, civilization, world, x, y):
        """Return whether a tile lies within the city radius of a known city of another civilization, where a unit may not go without a war."""
        half = game.get_theme().CITY.RADIUS_SIZE // 2
        land = game.get_world(world)
        return any(distance(world=land, from_x=x, from_y=y, to_x=city.get_x(), to_y=city.get_y()) <= half for city in Knowledge.foreign_cities(game=game, civilization=civilization, world=world))

    @staticmethod
    def is_site(*, game, civilization, world, x, y):
        """Return whether the civilization remembers a tile as one where a city could be built.

        A tile never seen, or too close to a city the civilization knows of, is passed over
        before the full check of the site, which reads the whole city radius, so that the
        search stays cheap.
        """
        memory = game.get_civilization(civilization).get_memory(world)
        if not memory.has_seen(x=x, y=y):
            return False
        land = game.get_world(world)
        too_close = game.get_theme().CITY.RADIUS_SIZE
        known = [game.get_city(city) for city in game.get_city_ids() if memory.get_owner(city) != NOTHING and game.get_city(city).get_world() == world]
        if any(distance(world=land, from_x=x, from_y=y, to_x=city.get_x(), to_y=city.get_y()) < too_close for city in known):
            return False
        return CityControl.problem_with_site(game=game, tiles=memory, x=x, y=y) is None

    @staticmethod
    def nearest_site(*, game, civilization, unit, taken):
        """Return (world, x, y) of the nearest tile, within SITE_REACH and on every SITE_STEP column and row of the world, that the civilization remembers as a site and that is not too close to a place already taken by another settler, or None."""
        world, from_x, from_y = UnitControl.tile_of(game=game, unit=unit)
        land = game.get_world(world)
        too_close = game.get_theme().CITY.RADIUS_SIZE
        candidates = []
        for dy in range(-SITE_REACH, SITE_REACH + 1):
            for dx in range(-SITE_REACH, SITE_REACH + 1):
                x = land.column(from_x + dx)
                y = from_y + dy
                if 0 <= y < land.get_height() and x % SITE_STEP == 0 and y % SITE_STEP == 0:
                    candidates.append((max(abs(dx), abs(dy)), x, y))
        for _, x, y in sorted(candidates):
            if any(place.world == world and distance(world=land, from_x=x, from_y=y, to_x=place.x, to_y=place.y) < too_close for place in taken):
                continue
            if Knowledge.is_site(game=game, civilization=civilization, world=world, x=x, y=y):
                return (world, x, y)
        return None
