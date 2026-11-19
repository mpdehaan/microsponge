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
    CIVILIZATION_NAMES, SETTLER_TILES, THE_WORLD, end_rounds, found_village, give_building, held, learn, new_caveman_game, resource_id, settler_of, started_caveman_game,
)
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.kinds.control_points import Policy, points_given
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.game.game import FIRST_TURN, Game
from microsponge.engine.kinds.bonuses import WHOLE
from microsponge.engine.cities.production import Production
from microsponge.engine.kinds.building import Building
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import LEAST_STORE_FOOD, TurnControl
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.err_messages import ERR_GAME_NOT_STARTED, ERR_GAME_OVER, ERR_GAME_STARTED, ERR_NO_CIVILIZATIONS
from microsponge.themes.caveman.buildings import ArrangementOfRocks, Granary, GreatCavePainting
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.resources import Currency, Food, Stone
from microsponge.themes.caveman.technologies import Agriculture, Clubs
from microsponge.themes.caveman.terrains import Grassland
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Clubber

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
MANY_CLUBBERS = 10
NOTHING_LEFT = 0
# What a test says when the theme's numbers allow no village it needs.
NO_SUCH_VILLAGE = 'the theme allows no village whose income pays its clubbers with too little left for a part of a build'
HURT = 5
NEARLY_HEALED = Clubber.HIT_POINTS - 1
NO_POINTS = 0
A_FEW_TURNS = 3
NOT_BANKRUPT = 0
# The constant of a theme that holds what a city means there.
CITY = 'CITY'
# A tile next to the center of the first village, as how far it is east of the middle.
BESIDE_CENTER = 3
# Open grassland with room for a second village of the first civilization, as (x, y).
A_SECOND_SITE = (20, 20)
ONE_CLUBBER = 1
TWO_CLUBBERS = 2



def citizens_and_clubbers(part):
    """Return (citizens, clubbers): the fewest citizens of a village, beyond the one a settler uses, and a number of clubbers, such that the village's income pays the clubbers' upkeep with something left, but too little for a part of a build, while the income alone would pay the part. Read from the theme's numbers."""
    support = Clubber.SUPPORT[Currency]
    for citizens in range(TWO_CITIZENS, MANY_CITIZENS + 1):
        income = CURRENCY_A_TURN * citizens
        for count in range(1, MANY_CLUBBERS):
            if NOTHING_LEFT < income - support * count < part <= income:
                return (citizens, count)
    raise AssertionError(NO_SUCH_VILLAGE)

class HungryVillage(Village):
    """A city whose citizens eat more than a city of one citizen collects."""

    CITIZEN_FOOD = 5


HUNGRY_CAVEMAN = later_caveman({CITY: HungryVillage})


class Hothouse(Building):
    """A building that takes more food off each citizen's share of a full store than the share is."""

    GROWS_SOONER = 100


HOTHOUSE_CAVEMAN = later_caveman({Category.BUILDINGS: (*Caveman.BUILDINGS, Hothouse)})


