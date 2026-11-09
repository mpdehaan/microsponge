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

"""Tests for the orders a civilization gives on its turn: moving, building a village, going in and out of one, priorities, war and ending the turn."""

import unittest

from caveman_game import (
    LAKE_COLUMNS, LAKE_ROWS, MOUNTAIN_TILE, SETTLER_TILES, TARPIT_TILE, THE_WORLD, WORLD_HEIGHT, WORLD_WIDTH, end_rounds, end_turn_by_order, game_facts, new_caveman_game,
    resource_id, settler_of, started_caveman_game,
)
from refusals import Refusals
from microsponge.engine.game.game import FIRST_TURN
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.city_spec import CitySpec
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_CANNOT_BE_ON, ERR_CITY_TOO_CLOSE, ERR_GAME_NOT_STARTED, ERR_GAME_OVER, ERR_NO_ACTION_POINTS, ERR_NO_CIVILIZATION_ACTION_POINTS, ERR_NO_SUCH_CIVILIZATION,
    ERR_NOT_AT_WAR, ERR_NOT_NEXT_TO_UNIT, ERR_NOT_YOUR_TURN, ERR_PRIORITY, ERR_PRIORITY_FOOD, ERR_ROW_OFF_THE_MAP, ERR_TILE_HAS_A_UNIT, ERR_TILE_IN_A_CITY_CENTER,
    ERR_UNIT_IN_A_CITY, ERR_WAR_ON_YOURSELF,
)
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.resources import Food, Stone
from microsponge.themes.caveman.terrains import Mountains, Tarpit, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import AngryBird, Settler, Warrior

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
NO_SUCH_CIVILIZATION = 9
FIRST_NAME = 'Ugg'
SECOND_NAME = 'Grok'
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
VILLAGE = Caveman.CITY.NAME
ONE_STEP = 1
TWO_STEPS = 2
ONE_ROUND = 1
NO_POINTS = 0
NO_CITIZENS = 0
STRAIGHT = Caveman.STRAIGHT_MOVE_COST_BASE
DIAGONAL = Caveman.DIAGONAL_MOVE_COST_BASE
# A row of open grassland, away from both settlers, the lake and the mountains.
OPEN_ROW = 2
OPEN_COLUMN = 20
EAST_EDGE = WORLD_WIDTH - 1
WEST_EDGE = 0
TOP_ROW = 0
BOTTOM_ROW = WORLD_HEIGHT - 1
# The grassland tile just north of the lake, and the water tile south of it, as (x, y).
SHORE_TILE = (LAKE_COLUMNS[0], LAKE_ROWS[0] - 1)
LAKE_TILE = (LAKE_COLUMNS[0], LAKE_ROWS[0])
# How far the city center and the city radius reach from the middle tile, and one tile further.
JUST_PAST_CENTER = CitySpec.CENTER_SIZE // 2 + 1
RADIUS_REACH = CitySpec.RADIUS_SIZE // 2
JUST_PAST_RADIUS = RADIUS_REACH + 1
A_FEW_CITIZENS = 2
NOT_CITIZENS = (-1, 1.5, None)


class OrdersCase(Refusals, unittest.TestCase):
    """A started game of caveman, and what the tests of orders ask of it."""

    def setUp(self):
        self.game = started_caveman_game()
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        self.first = self.game.get_civilization(FIRST_CIVILIZATION)
        self.second = self.game.get_civilization(SECOND_CIVILIZATION)
        self.settler = settler_of(game=self.game, civilization=FIRST_CIVILIZATION)
        self.other_settler = settler_of(game=self.game, civilization=SECOND_CIVILIZATION)

    def warrior(self, *, civilization, x, y):
        return UnitControl.place(game=self.game, kind=Warrior, owner=civilization, world=THE_WORLD, x=x, y=y)

    def points_of(self, unit):
        return self.units.get_value(column=UnitColumn.ACTION_POINTS, unit=unit)

    def place_of(self, unit):
        _, x, y = UnitControl.tile_of(game=self.game, unit=unit)
        return (x, y)

    def unit_at(self, *, x, y):
        return self.world.get_value(layer=Layer.UNIT, x=x, y=y)

    def refused_and_unchanged(self, action):
        """Return the message an order is refused with, having checked that the refusal changed nothing in the game."""
        before = game_facts(self.game)
        message = self.refused(action)
        self.assertEqual(game_facts(self.game), before)
        return message


