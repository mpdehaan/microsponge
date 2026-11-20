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

"""Obsolete units: a city cannot build a unit once it can build the unit that made it obsolete, and a unit of an obsolete kind can be upgraded within its civilization's borders."""

import unittest

from caveman_game import FIRST_CIVILIZATION, GRASSLAND_TILE, THE_WORLD, found_village, held, learn, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.production import Production
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.dice import Dice
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.kinds.unit_kinds import LandUnit
from microsponge.engine.orders.order import UpgradeOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.given_order import Reason
from microsponge.engine.orders.thing import city_thing, division_thing
from microsponge.engine.orders.what import NoDetails
from microsponge.engine.players.hand import Hand
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.units.upgrades import Upgrades
from microsponge.err_messages import ERR_NOT_OBSOLETE, ERR_OBSOLETE, ERR_UPGRADE_NOT_BUILDABLE, ERR_UPGRADE_OUTSIDE_BORDERS, ERR_UPGRADE_PRICE
from microsponge.themes.caveman.resources import Currency, Flint
from microsponge.themes.caveman.theme import Caveman

FIRST = FIRST_CIVILIZATION
A_NAME = 'Bedrock'
A_LEVEL = 3
SOME_EXPERIENCE = 40
WHOLE = 100
PLENTY = 10000
# A tile of the first village's radius, as (x, y).
NEAR_TILE = (9, 12)


class Knapping(Technology):
    """The technology the newer kind requires."""


class Bruiser(LandUnit):
    """A newer kind of unit, which makes the older one obsolete."""

    REQUIRES = (Knapping,)
    COST = {Currency: 90}
    ATTACK = Dice(count=3, sides=6)
    HIT_POINTS = 30


class Brawler(LandUnit):
    """An older kind of unit, made obsolete by the bruiser."""

    OBSOLETED_BY = Bruiser
    COST = {Currency: 30}
    ATTACK = Dice(count=1, sides=6)
    HIT_POINTS = 10


class FlintBruiser(LandUnit):
    """A newer kind of unit that requires a strategic resource, which therefore makes nothing obsolete."""

    REQUIRES = (Flint,)
    COST = {Currency: 90}
    ATTACK = Dice(count=3, sides=6)
    HIT_POINTS = 30


class Scrapper(LandUnit):
    """An older kind of unit that names a newer kind requiring a strategic resource."""

    OBSOLETED_BY = FlintBruiser
    COST = {Currency: 30}
    ATTACK = Dice(count=1, sides=6)
    HIT_POINTS = 10


OBSOLETE_CAVEMAN = later_caveman({
    Category.TECHNOLOGIES: (*Caveman.TECHNOLOGIES, Knapping),
    Category.UNITS: (*Caveman.UNITS, Bruiser, Brawler, FlintBruiser, Scrapper),
})


class UpgradesCase(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game(theme=OBSOLETE_CAVEMAN)
        self.city = found_village(game=self.game, civilization=FIRST, name=A_NAME)
        self.first = self.game.get_civilization(FIRST)
        self.currency = self.game.get_catalog().get_id(category=Category.RESOURCES, kind=Currency)
        self.first.add(resource=self.currency, amount=PLENTY)

    def brawler(self, *, tile=NEAR_TILE):
        return UnitControl.place(game=self.game, kind=Brawler, owner=FIRST, world=THE_WORLD, x=tile[0], y=tile[1])


class TestObsoleteUnits(UpgradesCase):

    def test_a_city_cannot_build_a_unit_once_it_can_build_the_unit_that_made_it_obsolete(self):
        self.assertIsNone(Production.problem_queueing(game=self.game, city=self.city, kind=Brawler))
        learn(game=self.game, civilization=FIRST, technology=Knapping)
        expected = ERR_OBSOLETE.format(unit=shown_name(Brawler), name=A_NAME, newer=shown_name(Bruiser))
        self.assertEqual(Production.problem_queueing(game=self.game, city=self.city, kind=Brawler), expected)
        self.assertEqual(self.refused(lambda: Orders.build(game=self.game, city=self.city, kind=Brawler)), expected)

    def test_a_unit_that_requires_a_strategic_resource_makes_nothing_obsolete(self):
        self.assertIsNone(Upgrades.newer_of(Scrapper))
        self.assertIs(Upgrades.newer_of(Brawler), Bruiser)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=self.city, kind=Scrapper))


