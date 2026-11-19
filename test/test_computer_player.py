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

"""The computer player: a whole game of caveman played by two computer players through standing orders, and how the traits tip its decisions."""

import time
import unittest

from caveman_game import FIRST_CIVILIZATION, THE_WORLD, computer_played_caveman_game, found_village, learn, play_turns, started_caveman_game
from microsponge.engine.kinds.control_points import CONTROL_POINTS, Policy
from microsponge.engine.orders.thing import city_thing
from microsponge.engine.orders.what import Buildings, NoDetails, Priority
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.players.hand import Hand
from microsponge.engine.turns.orders import Orders
from microsponge.engine.kinds.category import Category
from microsponge.engine.orders.order import BuildOrder, ExpandOrder, GarrisonOrder, MarchOrder, RaiseOrder, ResearchOrder, ResourcesPolicyOrder, RetireOrder, SettlerOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.unit_kinds import can_hit
from microsponge.engine.players.appraisal import Appraisal
from microsponge.engine.players.computer_player import ComputerPlayer, Weights
from microsponge.engine.players.knowledge import Knowledge
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.players.traits import AGGRESSIVE_HYPERFOCUS, BOLDNESS, CONQUEST, EXPANSION, LEAST, LOGICAL, MIDDLE, MOST, PEACE, SCIENCE, TRAITS
from microsponge.themes.caveman.theme import Caveman

FIRST = FIRST_CIVILIZATION
A_NAME = 'Bedrock'
# Currency enough that a civilization can raise its division whatever the theme's economy, so that a test sees only what a trait decides.
WEALTH = 10000
# A kind of unit of the theme that requires nothing and uses up no citizen, which any city can build.
FREE_UNIT = next(kind for kind in Caveman.UNITS if not kind.REQUIRES and not kind.CITIZENS)
# Open tiles near the first civilization's first village, as (x, y), for fighters beyond its garrison.
SPARE_TILES = ((9, 10), (9, 12), (9, 14))
SECOND = FIRST + 1
A_SEED = 7
A_FEW_TURNS = 3
TURNS = 60
LONG_GAME = 100
# A turn of two computer players on the test world should take far less than this, in seconds.
SLOW = 0.1
EVERYTHING_MIDDLE = {trait: MIDDLE for trait in TRAITS}
EXPANDING = {**EVERYTHING_MIDDLE, EXPANSION: MOST, PEACE: MOST}
STAYING = {**EVERYTHING_MIDDLE, EXPANSION: LEAST, PEACE: MOST}
WARLIKE = {**EVERYTHING_MIDDLE, PEACE: LEAST, CONQUEST: MOST}
PACIFIST = {**EVERYTHING_MIDDLE, PEACE: MOST}
RECKLESS = {**WARLIKE, BOLDNESS: MOST, AGGRESSIVE_HYPERFOCUS: MOST}
CAREFUL = {**WARLIKE, BOLDNESS: LEAST, AGGRESSIVE_HYPERFOCUS: LEAST}
SCIENTIST = {**EVERYTHING_MIDDLE, SCIENCE: MOST}
SOLDIER = {**EVERYTHING_MIDDLE, SCIENCE: LEAST}


def currency_of(game):
    """Return the id of the theme's primary resource."""
    return game.get_catalog().get_id(category=Category.RESOURCES, kind=game.get_theme().PRIMARY_RESOURCE)


def given(*, game, civilization, kind):
    """Return the orders of a kind a civilization's player gave."""
    return [order for order in game.get_civilization(civilization).get_orders().get_orders() if order.is_a(kind)]


