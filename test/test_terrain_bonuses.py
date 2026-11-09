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

"""Tests for terrain bonuses: special tiles that give more when they are worked, like bison on grassland."""

import os
import tempfile
import unittest

from caveman_game import BISON_TILE, ELEPHANT_TILE, FOREST_TILE, GRASSLAND_TILE, THE_WORLD, WATER_TILE, end_rounds, found_village, game_facts, started_caveman_game
from later_caveman import REORDERED_CAVEMAN, later_caveman
from refusals import Refusals
from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.terrain_bonus import TerrainBonus
from microsponge.engine.saving.saved_game import load_game, save_game
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl
from microsponge.err_messages import ERR_BONUS_NOT_ON
from microsponge.themes.caveman.improvements import Clearing, Farm
from microsponge.themes.caveman.resources import Food, Wood
from microsponge.themes.caveman.terrain_bonuses import Bison, Elephants
from microsponge.themes.caveman.terrains import Forest, Grassland, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Worker

FIRST_CIVILIZATION = 1
A_NAME = 'Ugghome'
A_FILE_NAME = 'bonuses.json'
ONE_CITIZEN = 1
# A grassland tile and a forest tile inside the first civilization's first city radius, away from the city center, as (x, y).
INSIDE = (8, 8)
INSIDE_FOREST = (12, 8)


class Mushrooms(TerrainBonus):
    """A bonus that forest and grassland are both compatible with, which caveman does not have."""

    ON = (Forest, Grassland)
    GIVES = {Food: 1}


class Beavers(TerrainBonus):
    """A bonus that only forest is compatible with."""

    ON = (Forest,)
    GIVES = {Wood: 2}


BONUS_CAVEMAN = later_caveman({Category.TERRAIN_BONUSES: (*Caveman.TERRAIN_BONUSES, Mushrooms, Beavers)})


class BonusCase(Refusals, unittest.TestCase):
    """A started game of caveman with two bonuses of the tests' own."""

    def setUp(self):
        self.game = started_caveman_game(theme=BONUS_CAVEMAN)
        self.world = self.game.get_world(THE_WORLD)

    def put(self, *, bonus, tile):
        x, y = tile
        TerrainBonusControl.place(game=self.game, world=THE_WORLD, x=x, y=y, bonus=bonus)

    def at(self, tile):
        x, y = tile
        return TerrainBonusControl.bonus_at(game=self.game, world=THE_WORLD, x=x, y=y)

    def gives(self, tile):
        x, y = tile
        return Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y)


class TestWhereTerrainBonusesAre(BonusCase):

    def test_the_test_world_has_bison_and_elephants_on_grassland(self):
        self.assertIs(self.at(BISON_TILE), Bison)
        self.assertIs(self.at(ELEPHANT_TILE), Elephants)
        self.assertIsNone(self.at(GRASSLAND_TILE))

    def test_a_bonus_is_put_on_a_tile_of_a_compatible_terrain_and_a_tile_has_one_bonus(self):
        self.put(bonus=Mushrooms, tile=INSIDE_FOREST)
        self.assertIs(self.at(INSIDE_FOREST), Mushrooms)
        self.put(bonus=Beavers, tile=INSIDE_FOREST)
        self.assertIs(self.at(INSIDE_FOREST), Beavers)
        x, y = INSIDE_FOREST
        TerrainBonusControl.remove(game=self.game, world=THE_WORLD, x=x, y=y)
        self.assertIsNone(self.at(INSIDE_FOREST))

    def test_a_bonus_is_refused_on_a_terrain_that_is_not_compatible(self):
        for bonus, tile, terrain in ((Beavers, GRASSLAND_TILE, Grassland), (Bison, FOREST_TILE, Forest), (Mushrooms, WATER_TILE, Water)):
            with self.subTest(bonus=bonus):
                refused = self.refused(lambda: self.put(bonus=bonus, tile=tile))
                self.assertEqual(refused, ERR_BONUS_NOT_ON.format(bonus=shown_name(bonus), terrain=shown_name(terrain)))
                self.assertIsNone(self.at(tile))