class TestStartingAGame(Refusals, unittest.TestCase):

    def test_a_started_game_gives_each_civilization_what_the_theme_starts_with_and_its_policy_points(self):
        game = started_caveman_game()
        for civilization in (FIRST_CIVILIZATION, SECOND_CIVILIZATION):
            with self.subTest(civilization=civilization):
                self.assertEqual(held(game=game, civilization=civilization, resource=Currency), STARTING_CURRENCY)
                self.assertEqual(held(game=game, civilization=civilization, resource=Food), NOTHING_HELD)
                self.assertEqual(game.get_civilization(civilization).get_policy_points(), points_given(by=Caveman, points=Policy))
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

    def stored(self, city):
        """Return the food a village has stored."""
        return self.game.get_city(city).get_food()

    def village(self, citizens):
        """Build the first civilization's village, give it so many citizens, and return its id."""
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.game.get_city(city).set_citizens(citizens)
        return city

    def clubbers(self, *, civilization, count):
        """Put so many clubbers of a civilization in a row on open grassland, and return their ids."""
        return [UnitControl.place(game=self.game, kind=Clubber, owner=civilization, world=THE_WORLD, x=OPEN_COLUMN + place, y=OPEN_ROW) for place in range(count)]

    def spend_all_currency(self, civilization):
        civilization.pay(resource=resource_id(game=self.game, resource=Currency), amount=STARTING_CURRENCY)

    def hit_points(self, unit):
        return self.units.get_value(column=UnitColumn.HIT_POINTS, unit=unit)

    def test_a_village_adds_its_currency_to_what_its_civilization_holds_and_its_food_to_its_own_store(self):
        city = self.village(ONE_CITIZEN)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY + CURRENCY_A_TURN)
        self.assertEqual(self.stored(city), FOOD_A_TURN)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), NOTHING_HELD)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Stone), NOTHING_HELD)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.stored(city), FOOD_A_TURN + FOOD_A_TURN)

    def test_every_village_of_a_civilization_adds_its_currency_to_the_same_holdings_and_keeps_its_own_food(self):
        city = self.village(ONE_CITIZEN)
        x, y = A_SECOND_SITE
        second_settler = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        other = CityControl.found(game=self.game, settler=second_settler, name=ANOTHER_NAME)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), STARTING_CURRENCY + CURRENCY_A_TURN + CURRENCY_A_TURN)
        self.assertEqual((self.stored(city), self.stored(other)), (FOOD_A_TURN, FOOD_A_TURN))

    def test_a_civilization_collects_only_at_the_end_of_its_own_turn(self):
        city = self.village(ONE_CITIZEN)
        TurnControl.end_turn(self.game)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.stored(city), FOOD_A_TURN)

    def test_every_citizen_eats_from_the_store_of_its_own_village_each_turn(self):
        city = self.village(MANY_CITIZENS)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        collected = Grassland.GIVES[Food] * MANY_CITIZENS + Village.PRODUCES[Food]
        self.assertEqual(self.stored(city), collected - Village.CITIZEN_FOOD * MANY_CITIZENS)

    def test_a_village_whose_store_cannot_feed_its_citizens_loses_a_citizen_but_never_its_last_and_its_store_is_empty(self):
        game = started_caveman_game(theme=HUNGRY_CAVEMAN)
        city = game.get_city(found_village(game=game, civilization=FIRST_CIVILIZATION, name=A_NAME))
        city.set_citizens(SEVERAL_CITIZENS)
        self.assertGreater(HungryVillage.CITIZEN_FOOD, Grassland.GIVES[Food] + Village.PRODUCES[Food])
        end_rounds(game=game, rounds=ONE_ROUND)
        self.assertEqual((city.get_citizens(), city.get_food()), (SEVERAL_CITIZENS - 1, NOTHING_HELD))
        end_rounds(game=game, rounds=SEVERAL_CITIZENS)
        self.assertEqual((city.get_citizens(), city.get_food()), (ONE_CITIZEN, NOTHING_HELD))

    def test_units_are_paid_for_each_turn_with_what_their_kind_costs_to_support(self):
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=SECOND_CIVILIZATION, resource=Currency), STARTING_CURRENCY - Settler.SUPPORT[Currency])

    def test_what_units_cost_to_support_adds_up_over_every_unit_of_the_civilization(self):
        self.clubbers(civilization=SECOND_CIVILIZATION, count=MANY_CLUBBERS)
        cost = TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)
        expected = {resource_id(game=self.game, resource=resource): amount * MANY_CLUBBERS + Settler.SUPPORT[resource] for resource, amount in Clubber.SUPPORT.items()}
        self.assertEqual(cost, expected)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION), {resource_id(game=self.game, resource=resource): amount for resource, amount in Settler.SUPPORT.items()})

    def test_a_technology_takes_its_percent_off_the_support_of_units_rounded_down(self):
        self.clubbers(civilization=SECOND_CIVILIZATION, count=MANY_CLUBBERS)
        currency = resource_id(game=self.game, resource=Currency)
        plain = TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)[currency]
        learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=Clubs)
        cheaper = TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)[currency]
        self.assertEqual(cheaper, plain * (WHOLE - Clubs.UNIT_SUPPORT_BONUS) // WHOLE)
        self.assertLess(cheaper, plain)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], Settler.SUPPORT[Currency])

    def test_a_technology_makes_the_harvest_of_its_resource_faster_rounded_down(self):
        city = self.village(MANY_CITIZENS)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Agriculture)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        plain = Grassland.GIVES[Food] * MANY_CITIZENS + Village.PRODUCES[Food]
        faster = plain * (WHOLE + Agriculture.HARVEST_BONUS[Food]) // WHOLE
        self.assertGreater(faster, plain)
        self.assertEqual(self.stored(city), faster - Village.CITIZEN_FOOD * MANY_CITIZENS)
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
        city = self.village(MANY_CITIZENS)
        self.spend_all_currency(self.first)
        self.first.set_bankrupt_turns(A_FEW_TURNS)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        kept = WHOLE - Caveman.BANKRUPTCY_HARVEST_PENALTY
        collected = (Grassland.GIVES[Food] * MANY_CITIZENS + Village.PRODUCES[Food]) * kept // WHOLE
        self.assertEqual(self.stored(city), collected - Village.CITIZEN_FOOD * MANY_CITIZENS)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), max(Village.CITIZEN_CURRENCY * MANY_CITIZENS * kept // WHOLE, Caveman.LEAST_INCOME))
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

    def test_a_village_grows_a_citizen_when_its_food_store_is_full_and_its_store_starts_again_from_nothing(self):
        city = self.village(ONE_CITIZEN)
        target = self.game.get_city(city)
        size = TurnControl.store_size(game=self.game, city=city)
        target.set_food(size - FOOD_A_TURN - 1)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((target.get_citizens(), target.get_food()), (ONE_CITIZEN, size - 1))
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((target.get_citizens(), target.get_food()), (ONE_CITIZEN + 1, NOTHING_HELD))

    def test_a_full_store_holds_the_themes_food_for_each_citizen_of_the_village(self):
        city = self.village(ONE_CITIZEN)
        for citizens in (ONE_CITIZEN, ONE_CITIZEN + 1, SEVERAL_CITIZENS, MANY_CITIZENS):
            with self.subTest(citizens=citizens):
                self.game.get_city(city).set_citizens(citizens)
                self.assertEqual(TurnControl.store_size(game=self.game, city=city), Village.STORE_FOOD * citizens)

    def test_food_is_never_held_by_the_civilization(self):
        self.village(ONE_CITIZEN)
        end_rounds(game=self.game, rounds=SEVERAL_CITIZENS)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Food), NOTHING_HELD)

    def test_a_village_of_the_most_citizens_does_not_grow_and_keeps_a_full_store(self):
        city = self.village(MANY_CITIZENS)
        target = self.game.get_city(city)
        size = TurnControl.store_size(game=self.game, city=city)
        target.set_food(size)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((target.get_citizens(), target.get_food()), (MANY_CITIZENS, size))

    def test_a_unit_on_a_tile_heals_a_little_each_turn_and_a_unit_inside_a_village_heals_more(self):
        city = self.village(ONE_CITIZEN)
        outside, inside = self.clubbers(civilization=FIRST_CIVILIZATION, count=TWO_CLUBBERS)
        x, y = self.game.get_city(city).get_x(), self.game.get_city(city).get_y()
        UnitControl.move_to(game=self.game, unit=inside, x=x + BESIDE_CENTER, y=y)
        CityControl.enter(game=self.game, unit=inside, city=city)
        for unit in (outside, inside):
            self.units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=HURT)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.hit_points(outside), HURT + Clubber.HEAL)
        self.assertEqual(self.hit_points(inside), HURT + Clubber.CITY_HEAL)
        self.assertGreater(Clubber.CITY_HEAL, Clubber.HEAL)

    def test_a_unit_never_heals_past_the_hit_points_of_its_kind(self):
        city = self.village(ONE_CITIZEN)
        whole, nearly = self.clubbers(civilization=FIRST_CIVILIZATION, count=TWO_CLUBBERS)
        x, y = self.game.get_city(city).get_x(), self.game.get_city(city).get_y()
        UnitControl.move_to(game=self.game, unit=nearly, x=x + BESIDE_CENTER, y=y)
        CityControl.enter(game=self.game, unit=nearly, city=city)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=nearly, value=NEARLY_HEALED)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual((self.hit_points(whole), self.hit_points(nearly)), (Clubber.HIT_POINTS, Clubber.HIT_POINTS))

    def test_a_unit_heals_only_at_the_end_of_its_own_civilizations_turn(self):
        clubber, = self.clubbers(civilization=SECOND_CIVILIZATION, count=ONE_CLUBBER)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=clubber, value=HURT)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.hit_points(clubber), HURT)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.hit_points(clubber), HURT + Clubber.HEAL)

    def test_all_points_refill_at_the_end_of_a_turn_and_each_village_adds_to_its_civilizations_policy_points(self):
        self.village(ONE_CITIZEN)
        clubber, = self.clubbers(civilization=FIRST_CIVILIZATION, count=ONE_CLUBBER)
        self.units.set_value(column=UnitColumn.ACTION_POINTS, unit=clubber, value=NO_POINTS)
        self.first.set_policy_points(NO_POINTS)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.units.get_value(column=UnitColumn.ACTION_POINTS, unit=clubber), Clubber.ACTION_POINTS)
        self.assertEqual(self.first.get_policy_points(), points_given(by=Caveman, points=Policy) + points_given(by=Village, points=Policy) + Village.IDLE_CONTROL_POINTS[Policy])
        self.assertEqual(self.second.get_policy_points(), points_given(by=Caveman, points=Policy))
        self.assertEqual(TurnControl.control_points(game=self.game, civilization=FIRST_CIVILIZATION, points=Policy), points_given(by=Caveman, points=Policy) + points_given(by=Village, points=Policy) + Village.IDLE_CONTROL_POINTS[Policy])

    def test_buildings_are_paid_for_each_turn_and_a_technology_takes_nothing_off_what_buildings_cost(self):
        city = self.village(ONE_CITIZEN)
        currency = resource_id(game=self.game, resource=Currency)
        self.clubbers(civilization=FIRST_CIVILIZATION, count=MANY_CLUBBERS)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Clubs)
        for_units = TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency]
        self.assertEqual(for_units, Clubber.SUPPORT[Currency] * MANY_CLUBBERS * (WHOLE - Clubs.UNIT_SUPPORT_BONUS) // WHOLE)
        for building in (Granary, GreatCavePainting):
            give_building(game=self.game, city=city, building=building)
        for_buildings = Granary.SUPPORT[Currency] + GreatCavePainting.SUPPORT[Currency]
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], for_units + for_buildings)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=SECOND_CIVILIZATION)[currency], Settler.SUPPORT[Currency])
        end_rounds(game=self.game, rounds=ONE_ROUND)
        paid = STARTING_CURRENCY + CURRENCY_A_TURN - for_units - for_buildings
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), max(paid, STARTING_CURRENCY + Caveman.LEAST_INCOME))

    def test_a_civilization_with_a_city_always_gains_the_least_income_and_one_with_no_city_does_not(self):
        self.village(ONE_CITIZEN)
        self.clubbers(civilization=FIRST_CIVILIZATION, count=MANY_CLUBBERS)
        currency = resource_id(game=self.game, resource=Currency)
        self.assertGreater(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], CURRENCY_A_TURN)
        first = self.held(civilization=FIRST_CIVILIZATION, resource=Currency)
        second = self.held(civilization=SECOND_CIVILIZATION, resource=Currency)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), first + Caveman.LEAST_INCOME)
        self.assertLess(self.held(civilization=SECOND_CIVILIZATION, resource=Currency), second)
        for _ in range(Caveman.BANKRUPTCY_TURNS):
            end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertFalse(self.first.is_bankrupt())
        self.assertFalse(self.first.has_lost())

    def test_a_civilization_with_buildings_and_no_units_pays_for_the_buildings(self):
        city = self.village(ONE_CITIZEN)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION), {})
        give_building(game=self.game, city=city, building=Granary)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION), {resource_id(game=self.game, resource=Currency): Granary.SUPPORT[Currency]})

    def test_a_granary_makes_the_store_of_its_village_smaller_and_no_other_village(self):
        city = self.village(ONE_CITIZEN)
        other = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        give_building(game=self.game, city=city, building=Granary)
        self.assertEqual(TurnControl.store_size(game=self.game, city=city), Village.STORE_FOOD - Granary.GROWS_SOONER)
        self.assertEqual(TurnControl.store_size(game=self.game, city=other), Village.STORE_FOOD)

    def test_each_citizens_share_of_a_full_store_is_never_less_than_the_least_however_much_sooner_buildings_make_it(self):
        game = started_caveman_game(theme=HOTHOUSE_CAVEMAN)
        city = found_village(game=game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        give_building(game=game, city=city, building=Hothouse)
        self.assertGreater(Hothouse.GROWS_SOONER, Village.STORE_FOOD)
        self.assertEqual(TurnControl.store_size(game=game, city=city), LEAST_STORE_FOOD)
        end_rounds(game=game, rounds=ONE_ROUND)
        self.assertEqual(game.get_city(city).get_citizens(), ONE_CITIZEN + 1)

    def test_a_building_can_add_policy_points_to_its_civilization(self):
        city = self.village(ONE_CITIZEN)
        give_building(game=self.game, city=city, building=ArrangementOfRocks)
        expected = points_given(by=Caveman, points=Policy) + points_given(by=Village, points=Policy) + Village.IDLE_CONTROL_POINTS[Policy] + points_given(by=ArrangementOfRocks, points=Policy)
        self.assertEqual(TurnControl.control_points(game=self.game, civilization=FIRST_CIVILIZATION, points=Policy), expected)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.first.get_policy_points(), expected)
        self.assertEqual(self.second.get_policy_points(), points_given(by=Caveman, points=Policy))

    def test_units_are_paid_for_before_what_a_village_builds(self):
        part = Production.part(kind=Settler, turn=FIRST_TURN)[Currency]
        citizens, count = citizens_and_clubbers(part)
        city = self.village(citizens)
        self.spend_all_currency(self.first)
        self.clubbers(civilization=FIRST_CIVILIZATION, count=count)
        Orders.build(game=self.game, city=city, kind=Settler)
        income = CURRENCY_A_TURN * citizens
        after_support = income - Clubber.SUPPORT[Currency] * count
        self.assertTrue(NOTHING_LEFT < after_support < part <= income)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertTrue(self.game.get_city(city).is_blocked())
        self.assertEqual(self.held(civilization=FIRST_CIVILIZATION, resource=Currency), after_support)
        self.assertFalse(self.first.is_bankrupt())


