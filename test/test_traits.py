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

"""The traits of a computer-played civilization: their numbers, how they are dealt, and how they are kept."""

import os
import random
import tempfile
import unittest

from caveman_game import game_facts, started_caveman_game
from refusals import Refusals
from microsponge.engine.players.traits import (
    AGGRESSIVE_HYPERFOCUS, BOLDNESS, CAMPAIGNER, LEAST, LEAST_DEALT_PERCENT, LOGICAL, MOST, MOST_DEALT_PERCENT, NUDGE, PEACEFUL_BUILDER, SCIENCE, TENDENCIES,
    TRAITS, WHOLE, Traits,
)
from microsponge.engine.saving.saved_game import load_game, save_game
from microsponge.err_messages import ERR_NO_SUCH_TRAIT, ERR_TRAIT_VALUE
from microsponge.themes import THEMES

FIRST = 1
SECOND = 2
A_SEED = 11
DRAWS = 200
DEALS = 20
NO_SUCH_TRAIT = 'tidiness'
SAVED_GAME = 'traits.json'


class TestTraits(Refusals, unittest.TestCase):

    def test_there_are_eight_traits_each_a_whole_number_from_0_to_100_and_nothing_else_is_accepted(self):
        self.assertEqual(len(TRAITS), 8)
        traits = Traits({BOLDNESS: 70})
        self.assertEqual(traits.get(BOLDNESS), 70)
        self.assertEqual(traits.get(SCIENCE), LEAST)
        traits.set(trait=SCIENCE, value=MOST)
        self.assertEqual(traits.get_values(), {**{trait: LEAST for trait in TRAITS}, BOLDNESS: 70, SCIENCE: MOST})
        self.assertEqual(traits.total(), 70 + MOST)
        self.assertEqual(self.refused(lambda: traits.set(trait=BOLDNESS, value=MOST + 1)), ERR_TRAIT_VALUE.format(least=LEAST, most=MOST, value=MOST + 1))
        self.assertEqual(self.refused(lambda: traits.set(trait=BOLDNESS, value=-1)), ERR_TRAIT_VALUE.format(least=LEAST, most=MOST, value=-1))
        self.assertEqual(self.refused(lambda: traits.set(trait=BOLDNESS, value=7.5)), ERR_TRAIT_VALUE.format(least=LEAST, most=MOST, value=7.5))
        self.assertEqual(self.refused(lambda: traits.get(NO_SUCH_TRAIT)), ERR_NO_SUCH_TRAIT.format(trait=NO_SUCH_TRAIT))
        self.assertEqual(self.refused(lambda: Traits({NO_SUCH_TRAIT: 1})), ERR_NO_SUCH_TRAIT.format(trait=NO_SUCH_TRAIT))

    def test_dealt_traits_hold_40_to_60_percent_of_all_the_points_there_could_be_with_no_trait_above_100_and_the_same_seed_deals_the_same(self):
        could_hold = MOST * len(TRAITS)
        for deal in range(DEALS):
            with self.subTest(deal=deal):
                traits = Traits.dealt(random.Random(A_SEED + deal))
                self.assertGreaterEqual(traits.total(), could_hold * LEAST_DEALT_PERCENT // WHOLE)
                self.assertLessEqual(traits.total(), could_hold * MOST_DEALT_PERCENT // WHOLE)
                self.assertTrue(all(LEAST <= value <= MOST for value in traits.get_values().values()))
        self.assertEqual(Traits.dealt(random.Random(A_SEED)).get_values(), Traits.dealt(random.Random(A_SEED)).get_values())
        self.assertNotEqual(Traits.dealt(random.Random(A_SEED)).get_values(), Traits.dealt(random.Random(A_SEED + 1)).get_values())

    def test_a_named_tendency_is_nudged_a_little_each_way_and_stays_within_the_scale(self):
        self.assertEqual(len(TENDENCIES), 3)
        self.assertGreater(CAMPAIGNER[AGGRESSIVE_HYPERFOCUS], LOGICAL[AGGRESSIVE_HYPERFOCUS])
        self.assertGreater(LOGICAL[SCIENCE], CAMPAIGNER[SCIENCE])
        for tendency in TENDENCIES:
            for deal in range(DEALS):
                with self.subTest(tendency=tendency, deal=deal):
                    traits = Traits.tending_to(tendency=tendency, random=random.Random(A_SEED + deal))
                    for trait, value in traits.get_values().items():
                        self.assertLessEqual(abs(value - tendency[trait]), NUDGE)
                        self.assertTrue(LEAST <= value <= MOST)
        peaceful = Traits.tending_to(tendency=PEACEFUL_BUILDER, random=random.Random(A_SEED))
        self.assertGreater(peaceful.get(BOLDNESS), LEAST)

    def test_a_trait_wins_a_draw_as_often_as_its_number_says_never_at_0_and_always_at_100(self):
        never = Traits({BOLDNESS: LEAST})
        always = Traits({BOLDNESS: MOST})
        source = random.Random(A_SEED)
        self.assertFalse(any(never.favors(trait=BOLDNESS, random=source) for _ in range(DRAWS)))
        self.assertTrue(all(always.favors(trait=BOLDNESS, random=source) for _ in range(DRAWS)))
        half = Traits({BOLDNESS: MOST // 2})
        wins = sum(half.favors(trait=BOLDNESS, random=source) for _ in range(DRAWS))
        self.assertTrue(DRAWS // 4 < wins < DRAWS * 3 // 4)

    def test_a_civilization_with_traits_is_computer_played_and_keeps_them_through_the_saved_game(self):
        game = started_caveman_game()
        first = game.get_civilization(FIRST)
        second = game.get_civilization(SECOND)
        self.assertFalse(first.is_computer_played())
        self.assertIsNone(first.get_traits())
        first.set_traits(Traits(CAMPAIGNER))
        self.assertTrue(first.is_computer_played())
        self.assertFalse(second.is_computer_played())
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, SAVED_GAME)
            save_game(game=game, path=path)
            loaded = load_game(path=path, themes=THEMES)
        self.assertEqual(game_facts(loaded), game_facts(game))
        self.assertEqual(loaded.get_civilization(FIRST).get_traits().get_values(), CAMPAIGNER)
        self.assertIsNone(loaded.get_civilization(SECOND).get_traits())
