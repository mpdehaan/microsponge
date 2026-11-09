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

"""Tests for a civilization: its name, what it holds, the technologies it knows, its action points, its wars and whether it has lost."""

import json
import unittest

from refusals import Refusals
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.kinds.category import Category
from microsponge.err_messages import ERR_AMOUNT, ERR_CIVILIZATION_NAME, ERR_UNKNOWN_ID

A_NAME = 'Ugg'
ANOTHER_NAME = 'Grok'
BLANK = '   '
SMALL = 3
# Ids of resources, technologies and other civilizations, as a game's catalog would give them.
CURRENCY = 1
FOOD = 2
STONE = 3
CLUBS = 1
FARMING = 2
A_NEIGHBOR = 2
ANOTHER_NEIGHBOR = 5
SOME = 30
MORE = 12
A_FEW_POINTS = 4
A_FEW_TURNS = 7
NONE = 0
NOT_AMOUNTS = (-1, 1.5, '3', None, True)
# A later version's ids for the resources and the technologies above.
LATER_RESOURCES = {0: 0, CURRENCY: STONE, FOOD: FOOD, STONE: CURRENCY}
LATER_TECHNOLOGIES = {0: 0, CLUBS: FARMING, FARMING: CLUBS}
ONLY_CURRENCY = {0: 0, CURRENCY: CURRENCY}


def through_json(data):
    """Return data as it comes back from a JSON file."""
    return json.loads(json.dumps(data))


