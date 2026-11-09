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

"""A small game of caveman for the tests to play with, and a way to compare two games.

The world is 40 by 24 tiles of grassland, with a lake in the middle, a range of mountains east
of the lake and a strip of forest west of the lake. Two civilizations each start with one
settler and nothing else. The forest is at the east edge of the first civilization's first
city radius, and the mountains are inside the second civilization's. One tile in the south is
a tarpit. There is flint on one mountain tile, and bison and elephants on two grassland tiles
far from both settlers.
"""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.civilizations.research import Research
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.game.game import Game
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import saved_name
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.unit_column import COLUMN_CATEGORIES, UNIT_COLUMNS
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import LAYER_CATEGORIES, LAYERS, Layer
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl
from microsponge.engine.world.world import World
from microsponge.themes.caveman.resources import Flint
from microsponge.themes.caveman.terrain_bonuses import Bison, Elephants
from microsponge.themes.caveman.terrains import Forest, Grassland, Mountains, Tarpit, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler

WORLD_WIDTH = 48
WORLD_HEIGHT = 24
LAKE_COLUMNS = range(18, 22)
LAKE_ROWS = range(8, 16)
MOUNTAIN_COLUMN = 30
MOUNTAIN_ROWS = range(4, 20)
FOREST_COLUMN = 12
FOREST_ROWS = range(4, 20)
# A tile of each terrain, as (x, y).
GRASSLAND_TILE = (2, 2)
WATER_TILE = (19, 10)
MOUNTAIN_TILE = (30, 10)
FOREST_TILE = (12, 10)
TARPIT_TILE = (25, 21)
# Where the strategic resource is, flint on the mountain tile inside the second civilization's first city radius, and
# where the terrain bonuses are: bison and elephants on grassland far from both civilizations' first city radii.
FLINT_TILE = MOUNTAIN_TILE
BISON_TILE = (24, 2)
ELEPHANT_TILE = (20, 2)
CIVILIZATION_NAMES = ('Ugg', 'Grok')
# Where each civilization's settler starts, as (x, y).
SETTLER_TILES = ((5, 12), (35, 12))
# A tile from which a city radius would overlap the first civilization's first city radius without touching the city center, as (x, y).
OVERLAPPING_TILE = (18, 20)
THE_WORLD = 0
# What game_facts() calls the parts of a game.
FACTS = ('theme', 'turn', 'playing', 'civilizations', 'worlds', 'cities', 'units')


def terrain_id(*, game, terrain):
    return game.get_catalog().get_id(category=Category.TERRAINS, kind=terrain)


def resource_id(*, game, resource):
    return game.get_catalog().get_id(category=Category.RESOURCES, kind=resource)


def held(*, game, civilization, resource):
    """Return how much of a resource a civilization holds."""
    return game.get_civilization(civilization).get_amount(resource_id(game=game, resource=resource))


def give_building(*, game, city, building):
    """Put a building in a city, as finishing the build will."""
    game.get_city(city).add_building(game.get_catalog().get_id(category=Category.BUILDINGS, kind=building))


def learn(*, game, civilization, technology):
    """Give a civilization a technology, as research will."""
    game.get_civilization(civilization).learn(game.get_catalog().get_id(category=Category.TECHNOLOGIES, kind=technology))


def caveman_world(game):
    """Return the small world, with its terrain numbered by a game's catalog."""
    world = World(width=WORLD_WIDTH, height=WORLD_HEIGHT)
    world.fill(layer=Layer.TERRAIN, value=terrain_id(game=game, terrain=Grassland))
    for y in LAKE_ROWS:
        for x in LAKE_COLUMNS:
            world.set_value(layer=Layer.TERRAIN, x=x, y=y, value=terrain_id(game=game, terrain=Water))
    for y in MOUNTAIN_ROWS:
        world.set_value(layer=Layer.TERRAIN, x=MOUNTAIN_COLUMN, y=y, value=terrain_id(game=game, terrain=Mountains))
    for y in FOREST_ROWS:
        world.set_value(layer=Layer.TERRAIN, x=FOREST_COLUMN, y=y, value=terrain_id(game=game, terrain=Forest))
    x, y = TARPIT_TILE
    world.set_value(layer=Layer.TERRAIN, x=x, y=y, value=terrain_id(game=game, terrain=Tarpit))
    return world


def new_caveman_game(*, theme=Caveman):
    """Return a game of caveman, or of a theme made from caveman, before its start: the small world, and two civilizations with a settler each."""
    game = Game(theme)
    world = game.add_world(caveman_world(game))
    x, y = FLINT_TILE
    Strategic.place(game=game, world=world, x=x, y=y, resource=Flint)
    for bonus, (x, y) in ((Bison, BISON_TILE), (Elephants, ELEPHANT_TILE)):
        TerrainBonusControl.place(game=game, world=world, x=x, y=y, bonus=bonus)
    for name, (x, y) in zip(CIVILIZATION_NAMES, SETTLER_TILES):
        civilization = game.add_civilization(Civilization(name))
        UnitControl.place(game=game, kind=Settler, owner=civilization, world=world, x=x, y=y)
    return game


