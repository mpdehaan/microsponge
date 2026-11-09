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

"""Tests for research: the points a civilization gathers, the one technology it researches, and picking the next."""

import unittest

from caveman_game import end_rounds, found_village, game_facts, give_building, held, learn, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.civilizations.research import Research
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.turns.orders import Orders
from microsponge.support.numbers import divided_rounding_up
from microsponge.err_messages import ERR_ALREADY_KNOWN, ERR_ALREADY_RESEARCHING, ERR_BUILD_REQUIRES, ERR_MUST_PICK_RESEARCH, ERR_NOT_YOUR_TURN, ERR_RESEARCH_REQUIRES
from microsponge.themes.caveman.buildings import GreatCavePainting
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.resources import Currency
from microsponge.themes.caveman.technologies import Agriculture, Clubs, Discipline, Fire
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Warrior

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
FIRST_NAME = 'Ugg'
SECOND_NAME = 'Grok'
A_NAME = 'Ugghome'
ONE_ROUND = 1
NO_POINTS = 0
# What the one city of the first civilization earns in currency each turn, with its one citizen working.
INCOME = Village.CITIZEN_CURRENCY
# The research points one city gathers each turn, and one city with the great cave painting.
CITY_POINTS = Village.RESEARCH_POINTS
PAINTING_POINTS = CITY_POINTS + GreatCavePainting.RESEARCH_POINTS
# The rounds one city takes to research clubs, and half of them.
CLUBS_ROUNDS = Clubs.RESEARCH // CITY_POINTS
HALF_THE_ROUNDS = CLUBS_ROUNDS // 2


class Pottery(Technology):
    """A technology that requires another."""

    REQUIRES = (Agriculture,)
    RESEARCH = 5


POTTERY_CAVEMAN = later_caveman({Category.TECHNOLOGIES: (*Caveman.TECHNOLOGIES, Pottery)})


class ResearchCase(Refusals, unittest.TestCase):
    """A started game in which the first civilization has one city and the second has none."""

    THEME = Caveman

    def setUp(self):
        self.game = started_caveman_game(theme=self.THEME)
        self.first = self.game.get_civilization(FIRST_CIVILIZATION)
        self.second = self.game.get_civilization(SECOND_CIVILIZATION)
        self.city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)

    def research(self, technology):
        Orders.research(game=self.game, civilization=FIRST_CIVILIZATION, technology=technology)

    def researching(self):
        return Research.researching(game=self.game, civilization=FIRST_CIVILIZATION)

    def available(self):
        return Research.available(game=self.game, civilization=FIRST_CIVILIZATION)

    def knows(self, technology):
        return self.first.knows(self.game.get_catalog().get_id(category=Category.TECHNOLOGIES, kind=technology))

    def rounds(self, rounds):
        end_rounds(game=self.game, rounds=rounds)

    def refused_and_unchanged(self, action):
        """Return the message an order is refused with, having checked that the refusal changed nothing in the game."""
        before = game_facts(self.game)
        message = self.refused(action)
        self.assertEqual(game_facts(self.game), before)
        return message