class TestComputerPlayer(unittest.TestCase):

    def test_the_computer_player_knows_no_theme_and_reads_every_kind_from_the_themes_properties(self):
        self.assertIs(Caveman.PLAYER, ComputerPlayer)
        theme = Caveman
        for kind in Appraisal.fighters(theme):
            self.assertTrue(kind.TAKES_CITIES and kind.DOMAIN == Domain.LAND and kind.ATTACK is not NO_DICE)
        fighters = Appraisal.fighters(theme)
        self.assertEqual(fighters, sorted(fighters, key=Appraisal.unit_worth, reverse=True))
        for kind in Appraisal.water_fighters(theme):
            self.assertTrue(kind.ON_WATER and kind.ATTACK is not NO_DICE)
        for enemy in theme.UNITS:
            for kind in Appraisal.counters_to(theme=theme, enemy=enemy):
                self.assertTrue(can_hit(kind=kind, target=enemy))
            for kind in Appraisal.unhittable_by(theme=theme, enemies=[enemy]):
                self.assertTrue(enemy.ATTACK is not NO_DICE and not can_hit(kind=enemy, target=kind))
        for kind in Appraisal.engineers(theme):
            self.assertTrue(kind.BUILDS)
        self.assertEqual(set(Appraisal.ranked_buildings(theme=theme, weights=Weights)), set(theme.BUILDINGS))
        self.assertEqual(set(Appraisal.ranked_technologies(theme=theme, weights=Weights)), set(theme.TECHNOLOGIES))

    def test_two_computer_players_play_a_whole_game_founding_cities_researching_and_building_units_quickly(self):
        game = computer_played_caveman_game(seed=A_SEED)
        started = time.perf_counter()
        play_turns(game=game, turns=TURNS)
        seconds = time.perf_counter() - started
        self.assertTrue(game.get_turn() == TURNS or game.is_over())
        self.assertLess(seconds / game.get_turn(), SLOW)
        for civilization in (FIRST, SECOND):
            with self.subTest(civilization=civilization):
                holder = game.get_civilization(civilization)
                self.assertGreaterEqual(holder.get_cities_founded(), 1)
                self.assertTrue(holder.get_technologies())
        self.assertEqual([game.get_city(city).get_founded() for city in game.get_city_ids()[:SECOND]], [0, 0])
        self.assertTrue(any(game.get_city(city).get_units() for city in game.get_city_ids()))

    def test_the_same_seed_plays_the_same_game_again(self):
        first = computer_played_caveman_game(seed=A_SEED)
        second = computer_played_caveman_game(seed=A_SEED)
        play_turns(game=first, turns=TURNS)
        play_turns(game=second, turns=TURNS)
        self.assertEqual([city.get_name() for city in first.get_cities()], [city.get_name() for city in second.get_cities()])
        self.assertEqual(first.get_units().count(), second.get_units().count())
        self.assertEqual(first.get_civilization(FIRST).get_traits().get_values(), second.get_civilization(FIRST).get_traits().get_values())

    def test_the_player_plays_only_by_giving_orders_and_gives_each_kind_where_it_belongs(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(LOGICAL, LOGICAL))
        ComputerPlayer.plan(game=game, civilization=FIRST)
        self.assertEqual(len(given(game=game, civilization=FIRST, kind=ResearchOrder)), 1)
        self.assertEqual(len(given(game=game, civilization=FIRST, kind=SettlerOrder)), 1)
        self.assertEqual(game.get_cities_of(FIRST), [])
        play_turns(game=game, turns=A_FEW_TURNS)
        city = game.get_cities_of(FIRST)[0]
        for kind in (BuildOrder, RaiseOrder, ExpandOrder, GarrisonOrder):
            with self.subTest(kind=kind):
                self.assertEqual(len(given(game=game, civilization=FIRST, kind=kind)), 1)
        self.assertEqual(given(game=game, civilization=FIRST, kind=SettlerOrder), [])
        self.assertEqual(given(game=game, civilization=FIRST, kind=GarrisonOrder)[0].get_what().place.city, city)
        forces = game.get_civilization(FIRST).get_forces()
        self.assertEqual((len(forces.get_armies()), len(forces.get_divisions())), (1, 1))
        self.assertEqual(forces.get_divisions()[0].get_bases(), [city])

    def test_the_player_never_ends_a_turn_with_orders_that_take_more_points_than_it_has(self):
        game = computer_played_caveman_game(seed=A_SEED)
        for _ in range(TURNS):
            civilization = game.get_playing()
            ComputerPlayer.plan(game=game, civilization=civilization)
            for points in CONTROL_POINTS:
                self.assertGreaterEqual(OrderControl.left(game=game, civilization=civilization, points=points), 0)
            ComputerPlayer.play_turn(game=game, civilization=civilization)

    def test_the_research_order_lists_only_what_could_be_researched_next_ranked_as_the_science_trait_decides(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(SCIENTIST, SOLDIER))
        first = Appraisal.researchable(theme=Caveman, known=set())
        for civilization, weights in ((FIRST, ComputerPlayer.SCIENCE_WEIGHTS), (SECOND, ComputerPlayer.MILITARY_WEIGHTS)):
            ComputerPlayer.plan(game=game, civilization=civilization)
            listed = given(game=game, civilization=civilization, kind=ResearchOrder)[0].get_what().kinds
            self.assertEqual(listed, tuple(Appraisal.ranked_technologies(theme=Caveman, weights=weights, among=first)))
        self.assertLess(len(first), len(Caveman.TECHNOLOGIES))

    def test_learning_a_technology_brings_a_new_research_order_with_what_it_opens(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(SCIENTIST, SOLDIER))
        ComputerPlayer.plan(game=game, civilization=FIRST)
        before, = given(game=game, civilization=FIRST, kind=ResearchOrder)
        technology = next(technology for technology in Appraisal.researchable(theme=Caveman, known=set()) if any(technology in later.REQUIRES for later in Caveman.TECHNOLOGIES))
        learn(game=game, civilization=FIRST, technology=technology)
        ComputerPlayer.plan(game=game, civilization=FIRST)
        after, = given(game=game, civilization=FIRST, kind=ResearchOrder)
        self.assertIsNot(after, before)
        self.assertEqual(set(after.get_what().kinds), set(Appraisal.researchable(theme=Caveman, known={technology})))
        self.assertNotIn(technology, after.get_what().kinds)

    def test_a_player_that_favors_expansion_founds_more_cities_than_one_that_never_does(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(EXPANDING, STAYING))
        play_turns(game=game, turns=LONG_GAME)
        self.assertGreater(len(game.get_cities_of(FIRST)), 1)
        self.assertEqual(len(game.get_cities_of(SECOND)), 1)
        self.assertEqual(Knowledge.settlers_of(game=game, civilization=SECOND), [])

    def test_a_player_that_values_peace_never_declares_war_and_one_that_does_not_declares_it_once_its_army_is_ready(self):
        for traits, wars in (((PACIFIST, PACIFIST), []), ((WARLIKE, WARLIKE), [SECOND])):
            with self.subTest(wars=wars):
                game = computer_played_caveman_game(seed=A_SEED, traits=traits)
                for civilization in (FIRST, SECOND):
                    game.get_civilization(civilization).add(resource=currency_of(game), amount=WEALTH)
                play_turns(game=game, turns=LONG_GAME)
                self.assertEqual(game.get_civilization(FIRST).get_wars(), wars)
                if not wars:
                    self.assertEqual(given(game=game, civilization=FIRST, kind=MarchOrder), [])

    def test_boldness_and_aggressive_hyperfocus_decide_how_an_order_to_march_tells_the_units_to_behave(self):
        for traits, expected in ((RECKLESS, True), (CAREFUL, False)):
            with self.subTest(expected=expected):
                game = computer_played_caveman_game(seed=A_SEED, traits=(traits, traits))
                play_turns(game=game, turns=A_FEW_TURNS)
                what = ComputerPlayer.march_on(game=game, civilization=FIRST, city=game.get_cities_of(SECOND)[0])
                self.assertEqual((what.bold, what.ignore_units), (expected, expected))
                self.assertEqual(what.target.city, game.get_cities_of(SECOND)[0])


