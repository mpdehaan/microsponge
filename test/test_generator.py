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

"""The map generator: the worlds it makes from a seed, where each civilization starts, and the preview printed of them."""

import subprocess
import sys
import unittest
from pathlib import Path

from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl, on_the_map, square
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.game.game import Game
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import saved_name, shown_name
from microsponge.engine.players.traits import Traits
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.world.generator import MapGenerator, distance
from microsponge.engine.world.land import NO_PIECE, Land
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.square_count import SquareCount
from microsponge.engine.world.start_improver import StartImprover
from microsponge.engine.world.start_survey import StartSurvey, square_size
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl
from microsponge.engine.world.terrain_control import TerrainControl
from microsponge.engine.world.world import World
from microsponge.err_messages import ERR_NO_MAP, ERR_NO_ROOM_TO_START
from microsponge.support.map_preview import marks_for, preview_lines, previewed_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes.caveman.map import CavemanMap
from microsponge.themes.caveman.resources import Flint, Food, Stone, Wood
from microsponge.themes.caveman.terrain_bonuses import Bison
from microsponge.themes.caveman.terrains import Forest, Grassland, Mountains, Tarpit, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler
from microsponge.themes.classic.theme import Classic
from microsponge.ui_strings import MSG_MAP_LEGEND_ITEM, MSG_MAP_LEGEND_TITLE, MSG_MAP_STARTS, MSG_MAP_TITLE

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'map_preview.py'
A_SEED = 5
ANOTHER_SEED = 6
SEEDS = range(1, 9)
THREE = 3
NAMES = ('Ugg', 'Grok', 'Thag')
# A world too small for three cities that may not overlap.
TINY = 16
# A terrain's share of a generated world may fall short of its percent when patches overlap, by at most this many points.
SHORTFALL = 3
NOT_A_NUMBER = 'seven'
TURNS = 30


def caveman_game(seed):
    game = Game(Caveman)
    game.set_seed(seed)
    for name in NAMES:
        game.add_civilization(Civilization(name))
    return game


def terrain_counts(*, game, world_id):
    world = game.get_world(world_id)
    counts = {}
    for x, y in MapGenerator.every_tile(world):
        terrain = game.get_terrain(world=world_id, x=x, y=y)
        counts[terrain] = counts.get(terrain, 0) + 1
    return counts


