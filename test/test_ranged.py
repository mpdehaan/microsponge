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

"""Weight classes, bonuses versus a class of unit, a weight class or a unit inside a city, units that cannot attack cities, ranged attacks, and the losses counted four ways."""

import unittest

from caveman_game import FIRST_CIVILIZATION, SETTLER_TILES, THE_WORLD, found_village, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.dice import Dice
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit, armor_against, attack_dice
from microsponge.engine.kinds.weight import Versus, Weight
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.combat import Tally
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.err_messages import ERR_CANNOT_ATTACK_CITIES, ERR_NO_MELEE, ERR_NO_RANGED, ERR_NOT_IN_SIGHT, ERR_OUT_OF_RANGE
from microsponge.themes.caveman.theme import Caveman

FIRST = FIRST_CIVILIZATION
SECOND = FIRST + 1
A_NAME = 'Bedrock'
ROW = 2
COLUMN = 20
NO_POINTS = 0
TOUGH = 1000
WEAK = 1


def fixed(roll):
    """Return dice that always roll a number."""
    return Dice(count=0, sides=0, plus=roll)


class Brute(LandUnit):
    """A heavy land unit with a melee attack, whose armor is better versus light units."""

    WEIGHT = Weight.HEAVY
    ATTACK = fixed(6)
    ARMOR_BONUS_AGAINST = {Weight.LIGHT: 2}
    HIT_POINTS = 20


class Pincher(LandUnit):
    """A light land unit whose melee attack rolls an extra die versus heavy units and versus units inside a city."""

    ATTACK = Dice(count=1, sides=6)
    EXTRA_DICE = {Weight.HEAVY: 1, Versus.IN_CITY: 2}
    HIT_POINTS = 10


class Lobber(LandUnit):
    """A land unit with only a ranged attack, of 3 tiles, which never strikes back, and which sees only the tiles next to it."""

    RANGED_ATTACK = Dice(count=2, sides=6)
    RANGE = 3
    VISION = 1
    RANGED_EXTRA_DICE = {Versus.IN_CITY: 1}
    STRIKES_BACK = False
    TAKES_CITIES = False


class Archer(LandUnit):
    """A land unit with a melee attack and a ranged attack of 2 tiles."""

    ATTACK = fixed(4)
    RANGED_ATTACK = fixed(3)
    RANGE = 2
    HIT_POINTS = 10


class Gull(AirUnit):
    """An air unit that cannot attack the units inside a city."""

    ATTACK = fixed(4)
    ATTACKS_CITIES = False


VERSUS_CAVEMAN = later_caveman({Category.UNITS: (*Caveman.UNITS, Brute, Pincher, Lobber, Archer, Gull)})


