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

"""Tests for what the citizens of a city collect: what a tile gives, which tile each citizen takes, and what a city collects in a turn."""

import unittest

from caveman_game import (
    FOREST_TILE, GRASSLAND_TILE, MOUNTAIN_COLUMN, MOUNTAIN_TILE, SETTLER_TILES, TARPIT_TILE, THE_WORLD, WATER_TILE, found_village, give_building, new_caveman_game, resource_id, terrain_id,
)
from later_caveman import later_caveman
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.kinds.bonuses import WHOLE
from microsponge.engine.kinds.building import Building
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.city_spec import CitySpec
from microsponge.engine.kinds.terrain import Terrain
from microsponge.engine.world.layer import Layer
from microsponge.themes.caveman.buildings import ArrangementOfRocks, Granary
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.improvements import Farm
from microsponge.themes.caveman.resources import Currency, Food, Stone, Wood
from microsponge.themes.caveman.terrains import Forest, Grassland, Mountains, Tarpit, Water
from microsponge.themes.caveman.theme import Caveman

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
# How far the city center and the city radius reach from the middle tile.
CENTER_REACH = CitySpec.CENTER_SIZE // 2
RADIUS_REACH = CitySpec.RADIUS_SIZE // 2
JUST_PAST_CENTER = CENTER_REACH + 1
WORKABLE_TILES = CitySpec.RADIUS_SIZE * CitySpec.RADIUS_SIZE - CitySpec.CENTER_SIZE * CitySpec.CENTER_SIZE
ONE_CITIZEN = 1
TWO_CITIZENS = 2
SEVERAL_CITIZENS = 3
MANY_CITIZENS = 10
NO_CURRENCY = 0
# A tile of the first village's radius that is not among the nearest, as how far it is east of the middle.
FURTHER_EAST = 5
# How far the mountains are west of the middle of the second village.
MOUNTAIN_STEPS = SETTLER_TILES[1][0] - MOUNTAIN_COLUMN


class Barren(Terrain):
    """A terrain that gives nothing."""


BARREN_CAVEMAN = later_caveman({Category.TERRAINS: (*Caveman.TERRAINS, Barren)})


class Hoard(Building):
    """A building that adds a percent to the currency of its city, which does not come out even for a city of several citizens."""

    INCOME_BONUS = 25


HOARD_CAVEMAN = later_caveman({Category.BUILDINGS: (*Caveman.BUILDINGS, Hoard)})


