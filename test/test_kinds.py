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

"""The kinds a theme defines, and the catalog that numbers them."""

import unittest

from later_caveman import EXTENDED_CAVEMAN, REORDERED_CAVEMAN, SETTLERLESS_CAVEMAN, later_caveman
from refusals import Refusals
from microsponge.engine.kinds.catalog import NOTHING, Catalog, renumbered
from microsponge.engine.kinds.category import CATEGORIES, Category, shown_category
from microsponge.engine.kinds.kind import saved_name, shown_name
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.err_messages import ERR_KIND_GONE, ERR_KIND_TWICE, ERR_NO_SUCH_KIND_ID, ERR_NOT_IN_THEME, ERR_SETTLER_REQUIRES, ERR_UNKNOWN_ID
from microsponge.themes.caveman.buildings import GreatCavePainting
from microsponge.themes.caveman.resources import Food
from microsponge.themes.caveman.technologies import Clubs
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Warrior
from microsponge.themes.classic.units import Phalanx

FIRST_ID = 1
SAVED_NAME = 'GreatCavePainting'
SHOWN_NAME = 'great cave painting'
NOT_AN_ID = 'one'
AN_ID_NOBODY_SAVED = 99


class FedSettler(SettlerUnit):
    """A settler that costs a resource, as a settler may."""

    COST = {Food: 1}


class TaughtSettler(SettlerUnit):
    """A settler that wrongly needs a technology."""

    REQUIRES = (Clubs,)


def ids_in_order(kinds):
    """Return the id each kind of a theme's list should get: its place, counted from 1."""
    return {kind: place + FIRST_ID for place, kind in enumerate(kinds)}


class TestKindNames(unittest.TestCase):

    def test_a_saved_game_calls_a_kind_by_its_class_name(self):
        self.assertEqual(saved_name(GreatCavePainting), SAVED_NAME)

    def test_people_read_a_kind_as_the_words_of_its_class_name(self):
        self.assertEqual(shown_name(GreatCavePainting), SHOWN_NAME)


class TestCatalog(Refusals, unittest.TestCase):

    def setUp(self):
        self.catalog = Catalog(Caveman)

    def test_the_catalog_knows_its_theme(self):
        self.assertIs(self.catalog.get_theme(), Caveman)

    def test_ids_count_from_one_in_the_order_the_theme_lists_its_kinds(self):
        for category in CATEGORIES:
            for kind, kind_id in ids_in_order(getattr(Caveman, category)).items():
                with self.subTest(category=category, kind=kind):
                    self.assertEqual(self.catalog.get_id(category=category, kind=kind), kind_id)
                    self.assertIs(self.catalog.get_kind(category=category, kind_id=kind_id), kind)

    def test_the_kinds_of_a_category_are_indexed_by_id_with_no_kind_at_nothing(self):
        self.assertEqual(self.catalog.get_kinds(Category.UNITS), (None, *Caveman.UNITS))
        self.assertEqual(self.catalog.get_kinds(Category.UNITS)[FIRST_ID], Settler)

    def test_an_id_that_is_not_a_kinds_is_refused(self):
        for kind_id in (NOTHING, len(Caveman.UNITS) + FIRST_ID, -FIRST_ID, NOT_AN_ID, None):
            with self.subTest(kind_id=kind_id):
                message = self.refused(lambda: self.catalog.get_kind(category=Category.UNITS, kind_id=kind_id))
                self.assertEqual(message, ERR_NO_SUCH_KIND_ID.format(category=shown_category(Category.UNITS), kind_id=kind_id, theme=saved_name(Caveman)))

    def test_a_kind_the_theme_does_not_list_in_the_category_is_refused(self):
        for kind in (Phalanx, Food, None):
            with self.subTest(kind=kind):
                message = self.refused(lambda: self.catalog.get_id(category=Category.UNITS, kind=kind))
                self.assertEqual(message, ERR_NOT_IN_THEME.format(kind=kind, category=shown_category(Category.UNITS), theme=saved_name(Caveman)))

    def test_a_theme_that_lists_a_kind_twice_is_refused(self):
        twice = later_caveman({Category.UNITS: (Settler, Warrior, Settler)})
        message = self.refused(lambda: Catalog(twice))
        self.assertEqual(message, ERR_KIND_TWICE.format(category=shown_category(Category.UNITS), theme=saved_name(twice), name=saved_name(Settler)))

    def test_a_settler_requires_nothing_and_may_cost_resources(self):
        Catalog(later_caveman({Category.UNITS: (Settler,)}))
        Catalog(later_caveman({Category.UNITS: (FedSettler,)}))
        theme = later_caveman({Category.UNITS: (TaughtSettler,)})
        self.assertEqual(self.refused(lambda: Catalog(theme)), ERR_SETTLER_REQUIRES.format(name=saved_name(TaughtSettler), theme=saved_name(theme)))

    def test_a_saved_game_records_the_name_of_every_id(self):
        names = self.catalog.get_names()
        self.assertEqual(set(names), set(CATEGORIES))
        for category in CATEGORIES:
            expected = {str(kind_id): saved_name(kind) for kind, kind_id in ids_in_order(getattr(Caveman, category)).items()}
            self.assertEqual(names[category], expected)

    def test_names_saved_by_the_same_theme_need_no_renumbering(self):
        names = self.catalog.get_names()
        for category in CATEGORIES:
            self.assertIsNone(self.catalog.renumbering(category=category, saved_names=names[category]))
        self.assertEqual(self.catalog.renumberings(names), dict.fromkeys(CATEGORIES))

    def test_a_kind_added_after_the_others_changes_no_id(self):
        later = Catalog(EXTENDED_CAVEMAN)
        self.assertEqual(later.renumberings(self.catalog.get_names()), dict.fromkeys(CATEGORIES))

    def test_kinds_in_another_order_are_matched_by_name(self):
        later = Catalog(REORDERED_CAVEMAN)
        numbers = later.renumbering(category=Category.UNITS, saved_names=self.catalog.get_names()[Category.UNITS])
        expected = {NOTHING: NOTHING}
        for kind in Caveman.UNITS:
            expected[self.catalog.get_id(category=Category.UNITS, kind=kind)] = later.get_id(category=Category.UNITS, kind=kind)
        self.assertEqual(numbers, expected)
        self.assertNotEqual(expected[FIRST_ID], FIRST_ID)

    def test_a_category_the_saved_game_lacks_changes_nothing(self):
        self.assertEqual(Catalog(REORDERED_CAVEMAN).renumberings({}), dict.fromkeys(CATEGORIES))

    def test_a_saved_kind_the_theme_no_longer_has_is_refused(self):
        later = Catalog(SETTLERLESS_CAVEMAN)
        message = self.refused(lambda: later.renumberings(self.catalog.get_names()))
        self.assertEqual(message, ERR_KIND_GONE.format(name=saved_name(Settler), category=shown_category(Category.UNITS), theme=saved_name(Caveman)))

    def test_renumbering_replaces_each_id_and_refuses_one_it_was_not_given(self):
        numbers = {NOTHING: NOTHING, 1: 2, 2: 1}
        self.assertEqual(renumbered(values=[1, 2, NOTHING, 1], numbers=numbers), [2, 1, NOTHING, 2])
        message = self.refused(lambda: renumbered(values=[1, AN_ID_NOBODY_SAVED], numbers=numbers))
        self.assertEqual(message, ERR_UNKNOWN_ID.format(known=sorted(numbers)))


if __name__ == '__main__':
    unittest.main()
