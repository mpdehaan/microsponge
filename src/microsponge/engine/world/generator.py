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

"""The map generator: makes a world for a theme from the game's seeded random source, and finds where each civilization starts.

It makes a map one way for now (`.claude/TESTING.md`, "The first scripted game"): grassland, or
whatever the theme's BASE_TERRAIN is, with patches of the theme's other terrains grown by a
random walk, then strategic resources and terrain bonuses scattered on the terrains that can
have them. The numbers are the theme's MAP spec (`kinds/map_spec.py`). The person who designs
the game will look at what it makes and ask for styles later.

Civilizations start on the best sites the world has (`start_survey.py`), far apart, and the
world is then revised a little around a site that lacks something (`start_improver.py`).
"""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.sight import FIRST_CIVILIZATION
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import saved_name
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.start_improver import StartImprover
from microsponge.engine.world.start_survey import StartSurvey
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl
from microsponge.engine.world.world import World
from microsponge.err_messages import ERR_NO_MAP, ERR_NO_ROOM_TO_START

WHOLE = 100
# The four tiles a patch grows into from a tile, as (dx, dy).
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))
# Starting sites are looked for on every this many columns and rows, which is plenty and keeps the search quick.
SITE_STEP = 2


def distance(*, world, from_x, from_y, to_x, to_y):
    """Return how many moves apart two tiles are, going around the world the shorter way."""
    return max(world.columns_apart(first=from_x, second=to_x), abs(from_y - to_y))


