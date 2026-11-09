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

"""Tests for a worker building an improvement: who can, where, how long it takes, and abandoning it."""

import unittest

from caveman_game import FOREST_TILE, GRASSLAND_TILE, MOUNTAIN_TILE, SETTLER_TILES, TARPIT_TILE, THE_WORLD, end_rounds, end_turn_by_order, found_village, game_facts, learn, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.city_spec import CitySpec
from microsponge.engine.kinds.improvement import Improvement
from microsponge.engine.kinds.unit_kinds import AirUnit
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.units.work_control import WorkControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_CANNOT_BUILD_IMPROVEMENT, ERR_IMPROVEMENT_NOT_ON, ERR_IMPROVEMENT_REQUIRES, ERR_NO_ACTION_POINTS, ERR_NOT_YOUR_TURN, ERR_TILE_IMPROVED, ERR_UNIT_IN_A_CITY,
    ERR_UNIT_NOT_WORKING, ERR_UNIT_WORKING,
)
from microsponge.themes.caveman.improvements import Clearing, Farm
from microsponge.themes.caveman.resources import Food
from microsponge.themes.caveman.technologies import Agriculture, Clubs
from microsponge.themes.caveman.terrains import Forest, Grassland, Mountains, Tarpit
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import CavemanUnit, Warrior, Worker

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
FIRST_NAME = 'Ugg'
SECOND_NAME = 'Grok'
A_NAME = 'Ugghome'
VILLAGE = Caveman.CITY.NAME
ONE_STEP = 1
ONE_ROUND = 1
NO_POINTS = 0
NO_TURNS = 0
JUST_PAST_CENTER = CitySpec.CENTER_SIZE // 2 + 1


class Boardwalk(Improvement):
    """An improvement that a theme lists for a terrain nothing can be built on, and for forest."""

    ON = (Tarpit, Forest)


class Buzzard(CavemanUnit, AirUnit):
    """An air unit that builds, so that a unit can stand on a tarpit and try."""

    BUILDS = (Boardwalk,)


BOARDWALK_CAVEMAN = later_caveman({Category.UNITS: (*Caveman.UNITS, Buzzard), Category.IMPROVEMENTS: (*Caveman.IMPROVEMENTS, Boardwalk)})