class TestMoving(OrdersCase):

    def test_a_unit_moves_onto_a_tile_next_to_it_for_one_action_point_from_both_pools(self):
        x, y = SETTLER_TILES[0]
        Orders.move(game=self.game, unit=self.settler, x=x + ONE_STEP, y=y)
        self.assertEqual(self.place_of(self.settler), (x + ONE_STEP, y))
        self.assertEqual(self.unit_at(x=x + ONE_STEP, y=y), self.settler)
        self.assertEqual(self.unit_at(x=x, y=y), NOTHING)
        self.assertEqual(self.points_of(self.settler), Settler.ACTION_POINTS - STRAIGHT)
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS - STRAIGHT)
        self.assertEqual(self.second.get_action_points(), Caveman.ACTION_POINTS)

    def test_a_unit_moves_diagonally_for_the_diagonal_cost(self):
        x, y = SETTLER_TILES[0]
        Orders.move(game=self.game, unit=self.settler, x=x + ONE_STEP, y=y + ONE_STEP)
        self.assertEqual(self.place_of(self.settler), (x + ONE_STEP, y + ONE_STEP))
        Orders.move(game=self.game, unit=self.settler, x=x, y=y)
        self.assertEqual(self.place_of(self.settler), (x, y))
        self.assertEqual(self.points_of(self.settler), Settler.ACTION_POINTS - DIAGONAL - DIAGONAL)

    def test_moving_onto_mountains_costs_the_terrains_cost_and_needs_that_many_points(self):
        x, y = MOUNTAIN_TILE
        climber = self.warrior(civilization=FIRST_CIVILIZATION, x=x - ONE_STEP, y=y)
        tired = self.warrior(civilization=FIRST_CIVILIZATION, x=x - ONE_STEP, y=y + TWO_STEPS)
        Orders.move(game=self.game, unit=climber, x=x, y=y)
        self.assertEqual(self.place_of(climber), (x, y))
        self.assertEqual(self.points_of(climber), Warrior.ACTION_POINTS - STRAIGHT * Mountains.MOVE_COST)
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS - STRAIGHT * Mountains.MOVE_COST)
        Orders.move(game=self.game, unit=tired, x=x - ONE_STEP, y=y + ONE_STEP)
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=tired, x=x, y=y + ONE_STEP))
        self.assertEqual(message, ERR_NO_ACTION_POINTS.format(unit=tired, left=Warrior.ACTION_POINTS - STRAIGHT, cost=STRAIGHT * Mountains.MOVE_COST))

    def test_a_unit_moves_around_the_world_from_the_east_edge_to_the_west_edge_and_back(self):
        walker = self.warrior(civilization=FIRST_CIVILIZATION, x=EAST_EDGE, y=OPEN_ROW)
        Orders.move(game=self.game, unit=walker, x=EAST_EDGE + ONE_STEP, y=OPEN_ROW)
        self.assertEqual(self.place_of(walker), (WEST_EDGE, OPEN_ROW))
        self.assertEqual(self.unit_at(x=WEST_EDGE, y=OPEN_ROW), walker)
        Orders.move(game=self.game, unit=walker, x=EAST_EDGE, y=OPEN_ROW + ONE_STEP)
        self.assertEqual(self.place_of(walker), (EAST_EDGE, OPEN_ROW + ONE_STEP))

    def test_a_unit_cannot_move_past_the_top_or_the_bottom_of_the_world(self):
        top = self.warrior(civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=TOP_ROW)
        bottom = self.warrior(civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=BOTTOM_ROW)
        for unit, y in ((top, TOP_ROW - ONE_STEP), (bottom, BOTTOM_ROW + ONE_STEP)):
            with self.subTest(y=y):
                message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=unit, x=OPEN_COLUMN, y=y))
                self.assertEqual(message, ERR_ROW_OFF_THE_MAP.format(last=BOTTOM_ROW, value=y))

    def test_a_tile_that_is_not_next_to_the_unit_is_refused(self):
        x, y = SETTLER_TILES[0]
        for to_x, to_y in ((x + TWO_STEPS, y), (x, y - TWO_STEPS), (x, y), (x + TWO_STEPS, y + TWO_STEPS)):
            with self.subTest(to=(to_x, to_y)):
                message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.settler, x=to_x, y=to_y))
                self.assertEqual(message, ERR_NOT_NEXT_TO_UNIT.format(x=to_x, y=to_y, unit=self.settler))

    def test_a_land_unit_cannot_move_into_a_tarpit_and_an_air_unit_flies_over(self):
        x, y = TARPIT_TILE
        walker = self.warrior(civilization=FIRST_CIVILIZATION, x=x - ONE_STEP, y=y)
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=walker, x=x, y=y))
        self.assertEqual(message, ERR_CANNOT_BE_ON.format(unit=shown_name(Warrior), terrain=shown_name(Tarpit)))
        bird = UnitControl.place(game=self.game, kind=AngryBird, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + ONE_STEP, y=y)
        Orders.move(game=self.game, unit=bird, x=x, y=y)
        self.assertEqual(self.place_of(bird), (x, y))

    def test_a_land_unit_cannot_move_into_water(self):
        x, y = SHORE_TILE
        wader = self.warrior(civilization=FIRST_CIVILIZATION, x=x, y=y)
        x, y = LAKE_TILE
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=wader, x=x, y=y))
        self.assertEqual(message, ERR_CANNOT_BE_ON.format(unit=shown_name(Warrior), terrain=shown_name(Water)))

    def test_a_unit_cannot_move_onto_a_tile_that_holds_a_unit(self):
        x, y = SETTLER_TILES[0]
        self.warrior(civilization=FIRST_CIVILIZATION, x=x + ONE_STEP, y=y)
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.settler, x=x + ONE_STEP, y=y))
        self.assertEqual(message, ERR_TILE_HAS_A_UNIT.format(x=x + ONE_STEP, y=y))

    def test_a_unit_moves_only_on_the_turn_of_its_civilization(self):
        x, y = SETTLER_TILES[1]
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.other_settler, x=x + ONE_STEP, y=y))
        self.assertEqual(message, ERR_NOT_YOUR_TURN.format(name=SECOND_NAME))
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        Orders.move(game=self.game, unit=self.other_settler, x=x + ONE_STEP, y=y)
        self.assertEqual(self.place_of(self.other_settler), (x + ONE_STEP, y))

    def test_a_unit_with_no_action_points_left_cannot_move_until_its_points_refill(self):
        x, y = SETTLER_TILES[0]
        for step in range(ONE_STEP, Settler.ACTION_POINTS + ONE_STEP):
            Orders.move(game=self.game, unit=self.settler, x=x + step, y=y)
        beyond = x + Settler.ACTION_POINTS + ONE_STEP
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.settler, x=beyond, y=y))
        self.assertEqual(message, ERR_NO_ACTION_POINTS.format(unit=self.settler, left=NO_POINTS, cost=STRAIGHT))
        end_rounds(game=self.game, rounds=ONE_ROUND)
        Orders.move(game=self.game, unit=self.settler, x=beyond, y=y)
        self.assertEqual(self.place_of(self.settler), (beyond, y))

    def test_a_civilization_cannot_move_all_of_its_units_once_its_own_action_points_run_out(self):
        movers = [self.warrior(civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN + TWO_STEPS * place, y=OPEN_ROW) for place in range(Caveman.ACTION_POINTS + ONE_STEP)]
        *moved, left_behind = movers
        for unit in moved:
            x, y = self.place_of(unit)
            Orders.move(game=self.game, unit=unit, x=x, y=y + ONE_STEP)
        self.assertEqual(self.first.get_action_points(), NO_POINTS)
        x, y = self.place_of(left_behind)
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=left_behind, x=x, y=y + ONE_STEP))
        self.assertEqual(message, ERR_NO_CIVILIZATION_ACTION_POINTS.format(name=FIRST_NAME, left=NO_POINTS, cost=STRAIGHT))
        self.assertEqual(self.points_of(left_behind), Warrior.ACTION_POINTS)

    def test_no_order_is_taken_after_the_game_ends(self):
        x, y = SETTLER_TILES[0]
        self.second.lose()
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.settler, x=x + ONE_STEP, y=y))
        self.assertEqual(message, ERR_GAME_OVER)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.end_turn(game=self.game, civilization=FIRST_CIVILIZATION)), ERR_GAME_OVER)

    def test_no_order_is_taken_before_the_game_starts(self):
        game = new_caveman_game()
        x, y = SETTLER_TILES[0]
        settler = settler_of(game=game, civilization=FIRST_CIVILIZATION)
        self.assertEqual(self.refused(lambda: Orders.move(game=game, unit=settler, x=x + ONE_STEP, y=y)), ERR_GAME_NOT_STARTED)
        self.assertEqual(self.refused(lambda: Orders.end_turn(game=game, civilization=FIRST_CIVILIZATION)), ERR_GAME_NOT_STARTED)
        self.assertEqual(game.get_world(THE_WORLD).get_value(layer=Layer.UNIT, x=x, y=y), settler)