class MapGenerator:
    """Static: makes worlds and starting places. It is never made into an object."""

    __slots__ = ()

    @staticmethod
    def make(*, game, width=None, height=None):
        """Make a world for the game's theme, add it to the game and return its id. The size is the theme's MAP size unless given."""
        spec = game.get_theme().MAP
        if spec.BASE_TERRAIN is None:
            raise ValueError(ERR_NO_MAP.format(theme=saved_name(game.get_theme())))
        world = World(width=spec.WIDTH if width is None else width, height=spec.HEIGHT if height is None else height)
        world.fill(layer=Layer.TERRAIN, value=MapGenerator.terrain_id(game=game, terrain=spec.BASE_TERRAIN))
        world_id = game.add_world(world)
        for terrain, percent in spec.TERRAIN_PERCENT.items():
            MapGenerator.grow(game=game, world=world, terrain=terrain, tiles=world.get_width() * world.get_height() * percent // WHOLE)
        MapGenerator.scatter_strategic(game=game, world_id=world_id)
        MapGenerator.scatter_bonuses(game=game, world_id=world_id)
        return world_id

    @staticmethod
    def terrain_id(*, game, terrain):
        return game.get_catalog().get_id(category=Category.TERRAINS, kind=terrain)

    @staticmethod
    def every_tile(world):
        return [(x, y) for y in range(world.get_height()) for x in range(world.get_width())]

    @staticmethod
    def grow(*, game, world, terrain, tiles):
        """Turn about so many tiles of the base terrain into a terrain, in patches that each grow from a random tile by a random walk."""
        random = game.get_random()
        base = MapGenerator.terrain_id(game=game, terrain=game.get_theme().MAP.BASE_TERRAIN)
        grown = MapGenerator.terrain_id(game=game, terrain=terrain)
        patch_size = game.get_theme().MAP.PATCH_SIZE
        left = tiles
        tries = tiles * patch_size
        while left > 0 and tries > 0:
            tries -= 1
            x, y = random.randrange(world.get_width()), random.randrange(world.get_height())
            for _ in range(patch_size):
                if world.get_value(layer=Layer.TERRAIN, x=x, y=y) == base:
                    world.set_value(layer=Layer.TERRAIN, x=x, y=y, value=grown)
                    left -= 1
                    if left == 0:
                        return
                dx, dy = random.choice(SIDES)
                x = world.column(x + dx)
                y = min(max(y + dy, 0), world.get_height() - 1)

    @staticmethod
    def scatter_strategic(*, game, world_id):
        """Give the theme's percent of the tiles that can have a strategic resource one of the resources their terrain can have."""
        random = game.get_random()
        world = game.get_world(world_id)
        for x, y in MapGenerator.every_tile(world):
            terrain = game.get_terrain(world=world_id, x=x, y=y)
            if terrain.CAN_HAVE and random.randrange(WHOLE) < game.get_theme().MAP.STRATEGIC_PERCENT:
                Strategic.place(game=game, world=world_id, x=x, y=y, resource=random.choice(terrain.CAN_HAVE))

    @staticmethod
    def scatter_bonuses(*, game, world_id):
        """Give the theme's percent of the tiles each terrain bonus can be on that bonus, one bonus to a tile."""
        random = game.get_random()
        world = game.get_world(world_id)
        for x, y in MapGenerator.every_tile(world):
            terrain = game.get_terrain(world=world_id, x=x, y=y)
            for bonus in game.get_theme().TERRAIN_BONUSES:
                if terrain in bonus.ON and random.randrange(WHOLE) < game.get_theme().MAP.TERRAIN_BONUS_PERCENT:
                    TerrainBonusControl.place(game=game, world=world_id, x=x, y=y, bonus=bonus)
                    break

    @staticmethod
    def sites(*, game, world_id):
        """Return the tiles of a world where a city could be built and a settler could stand, on every SITE_STEP columns and rows."""
        world = game.get_world(world_id)
        settler = MapGenerator.settler_kind(game)
        found = []
        for y in range(0, world.get_height(), SITE_STEP):
            for x in range(0, world.get_width(), SITE_STEP):
                if UnitControl.problem_standing(game=game, kind=settler, world=world_id, x=x, y=y) is None \
                        and CityControl.problem_with_site(game=game, tiles=world, x=x, y=y) is None:
                    found.append((x, y))
        return found

    @staticmethod
    def settler_kind(game):
        """Return the theme's first settler unit, the one each civilization starts with."""
        return next(kind for kind in game.get_theme().UNITS if issubclass(kind, SettlerUnit))

    @staticmethod
    def starting_tiles(*, game, world_id, count):
        """Return a tile for each of count civilizations to start on: the best sites the world has, as far from one another as those sites allow.

        The sites that are good as the world is are tried first, then the sites that only have
        room, which the generator can improve, and then every site, for a world too small to
        have a good one. Two starting tiles are at least a city radius apart, so that the first
        cities founded where the settlers stand never overlap.
        """
        candidates = MapGenerator.sites(game=game, world_id=world_id)
        survey = StartSurvey(game=game, world_id=world_id, kind=MapGenerator.settler_kind(game))
        roomy = [(x, y) for x, y in candidates if survey.has_room(x=x, y=y)]
        ready = [(x, y) for x, y in roomy if survey.is_ready(x=x, y=y)]
        chosen = []
        for pool in (ready, roomy, candidates):
            chosen = MapGenerator.spread(game=game, world_id=world_id, candidates=pool, count=count)
            if len(chosen) == count:
                return chosen
        raise ValueError(ERR_NO_ROOM_TO_START.format(count=count, room=len(chosen)))

    @staticmethod
    def spread(*, game, world_id, candidates, count):
        """Return up to count of the candidate tiles, as far from one another as the candidates allow and at least a city radius apart: the first at random, each next the candidate farthest from those chosen."""
        world = game.get_world(world_id)
        apart = game.get_theme().CITY.RADIUS_SIZE
        chosen = [game.get_random().choice(candidates)] if candidates else []
        while chosen and len(chosen) < count:
            farthest = max(candidates, key=lambda tile: MapGenerator.nearest(world=world, tile=tile, others=chosen))
            if MapGenerator.nearest(world=world, tile=farthest, others=chosen) < apart:
                break
            chosen.append(farthest)
        return chosen

    @staticmethod
    def nearest(*, world, tile, others):
        """Return how far a tile is from the nearest of other tiles."""
        x, y = tile
        return min(distance(world=world, from_x=x, from_y=y, to_x=other_x, to_y=other_y) for other_x, other_y in others)

    @staticmethod
    def place_civilizations(*, game, world_id):
        """Choose each civilization's starting tile, improve the world around each tile that lacks something, put each starting settler on its tile, and return the tiles in turn order."""
        tiles = MapGenerator.starting_tiles(game=game, world_id=world_id, count=len(game.get_civilizations()))
        settler = MapGenerator.settler_kind(game)
        for x, y in tiles:
            StartImprover.improve(game=game, world_id=world_id, kind=settler, x=x, y=y)
        for civilization, (x, y) in enumerate(tiles, start=FIRST_CIVILIZATION):
            UnitControl.place(game=game, kind=settler, owner=civilization, world=world_id, x=x, y=y)
        return tiles