class TestUpgrading(UpgradesCase):

    def test_an_obsolete_unit_within_the_borders_is_upgraded_for_the_themes_percent_keeping_its_level_experience_and_share_of_hit_points(self):
        learn(game=self.game, civilization=FIRST, technology=Knapping)
        unit = self.brawler()
        units = self.game.get_units()
        units.set_value(column=UnitColumn.LEVEL, unit=unit, value=A_LEVEL)
        units.set_value(column=UnitColumn.EXPERIENCE, unit=unit, value=SOME_EXPERIENCE)
        whole = UnitControl.max_hit_points(game=self.game, unit=unit)
        units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=whole // 2)
        before = held(game=self.game, civilization=FIRST, resource=Currency)
        Orders.upgrade(game=self.game, unit=unit)
        self.assertIs(UnitControl.kind_of(game=self.game, unit=unit), Bruiser)
        self.assertEqual(held(game=self.game, civilization=FIRST, resource=Currency), before - Bruiser.COST[Currency] * OBSOLETE_CAVEMAN.UPGRADE_PERCENT // WHOLE)
        self.assertEqual((units.get_value(column=UnitColumn.LEVEL, unit=unit), units.get_value(column=UnitColumn.EXPERIENCE, unit=unit)), (A_LEVEL, SOME_EXPERIENCE))
        self.assertEqual(units.get_value(column=UnitColumn.HIT_POINTS, unit=unit), whole // 2 * UnitControl.max_hit_points(game=self.game, unit=unit) // whole)

    def test_an_upgrade_is_refused_for_a_kind_nothing_makes_obsolete_before_the_newer_kind_can_be_built_outside_the_borders_and_without_the_price(self):
        unit = self.brawler()
        scrapper = UnitControl.place(game=self.game, kind=Scrapper, owner=FIRST, world=THE_WORLD, x=NEAR_TILE[0], y=NEAR_TILE[1] + 1)
        self.assertEqual(self.refused(lambda: Orders.upgrade(game=self.game, unit=scrapper)), ERR_NOT_OBSOLETE.format(unit=shown_name(Scrapper)))
        self.assertEqual(self.refused(lambda: Orders.upgrade(game=self.game, unit=unit)), ERR_UPGRADE_NOT_BUILDABLE.format(unit=shown_name(Brawler), newer=shown_name(Bruiser)))
        learn(game=self.game, civilization=FIRST, technology=Knapping)
        outside = self.brawler(tile=GRASSLAND_TILE)
        self.assertEqual(self.refused(lambda: Orders.upgrade(game=self.game, unit=outside)), ERR_UPGRADE_OUTSIDE_BORDERS.format(unit=shown_name(Brawler)))
        self.first.pay(resource=self.currency, amount=held(game=self.game, civilization=FIRST, resource=Currency))
        self.assertEqual(self.refused(lambda: Orders.upgrade(game=self.game, unit=unit)), ERR_UPGRADE_PRICE.format(unit=shown_name(Brawler), newer=shown_name(Bruiser)))
        self.assertIs(UnitControl.kind_of(game=self.game, unit=unit), Brawler)

    def test_an_order_to_upgrade_a_division_upgrades_every_unit_it_can_and_is_completed_when_none_is_left_obsolete(self):
        learn(game=self.game, civilization=FIRST, technology=Knapping)
        army = OrderControl.add_army(game=self.game, civilization=FIRST)
        division = OrderControl.add_division(game=self.game, civilization=FIRST, army=army)
        unit = self.brawler()
        division.add_unit(unit)
        me = division_thing(division.get_id())
        order = OrderControl.give(game=self.game, civilization=FIRST, kind=UpgradeOrder, giver=city_thing(self.city), receiver=me, what=NoDetails())
        self.assertEqual(OrderControl.cost(game=self.game, civilization=FIRST, order=order), 0)
        Hand.upgrade(game=self.game, civilization=FIRST)
        self.assertIs(UnitControl.kind_of(game=self.game, unit=unit), Bruiser)
        self.assertEqual(order.get_reason(), Reason.COMPLETED)