class Haste(Technology):
    """A technology that makes every city of the civilization that knows it grow a citizen sooner."""

    GROWS_SOONER = 2


class Feast(Building):
    """A building that takes an amount off the upkeep of each unit of its civilization."""

    SUPPORT = {Currency: 1}
    UNIT_SUPPORT_DISCOUNT = {Currency: 2}


class Banquet(Building):
    """A building that takes more off the upkeep of each unit than any unit costs, so that the units cost nothing."""

    SUPPORT = {Currency: 1}
    UNIT_SUPPORT_DISCOUNT = {Currency: 100}


HASTY_CAVEMAN = later_caveman({Category.TECHNOLOGIES: (*Caveman.TECHNOLOGIES, Haste), Category.BUILDINGS: (*Caveman.BUILDINGS, Feast, Banquet)})


class TestGrowthAndUpkeepEffects(unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game(theme=HASTY_CAVEMAN)
        self.city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)

    def test_a_technology_makes_the_store_of_every_city_of_its_civilization_smaller(self):
        plain = TurnControl.store_size(game=self.game, city=self.city)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Haste)
        self.assertEqual(TurnControl.store_size(game=self.game, city=self.city), plain - Haste.GROWS_SOONER)

    def test_a_building_takes_an_amount_off_each_units_upkeep_and_never_below_nothing(self):
        currency = resource_id(game=self.game, resource=Currency)
        x, _ = SETTLER_TILES[0]
        units = [UnitControl.place(game=self.game, kind=Clubber, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + step, y=OPEN_ROW) for step in range(TWO_CLUBBERS)]
        plain = TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency]
        give_building(game=self.game, city=self.city, building=Feast)
        each = min(Feast.UNIT_SUPPORT_DISCOUNT[Currency], Clubber.SUPPORT[Currency])
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], plain - each * len(units) + Feast.SUPPORT[Currency])
        give_building(game=self.game, city=self.city, building=Banquet)
        self.assertEqual(TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION)[currency], Feast.SUPPORT[Currency] + Banquet.SUPPORT[Currency])