def started_caveman_game(*, theme=Caveman):
    """Return a game of caveman that has started: it is the first civilization's turn."""
    game = new_caveman_game(theme=theme)
    TurnControl.start(game)
    return game


def settler_of(*, game, civilization):
    """Return the settler a civilization starts with, which has to be where it started."""
    x, y = SETTLER_TILES[civilization - 1]
    return game.get_world(THE_WORLD).get_value(layer=Layer.UNIT, x=x, y=y)


def found_village(*, game, civilization, name):
    """Build a village where a civilization's settler starts, whoever's turn it is, and return the village's id."""
    return CityControl.found(game=game, settler=settler_of(game=game, civilization=civilization), name=name)


def end_turn_by_order(*, game, civilization):
    """End a civilization's turn the way a player does: picking the first technology left to research when one is, since the game forces a pick."""
    if Research.must_choose(game=game, civilization=civilization):
        Orders.research(game=game, civilization=civilization, technology=Research.available(game=game, civilization=civilization)[0])
    Orders.end_turn(game=game, civilization=civilization)


def end_rounds(*, game, rounds):
    """End the turn of every civilization still playing, in turn order, so many times over."""
    for _ in range(rounds * len(game.get_still_playing())):
        TurnControl.end_turn(game)


def name_of(*, game, category, kind_id):
    """Return the saved name of a kind's id, or NOTHING for no kind, so that two games with different ids compare."""
    if kind_id == NOTHING:
        return NOTHING
    return saved_name(game.get_catalog().get_kind(category=category, kind_id=kind_id))


def named(*, game, category, value):
    """Return a value as it is, or as its kind's name when it's an id of a category."""
    return value if category is None else name_of(game=game, category=category, kind_id=value)


def layer_facts(*, game, world, layer):
    category = LAYER_CATEGORIES.get(layer)
    return [
        [named(game=game, category=category, value=world.get_value(layer=layer, x=x, y=y)) for x in range(world.get_width())]
        for y in range(world.get_height())
    ]


def world_facts(*, game, world):
    return (world.get_width(), world.get_height(), [layer_facts(game=game, world=world, layer=layer) for layer in LAYERS])


def unit_facts(*, game, unit):
    units = game.get_units()
    return [named(game=game, category=COLUMN_CATEGORIES.get(column), value=units.get_value(column=column, unit=unit)) for column in UNIT_COLUMNS]


def names_of(*, game, category, kind_ids):
    return [name_of(game=game, category=category, kind_id=kind_id) for kind_id in kind_ids]


def by_resource_name(*, game, amounts):
    """Return amounts keyed by resource ids as amounts keyed by the names of the resources."""
    return {name_of(game=game, category=Category.RESOURCES, kind_id=resource): amount for resource, amount in amounts.items()}


def city_facts(*, game, city):
    return (
        city.get_name(), city.get_owner(), city.get_world(), city.get_x(), city.get_y(), city.get_founded(), city.get_citizens(), city.get_units(),
        city.get_growth(), by_resource_name(game=game, amounts=city.get_priorities()),
        names_of(game=game, category=Category.BUILDINGS, kind_ids=city.get_buildings()),
        [(category, name_of(game=game, category=category, kind_id=kind)) for category, kind in city.get_queue()],
        city.get_progress(), city.is_blocked(), city.builds_nothing(),
    )


def civilization_facts(*, game, civilization):
    return (
        civilization.get_name(), by_resource_name(game=game, amounts=civilization.get_holdings()),
        sorted(names_of(game=game, category=Category.TECHNOLOGIES, kind_ids=civilization.get_technologies())),
        name_of(game=game, category=Category.TECHNOLOGIES, kind_id=civilization.get_researching()), civilization.get_research(),
        civilization.get_action_points(), civilization.get_bankrupt_turns(), civilization.get_wars(), civilization.has_lost(),
    )


def game_facts(game):
    """Return everything a game holds, read through its getters, with kinds by name, so that two games can be compared."""
    facts = (
        saved_name(game.get_theme()),
        game.get_turn(),
        game.get_playing(),
        [civilization_facts(game=game, civilization=civilization) for civilization in game.get_civilizations()],
        [world_facts(game=game, world=world) for world in game.get_worlds()],
        [city_facts(game=game, city=city) for city in game.get_cities()],
        {unit: unit_facts(game=game, unit=unit) for unit in game.get_units().get_ids()},
    )
    return dict(zip(FACTS, facts))