class TestResearch(ResearchCase):

    def test_a_civilization_gathers_research_points_for_each_city_and_from_certain_buildings(self):
        self.assertEqual(Research.points_a_turn(game=self.game, civilization=FIRST_CIVILIZATION), CITY_POINTS)
        self.assertEqual(Research.points_a_turn(game=self.game, civilization=SECOND_CIVILIZATION), NO_POINTS)
        give_building(game=self.game, city=self.city, building=GreatCavePainting)
        self.assertEqual(Research.points_a_turn(game=self.game, civilization=FIRST_CIVILIZATION), PAINTING_POINTS)
        self.assertGreater(PAINTING_POINTS, CITY_POINTS)

    def test_a_civilization_has_to_pick_a_technology_while_it_researches_nothing_and_one_is_left(self):
        self.assertEqual(self.available(), list(Caveman.TECHNOLOGIES))
        self.assertIsNone(self.researching())
        self.assertTrue(Research.must_choose(game=self.game, civilization=FIRST_CIVILIZATION))
        pool = self.first.get_action_points()
        self.research(Clubs)
        self.assertIs(self.researching(), Clubs)
        self.assertFalse(Research.must_choose(game=self.game, civilization=FIRST_CIVILIZATION))
        self.assertEqual(self.first.get_action_points(), pool)
        self.assertTrue(Research.must_choose(game=self.game, civilization=SECOND_CIVILIZATION))

    def test_a_technology_is_known_once_the_points_put_toward_it_reach_what_the_technology_takes(self):
        self.research(Clubs)
        self.rounds(CLUBS_ROUNDS - ONE_ROUND)
        self.assertFalse(self.knows(Clubs))
        self.assertEqual(self.first.get_research(), Clubs.RESEARCH - CITY_POINTS)
        self.rounds(ONE_ROUND)
        self.assertTrue(self.knows(Clubs))
        self.assertEqual(self.first.get_research(), NO_POINTS)
        self.assertFalse(self.knows(Agriculture))

    def test_there_is_no_queue_so_the_civilization_has_to_pick_again_when_a_technology_is_known(self):
        self.research(Clubs)
        self.rounds(CLUBS_ROUNDS)
        self.assertIsNone(self.researching())
        self.assertTrue(Research.must_choose(game=self.game, civilization=FIRST_CIVILIZATION))
        self.assertEqual(self.available(), [Agriculture, Discipline, Fire])

    def test_the_points_past_what_a_technology_takes_are_lost(self):
        give_building(game=self.game, city=self.city, building=GreatCavePainting)
        self.research(Clubs)
        rounds = divided_rounding_up(amount=Clubs.RESEARCH, by=PAINTING_POINTS)
        self.rounds(rounds)
        self.assertTrue(self.knows(Clubs))
        self.assertGreater(PAINTING_POINTS * rounds - Clubs.RESEARCH, NO_POINTS)
        self.assertEqual(self.first.get_research(), NO_POINTS)

    def test_points_do_not_gather_while_nothing_is_researched_and_a_technology_is_left_to_pick(self):
        currency = held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Currency)
        self.rounds(HALF_THE_ROUNDS)
        self.assertEqual(self.first.get_research(), NO_POINTS)
        self.assertEqual(held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Currency), currency + INCOME * HALF_THE_ROUNDS)
        self.research(Clubs)
        self.rounds(CLUBS_ROUNDS - ONE_ROUND)
        self.assertFalse(self.knows(Clubs))
        self.rounds(ONE_ROUND)
        self.assertTrue(self.knows(Clubs))

    def test_a_civilization_cannot_switch_to_another_technology_for_now(self):
        self.research(Agriculture)
        self.rounds(HALF_THE_ROUNDS)
        message = self.refused_and_unchanged(lambda: self.research(Clubs))
        self.assertEqual(message, ERR_ALREADY_RESEARCHING.format(name=FIRST_NAME, technology=shown_name(Agriculture), wanted=shown_name(Clubs)))
        self.assertIs(self.researching(), Agriculture)
        self.assertEqual(self.first.get_research(), CITY_POINTS * HALF_THE_ROUNDS)

    def test_a_turn_cannot_be_ended_by_order_while_a_technology_is_left_to_pick_and_none_is_picked(self):
        self.assertIsNotNone(Research.problem_ending_turn(game=self.game, civilization=FIRST_CIVILIZATION))
        message = self.refused_and_unchanged(lambda: Orders.end_turn(game=self.game, civilization=FIRST_CIVILIZATION))
        self.assertEqual(message, ERR_MUST_PICK_RESEARCH.format(name=FIRST_NAME))
        self.research(Clubs)
        self.assertIsNone(Research.problem_ending_turn(game=self.game, civilization=FIRST_CIVILIZATION))
        Orders.end_turn(game=self.game, civilization=FIRST_CIVILIZATION)
        self.assertEqual(self.game.get_playing(), SECOND_CIVILIZATION)

    def test_a_turn_can_be_ended_by_order_once_every_technology_is_known(self):
        for technology in Caveman.TECHNOLOGIES:
            learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=technology)
        self.assertIsNone(Research.problem_ending_turn(game=self.game, civilization=FIRST_CIVILIZATION))
        Orders.end_turn(game=self.game, civilization=FIRST_CIVILIZATION)
        self.assertEqual(self.game.get_playing(), SECOND_CIVILIZATION)

    def test_picking_the_technology_being_researched_again_keeps_the_points_put_toward_it(self):
        self.research(Clubs)
        self.rounds(HALF_THE_ROUNDS)
        self.research(Clubs)
        self.assertEqual(self.first.get_research(), CITY_POINTS * HALF_THE_ROUNDS)

    def test_a_civilization_with_no_city_gathers_no_points(self):
        self.research(Agriculture)
        Orders.end_turn(game=self.game, civilization=FIRST_CIVILIZATION)
        Orders.research(game=self.game, civilization=SECOND_CIVILIZATION, technology=Clubs)
        Orders.end_turn(game=self.game, civilization=SECOND_CIVILIZATION)
        self.rounds(CLUBS_ROUNDS)
        self.assertEqual(self.second.get_research(), NO_POINTS)
        self.assertIs(Research.researching(game=self.game, civilization=SECOND_CIVILIZATION), Clubs)

    def test_a_technology_the_civilization_knows_cannot_be_researched_again(self):
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Clubs)
        self.assertEqual(self.available(), [Agriculture, Discipline, Fire])
        message = self.refused_and_unchanged(lambda: self.research(Clubs))
        self.assertEqual(message, ERR_ALREADY_KNOWN.format(name=FIRST_NAME, technology=shown_name(Clubs)))

    def test_when_every_technology_is_known_there_is_nothing_to_pick_and_the_points_become_currency(self):
        for technology in Caveman.TECHNOLOGIES:
            learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=technology)
        self.assertEqual(self.available(), [])
        self.assertFalse(Research.must_choose(game=self.game, civilization=FIRST_CIVILIZATION))
        currency = held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Currency)
        self.rounds(ONE_ROUND)
        self.assertEqual(self.first.get_research(), NO_POINTS)
        self.assertEqual(held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Currency), currency + INCOME + CITY_POINTS * Caveman.RESEARCH_TO_CURRENCY)

    def test_a_technology_is_picked_only_on_the_turn_of_the_civilization(self):
        message = self.refused_and_unchanged(lambda: Orders.research(game=self.game, civilization=SECOND_CIVILIZATION, technology=Clubs))
        self.assertEqual(message, ERR_NOT_YOUR_TURN.format(name=SECOND_NAME))

    def test_researching_clubs_lets_a_city_build_a_warrior(self):
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(Warrior), required=shown_name(Clubs))
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.build(game=self.game, city=self.city, kind=Warrior)), expected)
        self.research(Clubs)
        self.rounds(CLUBS_ROUNDS)
        Orders.build(game=self.game, city=self.city, kind=Warrior)
        self.rounds(Warrior.BUILD_TURNS)
        self.assertEqual(len(self.game.get_city(self.city).get_units()), ONE_ROUND)


class TestATechnologyThatRequiresAnother(ResearchCase):

    THEME = POTTERY_CAVEMAN

    def test_a_technology_cannot_be_researched_before_the_technology_it_requires(self):
        self.assertEqual(self.available(), list(Caveman.TECHNOLOGIES))
        expected = ERR_RESEARCH_REQUIRES.format(technology=shown_name(Pottery), required=shown_name(Agriculture))
        self.assertEqual(Research.problem_choosing(game=self.game, civilization=FIRST_CIVILIZATION, technology=Pottery), expected)
        self.assertEqual(self.refused_and_unchanged(lambda: self.research(Pottery)), expected)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Agriculture)
        self.assertEqual(self.available(), [Clubs, Discipline, Fire, Pottery])
        self.research(Pottery)
        self.assertIs(self.researching(), Pottery)
