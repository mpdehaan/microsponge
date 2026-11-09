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

"""One game being played."""

import random

from microsponge.engine.cities.city import City
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.kinds.catalog import NOTHING, Catalog
from microsponge.engine.kinds.category import CATEGORIES, Category
from microsponge.engine.kinds.kind import saved_name
from microsponge.engine.units.unit_column import COLUMN_CATEGORIES
from microsponge.engine.units.units import Units
from microsponge.engine.world.layer import LAYER_CATEGORIES, Layer
from microsponge.engine.world.world import World
from microsponge.err_messages import ERR_NO_SUCH_CITY, ERR_NO_SUCH_CIVILIZATION, ERR_NO_SUCH_THEME, ERR_NO_SUCH_WORLD, ERR_TOO_MANY_CIVILIZATIONS, ERR_TOO_MANY_WORLDS, ERR_TURN

# The most civilizations a game has, for now.
MAX_CIVILIZATIONS = 7
# A game goes on while this many civilizations are still playing, or all of them in a game of fewer.
ENOUGH_TO_PLAY = 2
FIRST_TURN = 0
# What a saved game calls the parts of a game.
THEME_KEY = 'theme'
TURN_KEY = 'turn'
PLAYING_KEY = 'playing'
NAMES_KEY = 'names'
CIVILIZATIONS_KEY = 'civilizations'
WORLDS_KEY = 'worlds'
CITIES_KEY = 'cities'
UNITS_KEY = 'units'
GAME_KEYS = (THEME_KEY, TURN_KEY, PLAYING_KEY, NAMES_KEY, CIVILIZATIONS_KEY, WORLDS_KEY, CITIES_KEY, UNITS_KEY)


def check_turn(turn):
    if type(turn) is not int or turn < FIRST_TURN:
        raise ValueError(ERR_TURN.format(value=turn))
    return turn


def theme_named(*, name, themes):
    """Return the theme among themes that a saved game calls name."""
    for theme in themes:
        if saved_name(theme) == name:
            return theme
    raise ValueError(ERR_NO_SUCH_THEME.format(name=name))


def data_of_each(things):
    """Return what a saved game holds for each of some civilizations, worlds or cities."""
    return [thing.to_data() for thing in things]