class TestRetiringToSaveTheIncome(unittest.TestCase):

    def test_a_starved_player_retires_a_fighter_beyond_its_garrisons_and_a_fed_player_does_not(self):
        game = started_caveman_game()
        city = found_village(game=game, civilization=FIRST, name=A_NAME)
        player = game.get_theme().PLAYER
        player.plan_division(game=game, civilization=FIRST)
        division = player.division_of(game=game, civilization=FIRST)
        for x, y in SPARE_TILES:
            division.add_unit(UnitControl.place(game=game, kind=Appraisal.fighters(game.get_theme())[-1], owner=FIRST, world=THE_WORLD, x=x, y=y))
        self.assertGreater(len(division.get_units()), len(game.get_cities_of(FIRST)))
        holder = game.get_civilization(FIRST)
        holder.pay(resource=currency_of(game), amount=holder.get_amount(currency_of(game)))
        self.assertTrue(player.is_starved(game=game, civilization=FIRST))
        player.plan_retirement(game=game, civilization=FIRST)
        retiring = given(game=game, civilization=FIRST, kind=RetireOrder)
        self.assertEqual(len(retiring), 1)
        self.assertIn(retiring[0].get_receiver().id, division.get_units())
        game.get_civilization(FIRST).add(resource=currency_of(game), amount=player.RESERVE)
        self.assertFalse(player.is_starved(game=game, civilization=FIRST))
        player.plan_retirement(game=game, civilization=FIRST)
        self.assertEqual(len(given(game=game, civilization=FIRST, kind=RetireOrder)), 1)
        self.assertIn(city, game.get_cities_of(FIRST))


