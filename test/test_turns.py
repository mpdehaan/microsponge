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

"""Tests for turns: starting a game, the turn order, and what happens when a civilization ends its turn."""

import unittest

from caveman_game import (
    CIVILIZATION_NAMES, THE_WORLD, end_rounds, found_village, give_building, held, learn, new_caveman_game, resource_id, settler_of, started_caveman_game,
)
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.game.game import FIRST_TURN, Game
from microsponge.engine.kinds.bonuses import WHOLE
from microsponge.engine.cities.production import Production
from microsponge.engine.kinds.building import Building
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import LEAST_GROWTH_TURNS, TurnControl
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.err_messages import ERR_GAME_NOT_STARTED, ERR_GAME_OVER, ERR_GAME_STARTED, ERR_NO_CIVILIZATIONS
from microsponge.themes.caveman.buildings import ArrangementOfRocks, Granary, GreatCavePainting
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.resources import Currency, Food, Stone
from microsponge.themes.caveman.technologies import Agriculture, Clubs
from microsponge.themes.caveman.terrains import Grassland
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Warrior

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
THIRD_CIVILIZATION = 3
A_THIRD_NAME = 'Thak'
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
ONE_ROUND = 1
STARTING_CURRENCY = Caveman.STARTS_WITH[Currency]
NOTHING_HELD = 0
PLENTY = 1000
ONE_CITIZEN = 1
TWO_CITIZENS = 2
SEVERAL_CITIZENS = 4
MANY_CITIZENS = Village.MAX_CITIZENS
# What a city of one citizen on grassland adds in a turn to what its civilization holds: what the city collects, less what the citizen eats.
FOOD_A_TURN = Grassland.GIVES[Food] + Village.PRODUCES[Food] - Village.CITIZEN_FOOD
CURRENCY_A_TURN = Village.CITIZEN_CURRENCY
# A row of open grassland, away from both settlers, the lake and the mountains, and the first column to put units on there.
OPEN_ROW = 2
OPEN_COLUMN = 20
MANY_WARRIORS = 10
HURT = 5
NEARLY_HEALED = Warrior.HIT_POINTS - 1
NO_POINTS = 0
A_FEW_TURNS = 3
NOT_BANKRUPT = 0
# The constant of a theme that holds what a city means there.
CITY = 'CITY'
# A tile next to the center of the first village, as how far it is east of the middle.
BESIDE_CENTER = 3
# Open grassland with room for a second village of the first civilization, as (x, y).
A_SECOND_SITE = (20, 20)
NOT_COUNTING = 0
ONE_TURN_COUNTED = 1
ONE_WARRIOR = 1
THREE_WARRIORS = 3
TWO_WARRIORS = 2


class HungryVillage(Village):
    """A city whose citizens eat more than a city of one citizen collects."""

    CITIZEN_FOOD = 5


HUNGRY_CAVEMAN = later_caveman({CITY: HungryVillage})


class Hothouse(Building):
    """A building that makes its city grow sooner by more turns than growing takes."""

    GROWS_SOONER = 100


HOTHOUSE_CAVEMAN = later_caveman({Category.BUILDINGS: (*Caveman.BUILDINGS, Hothouse)})