class TestVillageOrders(OrdersCase):

    def test_building_a_village_costs_the_civilization_an_action_point_and_the_settler_is_gone(self):
        city = Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        self.assertEqual(self.game.get_city(city).get_name(), A_NAME)
        self.assertEqual(self.game.get_cities_of(FIRST_CIVILIZATION), [city])
        self.assertEqual(self.game.get_cities_of(SECOND_CIVILIZATION), [])
        self.assertFalse(self.units.exists(self.settler))
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS - Caveman.ACTION_COST_BASE)

    def test_a_village_is_built_only_on_the_turn_of_the_settlers_civilization(self):
        message = self.refused_and_unchanged(lambda: Orders.found_city(game=self.game, settler=self.other_settler, name=ANOTHER_NAME))
        self.assertEqual(message, ERR_NOT_YOUR_TURN.format(name=SECOND_NAME))

    def test_a_village_that_cannot_be_built_costs_nothing(self):
        Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        late = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + JUST_PAST_RADIUS, y=y)
        message = self.refused_and_unchanged(lambda: Orders.found_city(game=self.game, settler=late, name=ANOTHER_NAME))
        self.assertEqual(message, ERR_CITY_TOO_CLOSE.format(city=VILLAGE, name=A_NAME))

    def test_a_settler_with_no_action_points_left_cannot_build_a_village(self):
        x, y = SETTLER_TILES[0]
        for step in range(ONE_STEP, Settler.ACTION_POINTS + ONE_STEP):
            Orders.move(game=self.game, unit=self.settler, x=x + step, y=y)
        message = self.refused_and_unchanged(lambda: Orders.found_city(game=self.game, settler=self.settler, name=A_NAME))
        self.assertEqual(message, ERR_NO_ACTION_POINTS.format(unit=self.settler, left=NO_POINTS, cost=Caveman.ACTION_COST_BASE))

    def test_going_into_a_village_and_coming_out_each_cost_an_action_point_from_both_pools(self):
        city = Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        guard = self.warrior(civilization=FIRST_CIVILIZATION, x=x + JUST_PAST_CENTER, y=y)
        pool = self.first.get_action_points()
        Orders.enter_city(game=self.game, unit=guard, city=city)
        self.assertEqual(self.game.get_city(city).get_units(), [guard])
        self.assertEqual((self.points_of(guard), self.first.get_action_points()), (Warrior.ACTION_POINTS - STRAIGHT, pool - STRAIGHT))
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=guard, x=x + ONE_STEP, y=y))
        self.assertEqual(message, ERR_UNIT_IN_A_CITY.format(unit=guard, city=VILLAGE))
        Orders.leave_city(game=self.game, unit=guard, x=x + JUST_PAST_CENTER, y=y + ONE_STEP)
        self.assertEqual(self.game.get_city(city).get_units(), [])
        self.assertEqual(self.place_of(guard), (x + JUST_PAST_CENTER, y + ONE_STEP))
        self.assertEqual((self.points_of(guard), self.first.get_action_points()), (Warrior.ACTION_POINTS - STRAIGHT - STRAIGHT, pool - STRAIGHT - STRAIGHT))
        message = self.refused_and_unchanged(lambda: Orders.enter_city(game=self.game, unit=guard, city=city))
        self.assertEqual(message, ERR_NO_ACTION_POINTS.format(unit=guard, left=NO_POINTS, cost=STRAIGHT))

    def test_a_unit_walks_up_to_a_village_center_but_not_onto_it(self):
        Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        guard = self.warrior(civilization=FIRST_CIVILIZATION, x=x + JUST_PAST_CENTER, y=y)
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=guard, x=x + JUST_PAST_CENTER - ONE_STEP, y=y))
        self.assertEqual(message, ERR_TILE_IN_A_CITY_CENTER.format(city=VILLAGE, x=x + JUST_PAST_CENTER - ONE_STEP, y=y))

    def test_a_village_is_told_how_many_citizens_look_for_a_resource_first_for_no_action_points(self):
        city = Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        pool = self.first.get_action_points()
        stone = resource_id(game=self.game, resource=Stone)
        Orders.prioritize(game=self.game, city=city, resource=Stone, citizens=A_FEW_CITIZENS)
        self.assertEqual(self.game.get_city(city).get_priorities(), {stone: A_FEW_CITIZENS})
        self.assertEqual(self.first.get_action_points(), pool)
        Orders.prioritize(game=self.game, city=city, resource=Stone, citizens=NO_CITIZENS)
        self.assertEqual(self.game.get_city(city).get_priorities(), {})

    def test_a_priority_for_food_or_for_a_number_that_counts_nothing_or_on_another_turn_is_refused(self):
        city = Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        message = self.refused_and_unchanged(lambda: Orders.prioritize(game=self.game, city=city, resource=Food, citizens=A_FEW_CITIZENS))
        self.assertEqual(message, ERR_PRIORITY_FOOD.format(resource=shown_name(Food)))
        for citizens in NOT_CITIZENS:
            with self.subTest(citizens=citizens):
                message = self.refused_and_unchanged(lambda: Orders.prioritize(game=self.game, city=city, resource=Stone, citizens=citizens))
                self.assertEqual(message, ERR_PRIORITY.format(value=citizens))
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        message = self.refused_and_unchanged(lambda: Orders.prioritize(game=self.game, city=city, resource=Stone, citizens=A_FEW_CITIZENS))
        self.assertEqual(message, ERR_NOT_YOUR_TURN.format(name=FIRST_NAME))


