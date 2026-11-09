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

"""Saving a game of caveman as JSON and loading it back, with this version's theme and with later ones."""

import json
import os
import tempfile
import unittest

from caveman_game import GRASSLAND_TILE, MOUNTAIN_TILE, SETTLER_TILES, THE_WORLD, WATER_TILE, end_rounds, end_turn_by_order, game_facts, give_building, held, learn, new_caveman_game, started_caveman_game
from later_caveman import EXTENDED_CAVEMAN, REORDERED_CAVEMAN, SETTLERLESS_CAVEMAN, Hunter
from refusals import Refusals
from microsponge.engine.game.game import GAME_KEYS, NAMES_KEY, THEME_KEY, UNITS_KEY, WORLDS_KEY
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import CATEGORIES, Category, shown_category
from microsponge.engine.kinds.kind import saved_name
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.research import Research
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.work_control import WorkControl
from microsponge.engine.saving.saved_game import REQUIRED_VERSION, REQUIRED_VERSION_KEY, SAVED_BY_KEY, load_game, save_game
from microsponge.engine.units.unit_column import UNIT_COLUMNS, UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import LAYERS, Layer
from microsponge.engine.world.world import LAYERS_KEY
from microsponge.err_messages import ERR_KIND_GONE, ERR_NO_SUCH_THEME, ERR_NOT_A_SAVED_GAME, ERR_SAVED_GAME_TOO_NEW, ERR_SAVED_GAME_TOO_OLD
from microsponge.support.version import VERSION, VERSION_SEPARATOR, is_version, version_numbers
from microsponge.themes import THEMES
from microsponge.themes.caveman.buildings import Granary, GreatCavePainting
from microsponge.themes.caveman.improvements import Farm
from microsponge.themes.caveman.resources import Currency, Food, Stone, Wood
from microsponge.themes.caveman.technologies import Agriculture, Clubs, Discipline
from microsponge.themes.caveman.terrains import Grassland, Mountains, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Warrior, Worker
from microsponge.themes.classic.theme import Classic

FILE_NAME = 'game.json'
A_TURN = 41
HURT = 3
FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
FIRST_CITY = 1
A_NAME = 'Ugghome'
A_FEW_ROUNDS = 2
A_LEVEL = 3
SOME_EXPERIENCE = 35
A_FEW_CITIZENS = 2
THE_EARLIEST_VERSION = '0.0.0'
NOT_JSON = 'once upon a time'
WRITE = 'w'
NO_SUCH_THEME = 'Atlantis'


def a_later_version():
    """Return a version after this one, as a saved game from a later microsponge would require."""
    first, _, _ = version_numbers(VERSION)
    return VERSION_SEPARATOR.join(str(number) for number in (first + 1, 0, 0))