class TestPointsAfterTheHandActs(unittest.TestCase):

    def test_a_city_that_starts_to_build_loses_its_idle_points_and_the_player_still_ends_its_turn_within_its_points(self):
        game = computer_played_caveman_game(seed=A_SEED)
        city = found_village(game=game, civilization=FIRST, name=A_NAME)
        ComputerPlayer.plan(game=game, civilization=FIRST)
        while OrderControl.left(game=game, civilization=FIRST, points=Policy) > 0:
            here = city_thing(city)
            OrderControl.give(game=game, civilization=FIRST, kind=ExpandOrder, giver=here, receiver=here, what=NoDetails())
        Orders.build(game=game, city=city, kind=FREE_UNIT)
        self.assertLess(OrderControl.left(game=game, civilization=FIRST, points=Policy), 0)
        ComputerPlayer.keep_within_points(game=game, civilization=FIRST)
        self.assertGreaterEqual(OrderControl.left(game=game, civilization=FIRST, points=Policy), 0)


class TestWhatTheDivisionAndTheCitiesAreGiven(unittest.TestCase):

    def setUp(self):
        self.game = computer_played_caveman_game(seed=A_SEED)
        self.city = found_village(game=self.game, civilization=FIRST, name=A_NAME)

    def test_an_enemy_kind_the_fighters_cannot_hit_makes_the_division_ask_for_a_unit_that_can(self):
        theme = self.game.get_theme()
        fighters = Appraisal.fighters(theme)
        unanswered = next(kind for kind in theme.UNITS if not can_hit(kind=fighters[0], target=kind))
        x, y = SPARE_TILES[0]
        UnitControl.place(game=self.game, kind=unanswered, owner=SECOND, world=THE_WORLD, x=x, y=y)
        Sight.refresh(game=self.game, civilization=FIRST)
        targets = ComputerPlayer.division_wanted(game=self.game, civilization=FIRST).targets
        self.assertEqual(targets[0].kinds, tuple(Appraisal.counters_to(theme=theme, enemy=unanswered)))
        self.assertEqual(targets[-1].kinds, tuple(fighters))

    def test_a_city_whose_next_building_costs_a_resource_the_bank_lacks_has_its_citizens_look_for_it_first(self):
        theme = self.game.get_theme()
        technologies = set(theme.TECHNOLOGIES)
        building = next(building for building in theme.BUILDINGS if set(building.REQUIRES) <= technologies and any(resource not in (theme.PRIMARY_RESOURCE, theme.FOOD) for resource in building.COST))
        resource = next(resource for resource in building.COST if resource not in (theme.PRIMARY_RESOURCE, theme.FOOD))
        for technology in theme.TECHNOLOGIES:
            learn(game=self.game, civilization=FIRST, technology=technology)
        here = city_thing(self.city)
        OrderControl.give(game=self.game, civilization=FIRST, kind=BuildOrder, giver=here, receiver=here, what=Buildings(kinds=(building,)))
        ComputerPlayer.plan_priorities(game=self.game, civilization=FIRST)
        order, = given(game=self.game, civilization=FIRST, kind=ResourcesPolicyOrder)
        self.assertEqual(order.get_what(), Priority(resource=resource, citizens=ComputerPlayer.PRIORITY_CITIZENS))
        Hand.direct_priorities(game=self.game, civilization=FIRST)
        resource_id = self.game.get_catalog().get_id(category=Category.RESOURCES, kind=resource)
        self.assertEqual(self.game.get_city(self.city).get_priorities(), {resource_id: ComputerPlayer.PRIORITY_CITIZENS})
        self.game.get_civilization(FIRST).add(resource=resource_id, amount=building.COST[resource])
        ComputerPlayer.plan_priorities(game=self.game, civilization=FIRST)
        self.assertEqual(given(game=self.game, civilization=FIRST, kind=ResourcesPolicyOrder), [])
        Hand.direct_priorities(game=self.game, civilization=FIRST)
        self.assertEqual(self.game.get_city(self.city).get_priorities(), {})
