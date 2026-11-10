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

"""The computer player: a whole game of caveman played by two computer players, and how the traits tip its decisions."""

import time
import unittest

from caveman_game import FIRST_CIVILIZATION, THE_WORLD, computer_played_caveman_game, play_turns
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.players.computer_player import ComputerPlayer, distance, ring
from microsponge.engine.players.traits import BOLDNESS, EXPANSION, LEAST, LOGICAL, MIDDLE, MOST, PEACE, TRAITS
from microsponge.engine.units.unit_control import UnitControl
from microsponge.themes.caveman.buildings import ArrangementOfRocks
from microsponge.themes.caveman.player import CavemanPlayer
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import CaptainCaveman, Settler, Warrior

FIRST = FIRST_CIVILIZATION
SECOND = FIRST + 1
A_SEED = 7
TURNS = 60
LONG_GAME = 100
# A turn of two computer players on the test world should take far less than this, in seconds.
SLOW = 0.1
EVERYTHING_MIDDLE = {trait: MIDDLE for trait in TRAITS}
EXPANDING = {**EVERYTHING_MIDDLE, EXPANSION: MOST, PEACE: MOST}
STAYING = {**EVERYTHING_MIDDLE, EXPANSION: LEAST, PEACE: MOST}
WARLIKE = {**EVERYTHING_MIDDLE, PEACE: LEAST}
PACIFIST = {**EVERYTHING_MIDDLE, PEACE: MOST}
A_TILE = (10, 10)