class TestWarAndTerritory(OrdersCase):

    def setUp(self):
        super().setUp()
        self.village = Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        # The second civilization's warrior stands just outside the first village's radius, to the east.
        self.border = (x + RADIUS_REACH, y)
        self.raider = self.warrior(civilization=SECOND_CIVILIZATION, x=x + JUST_PAST_RADIUS, y=y)
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)

    def test_a_unit_cannot_enter_the_radius_of_another_civilizations_village_without_a_war(self):
        x, y = self.border
        message = self.refused_and_unchanged(lambda: Orders.move(game=self.game, unit=self.raider, x=x, y=y))
        self.assertEqual(message, ERR_NOT_AT_WAR.format(name=FIRST_NAME))

    def test_declaring_war_puts_both_civilizations_at_war_and_lets_units_cross_the_border(self):
        x, y = self.border
        pool = self.second.get_action_points()
        Orders.declare_war(game=self.game, civilization=SECOND_CIVILIZATION, on=FIRST_CIVILIZATION)
        self.assertTrue(self.second.is_at_war_with(FIRST_CIVILIZATION))
        self.assertTrue(self.first.is_at_war_with(SECOND_CIVILIZATION))
        self.assertEqual(self.second.get_action_points(), pool)
        Orders.move(game=self.game, unit=self.raider, x=x, y=y)
        self.assertEqual(self.place_of(self.raider), (x, y))

    def test_a_civilizations_own_units_walk_its_own_radius_without_a_war(self):
        x, y = self.border
        end_turn_by_order(game=self.game, civilization=SECOND_CIVILIZATION)
        guard = self.warrior(civilization=FIRST_CIVILIZATION, x=x, y=y + ONE_STEP)
        Orders.move(game=self.game, unit=guard, x=x - ONE_STEP, y=y + ONE_STEP)
        self.assertEqual(self.place_of(guard), (x - ONE_STEP, y + ONE_STEP))

    def test_war_is_declared_only_on_the_turn_of_the_one_declaring_and_on_another_civilization_of_the_game(self):
        message = self.refused_and_unchanged(lambda: Orders.declare_war(game=self.game, civilization=FIRST_CIVILIZATION, on=SECOND_CIVILIZATION))
        self.assertEqual(message, ERR_NOT_YOUR_TURN.format(name=FIRST_NAME))
        message = self.refused_and_unchanged(lambda: Orders.declare_war(game=self.game, civilization=SECOND_CIVILIZATION, on=SECOND_CIVILIZATION))
        self.assertEqual(message, ERR_WAR_ON_YOURSELF)
        message = self.refused_and_unchanged(lambda: Orders.declare_war(game=self.game, civilization=SECOND_CIVILIZATION, on=NO_SUCH_CIVILIZATION))
        self.assertEqual(message, ERR_NO_SUCH_CIVILIZATION.format(civilization=NO_SUCH_CIVILIZATION))


class TestEndingTheTurn(OrdersCase):

    def test_a_civilization_ends_its_own_turn_and_no_other(self):
        message = self.refused_and_unchanged(lambda: Orders.end_turn(game=self.game, civilization=SECOND_CIVILIZATION))
        self.assertEqual(message, ERR_NOT_YOUR_TURN.format(name=SECOND_NAME))
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        self.assertEqual((self.game.get_playing(), self.game.get_turn()), (SECOND_CIVILIZATION, FIRST_TURN))
        end_turn_by_order(game=self.game, civilization=SECOND_CIVILIZATION)
        self.assertEqual((self.game.get_playing(), self.game.get_turn()), (FIRST_CIVILIZATION, FIRST_TURN + ONE_ROUND))

    def test_a_village_built_this_turn_adds_its_action_points_from_the_next_turn(self):
        Orders.found_city(game=self.game, settler=self.settler, name=A_NAME)
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS - Caveman.ACTION_COST_BASE)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS + Village.ACTION_POINTS)