class TestSaving(Refusals, unittest.TestCase):

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, FILE_NAME)
        self.game = new_caveman_game()
        x, y = GRASSLAND_TILE
        self.warrior = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        self.game.get_units().set_value(column=UnitColumn.HIT_POINTS, unit=self.warrior, value=HURT)
        x, y = MOUNTAIN_TILE
        gone = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        UnitControl.remove(game=self.game, unit=gone)
        self.game.set_turn(A_TURN)

    def saved_data(self):
        """Save the game and return what the file holds."""
        save_game(game=self.game, path=self.path)
        with open(self.path) as file:
            return json.load(file)

    def write(self, data):
        with open(self.path, WRITE) as file:
            json.dump(data, file)

    def terrain_at(self, *, game, tile):
        x, y = tile
        kind_id = game.get_world(THE_WORLD).get_value(layer=Layer.TERRAIN, x=x, y=y)
        return game.get_catalog().get_kind(category=Category.TERRAINS, kind_id=kind_id)

    def test_a_game_comes_back_from_its_file_as_it_was(self):
        save_game(game=self.game, path=self.path)
        loaded = load_game(path=self.path, themes=THEMES)
        self.assertIs(loaded.get_theme(), Caveman)
        self.assertEqual(loaded.get_turn(), A_TURN)
        self.assertEqual(game_facts(loaded), game_facts(self.game))
        self.assertEqual(loaded.get_units().get_value(column=UnitColumn.HIT_POINTS, unit=self.warrior), HURT)

    def test_a_loaded_game_can_be_played_on_and_saved_again(self):
        save_game(game=self.game, path=self.path)
        loaded = load_game(path=self.path, themes=THEMES)
        x, y = MOUNTAIN_TILE
        UnitControl.place(game=loaded, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        loaded.next_turn()
        save_game(game=loaded, path=self.path)
        again = load_game(path=self.path, themes=THEMES)
        self.assertEqual(game_facts(again), game_facts(loaded))
        self.assertNotEqual(game_facts(again), game_facts(self.game))

    def a_game_in_play(self):
        """Return a game a few turns in: a city with a priority, a building and a production queue, a war, technologies, research under way, and a worker part of the way through a farm."""
        game = started_caveman_game()
        x, y = SETTLER_TILES[0]
        settler = game.get_world(THE_WORLD).get_value(layer=Layer.UNIT, x=x, y=y)
        city = Orders.found_city(game=game, settler=settler, name=A_NAME)
        Orders.prioritize(game=game, city=city, resource=Wood, citizens=A_FEW_CITIZENS)
        Orders.declare_war(game=game, civilization=FIRST_CIVILIZATION, on=SECOND_CIVILIZATION)
        for technology in (Agriculture, Clubs):
            learn(game=game, civilization=FIRST_CIVILIZATION, technology=technology)
        learn(game=game, civilization=SECOND_CIVILIZATION, technology=Clubs)
        give_building(game=game, city=city, building=GreatCavePainting)
        Orders.build(game=game, city=city, kind=Granary)
        Orders.build(game=game, city=city, kind=Warrior)
        Orders.research(game=game, civilization=FIRST_CIVILIZATION, technology=Discipline)
        x, y = GRASSLAND_TILE
        self.worker = UnitControl.place(game=game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        Orders.build_improvement(game=game, unit=self.worker, improvement=Farm)
        end_rounds(game=game, rounds=A_FEW_ROUNDS)
        end_turn_by_order(game=game, civilization=FIRST_CIVILIZATION)
        return game

    def test_a_unit_keeps_its_level_and_experience_through_a_save(self):
        game = self.a_game_in_play()
        unit = UnitControl.units_of(game=game, civilization=FIRST_CIVILIZATION)[0]
        game.get_units().set_value(column=UnitColumn.LEVEL, unit=unit, value=A_LEVEL)
        game.get_units().set_value(column=UnitColumn.EXPERIENCE, unit=unit, value=SOME_EXPERIENCE)
        save_game(game=game, path=self.path)
        loaded = load_game(path=self.path, themes=THEMES)
        self.assertEqual(UnitControl.level_of(game=loaded, unit=unit), A_LEVEL)
        self.assertEqual(loaded.get_units().get_value(column=UnitColumn.EXPERIENCE, unit=unit), SOME_EXPERIENCE)
        self.assertEqual(game_facts(loaded), game_facts(game))

    def test_a_game_in_play_comes_back_as_it_was_and_goes_on_the_same_way(self):
        game = self.a_game_in_play()
        save_game(game=game, path=self.path)
        loaded = load_game(path=self.path, themes=THEMES)
        self.assertEqual(game_facts(loaded), game_facts(game))
        self.assertEqual(loaded.get_playing(), SECOND_CIVILIZATION)
        for either in (game, loaded):
            end_rounds(game=either, rounds=Farm.BUILD_TURNS)
        self.assertEqual(game_facts(loaded), game_facts(game))
        x, y = GRASSLAND_TILE
        self.assertNotEqual(loaded.get_world(THE_WORLD).get_value(layer=Layer.IMPROVEMENT, x=x, y=y), NOTHING)

    def test_a_game_in_play_loads_into_a_later_theme_whose_resources_technologies_and_improvements_have_other_ids(self):
        game = self.a_game_in_play()
        save_game(game=game, path=self.path)
        loaded = load_game(path=self.path, themes=(REORDERED_CAVEMAN,))
        self.assertEqual(game_facts(loaded), game_facts(game))
        for resource in (Currency, Food, Stone):
            with self.subTest(resource=resource):
                self.assertEqual(held(game=loaded, civilization=FIRST_CIVILIZATION, resource=resource), held(game=game, civilization=FIRST_CIVILIZATION, resource=resource))
        self.assertGreater(held(game=loaded, civilization=FIRST_CIVILIZATION, resource=Currency), held(game=loaded, civilization=FIRST_CIVILIZATION, resource=Stone))
        self.assertNotEqual(loaded.get_civilization(FIRST_CIVILIZATION).get_holdings(), game.get_civilization(FIRST_CIVILIZATION).get_holdings())
        self.assertNotEqual(loaded.get_civilization(FIRST_CIVILIZATION).get_technologies(), game.get_civilization(FIRST_CIVILIZATION).get_technologies())
        self.assertNotEqual(loaded.get_cities()[0].get_priorities(), game.get_cities()[0].get_priorities())
        self.assertIs(WorkControl.improvement_of(game=loaded, unit=self.worker), Farm)
        self.assertEqual(Production.queue_of(game=loaded, city=FIRST_CITY), [Granary, Warrior])
        self.assertEqual(loaded.get_cities()[0].get_progress(), game.get_cities()[0].get_progress())
        self.assertNotEqual(loaded.get_cities()[0].get_queue(), game.get_cities()[0].get_queue())
        self.assertNotEqual(loaded.get_cities()[0].get_buildings(), game.get_cities()[0].get_buildings())
        self.assertIs(Research.researching(game=loaded, civilization=FIRST_CIVILIZATION), Discipline)
        self.assertNotEqual(loaded.get_civilization(FIRST_CIVILIZATION).get_researching(), game.get_civilization(FIRST_CIVILIZATION).get_researching())
        self.assertNotEqual(loaded.get_units().get_value(column=UnitColumn.IMPROVEMENT, unit=self.worker), game.get_units().get_value(column=UnitColumn.IMPROVEMENT, unit=self.worker))
        for either in (game, loaded):
            end_rounds(game=either, rounds=Farm.BUILD_TURNS)
        self.assertEqual(game_facts(loaded), game_facts(game))

    def test_the_file_holds_the_versions_and_every_part_of_a_game(self):
        data = self.saved_data()
        self.assertEqual(data[REQUIRED_VERSION_KEY], REQUIRED_VERSION)
        self.assertEqual(data[SAVED_BY_KEY], VERSION)
        self.assertEqual(set(data), {REQUIRED_VERSION_KEY, SAVED_BY_KEY, *GAME_KEYS})
        self.assertEqual(data[THEME_KEY], saved_name(Caveman))

    def test_the_file_holds_numbers_under_numbered_layers_and_columns_and_a_name_for_each_id(self):
        data = self.saved_data()
        layers = data[WORLDS_KEY][THE_WORLD][LAYERS_KEY]
        self.assertEqual(set(layers), {str(layer) for layer in LAYERS})
        self.assertEqual(set(data[UNITS_KEY]), {str(column) for column in UNIT_COLUMNS})
        for rows in layers.values():
            self.assertTrue(all(type(value) is int for row in rows for value in row))
        for values in data[UNITS_KEY].values():
            self.assertTrue(all(type(value) is int for value in values))
        self.assertEqual(data[NAMES_KEY], self.game.get_catalog().get_names())
        self.assertEqual(set(data[NAMES_KEY]), set(CATEGORIES))

    def test_the_required_version_is_a_version_no_later_than_this_one(self):
        self.assertTrue(is_version(REQUIRED_VERSION))
        self.assertLessEqual(version_numbers(REQUIRED_VERSION), version_numbers(VERSION))

    def test_a_game_from_before_the_required_version_is_refused(self):
        self.assertLess(version_numbers(THE_EARLIEST_VERSION), version_numbers(REQUIRED_VERSION))
        data = self.saved_data()
        data[REQUIRED_VERSION_KEY] = THE_EARLIEST_VERSION
        self.write(data)
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), ERR_SAVED_GAME_TOO_OLD.format(oldest=REQUIRED_VERSION))

    def test_a_game_that_requires_a_later_version_is_refused(self):
        data = self.saved_data()
        data[REQUIRED_VERSION_KEY] = a_later_version()
        self.write(data)
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), ERR_SAVED_GAME_TOO_NEW.format(required=a_later_version(), version=VERSION))

    def test_a_game_saved_by_an_earlier_version_that_requires_no_more_than_this_one_loads(self):
        data = self.saved_data()
        data[SAVED_BY_KEY] = THE_EARLIEST_VERSION
        self.write(data)
        self.assertEqual(game_facts(load_game(path=self.path, themes=THEMES)), game_facts(self.game))

    def test_a_file_that_is_not_a_saved_game_is_refused(self):
        expected = ERR_NOT_A_SAVED_GAME.format(path=self.path)
        with open(self.path, WRITE) as file:
            file.write(NOT_JSON)
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), expected)
        whole = self.saved_data()
        for missing in (REQUIRED_VERSION_KEY, *GAME_KEYS):
            with self.subTest(missing=missing):
                self.write({key: value for key, value in whole.items() if key != missing})
                self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), expected)
        for data in ([], A_TURN, {**whole, REQUIRED_VERSION_KEY: NOT_JSON}, {**whole, REQUIRED_VERSION_KEY: A_TURN}):
            with self.subTest(data=data):
                self.write(data)
                self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), expected)

    def test_a_game_of_a_theme_that_is_not_offered_is_refused(self):
        save_game(game=self.game, path=self.path)
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=(Classic,))), ERR_NO_SUCH_THEME.format(name=saved_name(Caveman)))
        data = self.saved_data()
        data[THEME_KEY] = NO_SUCH_THEME
        self.write(data)
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), ERR_NO_SUCH_THEME.format(name=NO_SUCH_THEME))

    def test_a_game_loads_into_a_later_theme_that_added_a_kind_without_any_id_changing(self):
        save_game(game=self.game, path=self.path)
        loaded = load_game(path=self.path, themes=(EXTENDED_CAVEMAN,))
        self.assertIs(loaded.get_theme(), EXTENDED_CAVEMAN)
        self.assertEqual(game_facts(loaded), game_facts(self.game))
        saved_ids = self.game.get_units().get_value(column=UnitColumn.KIND, unit=self.warrior)
        self.assertEqual(loaded.get_units().get_value(column=UnitColumn.KIND, unit=self.warrior), saved_ids)
        x, y = MOUNTAIN_TILE
        hunter = UnitControl.place(game=loaded, kind=Hunter, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        self.assertIs(UnitControl.kind_of(game=loaded, unit=hunter), Hunter)

    def test_a_game_loads_into_a_later_theme_whose_kinds_are_in_another_order(self):
        save_game(game=self.game, path=self.path)
        loaded = load_game(path=self.path, themes=(REORDERED_CAVEMAN,))
        self.assertEqual(game_facts(loaded), game_facts(self.game))
        self.assertIs(self.terrain_at(game=loaded, tile=GRASSLAND_TILE), Grassland)
        self.assertIs(self.terrain_at(game=loaded, tile=WATER_TILE), Water)
        self.assertIs(self.terrain_at(game=loaded, tile=MOUNTAIN_TILE), Mountains)
        self.assertIs(UnitControl.kind_of(game=loaded, unit=self.warrior), Warrior)
        x, y = SETTLER_TILES[0]
        settler = loaded.get_world(THE_WORLD).get_value(layer=Layer.UNIT, x=x, y=y)
        self.assertIs(UnitControl.kind_of(game=loaded, unit=settler), Settler)
        saved_id = self.game.get_units().get_value(column=UnitColumn.KIND, unit=settler)
        self.assertNotEqual(loaded.get_units().get_value(column=UnitColumn.KIND, unit=settler), saved_id)
        x, y = GRASSLAND_TILE
        self.assertNotEqual(
            loaded.get_world(THE_WORLD).get_value(layer=Layer.TERRAIN, x=x, y=y),
            self.game.get_world(THE_WORLD).get_value(layer=Layer.TERRAIN, x=x, y=y),
        )

    def test_a_game_saved_by_a_later_theme_holds_a_kind_this_one_lacks_and_is_refused(self):
        save_game(game=self.game, path=self.path)
        later = load_game(path=self.path, themes=(REORDERED_CAVEMAN,))
        save_game(game=later, path=self.path)
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=THEMES)), ERR_KIND_GONE.format(name=saved_name(Hunter), category=shown_category(Category.UNITS), theme=saved_name(Caveman)))

    def test_a_game_that_holds_a_kind_the_theme_no_longer_has_is_refused(self):
        save_game(game=self.game, path=self.path)
        expected = ERR_KIND_GONE.format(name=saved_name(Settler), category=shown_category(Category.UNITS), theme=saved_name(Caveman))
        self.assertEqual(self.refused(lambda: load_game(path=self.path, themes=(SETTLERLESS_CAVEMAN,))), expected)


if __name__ == '__main__':
    unittest.main()