class TestVersus(unittest.TestCase):

    def test_extra_dice_are_rolled_versus_a_weight_class_and_a_unit_inside_a_city(self):
        self.assertEqual(attack_dice(kind=Pincher, target=Pincher), Pincher.ATTACK)
        self.assertEqual(attack_dice(kind=Pincher, target=Brute), Pincher.ATTACK.with_extra(dice=1))
        self.assertEqual(attack_dice(kind=Pincher, target=Brute, in_city=True), Pincher.ATTACK.with_extra(dice=3))
        self.assertEqual(attack_dice(kind=Lobber, target=Brute, in_city=True, ranged=True), Lobber.RANGED_ATTACK.with_extra(dice=1))
        self.assertEqual(attack_dice(kind=Lobber, target=Brute, ranged=True), Lobber.RANGED_ATTACK)

    def test_an_armor_bonus_versus_a_weight_class_makes_the_damage_less(self):
        self.assertEqual(armor_against(defender=Brute, attacker=Pincher), 2)
        self.assertEqual(armor_against(defender=Brute, attacker=Brute), 0)
        self.assertLess(UnitControl.damage(attacker=Archer, defender=Brute), UnitControl.damage(attacker=Brute, defender=Brute) * Archer.ATTACK.plus // Brute.ATTACK.plus + 1)
        self.assertEqual(Weight.LIGHT, LandUnit.WEIGHT)


class FightCase(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game(theme=VERSUS_CAVEMAN)
        Orders.declare_war(game=self.game, civilization=FIRST, on=SECOND)
        self.units = self.game.get_units()

    def place(self, *, kind, civilization, x, y):
        unit = UnitControl.place(game=self.game, kind=kind, owner=civilization, world=THE_WORLD, x=x, y=y)
        Sight.refresh(game=self.game, civilization=FIRST)
        return unit

    def hit_points(self, unit):
        return self.units.get_value(column=UnitColumn.HIT_POINTS, unit=unit)

    def tally(self, *, civilization, tally):
        catalog = self.game.get_catalog()
        return {catalog.get_kind(category=Category.UNITS, kind_id=kind): count for kind, count in self.game.get_civilization(civilization).get_tally(tally).items()}


class TestWhatCanBeAttacked(FightCase):

    def test_a_kind_with_no_melee_attack_cannot_make_one(self):
        lobber = self.place(kind=Lobber, civilization=FIRST, x=COLUMN, y=ROW)
        self.place(kind=Brute, civilization=SECOND, x=COLUMN + 1, y=ROW)
        self.assertEqual(self.refused(lambda: Orders.attack(game=self.game, unit=lobber, x=COLUMN + 1, y=ROW)), ERR_NO_MELEE.format(unit=shown_name(Lobber)))

    def test_a_kind_that_does_not_attack_cities_cannot_attack_the_units_inside_one(self):
        city = found_village(game=self.game, civilization=SECOND, name=A_NAME)
        x, y = SETTLER_TILES[1]
        defender = self.place(kind=Brute, civilization=SECOND, x=x, y=y + 3)
        CityControl.enter(game=self.game, unit=defender, city=city)
        gull = self.place(kind=Gull, civilization=FIRST, x=x + 3, y=y)
        message = self.refused(lambda: Orders.attack(game=self.game, unit=gull, x=x + 2, y=y))
        self.assertEqual(message, ERR_CANNOT_ATTACK_CITIES.format(unit=shown_name(Gull), city=Caveman.CITY.NAME))


class TestRangedAttacks(FightCase):

    def test_a_ranged_attack_reaches_its_range_ends_the_turn_draws_no_strike_back_from_a_unit_that_cannot_reach_and_counts(self):
        archer = self.place(kind=Archer, civilization=FIRST, x=COLUMN, y=ROW)
        brute = self.place(kind=Brute, civilization=SECOND, x=COLUMN + Archer.RANGE, y=ROW)
        outcome = Orders.ranged_attack(game=self.game, unit=archer, x=COLUMN + Archer.RANGE, y=ROW)
        self.assertEqual(outcome.defender, brute)
        self.assertEqual(outcome.strike_back, 0)
        self.assertEqual(self.hit_points(brute), Brute.HIT_POINTS - outcome.damage)
        self.assertEqual(self.units.get_value(column=UnitColumn.ACTION_POINTS, unit=archer), NO_POINTS)
        self.assertEqual(self.tally(civilization=FIRST, tally=Tally.ATTACKS), {Archer: 1})

    def test_a_unit_whose_ranged_attack_reaches_the_attacker_strikes_back(self):
        archer = self.place(kind=Archer, civilization=FIRST, x=COLUMN, y=ROW)
        other = self.place(kind=Archer, civilization=SECOND, x=COLUMN + Archer.RANGE, y=ROW)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=other, value=TOUGH)
        outcome = Orders.ranged_attack(game=self.game, unit=archer, x=COLUMN + Archer.RANGE, y=ROW)
        self.assertEqual(outcome.striker, other)
        self.assertGreater(outcome.strike_back, 0)

    def test_a_ranged_attack_is_refused_without_one_beyond_the_range_and_out_of_sight(self):
        brute = self.place(kind=Brute, civilization=FIRST, x=COLUMN, y=ROW)
        archer = self.place(kind=Archer, civilization=FIRST, x=COLUMN, y=ROW + 1)
        self.place(kind=Brute, civilization=SECOND, x=COLUMN + Archer.RANGE + 1, y=ROW + 1)
        self.assertEqual(self.refused(lambda: Orders.ranged_attack(game=self.game, unit=brute, x=COLUMN + 1, y=ROW)), ERR_NO_RANGED.format(unit=shown_name(Brute)))
        message = self.refused(lambda: Orders.ranged_attack(game=self.game, unit=archer, x=COLUMN + Archer.RANGE + 1, y=ROW + 1))
        self.assertEqual(message, ERR_OUT_OF_RANGE.format(unit=shown_name(Archer), range=Archer.RANGE))


    def test_a_ranged_attack_is_refused_on_a_tile_its_civilization_does_not_see(self):
        lobber = self.place(kind=Lobber, civilization=FIRST, x=COLUMN, y=ROW)
        self.place(kind=Brute, civilization=SECOND, x=COLUMN + Lobber.RANGE, y=ROW)
        self.assertFalse(Sight.view(game=self.game, civilization=FIRST).can_see(world=THE_WORLD, x=COLUMN + Lobber.RANGE, y=ROW))
        self.assertEqual(self.refused(lambda: Orders.ranged_attack(game=self.game, unit=lobber, x=COLUMN + Lobber.RANGE, y=ROW)), ERR_NOT_IN_SIGHT.format(unit=shown_name(Lobber)))

    def test_a_ranged_attack_never_takes_a_city_and_rolls_its_extra_dice_versus_the_units_inside(self):
        city = found_village(game=self.game, civilization=SECOND, name=A_NAME)
        x, y = SETTLER_TILES[1]
        defender = self.place(kind=Brute, civilization=SECOND, x=x, y=y + 3)
        CityControl.enter(game=self.game, unit=defender, city=city)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=defender, value=WEAK)
        self.place(kind=Archer, civilization=FIRST, x=x + Lobber.RANGE, y=y + 1)
        lobber = self.place(kind=Lobber, civilization=FIRST, x=x + Lobber.RANGE, y=y)
        outcome = Orders.ranged_attack(game=self.game, unit=lobber, x=x, y=y)
        self.assertTrue(outcome.defender_killed)
        self.assertEqual(self.game.get_city(city).get_owner(), SECOND)
        self.assertEqual(self.tally(civilization=FIRST, tally=Tally.CITY_ATTACKS), {Lobber: 1})
        self.assertEqual(self.tally(civilization=SECOND, tally=Tally.LOST_DEFENDING_CITY), {Brute: 1})


class TestLosses(FightCase):

    def test_a_unit_lost_attacking_in_the_field_and_one_lost_defending_in_the_field_are_counted_apart(self):
        attacker = self.place(kind=Pincher, civilization=FIRST, x=COLUMN, y=ROW)
        defender = self.place(kind=Archer, civilization=SECOND, x=COLUMN + 1, y=ROW)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=attacker, value=WEAK)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=defender, value=TOUGH)
        Orders.attack(game=self.game, unit=attacker, x=COLUMN + 1, y=ROW)
        self.assertEqual(self.tally(civilization=FIRST, tally=Tally.LOST_ATTACKING_FIELD), {Pincher: 1})
        other = self.place(kind=Pincher, civilization=FIRST, x=COLUMN, y=ROW)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=defender, value=WEAK)
        Orders.attack(game=self.game, unit=other, x=COLUMN + 1, y=ROW)
        self.assertEqual(self.tally(civilization=SECOND, tally=Tally.LOST_DEFENDING_FIELD), {Archer: 1})
        self.assertEqual(Domain.LAND, Archer.DOMAIN)
