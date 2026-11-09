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

"""A game and its civilizations."""

import unittest

from refusals import Refusals
from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.game.game import FIRST_TURN, MAX_CIVILIZATIONS, Game
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.world.world import World
from microsponge.engine.kinds.kind import saved_name
from microsponge.err_messages import ERR_NO_SUCH_CIVILIZATION, ERR_NO_SUCH_WORLD, ERR_TOO_MANY_CIVILIZATIONS, ERR_TOO_MANY_WORLDS, ERR_TURN
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.scifi.theme import SciFi

A_NAME = 'Ugg'
ANOTHER_NAME = 'Grok'
NAME_TEMPLATE = 'Tribe {number}'
FIRST_CIVILIZATION = 1
FIRST_WORLD = 0
A_TURN = 37
NOT_A_TURN = 'later'
SMALL = 3


class TestGame(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = Game(Caveman)

    def test_a_new_game_is_at_its_first_turn_with_nothing_in_it(self):
        self.assertIs(self.game.get_theme(), Caveman)
        self.assertIs(self.game.get_catalog().get_theme(), Caveman)
        self.assertEqual(self.game.get_turn(), FIRST_TURN)
        self.assertEqual(self.game.get_civilizations(), [])
        self.assertEqual(self.game.get_worlds(), [])
        self.assertEqual(self.game.get_units().count(), 0)

    def test_time_is_counted_in_turns(self):
        self.game.next_turn()
        self.game.next_turn()
        self.assertEqual(self.game.get_turn(), FIRST_TURN + 2)
        self.game.set_turn(A_TURN)
        self.game.next_turn()
        self.assertEqual(self.game.get_turn(), A_TURN + 1)

    def test_a_turn_that_is_negative_or_not_a_whole_number_is_refused(self):
        self.game.set_turn(A_TURN)
        for turn in (FIRST_TURN - 1, NOT_A_TURN, None, 1.5):
            with self.subTest(turn=turn):
                self.assertEqual(self.refused(lambda: self.game.set_turn(turn)), ERR_TURN.format(value=turn))
        self.assertEqual(self.game.get_turn(), A_TURN)

    def test_civilizations_are_numbered_from_one(self):
        first = Civilization(A_NAME)
        second = Civilization(ANOTHER_NAME)
        self.assertEqual(self.game.add_civilization(first), FIRST_CIVILIZATION)
        self.assertEqual(self.game.add_civilization(second), FIRST_CIVILIZATION + 1)
        self.assertIs(self.game.get_civilization(FIRST_CIVILIZATION), first)
        self.assertIs(self.game.get_civilization(FIRST_CIVILIZATION + 1), second)
        self.assertEqual(self.game.get_civilizations(), [first, second])

    def test_an_id_that_is_no_civilization_is_refused(self):
        self.game.add_civilization(Civilization(A_NAME))
        for civilization in (NOTHING, FIRST_CIVILIZATION + 1, -1, A_NAME, None):
            with self.subTest(civilization=civilization):
                self.assertEqual(self.refused(lambda: self.game.get_civilization(civilization)), ERR_NO_SUCH_CIVILIZATION.format(civilization=civilization))

    def test_a_game_has_at_most_seven_civilizations(self):
        for number in range(MAX_CIVILIZATIONS):
            self.game.add_civilization(Civilization(NAME_TEMPLATE.format(number=number)))
        one_too_many = Civilization(A_NAME)
        self.assertEqual(self.refused(lambda: self.game.add_civilization(one_too_many)), ERR_TOO_MANY_CIVILIZATIONS.format(most=MAX_CIVILIZATIONS))
        self.assertEqual(len(self.game.get_civilizations()), MAX_CIVILIZATIONS)

    def test_the_list_of_civilizations_is_a_copy(self):
        self.game.add_civilization(Civilization(A_NAME))
        self.game.get_civilizations().clear()
        self.assertEqual(len(self.game.get_civilizations()), 1)

    def test_a_game_of_a_theme_with_planets_holds_several_worlds_numbered_from_zero(self):
        game = Game(SciFi)
        first = World(width=SMALL, height=SMALL)
        second = World(width=SMALL + 1, height=SMALL)
        self.assertEqual(game.add_world(first), FIRST_WORLD)
        self.assertEqual(game.add_world(second), FIRST_WORLD + 1)
        self.assertIs(game.get_world(FIRST_WORLD), first)
        self.assertIs(game.get_world(FIRST_WORLD + 1), second)
        self.assertEqual(game.get_worlds(), [first, second])

    def test_a_game_holds_no_more_worlds_than_its_theme_allows(self):
        for theme in (Caveman, SciFi):
            with self.subTest(theme=theme):
                game = Game(theme)
                for _ in range(theme.MAX_WORLDS):
                    game.add_world(World(width=SMALL, height=SMALL))
                one_too_many = World(width=SMALL, height=SMALL)
                self.assertEqual(self.refused(lambda: game.add_world(one_too_many)), ERR_TOO_MANY_WORLDS.format(theme=saved_name(theme), most=theme.MAX_WORLDS))
                self.assertEqual(len(game.get_worlds()), theme.MAX_WORLDS)

    def test_an_id_that_is_no_world_is_refused(self):
        self.game.add_world(World(width=SMALL, height=SMALL))
        for world in (FIRST_WORLD + 1, -1, A_NAME, None):
            with self.subTest(world=world):
                self.assertEqual(self.refused(lambda: self.game.get_world(world)), ERR_NO_SUCH_WORLD.format(world=world))


if __name__ == '__main__':
    unittest.main()