class Game:
    """A game of one theme: the turn it has reached, and its civilizations, worlds, cities and units.

    A civilization's id is its place among the civilizations, counted from 1, since NOTHING
    means no civilization, and a city's id is its place among the cities, counted from 1 the
    same way. A world's id is its place among the worlds, counted from 0.
    """

    __slots__ = ('_theme', '_catalog', '_turn', '_playing', '_civilizations', '_worlds', '_cities', '_units', '_random')

    def __init__(self, theme):
        self._theme = theme
        self._catalog = Catalog(theme)
        self._turn = FIRST_TURN
        self._playing = NOTHING
        self._civilizations = []
        self._worlds = []
        self._cities = []
        self._units = Units()
        self._random = random.Random()

    def get_theme(self):
        return self._theme

    def get_catalog(self):
        return self._catalog

    def get_turn(self):
        return self._turn

    def set_turn(self, turn):
        self._turn = check_turn(turn)

    def next_turn(self):
        self._turn += 1

    def get_playing(self):
        """Return the id of the civilization whose turn it is, or NOTHING before the game has started."""
        return self._playing

    def set_playing(self, civilization):
        self.get_civilization(civilization)
        self._playing = civilization

    def get_still_playing(self):
        """Return the ids of the civilizations that have not lost, in turn order."""
        return [place + 1 for place, civilization in enumerate(self._civilizations) if not civilization.has_lost()]

    def is_over(self):
        """Return whether the game has ended: one civilization is the only one remaining, or none is."""
        return len(self.get_still_playing()) < min(ENOUGH_TO_PLAY, len(self._civilizations))

    def add_civilization(self, civilization):
        """Add a civilization and return its id."""
        if len(self._civilizations) >= MAX_CIVILIZATIONS:
            raise ValueError(ERR_TOO_MANY_CIVILIZATIONS.format(most=MAX_CIVILIZATIONS))
        self._civilizations.append(civilization)
        return len(self._civilizations)

    def get_civilization(self, civilization):
        if type(civilization) is not int or not NOTHING < civilization <= len(self._civilizations):
            raise ValueError(ERR_NO_SUCH_CIVILIZATION.format(civilization=civilization))
        return self._civilizations[civilization - 1]

    def get_civilizations(self):
        return list(self._civilizations)

    def add_world(self, world):
        """Add a world and return its id. A theme allows only so many worlds."""
        if len(self._worlds) >= self._theme.MAX_WORLDS:
            raise ValueError(ERR_TOO_MANY_WORLDS.format(theme=saved_name(self._theme), most=self._theme.MAX_WORLDS))
        self._worlds.append(world)
        return len(self._worlds) - 1

    def get_world(self, world):
        if type(world) is not int or not 0 <= world < len(self._worlds):
            raise ValueError(ERR_NO_SUCH_WORLD.format(world=world))
        return self._worlds[world]

    def get_worlds(self):
        return list(self._worlds)

    def get_terrain(self, *, world, x, y):
        """Return the terrain of a tile of a world, as the theme's class."""
        terrain = self.get_world(world).get_value(layer=Layer.TERRAIN, x=x, y=y)
        return self._catalog.get_kind(category=Category.TERRAINS, kind_id=terrain)

    def add_city(self, city):
        """Add a city and return its id."""
        self._cities.append(city)
        return len(self._cities)

    def get_city(self, city):
        if type(city) is not int or not NOTHING < city <= len(self._cities):
            raise ValueError(ERR_NO_SUCH_CITY.format(city=city))
        return self._cities[city - 1]

    def get_cities(self):
        return list(self._cities)

    def get_city_ids(self):
        """Return the ids of every city of the game, oldest first."""
        return [place + 1 for place in range(len(self._cities))]

    def get_cities_of(self, civilization):
        """Return the ids of the cities that belong to a civilization, oldest first."""
        return [city for city in self.get_city_ids() if self.get_city(city).get_owner() == civilization]

    def get_units(self):
        return self._units

    def get_random(self):
        """Return the one source of every random draw in the game, so that a seed makes a game play the same way again."""
        return self._random

    def set_seed(self, seed):
        self._random.seed(seed)

    def to_data(self):
        """Return the game as a saved game holds it: mostly integers, and the name of each kind's id."""
        return {
            THEME_KEY: saved_name(self._theme),
            TURN_KEY: self._turn,
            PLAYING_KEY: self._playing,
            NAMES_KEY: self._catalog.get_names(),
            CIVILIZATIONS_KEY: data_of_each(self._civilizations),
            WORLDS_KEY: data_of_each(self._worlds),
            CITIES_KEY: data_of_each(self._cities),
            UNITS_KEY: self._units.to_data(),
        }

    @classmethod
    def from_data(cls, *, data, themes):
        """Return the game a saved game holds, played in whichever of themes the saved game names."""
        game = cls(theme_named(name=data[THEME_KEY], themes=themes))
        game.set_turn(data[TURN_KEY])
        game._playing = data[PLAYING_KEY]
        for civilization in data[CIVILIZATIONS_KEY]:
            game.add_civilization(Civilization.from_data(civilization))
        for world in data[WORLDS_KEY]:
            game.add_world(World.from_data(world))
        for city in data[CITIES_KEY]:
            game.add_city(City.from_data(city))
        game._units = Units.from_data(data[UNITS_KEY])
        game._renumber(data[NAMES_KEY])
        return game

    def _renumber(self, saved_names):
        """Change the ids a saved game holds into this game's catalog's, wherever the theme has changed since."""
        numbers = self._catalog.renumberings(saved_names)
        for layer, category in LAYER_CATEGORIES.items():
            if numbers[category] is not None:
                for world in self._worlds:
                    world.renumber(layer=layer, numbers=numbers[category])
        for column, category in COLUMN_CATEGORIES.items():
            if numbers[category] is not None:
                self._units.renumber(column=column, numbers=numbers[category])
        for category in CATEGORIES:
            if numbers[category] is not None:
                for holder in self._civilizations + self._cities:
                    holder.renumber(category=category, numbers=numbers[category])