class TestBuildingAnImprovement(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        self.first = self.game.get_civilization(FIRST_CIVILIZATION)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Agriculture)
        self.field = GRASSLAND_TILE
        x, y = self.field
        self.worker = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)

    def improvement_at(self, tile):
        """Return the improvement on a tile, as the theme's class, or None."""
        x, y = tile
        improvement = self.world.get_value(layer=Layer.IMPROVEMENT, x=x, y=y)
        return None if improvement == NOTHING else self.game.get_catalog().get_kind(category=Category.IMPROVEMENTS, kind_id=improvement)

    def points_of(self, unit):
        return self.units.get_value(column=UnitColumn.ACTION_POINTS, unit=unit)

    def refused_and_unchanged(self, action):
        """Return the message an order is refused with, having checked that the refusal changed nothing in the game."""
        before = game_facts(self.game)
        message = self.refused(action)
        self.assertEqual(game_facts(self.game), before)
        return message

    def start_farm(self):
        Orders.build_improvement(game=self.game, unit=self.worker, improvement=Farm)

    def test_a_worker_starts_a_farm_for_an_action_point_from_both_pools_and_the_farm_is_not_there_yet(self):
        self.assertIsNone(WorkControl.problem_starting(game=self.game, unit=self.worker, improvement=Farm))
        self.assertIsNone(WorkControl.improvement_of(game=self.game, unit=self.worker))
        self.start_farm()
        self.assertIs(WorkControl.improvement_of(game=self.game, unit=self.worker), Farm)
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=self.worker), Farm.BUILD_TURNS)
        self.assertIsNone(self.improvement_at(self.field))
        self.assertEqual(self.points_of(self.worker), Worker.ACTION_POINTS - Caveman.ACTION_COST_BASE)
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS - Caveman.ACTION_COST_BASE)

    def test_the_farm_is_on_the_tile_after_the_turns_a_farm_takes_and_not_a_turn_sooner(self):
        self.start_farm()
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS - ONE_ROUND)
        self.assertIsNone(self.improvement_at(self.field))
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=self.worker), ONE_ROUND)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertIs(self.improvement_at(self.field), Farm)
        self.assertIsNone(WorkControl.improvement_of(game=self.game, unit=self.worker))
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=self.worker), NO_TURNS)

    def test_a_finished_farm_makes_its_tile_give_more_food(self):
        x, y = self.field
        self.start_farm()
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS)
        self.assertEqual(Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y), {Food: Grassland.GIVES[Food] + Farm.TILE_BONUS[Food]})

    def test_a_unit_that_is_building_cannot_move_until_the_improvement_is_done(self):
        x, y = self.field
        self.start_farm()
        expected = ERR_UNIT_WORKING.format(unit=self.worker, improvement=shown_name(Farm))
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.worker, x=x + ONE_STEP, y=y)), expected)
        self.assertEqual(self.refused_and_unchanged(self.start_farm), expected)
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS - ONE_ROUND)
        Orders.move(game=self.game, unit=self.worker, x=x + ONE_STEP, y=y)
        self.assertEqual(UnitControl.tile_of(game=self.game, unit=self.worker), (THE_WORLD, x + ONE_STEP, y))
        self.assertIs(self.improvement_at(self.field), Farm)

    def test_abandoning_frees_the_unit_for_no_action_points_and_nothing_comes_of_the_turns_spent(self):
        x, y = self.field
        self.start_farm()
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS - ONE_ROUND)
        pool = self.first.get_action_points()
        Orders.abandon_improvement(game=self.game, unit=self.worker)
        self.assertEqual((self.first.get_action_points(), self.points_of(self.worker)), (pool, Worker.ACTION_POINTS))
        self.assertIsNone(WorkControl.improvement_of(game=self.game, unit=self.worker))
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertIsNone(self.improvement_at(self.field))
        self.start_farm()
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=self.worker), Farm.BUILD_TURNS)
        Orders.abandon_improvement(game=self.game, unit=self.worker)
        Orders.move(game=self.game, unit=self.worker, x=x + ONE_STEP, y=y)
        self.assertEqual(UnitControl.tile_of(game=self.game, unit=self.worker), (THE_WORLD, x + ONE_STEP, y))

    def test_a_unit_that_is_building_nothing_has_nothing_to_abandon(self):
        message = self.refused_and_unchanged(lambda: Orders.abandon_improvement(game=self.game, unit=self.worker))
        self.assertEqual(message, ERR_UNIT_NOT_WORKING.format(unit=self.worker))

    def test_a_farm_requires_agriculture_and_clubs_alone_are_not_enough(self):
        x, y = SETTLER_TILES[1]
        learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=Clubs)
        other = UnitControl.place(game=self.game, kind=Worker, owner=SECOND_CIVILIZATION, world=THE_WORLD, x=x + ONE_STEP, y=y)
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        expected = ERR_IMPROVEMENT_REQUIRES.format(improvement=shown_name(Farm), required=shown_name(Agriculture))
        self.assertEqual(WorkControl.problem_starting(game=self.game, unit=other, improvement=Farm), expected)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.build_improvement(game=self.game, unit=other, improvement=Farm)), expected)
        learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=Agriculture)
        Orders.build_improvement(game=self.game, unit=other, improvement=Farm)
        self.assertIs(WorkControl.improvement_of(game=self.game, unit=other), Farm)

    def test_a_warrior_cannot_build_a_farm(self):
        x, y = self.field
        warrior = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + ONE_STEP, y=y)
        message = self.refused_and_unchanged(lambda: Orders.build_improvement(game=self.game, unit=warrior, improvement=Farm))
        self.assertEqual(message, ERR_CANNOT_BUILD_IMPROVEMENT.format(unit=shown_name(Warrior), improvement=shown_name(Farm)))

    def test_a_farm_goes_on_grassland_and_not_on_mountains(self):
        x, y = MOUNTAIN_TILE
        climber = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        message = self.refused_and_unchanged(lambda: Orders.build_improvement(game=self.game, unit=climber, improvement=Farm))
        self.assertEqual(message, ERR_IMPROVEMENT_NOT_ON.format(improvement=shown_name(Farm), terrain=shown_name(Mountains)))

    def test_a_tile_that_has_a_farm_gets_no_second_one(self):
        x, y = self.field
        self.start_farm()
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS)
        message = self.refused_and_unchanged(self.start_farm)
        self.assertEqual(message, ERR_TILE_IMPROVED.format(x=x, y=y, improvement=shown_name(Farm)))

    def test_a_unit_inside_a_village_cannot_build_and_a_building_unit_cannot_go_inside(self):
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        x, y = SETTLER_TILES[0]
        inside = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + JUST_PAST_CENTER, y=y)
        builder = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x - JUST_PAST_CENTER, y=y)
        CityControl.enter(game=self.game, unit=inside, city=city)
        message = self.refused_and_unchanged(lambda: Orders.build_improvement(game=self.game, unit=inside, improvement=Farm))
        self.assertEqual(message, ERR_UNIT_IN_A_CITY.format(unit=inside, city=VILLAGE))
        Orders.build_improvement(game=self.game, unit=builder, improvement=Farm)
        message = self.refused_and_unchanged(lambda: Orders.enter_city(game=self.game, unit=builder, city=city))
        self.assertEqual(message, ERR_UNIT_WORKING.format(unit=builder, improvement=shown_name(Farm)))

    def test_building_is_ordered_and_abandoned_only_on_the_turn_of_the_units_civilization(self):
        self.start_farm()
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        expected = ERR_NOT_YOUR_TURN.format(name=FIRST_NAME)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.abandon_improvement(game=self.game, unit=self.worker)), expected)
        self.assertEqual(self.refused_and_unchanged(self.start_farm), expected)

    def test_a_unit_with_no_action_points_left_cannot_start_building(self):
        x, y = self.field
        for step in range(ONE_STEP, Worker.ACTION_POINTS + ONE_STEP):
            Orders.move(game=self.game, unit=self.worker, x=x + step, y=y)
        message = self.refused_and_unchanged(self.start_farm)
        self.assertEqual(message, ERR_NO_ACTION_POINTS.format(unit=self.worker, left=NO_POINTS, cost=Caveman.ACTION_COST_BASE))

    def test_only_the_units_of_the_civilization_ending_its_turn_go_on_building(self):
        x, y = SETTLER_TILES[1]
        learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=Agriculture)
        other = UnitControl.place(game=self.game, kind=Worker, owner=SECOND_CIVILIZATION, world=THE_WORLD, x=x + ONE_STEP, y=y)
        self.start_farm()
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        Orders.build_improvement(game=self.game, unit=other, improvement=Farm)
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=self.worker), Farm.BUILD_TURNS - ONE_ROUND)
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=other), Farm.BUILD_TURNS)
        end_turn_by_order(game=self.game, civilization=SECOND_CIVILIZATION)
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=self.worker), Farm.BUILD_TURNS - ONE_ROUND)
        self.assertEqual(WorkControl.turns_left(game=self.game, unit=other), Farm.BUILD_TURNS - ONE_ROUND)