class TestGenerator(Refusals, unittest.TestCase):

    def test_a_world_is_the_size_of_the_themes_map_spec_unless_another_size_is_asked_for(self):
        game = caveman_game(A_SEED)
        world = game.get_world(MapGenerator.make(game=game))
        self.assertEqual((world.get_width(), world.get_height()), (Caveman.MAP.WIDTH, Caveman.MAP.HEIGHT))
        game = caveman_game(A_SEED)
        world = game.get_world(MapGenerator.make(game=game, width=TINY, height=TINY))
        self.assertEqual((world.get_width(), world.get_height()), (TINY, TINY))

    def test_the_same_seed_makes_the_same_world_and_another_seed_another(self):
        worlds = []
        for seed in (A_SEED, A_SEED, ANOTHER_SEED):
            game = caveman_game(seed)
            world_id = MapGenerator.make(game=game)
            worlds.append([[game.get_world(world_id).get_value(layer=layer, x=x, y=y) for x, y in MapGenerator.every_tile(game.get_world(world_id))] for layer in (Layer.TERRAIN, Layer.STRATEGIC_RESOURCE, Layer.TERRAIN_BONUS)])
        self.assertEqual(worlds[0], worlds[1])
        self.assertNotEqual(worlds[0], worlds[2])

    def test_each_terrain_covers_about_its_percent_of_the_tiles_and_the_base_terrain_the_rest(self):
        game = caveman_game(A_SEED)
        world_id = MapGenerator.make(game=game)
        counts = terrain_counts(game=game, world_id=world_id)
        area = Caveman.MAP.WIDTH * Caveman.MAP.HEIGHT
        for terrain, percent in Caveman.MAP.TERRAIN_PERCENT.items():
            with self.subTest(terrain=terrain):
                self.assertLessEqual(counts[terrain] * 100, percent * area)
                self.assertGreaterEqual(counts[terrain] * 100, (percent - SHORTFALL) * area)
        self.assertEqual(sum(counts.values()), area)
        self.assertGreater(counts[Caveman.MAP.BASE_TERRAIN], area // 2)

    def test_strategic_resources_and_terrain_bonuses_are_only_on_terrains_that_can_have_them_and_some_are_placed(self):
        game = caveman_game(A_SEED)
        world_id = MapGenerator.make(game=game)
        world = game.get_world(world_id)
        catalog = game.get_catalog()
        resources = bonuses = 0
        for x, y in MapGenerator.every_tile(world):
            terrain = game.get_terrain(world=world_id, x=x, y=y)
            resource = world.get_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y)
            bonus = world.get_value(layer=Layer.TERRAIN_BONUS, x=x, y=y)
            if resource != NOTHING:
                resources += 1
                self.assertIn(catalog.get_kind(category=Category.RESOURCES, kind_id=resource), terrain.CAN_HAVE)
            if bonus != NOTHING:
                bonuses += 1
                self.assertIn(terrain, catalog.get_kind(category=Category.TERRAIN_BONUSES, kind_id=bonus).ON)
        self.assertGreater(resources, 0)
        self.assertGreater(bonuses, 0)

    def test_every_civilization_starts_where_its_settler_can_found_a_city_at_once_and_the_cities_would_not_overlap(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                game = caveman_game(seed)
                world_id = MapGenerator.make(game=game)
                tiles = MapGenerator.place_civilizations(game=game, world_id=world_id)
                world = game.get_world(world_id)
                self.assertEqual(len(tiles), THREE)
                for x, y in tiles:
                    settler = world.get_value(layer=Layer.UNIT, x=x, y=y)
                    self.assertNotEqual(settler, NOTHING)
                    self.assertIsNone(CityControl.problem_founding(game=game, settler=settler))
                for first in range(THREE):
                    for second in range(first + 1, THREE):
                        (x1, y1), (x2, y2) = tiles[first], tiles[second]
                        self.assertGreaterEqual(distance(world=world, from_x=x1, from_y=y1, to_x=x2, to_y=y2), Caveman.CITY.RADIUS_SIZE)

    def test_a_world_with_too_few_sites_and_a_theme_with_no_map_spec_are_refused(self):
        game = caveman_game(A_SEED)
        world_id = MapGenerator.make(game=game, width=TINY, height=TINY)
        self.assertTrue(MapGenerator.sites(game=game, world_id=world_id))
        self.assertEqual(self.refused(lambda: MapGenerator.place_civilizations(game=game, world_id=world_id)), ERR_NO_ROOM_TO_START.format(count=THREE, room=1))
        self.assertIsNone(Classic.MAP.BASE_TERRAIN)
        self.assertEqual(self.refused(lambda: MapGenerator.make(game=Game(Classic))), ERR_NO_MAP.format(theme=saved_name(Classic)))

    def test_three_computer_players_play_on_a_generated_world(self):
        game = caveman_game(A_SEED)
        world_id = MapGenerator.make(game=game)
        MapGenerator.place_civilizations(game=game, world_id=world_id)
        for holder in game.get_civilizations():
            holder.set_traits(Traits.dealt(game.get_random()))
        TurnControl.start(game)
        while game.get_turn() < TURNS and not game.is_over():
            Caveman.PLAYER.play_turn(game=game, civilization=game.get_playing())
        self.assertEqual(game.get_turn(), TURNS)
        self.assertEqual({game.get_city(city).get_owner() for city in game.get_city_ids()}, {1, 2, THREE})


class TestMapPreview(unittest.TestCase):

    def test_every_kind_gets_its_own_mark_from_its_name_where_it_can(self):
        marks = marks_for(kinds=Caveman.TERRAINS, alphabet='abcdefghijklmnopqrstuvwxyz')
        self.assertEqual(len(set(marks.values())), len(Caveman.TERRAINS))
        for terrain, mark in marks.items():
            self.assertIn(mark, shown_name(terrain))

    def test_the_preview_is_a_title_a_row_of_characters_for_each_row_of_the_world_and_a_legend(self):
        game, world_id = previewed_game(theme=Caveman, seed=A_SEED)
        world = game.get_world(world_id)
        lines = preview_lines(game=game, world_id=world_id, seed=A_SEED)
        self.assertEqual(lines[0], MSG_MAP_TITLE.format(theme=shown_name(Caveman), seed=A_SEED, width=world.get_width(), height=world.get_height()))
        grid = lines[1:1 + world.get_height()]
        self.assertTrue(all(len(row) == world.get_width() for row in grid))
        self.assertEqual(lines[1 + world.get_height()], MSG_MAP_LEGEND_TITLE)
        self.assertEqual(lines[-1], MSG_MAP_STARTS)
        for number in ('1', '2', '3'):
            self.assertEqual(sum(row.count(number) for row in grid), 1)
        legend = lines[2 + world.get_height():-1]
        self.assertIn(MSG_MAP_LEGEND_ITEM.format(mark='g', name=shown_name(Caveman.MAP.BASE_TERRAIN)), legend)

    def test_the_tool_prints_the_preview_of_the_seed_asked_for_and_refuses_a_bad_command_line(self):
        run = subprocess.run([sys.executable, str(TOOL), shown_name(Caveman), str(A_SEED)], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
        game, world_id = previewed_game(theme=Caveman, seed=A_SEED)
        self.assertEqual(run.stdout.splitlines(), preview_lines(game=game, world_id=world_id, seed=A_SEED))
        for arguments in ([], [shown_name(Caveman), NOT_A_NUMBER], [shown_name(Classic)]):
            with self.subTest(arguments=arguments):
                run = subprocess.run([sys.executable, str(TOOL), *arguments], capture_output=True, text=True, cwd=ROOT, check=False)
                self.assertEqual(run.returncode, FAILED)


# A world by hand, big enough that a site in the middle has room.
SIDE = 80
MIDDLE = 40
# A site this close to the top of a world has too many of the tiles around it off the world to have room.
NEAR_THE_TOP = 2
# A wall this many steps from a site shuts the site into too little land to have room.
WALL_STEPS = 10
# A world this short has no site with room, since too many of the tiles around any site are off the world.
SHORT = 30
RADIUS_REACH = Caveman.CITY.RADIUS_SIZE // 2
CENTER_REACH = Caveman.CITY.CENTER_SIZE // 2
# The farthest a strategic resource of a start may be from the starting site, in steps.
STRATEGIC_REACH = RADIUS_REACH + Caveman.MAP.START_STRATEGIC_DISTANCE
# How many tiles of the radius are left without bison in the test of special tiles: just enough for the wood and the stone a start needs.
LEFT_PLAIN = Caveman.MAP.START_NEEDS[Wood] + Caveman.MAP.START_NEEDS[Stone]


class NeedyMap(CavemanMap):
    """A map spec that asks a first city radius for a resource no terrain gives when worked, and for nothing else."""
    START_NEEDS = {Flint: 1}
    START_STRATEGIC = ()


class NeedyCaveman(Caveman):
    MAP = NeedyMap


def flat_game(*, theme=Caveman, terrain=Grassland, width=SIDE, height=SIDE):
    """Return a game on a world by hand, every tile one terrain, and the world's id."""
    game = Game(theme)
    game.set_seed(A_SEED)
    for name in NAMES:
        game.add_civilization(Civilization(name))
    world = World(width=width, height=height)
    world.fill(layer=Layer.TERRAIN, value=game.get_catalog().get_id(category=Category.TERRAINS, kind=terrain))
    return game, game.add_world(world)


def make(*, game, world_id, x, y, terrain):
    TerrainControl.change(game=game, world=world_id, x=x, y=y, terrain=terrain)


def survey_of(*, game, world_id):
    return StartSurvey(game=game, world_id=world_id, kind=MapGenerator.settler_kind(game))


def tiles_around(*, game, world_id, x, y, reach):
    return on_the_map(tiles=square(x=x, y=y, size=square_size(reach)), world=game.get_world(world_id))


def flint_tiles(*, game, world_id):
    return [(x, y) for x, y in MapGenerator.every_tile(game.get_world(world_id)) if Strategic.resource_at(game=game, world=world_id, x=x, y=y) is Flint]


def terrains_of(*, game, world_id, tiles):
    return [game.get_terrain(world=world_id, x=x, y=y) for x, y in tiles]


class TestSquareCount(unittest.TestCase):

    def test_a_square_counts_its_marked_tiles_around_the_world_and_nothing_off_the_world(self):
        world = World(width=10, height=6)
        count = SquareCount(world=world, marked=[(0, 0), (9, 0), (5, 3)])
        self.assertEqual(count.in_square(x=0, y=0, size=3), 2)
        self.assertEqual(count.in_square(x=9, y=1, size=3), 2)
        self.assertEqual(count.in_square(x=5, y=3, size=1), 1)
        self.assertEqual(count.in_square(x=4, y=3, size=1), 0)
        self.assertEqual(count.in_square(x=5, y=2, size=3), 1)
        self.assertEqual(count.in_square(x=2, y=4, size=3), 0)

    def test_a_square_wider_than_the_world_counts_each_tile_once(self):
        world = World(width=10, height=6)
        count = SquareCount(world=world, marked=[(0, 0), (9, 0), (5, 3)])
        self.assertEqual(count.in_square(x=3, y=1, size=11), 3)
        self.assertEqual(count.in_square(x=3, y=1, size=10), 3)
        self.assertEqual(count.in_square(x=3, y=5, size=25), 3)


class TestLand(unittest.TestCase):

    def walled_game(self):
        """Return a world 20 by 10 with a wall of water down column 5 and a wall of tarpit down column 15, so the land is two pieces."""
        game, world_id = flat_game(width=20, height=10)
        for y in range(10):
            make(game=game, world_id=world_id, x=5, y=y, terrain=Water)
            make(game=game, world_id=world_id, x=15, y=y, terrain=Tarpit)
        return game, world_id

    def test_water_and_terrain_land_units_cannot_cross_split_the_land_into_pieces_that_go_around_the_world(self):
        game, world_id = self.walled_game()
        land = Land(game=game, world_id=world_id, kind=Settler)
        self.assertEqual(land.get_piece(x=5, y=3), NO_PIECE)
        self.assertEqual(land.get_piece(x=15, y=3), NO_PIECE)
        self.assertNotEqual(land.get_piece(x=10, y=3), NO_PIECE)
        self.assertNotEqual(land.get_piece(x=10, y=3), land.get_piece(x=2, y=3))
        self.assertEqual(land.get_piece(x=2, y=0), land.get_piece(x=18, y=9))
        self.assertEqual(land.get_piece(x=22, y=0), land.get_piece(x=2, y=0))

    def test_one_gap_in_a_wall_joins_the_pieces_and_a_unit_walks_through_a_gap_diagonally(self):
        game, world_id = self.walled_game()
        make(game=game, world_id=world_id, x=5, y=4, terrain=Forest)
        land = Land(game=game, world_id=world_id, kind=Settler)
        self.assertEqual(land.get_piece(x=10, y=3), land.get_piece(x=2, y=3))
        game, world_id = flat_game(width=20, height=10)
        for x in range(20):
            make(game=game, world_id=world_id, x=x, y=4 + x % 2, terrain=Water)
        land = Land(game=game, world_id=world_id, kind=Settler)
        self.assertEqual(land.get_piece(x=0, y=0), land.get_piece(x=0, y=9))

    def test_the_tiles_a_unit_can_walk_to_in_a_square_leave_out_walls_other_pieces_and_tiles_off_the_world(self):
        game, world_id = self.walled_game()
        land = Land(game=game, world_id=world_id, kind=Settler)
        self.assertEqual(land.reachable_in(x=10, y=5, size=5), 25)
        self.assertEqual(land.reachable_in(x=7, y=5, size=5), 20)
        self.assertEqual(land.reachable_in(x=6, y=5, size=5), 15)
        self.assertEqual(land.reachable_in(x=10, y=0, size=5), 15)
        self.assertEqual(land.reachable_in(x=5, y=5, size=5), 0)
        self.assertEqual(land.reachable_in(x=10, y=5, size=21), 90)
        self.assertEqual(land.reachable_in(x=2, y=5, size=21), 90)


class TestStartSurvey(unittest.TestCase):

    def test_a_site_has_room_in_open_land_and_not_near_the_top_of_the_world_or_walled_in(self):
        game, world_id = flat_game()
        survey = survey_of(game=game, world_id=world_id)
        self.assertTrue(survey.has_room(x=MIDDLE, y=MIDDLE))
        self.assertFalse(survey.has_room(x=MIDDLE, y=NEAR_THE_TOP))
        self.assertFalse(survey.has_room(x=MIDDLE, y=SIDE - 1 - NEAR_THE_TOP))
        inside = set(tiles_around(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE, reach=WALL_STEPS - 1))
        for x, y in tiles_around(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE, reach=WALL_STEPS):
            if (x, y) not in inside:
                make(game=game, world_id=world_id, x=x, y=y, terrain=Water)
        survey = survey_of(game=game, world_id=world_id)
        self.assertFalse(survey.has_room(x=MIDDLE, y=MIDDLE))
        self.assertTrue(survey.has_room(x=0, y=MIDDLE))

    def test_the_room_a_site_needs_is_the_themes_percent_of_the_square_the_themes_reach_makes(self):
        game, world_id = flat_game()
        size = square_size(Caveman.MAP.START_REACH)
        needed = -(-Caveman.MAP.START_REACHABLE_PERCENT * size * size // 100)
        rows_needed = -(-needed // size)
        survey = survey_of(game=game, world_id=world_id)
        self.assertTrue(survey.has_room(x=MIDDLE, y=rows_needed - 1 - Caveman.MAP.START_REACH))
        self.assertFalse(survey.has_room(x=MIDDLE, y=rows_needed - 2 - Caveman.MAP.START_REACH))

    def test_a_site_lacks_each_needed_resource_too_few_tiles_of_its_radius_give_outside_the_center(self):
        game, world_id = flat_game()
        needs = Caveman.MAP.START_NEEDS
        self.assertEqual(survey_of(game=game, world_id=world_id).lacks(x=MIDDLE, y=MIDDLE), {Wood: needs[Wood], Stone: needs[Stone]})
        make(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE + CENTER_REACH, terrain=Forest)
        make(game=game, world_id=world_id, x=MIDDLE + RADIUS_REACH + 1, y=MIDDLE, terrain=Forest)
        self.assertEqual(survey_of(game=game, world_id=world_id).lacks(x=MIDDLE, y=MIDDLE)[Wood], needs[Wood])
        make(game=game, world_id=world_id, x=MIDDLE + RADIUS_REACH, y=MIDDLE, terrain=Forest)
        make(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE + CENTER_REACH + 1, terrain=Forest)
        self.assertEqual(survey_of(game=game, world_id=world_id).lacks(x=MIDDLE, y=MIDDLE)[Wood], needs[Wood] - 2)
        for step in range(needs[Stone]):
            make(game=game, world_id=world_id, x=MIDDLE - RADIUS_REACH, y=MIDDLE + step, terrain=Mountains)
            make(game=game, world_id=world_id, x=MIDDLE - RADIUS_REACH + 1, y=MIDDLE + step, terrain=Forest)
        survey = survey_of(game=game, world_id=world_id)
        self.assertEqual(survey.lacks(x=MIDDLE, y=MIDDLE), {})
        self.assertEqual(survey.radius_gives(x=MIDDLE, y=MIDDLE)[Stone], needs[Stone])

    def test_a_site_misses_a_strategic_resource_of_a_start_that_is_farther_than_the_themes_distance_from_the_radius(self):
        game, world_id = flat_game()
        self.assertEqual(survey_of(game=game, world_id=world_id).misses(x=MIDDLE, y=MIDDLE), [Flint])
        make(game=game, world_id=world_id, x=MIDDLE + STRATEGIC_REACH + 1, y=MIDDLE, terrain=Mountains)
        Strategic.place(game=game, world=world_id, x=MIDDLE + STRATEGIC_REACH + 1, y=MIDDLE, resource=Flint)
        self.assertEqual(survey_of(game=game, world_id=world_id).misses(x=MIDDLE, y=MIDDLE), [Flint])
        make(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE - STRATEGIC_REACH, terrain=Mountains)
        Strategic.place(game=game, world=world_id, x=MIDDLE, y=MIDDLE - STRATEGIC_REACH, resource=Flint)
        self.assertEqual(survey_of(game=game, world_id=world_id).misses(x=MIDDLE, y=MIDDLE), [])

    def test_a_site_is_ready_only_with_room_and_nothing_lacking_or_missing(self):
        game, world_id = flat_game()
        self.assertFalse(survey_of(game=game, world_id=world_id).is_ready(x=MIDDLE, y=MIDDLE))
        for site_y in (MIDDLE, NEAR_THE_TOP):
            StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=site_y)
        survey = survey_of(game=game, world_id=world_id)
        self.assertTrue(survey.is_ready(x=MIDDLE, y=MIDDLE))
        self.assertEqual((survey.lacks(x=MIDDLE, y=NEAR_THE_TOP), survey.misses(x=MIDDLE, y=NEAR_THE_TOP)), ({}, []))
        self.assertFalse(survey.is_ready(x=MIDDLE, y=NEAR_THE_TOP))


class TestStartImprover(unittest.TestCase):

    def test_a_site_on_bare_land_gets_the_tiles_it_lacks_in_its_radius_and_its_strategic_resource_and_the_center_is_left_alone(self):
        game, world_id = flat_game()
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        needs = Caveman.MAP.START_NEEDS
        radius = tiles_around(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE, reach=RADIUS_REACH)
        center = tiles_around(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE, reach=CENTER_REACH)
        found = terrains_of(game=game, world_id=world_id, tiles=radius)
        self.assertEqual((found.count(Forest), found.count(Mountains)), (needs[Wood], needs[Stone]))
        self.assertEqual(set(terrains_of(game=game, world_id=world_id, tiles=center)), {Grassland})
        flint = flint_tiles(game=game, world_id=world_id)
        self.assertEqual(len(flint), 1)
        self.assertIn(flint[0], radius)
        self.assertIs(game.get_terrain(world=world_id, x=flint[0][0], y=flint[0][1]), Mountains)
        everything = terrains_of(game=game, world_id=world_id, tiles=MapGenerator.every_tile(game.get_world(world_id)))
        self.assertEqual(everything.count(Grassland), SIDE * SIDE - needs[Wood] - needs[Stone])

    def test_with_no_tile_near_that_can_have_the_strategic_resource_a_tile_outside_the_radius_is_changed_to_hold_it(self):
        game, world_id = flat_game()
        StartImprover.add_strategic(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE, resource=Flint)
        flint = flint_tiles(game=game, world_id=world_id)
        self.assertEqual(len(flint), 1)
        self.assertIn(flint[0], tiles_around(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE, reach=STRATEGIC_REACH))
        self.assertNotIn(flint[0], tiles_around(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE, reach=RADIUS_REACH))
        everything = terrains_of(game=game, world_id=world_id, tiles=MapGenerator.every_tile(game.get_world(world_id)))
        self.assertEqual((everything.count(Mountains), everything.count(Grassland)), (1, SIDE * SIDE - 1))
        self.assertEqual(survey_of(game=game, world_id=world_id).misses(x=MIDDLE, y=MIDDLE), [])

    def test_a_site_that_lacks_nothing_is_left_as_it_is(self):
        game, world_id = flat_game()
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        before = terrains_of(game=game, world_id=world_id, tiles=MapGenerator.every_tile(game.get_world(world_id)))
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        self.assertEqual(terrains_of(game=game, world_id=world_id, tiles=MapGenerator.every_tile(game.get_world(world_id))), before)

    def test_a_tile_is_only_taken_from_a_resource_the_radius_can_spare(self):
        game, world_id = flat_game(terrain=Forest)
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        needs = Caveman.MAP.START_NEEDS
        gives = survey_of(game=game, world_id=world_id).radius_gives(x=MIDDLE, y=MIDDLE)
        self.assertEqual((gives[Food], gives[Stone]), (needs[Food], needs[Stone]))
        self.assertGreaterEqual(gives[Wood], needs[Wood])
        game, world_id = flat_game()
        outside = Caveman.CITY.RADIUS_SIZE ** 2 - Caveman.CITY.CENTER_SIZE ** 2
        radius = StartImprover.radius_outside_center(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE)
        for x, y in radius[:outside - needs[Food] - 1]:
            make(game=game, world_id=world_id, x=x, y=y, terrain=Tarpit)
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        gives = survey_of(game=game, world_id=world_id).radius_gives(x=MIDDLE, y=MIDDLE)
        self.assertEqual((gives[Food], gives[Wood], gives[Stone]), (needs[Food], 1, 0))

    def test_tiles_with_a_terrain_bonus_or_a_strategic_resource_and_water_and_tarpit_are_never_changed(self):
        game, world_id = flat_game()
        radius = StartImprover.radius_outside_center(game=game, world_id=world_id, x=MIDDLE, y=MIDDLE)
        water, tarpit, *special = radius[:-LEFT_PLAIN]
        make(game=game, world_id=world_id, x=water[0], y=water[1], terrain=Water)
        make(game=game, world_id=world_id, x=tarpit[0], y=tarpit[1], terrain=Tarpit)
        for x, y in special:
            TerrainBonusControl.place(game=game, world=world_id, x=x, y=y, bonus=Bison)
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        self.assertEqual(set(terrains_of(game=game, world_id=world_id, tiles=special)), {Grassland})
        self.assertTrue(all(TerrainBonusControl.bonus_at(game=game, world=world_id, x=x, y=y) is Bison for x, y in special))
        self.assertIs(game.get_terrain(world=world_id, x=water[0], y=water[1]), Water)
        self.assertIs(game.get_terrain(world=world_id, x=tarpit[0], y=tarpit[1]), Tarpit)
        changed = terrains_of(game=game, world_id=world_id, tiles=radius[-LEFT_PLAIN:])
        self.assertEqual((changed.count(Forest), changed.count(Mountains)), (Caveman.MAP.START_NEEDS[Wood], Caveman.MAP.START_NEEDS[Stone]))

    def test_the_strategic_resource_goes_on_a_tile_near_that_can_have_it_before_any_tile_is_changed_for_it(self):
        game, world_id = flat_game()
        make(game=game, world_id=world_id, x=MIDDLE + STRATEGIC_REACH, y=MIDDLE, terrain=Mountains)
        StartImprover.add_strategic(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE, resource=Flint)
        self.assertIs(Strategic.resource_at(game=game, world=world_id, x=MIDDLE + STRATEGIC_REACH, y=MIDDLE), Flint)
        everything = terrains_of(game=game, world_id=world_id, tiles=MapGenerator.every_tile(game.get_world(world_id)))
        self.assertEqual(everything.count(Mountains), 1)

    def test_a_need_no_terrain_of_the_theme_can_meet_changes_nothing(self):
        game, world_id = flat_game(theme=NeedyCaveman)
        self.assertEqual(survey_of(game=game, world_id=world_id).lacks(x=MIDDLE, y=MIDDLE), {Flint: 1})
        StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=MIDDLE, y=MIDDLE)
        self.assertEqual(set(terrains_of(game=game, world_id=world_id, tiles=MapGenerator.every_tile(game.get_world(world_id)))), {Grassland})


class TestStartingSites(unittest.TestCase):

    def test_on_a_generated_world_every_civilization_starts_on_a_site_with_room_that_lacks_and_misses_nothing(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                game = caveman_game(seed)
                world_id = MapGenerator.make(game=game)
                chosen = MapGenerator.starting_tiles(game=game, world_id=world_id, count=THREE)
                before = survey_of(game=game, world_id=world_id)
                self.assertTrue(all(before.has_room(x=x, y=y) for x, y in chosen))
                game = caveman_game(seed)
                world_id = MapGenerator.make(game=game)
                tiles = MapGenerator.place_civilizations(game=game, world_id=world_id)
                self.assertEqual(tiles, chosen)
                after = survey_of(game=game, world_id=world_id)
                for x, y in tiles:
                    self.assertTrue(after.is_ready(x=x, y=y))

    def test_sites_that_are_good_already_are_chosen_before_sites_that_need_improving(self):
        game, world_id = flat_game()
        good = [(MIDDLE - 20, MIDDLE), (MIDDLE, MIDDLE), (MIDDLE + 20, MIDDLE)]
        for x, y in good:
            StartImprover.improve(game=game, world_id=world_id, kind=Settler, x=x, y=y)
        survey = survey_of(game=game, world_id=world_id)
        chosen = MapGenerator.starting_tiles(game=game, world_id=world_id, count=THREE)
        self.assertTrue(all(survey.is_ready(x=x, y=y) for x, y in chosen))
        game, world_id = flat_game()
        chosen = MapGenerator.starting_tiles(game=game, world_id=world_id, count=THREE)
        survey = survey_of(game=game, world_id=world_id)
        self.assertTrue(all(survey.has_room(x=x, y=y) and not survey.is_ready(x=x, y=y) for x, y in chosen))

    def test_a_world_too_short_for_any_site_to_have_room_still_starts_every_civilization_and_improves_each_site(self):
        game = caveman_game(A_SEED)
        world_id = MapGenerator.make(game=game, height=SHORT)
        survey = survey_of(game=game, world_id=world_id)
        self.assertFalse(any(survey.has_room(x=x, y=y) for x, y in MapGenerator.sites(game=game, world_id=world_id)))
        tiles = MapGenerator.place_civilizations(game=game, world_id=world_id)
        self.assertEqual(len(tiles), THREE)
        after = survey_of(game=game, world_id=world_id)
        for x, y in tiles:
            self.assertEqual((after.lacks(x=x, y=y), after.misses(x=x, y=y)), ({}, []))