class TestWhatABonusGives(BonusCase):

    def test_a_tile_with_a_bonus_gives_the_terrain_and_the_bonus_together(self):
        self.assertEqual(self.gives(GRASSLAND_TILE), Grassland.GIVES)
        self.assertEqual(self.gives(BISON_TILE), {Food: Grassland.GIVES[Food] + Bison.GIVES[Food]})
        self.assertEqual(self.gives(ELEPHANT_TILE), {Food: Grassland.GIVES[Food] + Elephants.GIVES[Food]})
        self.put(bonus=Beavers, tile=FOREST_TILE)
        self.assertEqual(self.gives(FOREST_TILE), {Wood: Forest.GIVES[Wood] + Beavers.GIVES[Wood]})

    def test_a_bonus_and_an_improvement_both_add_to_the_tile(self):
        x, y = INSIDE
        self.put(bonus=Bison, tile=INSIDE)
        self.world.set_value(layer=Layer.IMPROVEMENT, x=x, y=y, value=self.game.get_catalog().get_id(category=Category.IMPROVEMENTS, kind=Farm))
        self.assertEqual(self.gives(INSIDE), {Food: Grassland.GIVES[Food] + Bison.GIVES[Food] + Farm.TILE_BONUS[Food]})

    def test_a_citizen_goes_to_the_bonus_tile_that_gives_the_most_food_and_the_village_collects_it(self):
        self.put(bonus=Elephants, tile=INSIDE)
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        taken = Harvest.assignments(game=self.game, city=city)
        self.assertEqual(len(taken), ONE_CITIZEN)
        self.assertEqual((taken[0].x, taken[0].y), INSIDE)
        self.assertEqual(taken[0].gives[Food], Grassland.GIVES[Food] + Elephants.GIVES[Food])
        self.assertEqual(Harvest.of_city(game=self.game, city=city)[Food], Grassland.GIVES[Food] + Elephants.GIVES[Food] + Caveman.CITY.PRODUCES.get(Food, 0))


class TestChangingTheTerrainUnderABonus(BonusCase):

    def clear(self, tile):
        """Have a worker of the first civilization cut the trees of a forest tile, which becomes grassland."""
        x, y = tile
        worker = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        Orders.build_improvement(game=self.game, unit=worker, improvement=Clearing)
        end_rounds(game=self.game, rounds=Clearing.BUILD_TURNS)
        self.assertIs(self.game.get_terrain(world=THE_WORLD, x=x, y=y), Grassland)

    def test_a_bonus_goes_away_for_good_when_its_terrain_changes_to_one_that_is_not_compatible(self):
        self.put(bonus=Beavers, tile=INSIDE_FOREST)
        self.clear(INSIDE_FOREST)
        self.assertIsNone(self.at(INSIDE_FOREST))
        self.assertEqual(self.gives(INSIDE_FOREST), Grassland.GIVES)

    def test_a_bonus_stays_when_its_terrain_changes_to_a_compatible_one(self):
        self.put(bonus=Mushrooms, tile=INSIDE_FOREST)
        self.clear(INSIDE_FOREST)
        self.assertIs(self.at(INSIDE_FOREST), Mushrooms)
        self.assertEqual(self.gives(INSIDE_FOREST), {Food: Grassland.GIVES[Food] + Mushrooms.GIVES[Food]})

    def test_changing_a_tile_with_no_bonus_changes_no_other_tile(self):
        self.clear(INSIDE_FOREST)
        self.assertIs(self.at(BISON_TILE), Bison)


class TestSavingTerrainBonuses(unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, A_FILE_NAME)

    def test_the_bonuses_on_the_map_come_back_from_a_saved_game_even_in_a_later_theme_whose_bonuses_have_other_ids(self):
        save_game(game=self.game, path=self.path)
        for theme in (Caveman, REORDERED_CAVEMAN):
            with self.subTest(theme=theme):
                loaded = load_game(path=self.path, themes=(theme,))
                self.assertEqual(game_facts(loaded), game_facts(self.game))
                x, y = BISON_TILE
                self.assertIs(TerrainBonusControl.bonus_at(game=loaded, world=THE_WORLD, x=x, y=y), Bison)
                x, y = ELEPHANT_TILE
                self.assertIs(TerrainBonusControl.bonus_at(game=loaded, world=THE_WORLD, x=x, y=y), Elephants)
        x, y = BISON_TILE
        loaded = load_game(path=self.path, themes=(REORDERED_CAVEMAN,))
        self.assertNotEqual(
            loaded.get_world(THE_WORLD).get_value(layer=Layer.TERRAIN_BONUS, x=x, y=y),
            self.game.get_world(THE_WORLD).get_value(layer=Layer.TERRAIN_BONUS, x=x, y=y),
        )


if __name__ == '__main__':
    unittest.main()