class TestCivilization(Refusals, unittest.TestCase):

    def setUp(self):
        self.civilization = Civilization(A_NAME)

    def test_a_civilization_has_a_name_that_can_change(self):
        self.assertEqual(self.civilization.get_name(), A_NAME)
        self.civilization.set_name(ANOTHER_NAME)
        self.assertEqual(self.civilization.get_name(), ANOTHER_NAME)

    def test_a_name_that_is_blank_or_not_text_is_refused_and_the_name_stays(self):
        for name in (BLANK, str(), None, SMALL):
            with self.subTest(name=name):
                expected = ERR_CIVILIZATION_NAME.format(value=name)
                self.assertEqual(self.refused(lambda: Civilization(name)), expected)
                self.assertEqual(self.refused(lambda: self.civilization.set_name(name)), expected)
        self.assertEqual(self.civilization.get_name(), A_NAME)

    def test_a_new_civilization_holds_nothing_knows_nothing_and_is_at_peace(self):
        self.assertEqual(self.civilization.get_holdings(), {})
        self.assertEqual(self.civilization.get_amount(CURRENCY), NONE)
        self.assertEqual(self.civilization.get_technologies(), [])
        self.assertEqual((self.civilization.get_researching(), self.civilization.get_research()), (NONE, NONE))
        self.assertEqual(self.civilization.get_action_points(), NONE)
        self.assertEqual(self.civilization.get_wars(), [])
        self.assertFalse(self.civilization.is_bankrupt())
        self.assertFalse(self.civilization.has_lost())

    def test_what_is_added_is_held_for_each_resource_apart(self):
        self.civilization.add(resource=CURRENCY, amount=SOME)
        self.civilization.add(resource=CURRENCY, amount=MORE)
        self.civilization.add(resource=FOOD, amount=MORE)
        self.assertEqual(self.civilization.get_amount(CURRENCY), SOME + MORE)
        self.assertEqual(self.civilization.get_amount(FOOD), MORE)
        self.assertEqual(self.civilization.get_amount(STONE), NONE)
        self.assertEqual(self.civilization.get_holdings(), {CURRENCY: SOME + MORE, FOOD: MORE})

    def test_paying_takes_the_amount_from_what_is_held(self):
        self.civilization.add(resource=CURRENCY, amount=SOME)
        self.assertEqual(self.civilization.pay(resource=CURRENCY, amount=MORE), MORE)
        self.assertEqual(self.civilization.get_amount(CURRENCY), SOME - MORE)

    def test_paying_more_than_is_held_takes_all_there_is_and_says_how_much(self):
        self.civilization.add(resource=CURRENCY, amount=MORE)
        self.assertEqual(self.civilization.pay(resource=CURRENCY, amount=SOME), MORE)
        self.assertEqual(self.civilization.get_amount(CURRENCY), NONE)
        self.assertEqual(self.civilization.pay(resource=FOOD, amount=SOME), NONE)

    def test_the_holdings_handed_out_are_a_copy(self):
        self.civilization.add(resource=CURRENCY, amount=SOME)
        self.civilization.get_holdings()[CURRENCY] = MORE
        self.assertEqual(self.civilization.get_amount(CURRENCY), SOME)

    def test_an_amount_that_is_negative_or_not_a_whole_number_is_refused_and_nothing_changes(self):
        self.civilization.add(resource=CURRENCY, amount=SOME)
        self.civilization.set_action_points(A_FEW_POINTS)
        self.civilization.set_bankrupt_turns(A_FEW_TURNS)
        for amount in NOT_AMOUNTS:
            with self.subTest(amount=amount):
                expected = ERR_AMOUNT.format(value=amount)
                self.assertEqual(self.refused(lambda: self.civilization.add(resource=CURRENCY, amount=amount)), expected)
                self.assertEqual(self.refused(lambda: self.civilization.pay(resource=CURRENCY, amount=amount)), expected)
                self.assertEqual(self.refused(lambda: self.civilization.set_action_points(amount)), expected)
                self.assertEqual(self.refused(lambda: self.civilization.set_bankrupt_turns(amount)), expected)
                self.assertEqual(self.refused(lambda: self.civilization.set_research(amount)), expected)
        self.assertEqual(self.civilization.get_amount(CURRENCY), SOME)
        self.assertEqual(self.civilization.get_action_points(), A_FEW_POINTS)
        self.assertEqual(self.civilization.get_bankrupt_turns(), A_FEW_TURNS)

    def test_a_civilization_is_bankrupt_while_it_counts_bankrupt_turns(self):
        self.civilization.set_bankrupt_turns(A_FEW_TURNS)
        self.assertTrue(self.civilization.is_bankrupt())
        self.civilization.set_bankrupt_turns(NONE)
        self.assertFalse(self.civilization.is_bankrupt())

    def test_a_civilization_knows_the_technologies_it_has_learnt(self):
        self.civilization.learn(FARMING)
        self.assertTrue(self.civilization.knows(FARMING))
        self.assertFalse(self.civilization.knows(CLUBS))
        self.civilization.learn(CLUBS)
        self.civilization.learn(FARMING)
        self.assertEqual(self.civilization.get_technologies(), [CLUBS, FARMING])

    def test_a_civilization_is_at_war_with_those_it_declared_war_on(self):
        self.civilization.declare_war(ANOTHER_NEIGHBOR)
        self.assertTrue(self.civilization.is_at_war_with(ANOTHER_NEIGHBOR))
        self.assertFalse(self.civilization.is_at_war_with(A_NEIGHBOR))
        self.civilization.declare_war(A_NEIGHBOR)
        self.civilization.declare_war(A_NEIGHBOR)
        self.assertEqual(self.civilization.get_wars(), [A_NEIGHBOR, ANOTHER_NEIGHBOR])

    def test_a_civilization_that_loses_has_lost(self):
        self.civilization.lose()
        self.assertTrue(self.civilization.has_lost())

    def every_fact(self, civilization):
        return (
            civilization.get_name(), civilization.get_holdings(), civilization.get_technologies(), civilization.get_researching(), civilization.get_research(),
            civilization.get_action_points(),
            civilization.get_bankrupt_turns(), civilization.get_wars(), civilization.has_lost(),
        )

    def a_busy_civilization(self):
        self.civilization.add(resource=CURRENCY, amount=SOME)
        self.civilization.add(resource=STONE, amount=MORE)
        self.civilization.learn(CLUBS)
        self.civilization.set_researching(FARMING)
        self.civilization.set_research(MORE)
        self.civilization.set_action_points(A_FEW_POINTS)
        self.civilization.set_bankrupt_turns(A_FEW_TURNS)
        self.civilization.declare_war(A_NEIGHBOR)
        self.civilization.lose()
        return self.civilization

    def test_a_civilization_comes_back_from_a_saved_game_as_it_was(self):
        new = Civilization.from_data(through_json(Civilization(A_NAME).to_data()))
        self.assertEqual(self.every_fact(new), self.every_fact(Civilization(A_NAME)))
        busy = self.a_busy_civilization()
        loaded = Civilization.from_data(through_json(busy.to_data()))
        self.assertEqual(self.every_fact(loaded), self.every_fact(busy))
        self.assertNotEqual(self.every_fact(loaded), self.every_fact(new))

    def test_a_later_version_can_renumber_what_a_civilization_holds_and_knows(self):
        busy = self.a_busy_civilization()
        busy.renumber(category=Category.RESOURCES, numbers=LATER_RESOURCES)
        busy.renumber(category=Category.TECHNOLOGIES, numbers=LATER_TECHNOLOGIES)
        self.assertEqual(busy.get_holdings(), {STONE: SOME, CURRENCY: MORE})
        self.assertEqual(busy.get_technologies(), [FARMING])
        self.assertEqual(busy.get_researching(), CLUBS)
        busy.renumber(category=Category.UNITS, numbers=ONLY_CURRENCY)
        self.assertEqual(busy.get_holdings(), {STONE: SOME, CURRENCY: MORE})

    def test_renumbering_an_id_the_later_version_does_not_know_is_refused(self):
        busy = self.a_busy_civilization()
        expected = ERR_UNKNOWN_ID.format(known=sorted(ONLY_CURRENCY))
        self.assertEqual(self.refused(lambda: busy.renumber(category=Category.RESOURCES, numbers=ONLY_CURRENCY)), expected)
        self.assertEqual(self.refused(lambda: busy.renumber(category=Category.TECHNOLOGIES, numbers=ONLY_CURRENCY)), expected)
