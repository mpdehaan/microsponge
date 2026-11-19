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

"""The helper AI: every order for a unit or a city passes through it to the game, and no player gives the game such an order directly."""

import ast
import inspect
import pathlib
import unittest
from unittest import mock

import microsponge
from caveman_game import settler_of, started_caveman_game
from refusals import Refusals
from microsponge.engine.players import helper_ai
from microsponge.engine.players.helper_ai import HelperAI
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_control import UnitControl

PACKAGE = pathlib.Path(microsponge.__file__).parent
# The files that hold a player: the common computer player, and each theme's own.
MAIN_AI_FILE = PACKAGE / 'engine' / 'players' / 'computer_player.py'
PLAYER_FILES = [MAIN_AI_FILE, PACKAGE / 'engine' / 'players' / 'hand.py', *sorted((PACKAGE / 'themes').glob('*/player.py'))]
# The name the main AI may not use, because the main AI cannot touch a unit or a city: only the Hand asks the helper for single actions.
HELPER_NAME = HelperAI.__name__
# The orders a player gives the game itself, because they are about the civilization as a whole and not about a unit or a city.
CIVILIZATION_ORDERS = {'research', 'declare_war', 'end_turn'}
ORDERS_NAME = 'Orders'
PATCHED = 'Orders'
FIRST = 1
A_NAME = 'Bedrock'
FAR = 5
AN_ANSWER = object()
# An order of the game is for a unit or a city when it takes one of these.
UNIT_OR_CITY = {'unit', 'settler', 'city'}
# What the game's orders are built from and a screen asks before ordering, which are not orders themselves.
NOT_ORDERS = {'owner_of', 'check_points', 'charge', 'step', 'move_cost', 'check_may_enter', 'attack_cost'}
RETURNS = 'return '


def helper_orders():
    """Return the name of every order the helper AI takes."""
    return [name for name, value in vars(HelperAI).items() if isinstance(value, staticmethod)]


def orders_given_directly(path):
    """Return the names of the orders a file gives the game itself, as Orders.name."""
    tree = ast.parse(path.read_text())
    return {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == ORDERS_NAME}


class TestHelperAI(Refusals, unittest.TestCase):

    def test_every_order_of_the_helper_passes_what_it_is_given_to_the_game_and_returns_what_the_game_returns(self):
        self.assertTrue(helper_orders())
        for name in helper_orders():
            with self.subTest(order=name), mock.patch.object(helper_ai, PATCHED) as orders:
                getattr(orders, name).return_value = AN_ANSWER
                given = {parameter: object() for parameter in inspect.signature(getattr(HelperAI, name)).parameters}
                answer = getattr(HelperAI, name)(**given)
                getattr(orders, name).assert_called_once_with(**given)
                self.assertEqual(list(inspect.signature(getattr(Orders, name)).parameters), list(given))
                if inspect.getsource(getattr(Orders, name)).count(RETURNS):
                    self.assertIs(answer, AN_ANSWER)

    def test_the_helper_takes_every_order_of_the_game_for_a_unit_or_a_city(self):
        game_orders = {name for name, value in vars(Orders).items() if isinstance(value, staticmethod) and set(inspect.signature(value.__func__).parameters) & UNIT_OR_CITY}
        self.assertEqual(game_orders - NOT_ORDERS, set(helper_orders()))

    def test_a_unit_moves_and_a_city_is_built_through_the_helper(self):
        game = started_caveman_game()
        settler = settler_of(game=game, civilization=FIRST)
        world, x, y = UnitControl.tile_of(game=game, unit=settler)
        HelperAI.move(game=game, unit=settler, x=x + 1, y=y)
        self.assertEqual(UnitControl.tile_of(game=game, unit=settler), (world, x + 1, y))
        city = HelperAI.found_city(game=game, settler=settler, name=A_NAME)
        self.assertEqual(game.get_city(city).get_name(), A_NAME)

    def test_an_order_the_game_refuses_is_refused_through_the_helper_and_changes_nothing(self):
        game = started_caveman_game()
        settler = settler_of(game=game, civilization=FIRST)
        before = UnitControl.tile_of(game=game, unit=settler)
        world, x, y = before
        self.assertEqual(self.refused(lambda: HelperAI.move(game=game, unit=settler, x=x + FAR, y=y)), self.refused(lambda: Orders.move(game=game, unit=settler, x=x + FAR, y=y)))
        self.assertEqual(UnitControl.tile_of(game=game, unit=settler), before)

    def test_no_player_gives_the_game_an_order_for_a_unit_or_a_city_directly(self):
        self.assertTrue(PLAYER_FILES)
        for path in PLAYER_FILES:
            with self.subTest(path=path.name):
                self.assertLessEqual(orders_given_directly(path), CIVILIZATION_ORDERS)

    def test_the_main_ai_never_asks_for_a_single_action_of_a_unit_or_a_city(self):
        for path in (MAIN_AI_FILE, *sorted((PACKAGE / 'themes').glob('*/player.py'))):
            with self.subTest(path=path.name):
                self.assertNotIn(HELPER_NAME, path.read_text())