class TestChangingTheTerrain(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game(theme=BOARDWALK_CAVEMAN)
        self.world = self.game.get_world(THE_WORLD)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Agriculture)
        self.woods = FOREST_TILE
        x, y = self.woods
        self.worker = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)

    def terrain_at(self, tile):
        x, y = tile
        return self.game.get_terrain(world=THE_WORLD, x=x, y=y)

    def improved(self, tile):
        """Return whether a tile has an improvement on it."""
        x, y = tile
        return self.world.get_value(layer=Layer.IMPROVEMENT, x=x, y=y) != NOTHING

    def gives(self, tile):
        x, y = tile
        return Harvest.tile_gives(game=self.game, world=THE_WORLD, x=x, y=y)

    def clear(self):
        Orders.build_improvement(game=self.game, unit=self.worker, improvement=Clearing)

    def test_a_worker_cuts_the_trees_of_a_forest_tile_which_is_grassland_after_the_turns_that_takes(self):
        self.clear()
        end_rounds(game=self.game, rounds=Clearing.BUILD_TURNS - ONE_ROUND)
        self.assertIs(self.terrain_at(self.woods), Forest)
        self.assertEqual(self.gives(self.woods), Forest.GIVES)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertIs(self.terrain_at(self.woods), Grassland)
        self.assertEqual(self.gives(self.woods), Grassland.GIVES)
        self.assertFalse(self.improved(self.woods))
        self.assertIsNone(WorkControl.improvement_of(game=self.game, unit=self.worker))

    def test_the_trees_next_to_the_tile_stay(self):
        x, y = self.woods
        self.clear()
        end_rounds(game=self.game, rounds=Clearing.BUILD_TURNS)
        self.assertIs(self.terrain_at((x, y + ONE_STEP)), Forest)
        self.assertIs(self.terrain_at((x, y - ONE_STEP)), Forest)

    def test_a_farm_goes_on_the_tile_once_the_trees_are_cut_and_not_before(self):
        expected = ERR_IMPROVEMENT_NOT_ON.format(improvement=shown_name(Farm), terrain=shown_name(Forest))
        self.assertEqual(WorkControl.problem_starting(game=self.game, unit=self.worker, improvement=Farm), expected)
        self.clear()
        end_rounds(game=self.game, rounds=Clearing.BUILD_TURNS)
        Orders.build_improvement(game=self.game, unit=self.worker, improvement=Farm)
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS)
        self.assertTrue(self.improved(self.woods))
        self.assertEqual(self.gives(self.woods)[Food], Grassland.GIVES[Food] + Farm.TILE_BONUS[Food])

    def test_trees_are_cut_only_where_there_is_forest(self):
        x, y = GRASSLAND_TILE
        other = UnitControl.place(game=self.game, kind=Worker, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        expected = ERR_IMPROVEMENT_NOT_ON.format(improvement=shown_name(Clearing), terrain=shown_name(Grassland))
        self.assertEqual(self.refused(lambda: Orders.build_improvement(game=self.game, unit=other, improvement=Clearing)), expected)

    def test_abandoning_the_cutting_leaves_the_forest(self):
        self.clear()
        end_rounds(game=self.game, rounds=Clearing.BUILD_TURNS - ONE_ROUND)
        Orders.abandon_improvement(game=self.game, unit=self.worker)
        end_rounds(game=self.game, rounds=Clearing.BUILD_TURNS)
        self.assertIs(self.terrain_at(self.woods), Forest)

    def test_nothing_is_built_on_a_tarpit_even_by_a_unit_that_can_be_there_with_an_improvement_listed_for_it(self):
        x, y = TARPIT_TILE
        buzzard = UnitControl.place(game=self.game, kind=Buzzard, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        expected = ERR_IMPROVEMENT_NOT_ON.format(improvement=shown_name(Boardwalk), terrain=shown_name(Tarpit))
        self.assertEqual(self.refused(lambda: Orders.build_improvement(game=self.game, unit=buzzard, improvement=Boardwalk)), expected)
        self.assertIs(self.terrain_at(TARPIT_TILE), Tarpit)

    def test_the_same_unit_builds_the_same_improvement_on_forest(self):
        x, y = self.woods
        buzzard = UnitControl.place(game=self.game, kind=Buzzard, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y + ONE_STEP)
        Orders.build_improvement(game=self.game, unit=buzzard, improvement=Boardwalk)
        end_rounds(game=self.game, rounds=Boardwalk.BUILD_TURNS)
        self.assertTrue(self.improved((x, y + ONE_STEP)))
        self.assertIs(self.terrain_at((x, y + ONE_STEP)), Forest)
