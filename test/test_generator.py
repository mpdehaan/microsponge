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
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.game.game import Game
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import saved_name, shown_name
from microsponge.engine.players.traits import Traits
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.world.generator import MapGenerator, distance
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_NO_MAP, ERR_NO_ROOM_TO_START
from microsponge.support.map_preview import marks_for, preview_lines, previewed_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes.caveman.theme import Caveman
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