class TestComputerPlayer(unittest.TestCase):

    def test_caveman_has_a_player_whose_kinds_are_cavemans(self):
        self.assertIs(Caveman.PLAYER, CavemanPlayer)
        self.assertTrue(issubclass(CavemanPlayer, ComputerPlayer))
        for kind in (*CavemanPlayer.DEFENDERS, *CavemanPlayer.ATTACKERS):
            self.assertIn(kind, Caveman.UNITS)
        for kind in CavemanPlayer.ECONOMY:
            self.assertIn(kind, Caveman.BUILDINGS)
        for technology in (*CavemanPlayer.SCIENCE_RESEARCH, *CavemanPlayer.MILITARY_RESEARCH):
            self.assertIn(technology, Caveman.TECHNOLOGIES)

    def test_two_computer_players_play_a_whole_game_founding_cities_researching_and_building_units_quickly(self):
        game = computer_played_caveman_game(seed=A_SEED)
        started = time.perf_counter()
        play_turns(game=game, turns=TURNS)
        seconds = time.perf_counter() - started
        self.assertEqual(game.get_turn(), TURNS)
        self.assertLess(seconds / TURNS, SLOW)
        for civilization in (FIRST, SECOND):
            with self.subTest(civilization=civilization):
                holder = game.get_civilization(civilization)
                self.assertGreaterEqual(len(game.get_cities_of(civilization)), 1)
                self.assertEqual(game.get_city(game.get_cities_of(civilization)[0]).get_founded(), 0)
                self.assertTrue(holder.get_technologies())
                self.assertTrue(Sight.units_of(game=game, civilization=civilization))
                self.assertGreater(len([city for city in game.get_cities_of(civilization) if game.get_city(city).get_units()]), 0)

    def test_the_same_seed_plays_the_same_game_again(self):
        first = computer_played_caveman_game(seed=A_SEED)
        second = computer_played_caveman_game(seed=A_SEED)
        play_turns(game=first, turns=TURNS)
        play_turns(game=second, turns=TURNS)
        self.assertEqual([city.get_name() for city in first.get_cities()], [city.get_name() for city in second.get_cities()])
        self.assertEqual(first.get_units().count(), second.get_units().count())
        self.assertEqual(first.get_civilization(FIRST).get_traits().get_values(), second.get_civilization(FIRST).get_traits().get_values())

    def test_a_player_that_favors_expansion_founds_more_cities_than_one_that_never_does(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(EXPANDING, STAYING))
        play_turns(game=game, turns=LONG_GAME)
        self.assertGreater(len(game.get_cities_of(FIRST)), 1)
        self.assertEqual(len(game.get_cities_of(SECOND)), 1)
        self.assertFalse(any(ComputerPlayer.is_settler(game=game, unit=unit) for unit in Sight.units_of(game=game, civilization=SECOND)))

    def test_a_player_that_values_peace_never_declares_war_and_one_that_does_not_declares_it_once_its_army_is_ready(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(PACIFIST, PACIFIST))
        play_turns(game=game, turns=LONG_GAME)
        self.assertEqual(game.get_civilization(FIRST).get_wars(), [])
        game = computer_played_caveman_game(seed=A_SEED, traits=(WARLIKE, WARLIKE))
        play_turns(game=game, turns=LONG_GAME)
        self.assertEqual(game.get_civilization(FIRST).get_wars(), [SECOND])

    def test_boldness_decides_an_attack_below_a_sure_win(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=({**EVERYTHING_MIDDLE, BOLDNESS: LEAST}, {**EVERYTHING_MIDDLE, BOLDNESS: MOST}))
        x, y = A_TILE
        weak = UnitControl.place(game=game, kind=Warrior, owner=FIRST, world=THE_WORLD, x=x, y=y)
        strong = UnitControl.place(game=game, kind=CaptainCaveman, owner=SECOND, world=THE_WORLD, x=x + 1, y=y)
        self.assertFalse(CavemanPlayer.worth_attacking(game=game, unit=weak, other=strong, civilization=FIRST))
        self.assertTrue(CavemanPlayer.worth_attacking(game=game, unit=strong, other=weak, civilization=SECOND))
        bold_weak = UnitControl.place(game=game, kind=Warrior, owner=SECOND, world=THE_WORLD, x=x + 2, y=y)
        self.assertTrue(CavemanPlayer.worth_attacking(game=game, unit=bold_weak, other=weak, civilization=SECOND))

    def test_a_city_whose_build_is_blocked_is_told_to_build_something_else(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(LOGICAL, LOGICAL))
        CavemanPlayer.play_turn(game=game, civilization=FIRST)
        CavemanPlayer.play_turn(game=game, civilization=SECOND)
        city = game.get_cities_of(FIRST)[0]
        rocks = Production.item_of(game=game, kind=ArrangementOfRocks)
        self.assertFalse(CavemanPlayer.can_pay_a_part(game=game, civilization=FIRST, kind=ArrangementOfRocks))
        self.assertIsNot(CavemanPlayer.choose_build(game=game, city=city, civilization=FIRST), ArrangementOfRocks)
        Production.switch(game=game, city=city, kind=ArrangementOfRocks)
        play_turns(game=game, turns=game.get_turn() + 2)
        self.assertNotIn(rocks, game.get_city(city).get_queue())
        self.assertFalse(game.get_city(city).is_blocked())

    def test_a_settler_looks_for_the_nearest_site_it_remembers_and_explores_toward_the_nearest_tile_never_seen(self):
        game = computer_played_caveman_game(seed=A_SEED, traits=(LOGICAL, LOGICAL))
        settler = [unit for unit in Sight.units_of(game=game, civilization=FIRST) if ComputerPlayer.is_settler(game=game, unit=unit)][0]
        world, x, y = UnitControl.tile_of(game=game, unit=settler)
        self.assertEqual(CavemanPlayer.nearest_site(game=game, unit=settler, civilization=FIRST), (x, y))
        unseen = CavemanPlayer.nearest_unseen(game=game, unit=settler, civilization=FIRST)
        self.assertFalse(game.get_civilization(FIRST).get_memory(THE_WORLD).has_seen(x=unseen[0], y=unseen[1]))
        self.assertEqual(distance(world=game.get_world(THE_WORLD), from_x=x, from_y=y, to_x=unseen[0], to_y=unseen[1]), Settler.VISION + 1)
        self.assertEqual(len(ring(x=x, y=y, reach=1)), 8)
        self.assertEqual(len(ring(x=x, y=y, reach=3)), 24)
        self.assertIsNone(CityControl.problem_with_site(game=game, tiles=game.get_civilization(FIRST).get_memory(THE_WORLD), x=x, y=y))
        self.assertIsNotNone(CityControl.problem_with_site(game=game, tiles=game.get_civilization(FIRST).get_memory(THE_WORLD), x=unseen[0], y=unseen[1]))