class TestStartingAGame(Refusals, unittest.TestCase):

    def test_a_started_game_gives_each_civilization_what_the_theme_starts_with_and_its_action_points(self):
        game = started_caveman_game()
        for civilization in (FIRST_CIVILIZATION, SECOND_CIVILIZATION):
            with self.subTest(civilization=civilization):
                self.assertEqual(held(game=game, civilization=civilization, resource=Currency), STARTING_CURRENCY)
                self.assertEqual(held(game=game, civilization=civilization, resource=Food), NOTHING_HELD)
                self.assertEqual(game.get_civilization(civilization).get_action_points(), Caveman.ACTION_POINTS)
                settler = settler_of(game=game, civilization=civilization)
                self.assertEqual(game.get_units().get_value(column=UnitColumn.ACTION_POINTS, unit=settler), Settler.ACTION_POINTS)

    def test_a_game_that_has_not_started_is_nobodys_turn_and_a_started_game_is_the_first_civilizations(self):
        game = new_caveman_game()
        self.assertEqual(game.get_playing(), NOTHING)
        self.assertEqual(self.refused(lambda: TurnControl.end_turn(game)), ERR_GAME_NOT_STARTED)
        TurnControl.start(game)
        self.assertEqual((game.get_playing(), game.get_turn()), (FIRST_CIVILIZATION, FIRST_TURN))

    def test_a_game_cannot_start_twice_or_with_no_civilization(self):
        game = started_caveman_game()
        self.assertEqual(self.refused(lambda: TurnControl.start(game)), ERR_GAME_STARTED)
        self.assertEqual(held(game=game, civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY)
        self.assertEqual(self.refused(lambda: TurnControl.start(Game(Caveman))), ERR_NO_CIVILIZATIONS)


class TestTurnOrder(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = new_caveman_game()
        self.game.add_civilization(Civilization(A_THIRD_NAME))
        TurnControl.start(self.game)

    def whose_turn(self):
        return (self.game.get_playing(), self.game.get_turn())

    def test_the_civilizations_play_in_the_order_they_joined_and_the_turn_goes_up_after_the_last(self):
        expected = [(SECOND_CIVILIZATION, FIRST_TURN), (THIRD_CIVILIZATION, FIRST_TURN), (FIRST_CIVILIZATION, FIRST_TURN + 1), (SECOND_CIVILIZATION, FIRST_TURN + 1)]
        for after in expected:
            TurnControl.end_turn(self.game)
            self.assertEqual(self.whose_turn(), after)

    def test_a_civilization_that_has_lost_is_passed_over(self):
        self.game.get_civilization(SECOND_CIVILIZATION).lose()
        self.assertEqual(self.game.get_still_playing(), [FIRST_CIVILIZATION, THIRD_CIVILIZATION])
        TurnControl.end_turn(self.game)
        self.assertEqual(self.whose_turn(), (THIRD_CIVILIZATION, FIRST_TURN))
        TurnControl.end_turn(self.game)
        self.assertEqual(self.whose_turn(), (FIRST_CIVILIZATION, FIRST_TURN + 1))

    def test_the_turn_goes_up_when_the_last_civilization_in_the_order_has_lost(self):
        self.game.get_civilization(THIRD_CIVILIZATION).lose()
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.whose_turn(), (FIRST_CIVILIZATION, FIRST_TURN + 1))

    def test_the_game_is_over_when_one_civilization_remains_and_no_turn_can_end(self):
        self.game.get_civilization(SECOND_CIVILIZATION).lose()
        self.assertFalse(self.game.is_over())
        self.game.get_civilization(FIRST_CIVILIZATION).lose()
        self.assertTrue(self.game.is_over())
        self.assertEqual(self.game.get_still_playing(), [THIRD_CIVILIZATION])
        before = self.whose_turn()
        self.assertEqual(self.refused(lambda: TurnControl.end_turn(self.game)), ERR_GAME_OVER)
        self.assertEqual(self.whose_turn(), before)

    def test_a_game_of_one_civilization_goes_on_until_that_civilization_loses(self):
        game = Game(Caveman)
        only = game.add_civilization(Civilization(CIVILIZATION_NAMES[0]))
        TurnControl.start(game)
        TurnControl.end_turn(game)
        self.assertEqual((game.get_playing(), game.get_turn(), game.is_over()), (only, FIRST_TURN + 1, False))
        game.get_civilization(only).lose()
        self.assertTrue(game.is_over())


class TestEndingATurn(unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        self.units = self.game.get_units()
        self.first = self.game.get_civilization(FIRST_CIVILIZATION)
        self.second = self.game.get_civilization(SECOND_CIVILIZATION)

    def held(self, *, civilization, resource):
        return held(game=self.game, civilization=civilization, resource=resource)

    def village(self, citizens):
        """Build the first civilization's village, give it so many citizens, and return its id."""
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.game.get_city(city).set_citizens(citizens)
        return city

    def warriors(self, *, civilization, count):
        """Put so many warriors of a civilization in a row on open grassland, and return their ids."""
        return [UnitControl.place(game=self.game, kind=Warrior, owner=civilization, world=THE_WORLD, x=OPEN_COLUMN + place, y=OPEN_ROW) for place in range(count)]

    def spend_all_currency(self, civilization):
        civilization.pay(resource=resource_id(game=self.game, resource=Currency), amount=STARTING_CURRENCY)

    def hit_points(self, unit):
        return self.units.get_value(column=UnitColumn.HIT_POINTS, unit=unit)

    def test_a_village_adds_what_it_collects_to_what_its_civilization_holds(self):
        self.village(ONE_CITIZEN)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY + CURRENCY_A_TURN)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), FOOD_A_TURN)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Stone), NOTHING_HELD)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), FOOD_A_TURN + FOOD_A_TURN)

    def test_every_village_of_a_civilization_adds_to_the_same_holdings(self):
        self.village(ONE_CITIZEN)
        x, y = A_SECOND_SITE
        second_settler = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        CityControl.found(game=self.game, settler=second_settler, name=ANOTHER_NAME)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), FOOD_A_TURN + FOOD_A_TURN)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY + CURRENCY_A_TURN + CURRENCY_A_TURN)

    def test_a_civilization_collects_only_at_the_end_of_its_own_turn(self):
        self.village(ONE_CITIZEN)
        TurnControl.end_turn(self.game)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), FOOD_A_TURN)

    def test_every_citizen_eats_food_each_turn(self):
        self.village(MANY_CITIZENS)
        self.first.add(resource=resource_id(game=self.game, resource=Food), amount=PLENTY)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        collected = Grassland.GIVES[Food] * MANY_CITIZENS + Village.PRODUCES[Food]
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), PLENTY + collected - Village.CITIZEN_FOOD * MANY_CITIZENS)
        self.assertEqual(self.held(civilization=SECOND_CIVILIZATION, resource=Food), NOTHING_HELD)

    def test_citizens_who_would_eat_more_than_there_is_eat_all_there_is_and_the_city_does_not_count_toward_growing(self):
        game = started_caveman_game(theme=HUNGRY_CAVEMAN)
        city = game.get_city(found_village(game=game, civilization=FIRST_CIVILIZATION, name=A_NAME))
        self.assertGreater(HungryVillage.CITIZEN_FOOD, Grassland.GIVES[Food] + Village.PRODUCES[Food])
        end_rounds(game=game, rounds=A_FEW_TURNS)
        self.assertEqual(held(game=game, civilization=FIRST_CIVILIZATION, resource=Food), NOTHING_HELD)
        self.assertEqual((city.get_citizens(), city.get_growth()), (ONE_CITIZEN, NOT_COUNTING))

    def test_units_are_paid_for_each_turn_in_currency_and_food_as_far_as_what_is_held_goes(self):
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=SECOND_CIVILIZATION, resource=Currency), STARTING_CURRENCY - Settler.SUPPORT[Currency])
        self.assertEqual(self.held(civilization=SECOND_CIVILIZATION, resource=Food), NOTHING_HELD)
        self.second.add(resource=resource_id(game=self.game, resource=Food), amount=PLENTY)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=SECOND_CIVILIZATION, resource=Food), PLENTY - Settler.SUPPORT[Food])

    def test_what_units_cost_to_support_adds_up_over_every_unit_of_the_civilization(self):
        self.warriors(civilization=SECOND_CIVILIZATION, count=MANY_WARRIORS)
        cost = TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)
        expected = {resource_id(game=self.game, resource=resource): amount * MANY_WARRIORS + Settler.SUPPORT[resource] for resource, amount in Warrior.SUPPORT.items()}
        self.assertEqual(cost, expected)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION), {resource_id(game=self.game, resource=resource): amount for resource, amount in Settler.SUPPORT.items()})

    def test_a_technology_takes_its_percent_off_the_support_of_units_rounded_down(self):
        self.warriors(civilization=SECOND_CIVILIZATION, count=MANY_WARRIORS)
        currency = resource_id(game=self.game, resource=Currency)
        plain = TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)[currency]
        learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=Clubs)
        cheaper = TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)[currency]
        self.assertEqual(cheaper, plain * (WHOLE - Clubs.UNIT_SUPPORT_BONUS) // WHOLE)
        self.assertLess(cheaper, plain)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], Settler.SUPPORT[Currency])

    def test_a_technology_makes_the_harvest_of_its_resource_faster_rounded_down(self):
        self.village(MANY_CITIZENS)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Agriculture)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        plain = Grassland.GIVES[Food] * MANY_CITIZENS + Village.PRODUCES[Food]
        faster = plain * (WHOLE + Agriculture.HARVEST_BONUS[Food]) // WHOLE
        self.assertGreater(faster, plain)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), faster - Village.CITIZEN_FOOD * MANY_CITIZENS)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY + Village.CITIZEN_CURRENCY * MANY_CITIZENS)

    def test_a_civilization_whose_currency_is_at_nothing_after_paying_is_bankrupt_until_it_holds_currency_again(self):
        self.spend_all_currency(self.first)
        end_rounds(game=self.game, rounds=A_FEW_TURNS)
        self.assertTrue(self.first.is_bankrupt())
        self.assertEqual(self.first.get_bankrupt_turns(), A_FEW_TURNS)
        self.assertFalse(self.second.is_bankrupt())
        self.first.add(resource=resource_id(game=self.game, resource=Currency), amount=PLENTY)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.first.get_bankrupt_turns(), NOT_BANKRUPT)
        self.assertFalse(self.first.is_bankrupt())

    def test_a_bankrupt_civilization_collects_less_of_everything(self):
        self.village(MANY_CITIZENS)
        self.spend_all_currency(self.first)
        self.first.set_bankrupt_turns(A_FEW_TURNS)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        kept = WHOLE - Caveman.BANKRUPTCY_HARVEST_PENALTY
        collected = (Grassland.GIVES[Food] * MANY_CITIZENS + Village.PRODUCES[Food]) * kept // WHOLE
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), collected - Village.CITIZEN_FOOD * MANY_CITIZENS)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), Village.CITIZEN_CURRENCY * MANY_CITIZENS * kept // WHOLE)
        self.assertFalse(self.first.is_bankrupt())

    def test_a_civilization_bankrupt_for_as_many_turns_in_a_row_as_the_theme_allows_loses_and_the_game_of_two_ends(self):
        self.spend_all_currency(self.first)
        end_rounds(game=self.game, rounds=Caveman.BANKRUPTCY_TURNS - 1)
        self.assertEqual(self.first.get_bankrupt_turns(), Caveman.BANKRUPTCY_TURNS - 1)
        self.assertFalse(self.first.has_lost())
        self.assertFalse(self.game.is_over())
        TurnControl.end_turn(self.game)
        self.assertTrue(self.first.has_lost())
        self.assertFalse(self.second.has_lost())
        self.assertEqual(self.game.get_still_playing(), [SECOND_CIVILIZATION])
        self.assertTrue(self.game.is_over())

    def test_a_village_grows_a_citizen_after_enough_turns_in_a_row_with_enough_food_and_then_counts_again(self):
        city = self.game.get_city(self.village(ONE_CITIZEN))
        self.first.add(resource=resource_id(game=self.game, resource=Food), amount=PLENTY)
        first_growth, second_growth = Village.GROWTH_TURNS
        end_rounds(game=self.game, rounds=first_growth - 1)
        self.assertEqual((city.get_citizens(), city.get_growth()), (ONE_CITIZEN, first_growth - 1))
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((city.get_citizens(), city.get_growth()), (ONE_CITIZEN + 1, NOT_COUNTING))
        end_rounds(game=self.game, rounds=second_growth - 1)
        self.assertEqual((city.get_citizens(), city.get_growth()), (ONE_CITIZEN + 1, second_growth - 1))
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((city.get_citizens(), city.get_growth()), (ONE_CITIZEN + 2, NOT_COUNTING))

    def test_each_size_of_village_needs_the_turns_the_theme_says_and_the_last_number_goes_for_every_larger_size(self):
        city = self.village(ONE_CITIZEN)
        first_growth, later_growth = Village.GROWTH_TURNS
        self.assertEqual(TurnControl.growth_turns(game=self.game, city=city), first_growth)
        for citizens in (ONE_CITIZEN + 1, SEVERAL_CITIZENS, MANY_CITIZENS - 1):
            with self.subTest(citizens=citizens):
                self.game.get_city(city).set_citizens(citizens)
                self.assertEqual(TurnControl.growth_turns(game=self.game, city=city), later_growth)

    def test_a_turn_counts_toward_growing_only_when_the_civilization_holds_enough_food_for_each_citizen(self):
        city = self.game.get_city(self.village(ONE_CITIZEN))
        self.assertLess(FOOD_A_TURN, Village.GROWTH_FOOD)
        self.assertGreaterEqual(FOOD_A_TURN + FOOD_A_TURN, Village.GROWTH_FOOD)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(city.get_growth(), NOT_COUNTING)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(city.get_growth(), ONE_TURN_COUNTED)

    def test_a_turn_without_enough_food_starts_the_count_again(self):
        city = self.game.get_city(self.village(SEVERAL_CITIZENS))
        city.set_growth(A_FEW_TURNS)
        self.assertLess(Grassland.GIVES[Food] * SEVERAL_CITIZENS + Village.PRODUCES[Food], Village.GROWTH_FOOD * SEVERAL_CITIZENS)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((city.get_citizens(), city.get_growth()), (SEVERAL_CITIZENS, NOT_COUNTING))

    def test_growing_spends_no_food(self):
        self.village(ONE_CITIZEN)
        self.first.add(resource=resource_id(game=self.game, resource=Food), amount=PLENTY)
        end_rounds(game=self.game, rounds=Village.GROWTH_TURNS[0])
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), PLENTY + FOOD_A_TURN * Village.GROWTH_TURNS[0])

    def test_a_village_of_the_most_citizens_does_not_grow_or_count(self):
        city = self.game.get_city(self.village(MANY_CITIZENS))
        self.first.add(resource=resource_id(game=self.game, resource=Food), amount=PLENTY)
        end_rounds(game=self.game, rounds=Village.GROWTH_TURNS[-1] + 1)
        self.assertEqual((city.get_citizens(), city.get_growth()), (MANY_CITIZENS, NOT_COUNTING))

    def test_a_unit_on_a_tile_heals_a_little_each_turn_and_a_unit_inside_a_village_heals_more(self):
        city = self.village(ONE_CITIZEN)
        outside, inside = self.warriors(civilization=FIRST_CIVILIZATION, count=TWO_WARRIORS)
        x, y = self.game.get_city(city).get_x(), self.game.get_city(city).get_y()
        UnitControl.move_to(game=self.game, unit=inside, x=x + BESIDE_CENTER, y=y)
        CityControl.enter(game=self.game, unit=inside, city=city)
        for unit in (outside, inside):
            self.units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=HURT)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.hit_points(outside), HURT + Warrior.HEAL)
        self.assertEqual(self.hit_points(inside), HURT + Warrior.CITY_HEAL)
        self.assertGreater(Warrior.CITY_HEAL, Warrior.HEAL)

    def test_a_unit_never_heals_past_the_hit_points_of_its_kind(self):
        city = self.village(ONE_CITIZEN)
        whole, nearly = self.warriors(civilization=FIRST_CIVILIZATION, count=TWO_WARRIORS)
        x, y = self.game.get_city(city).get_x(), self.game.get_city(city).get_y()
        UnitControl.move_to(game=self.game, unit=nearly, x=x + BESIDE_CENTER, y=y)
        CityControl.enter(game=self.game, unit=nearly, city=city)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=nearly, value=NEARLY_HEALED)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((self.hit_points(whole), self.hit_points(nearly)), (Warrior.HIT_POINTS, Warrior.HIT_POINTS))

    def test_a_unit_heals_only_at_the_end_of_its_own_civilizations_turn(self):
        warrior, = self.warriors(civilization=SECOND_CIVILIZATION, count=ONE_WARRIOR)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=warrior, value=HURT)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.hit_points(warrior), HURT)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.hit_points(warrior), HURT + Warrior.HEAL)

    def test_all_action_points_refill_at_the_end_of_a_turn_and_each_village_adds_to_its_civilizations(self):
        self.village(ONE_CITIZEN)
        warrior, = self.warriors(civilization=FIRST_CIVILIZATION, count=ONE_WARRIOR)
        self.units.set_value(column=UnitColumn.ACTION_POINTS, unit=warrior, value=NO_POINTS)
        self.first.set_action_points(NO_POINTS)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.units.get_value(column=UnitColumn.ACTION_POINTS, unit=warrior), Warrior.ACTION_POINTS)
        self.assertEqual(self.first.get_action_points(), Caveman.ACTION_POINTS + Village.ACTION_POINTS)
        self.assertEqual(self.second.get_action_points(), Caveman.ACTION_POINTS)
        self.assertEqual(TurnControl.action_points(game=self.game, civilization=FIRST_CIVILIZATION), Caveman.ACTION_POINTS + Village.ACTION_POINTS)

    def test_buildings_are_paid_for_each_turn_and_a_technology_takes_nothing_off_what_buildings_cost(self):
        city = self.village(ONE_CITIZEN)
        currency = resource_id(game=self.game, resource=Currency)
        self.warriors(civilization=FIRST_CIVILIZATION, count=MANY_WARRIORS)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Clubs)
        for_units = TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency]
        self.assertEqual(for_units, Warrior.SUPPORT[Currency] * MANY_WARRIORS * (WHOLE - Clubs.UNIT_SUPPORT_BONUS) // WHOLE)
        for building in (Granary, GreatCavePainting):
            give_building(game=self.game, city=city, building=building)
        for_buildings = Granary.SUPPORT[Currency] + GreatCavePainting.SUPPORT[Currency]
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], for_units + for_buildings)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)[currency], Settler.SUPPORT[Currency])
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY + CURRENCY_A_TURN - for_units - for_buildings)

    def test_a_civilization_with_buildings_and_no_units_pays_for_the_buildings(self):
        city = self.village(ONE_CITIZEN)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION), {})
        give_building(game=self.game, city=city, building=Granary)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION), {resource_id(game=self.game, resource=Currency): Granary.SUPPORT[Currency]})

    def test_a_granary_makes_its_village_grow_a_turn_sooner_and_no_other_village(self):
        city = self.village(ONE_CITIZEN)
        other = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        give_building(game=self.game, city=city, building=Granary)
        first_growth, later_growth = Village.GROWTH_TURNS
        sooner = first_growth - Granary.GROWS_SOONER
        self.assertEqual(TurnControl.growth_turns(game=self.game, city=city), sooner)
        self.assertEqual(TurnControl.growth_turns(game=self.game, city=other), first_growth)
        self.first.add(resource=resource_id(game=self.game, resource=Food), amount=PLENTY)
        end_rounds(game=self.game, rounds=sooner - ONE_ROUND)
        self.assertEqual(self.game.get_city(city).get_citizens(), ONE_CITIZEN)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.game.get_city(city).get_citizens(), ONE_CITIZEN + 1)
        self.assertEqual(TurnControl.growth_turns(game=self.game, city=city), later_growth - Granary.GROWS_SOONER)

    def test_growing_takes_at_least_one_turn_however_much_sooner_buildings_make_it(self):
        game = started_caveman_game(theme=HOTHOUSE_CAVEMAN)
        city = found_village(game=game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        give_building(game=game, city=city, building=Hothouse)
        self.assertGreater(Hothouse.GROWS_SOONER, max(Village.GROWTH_TURNS))
        self.assertEqual(TurnControl.growth_turns(game=game, city=city), LEAST_GROWTH_TURNS)
        game.get_civilization(FIRST_CIVILIZATION).add(resource=resource_id(game=game, resource=Food), amount=PLENTY)
        end_rounds(game=game, rounds=LEAST_GROWTH_TURNS)
        self.assertEqual(game.get_city(city).get_citizens(), ONE_CITIZEN + 1)

    def test_a_building_can_add_action_points_to_its_civilization(self):
        city = self.village(ONE_CITIZEN)
        give_building(game=self.game, city=city, building=ArrangementOfRocks)
        expected = Caveman.ACTION_POINTS + Village.ACTION_POINTS + ArrangementOfRocks.ACTION_POINTS
        self.assertEqual(TurnControl.action_points(game=self.game, civilization=FIRST_CIVILIZATION), expected)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.first.get_action_points(), expected)
        self.assertEqual(self.second.get_action_points(), Caveman.ACTION_POINTS)

    def test_units_are_paid_for_before_what_a_village_builds(self):
        city = self.village(TWO_CITIZENS)
        self.spend_all_currency(self.first)
        self.warriors(civilization=FIRST_CIVILIZATION, count=THREE_WARRIORS)
        Orders.build(game=self.game, city=city, kind=Settler)
        part = Production.part(kind=Settler, turn=FIRST_TURN)[Currency]
        income = CURRENCY_A_TURN * TWO_CITIZENS
        after_support = income - Warrior.SUPPORT[Currency] * THREE_WARRIORS
        self.assertTrue(after_support < part <= income)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertTrue(self.game.get_city(city).is_blocked())
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), after_support)
        self.assertFalse(self.first.is_bankrupt())