class TestHarvest(unittest.TestCase):

    def setUp(self):
        self.game = new_caveman_game()
        self.world = self.game.get_world(THE_WORLD)

    def village(self, *, game, civilization, citizens):
        """Build a civilization's village in a game, give it so many citizens, and return its id."""
        city = found_village(game=game, civilization=civilization, name=A_NAME)
        game.get_city(city).set_citizens(citizens)
        return city

    def game_of(self, terrain):
        """Return a game whose whole world is one terrain."""
        game = new_caveman_game(theme=BARREN_CAVEMAN)
        game.get_world(THE_WORLD).fill(layer=Layer.TERRAIN, value=terrain_id(game=game, terrain=terrain))
        return game

    def put_farm(self, *, x, y):
        farm = self.game.get_catalog().get_id(category=Category.IMPROVEMENTS, kind=Farm)
        self.world.set_value(layer=Layer.IMPROVEMENT, x=x, y=y, value=farm)

    def steps_away(self, *, tile, civilization):
        """Return how far a tile is from where a civilization's village is."""
        x, y = SETTLER_TILES[civilization - 1]
        return max(self.world.columns_apart(first=tile.x, second=x), abs(tile.y - y))

    def places(self, tiles):
        return [(tile.x, tile.y) for tile in tiles]

    def give_priority(self, *, city, resource, citizens):
        self.game.get_city(city).set_priority(resource=resource_id(game=self.game, resource=resource), citizens=citizens)

    def test_a_game_tells_the_terrain_of_a_tile(self):
        for terrain, (x, y) in ((Grassland, GRASSLAND_TILE), (Mountains, MOUNTAIN_TILE), (Water, WATER_TILE), (Forest, FOREST_TILE), (Tarpit, TARPIT_TILE)):
            with self.subTest(terrain=terrain):
                self.assertIs(self.game.get_terrain(world=THE_WORLD, x=x, y=y), terrain)

    def test_a_tarpit_gives_nothing(self):
        x, y = TARPIT_TILE
        self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y), {})

    def test_a_tile_gives_what_its_terrain_gives(self):
        for terrain, (x, y) in ((Grassland, GRASSLAND_TILE), (Mountains, MOUNTAIN_TILE), (Water, WATER_TILE)):
            with self.subTest(terrain=terrain):
                self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y), terrain.GIVES)

    def test_a_farm_adds_its_bonus_to_what_its_tile_gives_and_the_terrain_stays_as_it_was(self):
        x, y = GRASSLAND_TILE
        plain = dict(Grassland.GIVES)
        self.put_farm(x=x, y=y)
        self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y), {Food: plain[Food] + Farm.TILE_BONUS[Food]})
        self.assertEqual(Grassland.GIVES, plain)
        self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x + 1, y=y), plain)

    def test_citizens_can_work_every_tile_of_the_radius_outside_the_center(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        places = self.places(Harvest.workable_tiles(game=self.game, city=city))
        self.assertEqual(len(places), WORKABLE_TILES)
        self.assertEqual(len(set(places)), WORKABLE_TILES)
        self.assertFalse(set(places) & set(CityControl.center_tiles(game=self.game, city=city)))
        self.assertLessEqual(set(places), set(CityControl.radius_tiles(game=self.game, city=city)))

    def test_the_tiles_citizens_can_work_come_nearest_the_middle_first(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        steps = [self.steps_away(tile=tile, civilization=FIRST_CIVILIZATION) for tile in Harvest.workable_tiles(game=self.game, city=city)]
        self.assertEqual(steps, sorted(steps))
        self.assertEqual((steps[0], steps[-1]), (JUST_PAST_CENTER, RADIUS_REACH))

    def test_no_tile_is_workable_by_two_villages(self):
        first = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        second = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        first_places = self.places(Harvest.workable_tiles(game=self.game, city=first))
        second_places = self.places(Harvest.workable_tiles(game=self.game, city=second))
        self.assertFalse(set(first_places) & set(second_places))
        self.assertEqual((len(first_places), len(second_places)), (WORKABLE_TILES, WORKABLE_TILES))

    def test_a_citizen_with_no_priority_takes_the_nearest_tile_that_gives_the_most_food(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        taken = Harvest.assignments(game=self.game, city=city)
        self.assertEqual(len(taken), ONE_CITIZEN)
        self.assertEqual(self.steps_away(tile=taken[0], civilization=FIRST_CIVILIZATION), JUST_PAST_CENTER)
        self.assertEqual(taken[0].gives, Grassland.GIVES)

    def test_a_citizen_goes_further_for_a_tile_that_gives_more_food(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=TWO_CITIZENS)
        x, y = SETTLER_TILES[0]
        self.put_farm(x=x + FURTHER_EAST, y=y)
        first, second = Harvest.assignments(game=self.game, city=city)
        self.assertEqual((first.x, first.y), (x + FURTHER_EAST, y))
        self.assertEqual(first.amount_of(Food), Grassland.GIVES[Food] + Farm.TILE_BONUS[Food])
        self.assertEqual(self.steps_away(tile=second, civilization=FIRST_CIVILIZATION), JUST_PAST_CENTER)

    def test_no_two_citizens_share_a_tile(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=MANY_CITIZENS)
        places = self.places(Harvest.assignments(game=self.game, city=city))
        self.assertEqual(len(places), MANY_CITIZENS)
        self.assertEqual(len(set(places)), MANY_CITIZENS)

    def test_a_citizen_with_a_priority_takes_the_nearest_tile_that_gives_that_resource_and_the_others_take_food(self):
        city = self.village(game=self.game, civilization=SECOND_CIVILIZATION, citizens=SEVERAL_CITIZENS)
        self.give_priority(city=city, resource=Stone, citizens=ONE_CITIZEN)
        first, *others = Harvest.assignments(game=self.game, city=city)
        self.assertEqual(first.gives, Mountains.GIVES)
        self.assertEqual((first.x, self.steps_away(tile=first, civilization=SECOND_CIVILIZATION)), (MOUNTAIN_COLUMN, MOUNTAIN_STEPS))
        self.assertEqual([tile.gives for tile in others], [Grassland.GIVES] * (SEVERAL_CITIZENS - ONE_CITIZEN))

    def test_a_priority_that_cannot_be_met_falls_back_to_food(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=TWO_CITIZENS)
        self.give_priority(city=city, resource=Stone, citizens=TWO_CITIZENS)
        self.assertEqual([tile.gives for tile in Harvest.assignments(game=self.game, city=city)], [Grassland.GIVES] * TWO_CITIZENS)

    def test_a_priority_for_more_citizens_than_a_village_has_takes_every_citizen_it_has(self):
        city = self.village(game=self.game, civilization=SECOND_CIVILIZATION, citizens=TWO_CITIZENS)
        self.give_priority(city=city, resource=Stone, citizens=MANY_CITIZENS)
        self.assertEqual([tile.gives for tile in Harvest.assignments(game=self.game, city=city)], [Mountains.GIVES] * TWO_CITIZENS)

    def test_with_no_tile_that_gives_food_a_citizen_takes_a_tile_that_gives_anything(self):
        game = self.game_of(Barren)
        x, y = SETTLER_TILES[0]
        game.get_world(THE_WORLD).set_value(layer=Layer.TERRAIN, x=x + FURTHER_EAST, y=y, value=terrain_id(game=game, terrain=Mountains))
        city = self.village(game=game, civilization=FIRST_CIVILIZATION, citizens=TWO_CITIZENS)
        taken = Harvest.assignments(game=game, city=city)
        self.assertEqual(self.places(taken), [(x + FURTHER_EAST, y)])
        self.assertEqual(taken[0].gives, Mountains.GIVES)

    def test_a_citizen_with_nothing_to_collect_does_not_work_and_generates_no_currency(self):
        game = self.game_of(Barren)
        city = self.village(game=game, civilization=FIRST_CIVILIZATION, citizens=SEVERAL_CITIZENS)
        self.assertEqual(Harvest.assignments(game=game, city=city), [])
        self.assertEqual(Harvest.of_city(game=game, city=city), {Food: Village.PRODUCES[Food], Currency: NO_CURRENCY})

    def test_a_village_collects_what_its_tiles_give_what_it_produces_and_currency_for_each_working_citizen(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        for citizens in (ONE_CITIZEN, SEVERAL_CITIZENS, MANY_CITIZENS):
            with self.subTest(citizens=citizens):
                self.game.get_city(city).set_citizens(citizens)
                expected = {Food: Grassland.GIVES[Food] * citizens + Village.PRODUCES[Food], Currency: Village.CITIZEN_CURRENCY * citizens}
                self.assertEqual(Harvest.of_city(game=self.game, city=city), expected)

    def test_a_village_with_a_priority_for_stone_collects_stone(self):
        city = self.village(game=self.game, civilization=SECOND_CIVILIZATION, citizens=TWO_CITIZENS)
        self.give_priority(city=city, resource=Stone, citizens=ONE_CITIZEN)
        expected = {Stone: Mountains.GIVES[Stone], Food: Grassland.GIVES[Food] + Village.PRODUCES[Food], Currency: Village.CITIZEN_CURRENCY * TWO_CITIZENS}
        self.assertEqual(Harvest.of_city(game=self.game, city=city), expected)

    def test_a_village_with_a_priority_for_wood_collects_wood_from_the_forest(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=TWO_CITIZENS)
        x, y = FOREST_TILE
        self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y), Forest.GIVES)
        self.assertNotIn(Wood, Harvest.of_city(game=self.game, city=city))
        self.give_priority(city=city, resource=Wood, citizens=ONE_CITIZEN)
        expected = {Wood: Forest.GIVES[Wood], Food: Grassland.GIVES[Food] + Village.PRODUCES[Food], Currency: Village.CITIZEN_CURRENCY * TWO_CITIZENS}
        self.assertEqual(Harvest.of_city(game=self.game, city=city), expected)

    def test_a_granary_adds_food_to_each_worked_grassland_tile_of_its_village_and_to_no_other_terrain(self):
        city = self.village(game=self.game, civilization=SECOND_CIVILIZATION, citizens=SEVERAL_CITIZENS)
        self.give_priority(city=city, resource=Stone, citizens=ONE_CITIZEN)
        before = Harvest.of_city(game=self.game, city=city)
        give_building(game=self.game, city=city, building=Granary)
        after = Harvest.of_city(game=self.game, city=city)
        on_grassland = SEVERAL_CITIZENS - ONE_CITIZEN
        self.assertEqual(after[Food], before[Food] + Granary.WORKED_TILE_BONUS[Grassland][Food] * on_grassland)
        self.assertEqual((after[Stone], after[Currency]), (before[Stone], before[Currency]))
        x, y = MOUNTAIN_TILE
        self.assertEqual(Harvest.city_tile_gives(game=self.game, city=city, x=x, y=y), Mountains.GIVES)

    def test_a_granary_changes_what_a_tile_gives_its_village_and_not_the_tile_or_another_village(self):
        with_granary = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        without = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        give_building(game=self.game, city=with_granary, building=Granary)
        x, y = SETTLER_TILES[0][0] + JUST_PAST_CENTER, SETTLER_TILES[0][1]
        more_food = {Food: Grassland.GIVES[Food] + Granary.WORKED_TILE_BONUS[Grassland][Food]}
        self.assertEqual(Harvest.city_tile_gives(game=self.game, city=with_granary, x=x, y=y), more_food)
        self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y), Grassland.GIVES)
        self.assertEqual(Harvest.of_city(game=self.game, city=without)[Food], Grassland.GIVES[Food] + Village.PRODUCES[Food])

    def test_a_building_that_produces_something_adds_that_to_what_its_village_collects(self):
        city = self.village(game=self.game, civilization=FIRST_CIVILIZATION, citizens=ONE_CITIZEN)
        before = Harvest.of_city(game=self.game, city=city)
        give_building(game=self.game, city=city, building=ArrangementOfRocks)
        after = Harvest.of_city(game=self.game, city=city)
        self.assertEqual(after[Currency], before[Currency] + ArrangementOfRocks.PRODUCES[Currency])
        self.assertEqual(after[Food], before[Food])

    def test_a_building_can_add_a_percent_to_the_currency_of_its_village_rounded_down(self):
        game = new_caveman_game(theme=HOARD_CAVEMAN)
        city = self.village(game=game, civilization=FIRST_CIVILIZATION, citizens=SEVERAL_CITIZENS)
        plain = Harvest.of_city(game=game, city=city)
        give_building(game=game, city=city, building=Hoard)
        richer = Harvest.of_city(game=game, city=city)
        self.assertNotEqual(plain[Currency] * Hoard.INCOME_BONUS % WHOLE, 0)
        self.assertEqual(richer[Currency], plain[Currency] * (WHOLE + Hoard.INCOME_BONUS) // WHOLE)
        self.assertGreater(richer[Currency], plain[Currency])
        self.assertEqual(richer[Food], plain[Food])
