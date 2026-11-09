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

"""Putting units on the map and taking them off, in a game of caveman."""

import unittest

from caveman_game import GRASSLAND_TILE, MOUNTAIN_TILE, SETTLER_TILES, TARPIT_TILE, THE_WORLD, WATER_TILE, WORLD_HEIGHT, WORLD_WIDTH, new_caveman_game
from refusals import Refusals
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category, shown_category
from microsponge.engine.kinds.kind import saved_name, shown_name
from microsponge.engine.kinds.dice import Dice
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.unit_kinds import AirUnit, LandUnit, SeaUnit, SpaceUnit, UnitKind, can_hit
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.levels import LAST_LEVEL, Levels
from microsponge.engine.units.unit_control import BEST_ARMOR_CLASS, CHIP_DAMAGE, NO_DAMAGE, UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.support.numbers import divided_rounding_up
from microsponge.err_messages import ERR_CANNOT_BE_ON, ERR_NO_DOMAIN, ERR_NO_SUCH_CIVILIZATION, ERR_NO_SUCH_UNIT, ERR_NO_SUCH_WORLD, ERR_NOT_IN_THEME, ERR_ROW_OFF_THE_MAP, ERR_TILE_HAS_A_UNIT
from microsponge.themes.caveman.terrains import Grassland, Mountains, Tarpit, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import AngryBird, Raft, Settler, Warrior
from microsponge.themes.classic.units import Phalanx

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
NO_SUCH_CIVILIZATION = 3
NO_SUCH_WORLD = 1
THE_LEAST_DAMAGE = 1
STRIKE_BACK_PERCENT = 50
WHOLE = 100
PERCENT_PER_ARMOR_POINT = 10
NO_ARMOR = 10
HALF_ARMOR = 5
# Every test kind below rolls a fixed number, no dice and a number added, so that the damage is known.
FIXED_WARRIOR_ROLL = 5


def fixed(roll):
    """Return dice that always roll a number."""
    return Dice(count=0, sides=0, plus=roll)


class Mammoth(LandUnit):
    """A strong land unit with good armor, whose strike back at the default percent still hurts a warrior."""

    ATTACK = fixed(50)
    ARMOR_CLASS = 5
    HIT_POINTS = 100


class Hedgehog(LandUnit):
    """A land unit that strikes back with its whole roll."""

    ATTACK = fixed(10)
    STRIKE_BACK_PERCENT = 100


class Tortoise(LandUnit):
    """A land unit that does not strike back."""

    ATTACK = fixed(10)
    STRIKES_BACK = False


class SpearThrower(LandUnit):
    """A land unit that can hit air units."""

    ATTACK = fixed(10)
    CAN_HIT_AIR = True


class Slinger(LandUnit):
    """A land unit with extra dice against air units, which strikes back with its whole roll."""

    ATTACK = Dice(count=1, sides=1, plus=2)
    EXTRA_DICE = {Domain.AIR: 6}
    CAN_HIT_AIR = True
    STRIKE_BACK_PERCENT = 100


class Harpooner(SeaUnit):
    """A sea unit that can hit air units."""

    CAN_HIT_AIR = True


class Comet(SpaceUnit):
    """A space unit."""


class Mystery(UnitKind):
    """A kind of unit that is no class of unit."""


class Canoe(SeaUnit):
    """A naval unit with no attack dice."""


class Pterodactyl(AirUnit):
    """An aerial unit with no attack dice."""


class Boulder(SeaUnit):
    """A kind of unit with armor better than the best, which still lets chip damage through."""

    ARMOR_CLASS = BEST_ARMOR_CLASS - 1


class Pebble(SeaUnit):
    """A kind of unit with the best armor."""

    ARMOR_CLASS = BEST_ARMOR_CLASS


class Clubber(LandUnit):
    """A warrior that always rolls its average, against a warrior's armor."""

    ATTACK = fixed(FIXED_WARRIOR_ROLL)
    ARMOR_CLASS = Warrior.ARMOR_CLASS
    HIT_POINTS = Warrior.HIT_POINTS


class TestUnitControl(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = new_caveman_game()
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)

    def place(self, *, kind, tile, owner=FIRST_CIVILIZATION):
        x, y = tile
        return UnitControl.place(game=self.game, kind=kind, owner=owner, world=THE_WORLD, x=x, y=y)

    def unit_on(self, tile):
        x, y = tile
        return self.world.get_value(layer=Layer.UNIT, x=x, y=y)

    def test_each_civilization_starts_with_one_settler_and_nothing_else(self):
        self.assertEqual(self.units.count(), len(SETTLER_TILES))
        for place, tile in enumerate(SETTLER_TILES):
            unit = self.unit_on(tile)
            self.assertIs(UnitControl.kind_of(game=self.game, unit=unit), Settler)
            self.assertEqual(self.units.get_value(column=UnitColumn.OWNER, unit=unit), place + FIRST_CIVILIZATION)

    def test_a_placed_unit_is_on_its_tile_with_its_kinds_hit_points(self):
        unit = self.place(kind=Warrior, tile=GRASSLAND_TILE, owner=SECOND_CIVILIZATION)
        self.assertEqual(self.unit_on(GRASSLAND_TILE), unit)
        self.assertIs(UnitControl.kind_of(game=self.game, unit=unit), Warrior)
        self.assertEqual(self.units.get_value(column=UnitColumn.OWNER, unit=unit), SECOND_CIVILIZATION)
        self.assertEqual(self.units.get_value(column=UnitColumn.WORLD, unit=unit), THE_WORLD)
        self.assertEqual((self.units.get_value(column=UnitColumn.X, unit=unit), self.units.get_value(column=UnitColumn.Y, unit=unit)), GRASSLAND_TILE)
        self.assertEqual(self.units.get_value(column=UnitColumn.HIT_POINTS, unit=unit), Warrior.HIT_POINTS)

    def test_a_tile_holds_only_one_unit(self):
        self.place(kind=Warrior, tile=GRASSLAND_TILE)
        count = self.units.count()
        x, y = GRASSLAND_TILE
        self.assertEqual(self.refused(lambda: self.place(kind=Settler, tile=GRASSLAND_TILE, owner=SECOND_CIVILIZATION)), ERR_TILE_HAS_A_UNIT.format(x=x, y=y))
        self.assertEqual(self.units.count(), count)

    def test_a_land_unit_can_be_on_land_and_mountains_and_not_on_water(self):
        self.place(kind=Warrior, tile=MOUNTAIN_TILE)
        count = self.units.count()
        self.assertEqual(self.refused(lambda: self.place(kind=Warrior, tile=WATER_TILE)), ERR_CANNOT_BE_ON.format(unit=shown_name(Warrior), terrain=shown_name(Water)))
        self.assertEqual(self.unit_on(WATER_TILE), NOTHING)
        self.assertEqual(self.units.count(), count)

    def test_no_land_unit_or_naval_unit_can_be_on_a_tarpit_and_an_air_unit_can(self):
        for kind in (Warrior, Settler, Raft):
            with self.subTest(kind=kind):
                self.assertEqual(self.refused(lambda: self.place(kind=kind, tile=TARPIT_TILE)), ERR_CANNOT_BE_ON.format(unit=shown_name(kind), terrain=shown_name(Tarpit)))
                self.assertEqual(self.unit_on(TARPIT_TILE), NOTHING)
        bird = self.place(kind=AngryBird, tile=TARPIT_TILE)
        self.assertEqual(self.unit_on(TARPIT_TILE), bird)
        self.assertTrue(UnitControl.can_be_on(kind=AngryBird, terrain=Grassland))
        self.assertTrue(UnitControl.can_be_on(kind=Warrior, terrain=Grassland))

    def test_which_terrain_each_base_of_unit_can_be_on(self):
        expected = {
            (Warrior, Grassland): True, (Warrior, Mountains): True, (Warrior, Water): False,
            (Canoe, Grassland): False, (Canoe, Mountains): False, (Canoe, Water): True,
            (Pterodactyl, Grassland): True, (Pterodactyl, Mountains): True, (Pterodactyl, Water): True,
        }
        for (kind, terrain), allowed in expected.items():
            with self.subTest(kind=kind, terrain=terrain):
                self.assertEqual(UnitControl.can_be_on(kind=kind, terrain=terrain), allowed)

    def test_armor_takes_10_percent_off_a_roll_for_every_point_below_10_rounding_up(self):
        self.assertEqual(UnitControl.mitigated(roll=10, armor_class=NO_ARMOR), 10)
        self.assertEqual(UnitControl.mitigated(roll=10, armor_class=Warrior.ARMOR_CLASS), 10 * Warrior.ARMOR_CLASS * PERCENT_PER_ARMOR_POINT // WHOLE)
        self.assertEqual(UnitControl.mitigated(roll=7, armor_class=HALF_ARMOR), divided_rounding_up(amount=7, by=2))
        self.assertEqual(UnitControl.mitigated(roll=5, armor_class=HALF_ARMOR), 3)
        self.assertEqual(UnitControl.mitigated(roll=10, armor_class=NO_ARMOR + 1), 10)

    def test_the_best_armor_and_better_still_let_chip_damage_through(self):
        self.assertEqual(CHIP_DAMAGE, THE_LEAST_DAMAGE)
        self.assertEqual(UnitControl.mitigated(roll=50, armor_class=BEST_ARMOR_CLASS), CHIP_DAMAGE)
        self.assertEqual(UnitControl.mitigated(roll=50, armor_class=Boulder.ARMOR_CLASS), CHIP_DAMAGE)
        self.assertEqual(UnitControl.mitigated(roll=0, armor_class=NO_ARMOR), CHIP_DAMAGE)
        self.assertEqual(UnitControl.damage(attacker=Warrior, defender=Pebble), CHIP_DAMAGE)
        self.assertEqual(UnitControl.damage(attacker=Settler, defender=Warrior), CHIP_DAMAGE)

    def test_an_attack_on_an_average_roll_deals_the_dice_average_through_the_armor_of_the_unit_attacked(self):
        self.assertEqual(Warrior.ATTACK.average(), FIXED_WARRIOR_ROLL)
        self.assertEqual(UnitControl.damage(attacker=Warrior, defender=Settler), UnitControl.mitigated(roll=FIXED_WARRIOR_ROLL, armor_class=Settler.ARMOR_CLASS))
        self.assertEqual(UnitControl.damage(attacker=Warrior, defender=Warrior), UnitControl.mitigated(roll=FIXED_WARRIOR_ROLL, armor_class=Warrior.ARMOR_CLASS))
        self.assertEqual(UnitControl.damage(attacker=Warrior, defender=Warrior), UnitControl.damage(attacker=Clubber, defender=Clubber))
        self.assertGreater(UnitControl.damage(attacker=Warrior, defender=Warrior), CHIP_DAMAGE)
        self.assertEqual(UnitControl.damage(attacker=Raft, defender=Settler), int(Raft.ATTACK.average()))

    def test_a_kind_can_roll_extra_dice_against_air_units_attacking_and_striking_back(self):
        against_air = Slinger.ATTACK.with_extra(dice=Slinger.EXTRA_DICE[Domain.AIR])
        self.assertEqual(UnitControl.damage(attacker=Slinger, defender=Pterodactyl), UnitControl.mitigated(roll=int(against_air.average()), armor_class=Pterodactyl.ARMOR_CLASS))
        self.assertEqual(UnitControl.damage(attacker=Slinger, defender=Warrior), UnitControl.mitigated(roll=int(Slinger.ATTACK.average()), armor_class=Warrior.ARMOR_CLASS))
        self.assertEqual(UnitControl.damage(attacker=Slinger, defender=Canoe), UnitControl.mitigated(roll=int(Slinger.ATTACK.average()), armor_class=Canoe.ARMOR_CLASS))
        self.assertEqual(UnitControl.strike_back_damage(attacker=Pterodactyl, defender=Slinger), UnitControl.mitigated(roll=int(against_air.average()), armor_class=Pterodactyl.ARMOR_CLASS))
        self.assertEqual(UnitControl.strike_back_damage(attacker=Canoe, defender=Slinger), UnitControl.mitigated(roll=int(Slinger.ATTACK.average()), armor_class=Canoe.ARMOR_CLASS))
        self.assertGreater(against_air.average(), Slinger.ATTACK.average())

    def test_a_kind_with_no_extra_dice_against_air_units_hits_them_with_its_own_dice(self):
        self.assertEqual(SpearThrower.EXTRA_DICE, {})
        self.assertEqual(UnitControl.damage(attacker=SpearThrower, defender=Pterodactyl), UnitControl.mitigated(roll=int(SpearThrower.ATTACK.average()), armor_class=Pterodactyl.ARMOR_CLASS))

    def test_the_attacks_a_kind_needs_against_another_count_a_last_attack_for_the_hit_points_left_over(self):
        damage = UnitControl.damage(attacker=Hedgehog, defender=Warrior)
        self.assertNotEqual(Warrior.HIT_POINTS % damage, 0)
        self.assertEqual(UnitControl.attacks_to_kill(theme=Caveman, attacker=Hedgehog, defender=Warrior), Warrior.HIT_POINTS // damage + 1)
        self.assertEqual(UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Warrior), divided_rounding_up(amount=Warrior.HIT_POINTS, by=UnitControl.damage(attacker=Warrior, defender=Warrior)))
        self.assertEqual(UnitControl.attacks_to_kill(theme=Caveman, attacker=Settler, defender=Warrior), Warrior.HIT_POINTS)

    def test_a_kind_that_cannot_hit_another_needs_no_number_of_attacks(self):
        self.assertIsNone(UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Pterodactyl))
        self.assertIsNotNone(UnitControl.attacks_to_kill(theme=Caveman, attacker=SpearThrower, defender=Pterodactyl))

    def test_a_level_adds_to_the_roll_makes_the_armor_better_and_adds_hit_points_so_more_attacks_are_needed(self):
        recruit = UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Warrior)
        self.assertLess(UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Warrior, attacker_level=LAST_LEVEL), recruit)
        self.assertGreater(UnitControl.attacks_to_kill(theme=Caveman, attacker=Warrior, defender=Warrior, defender_level=LAST_LEVEL), recruit)
        self.assertEqual(UnitControl.average_roll(attacker=Warrior, defender=Warrior, level=LAST_LEVEL), FIXED_WARRIOR_ROLL + Levels.damage_bonus(level=LAST_LEVEL))
        self.assertEqual(UnitControl.armor_class(kind=Warrior, level=LAST_LEVEL), Warrior.ARMOR_CLASS - Levels.armor_bonus(level=LAST_LEVEL))
        self.assertEqual(UnitControl.armor_class(kind=Warrior, bonus=1), Warrior.ARMOR_CLASS - 1)

    def test_dividing_and_rounding_up_counts_a_part_left_over_as_one_more(self):
        self.assertEqual(divided_rounding_up(amount=10, by=4), 3)
        self.assertEqual(divided_rounding_up(amount=12, by=4), 3)
        self.assertEqual(divided_rounding_up(amount=1, by=4), 1)
        self.assertEqual(divided_rounding_up(amount=0, by=4), 0)

    def test_a_unit_strikes_back_with_half_of_its_roll_by_default_through_the_armor_of_the_attacker(self):
        self.assertEqual(Mammoth.STRIKE_BACK_PERCENT, STRIKE_BACK_PERCENT)
        expected = UnitControl.mitigated(roll=Mammoth.ATTACK.plus * STRIKE_BACK_PERCENT // WHOLE, armor_class=Warrior.ARMOR_CLASS)
        self.assertGreater(expected, CHIP_DAMAGE)
        self.assertEqual(UnitControl.strike_back_damage(attacker=Warrior, defender=Mammoth), expected)
        self.assertLess(expected, UnitControl.damage(attacker=Mammoth, defender=Warrior))
        self.assertEqual(UnitControl.strike_back_roll(attacker=Warrior, defender=Mammoth, roll=Mammoth.ATTACK.plus), Mammoth.ATTACK.plus * STRIKE_BACK_PERCENT // WHOLE)

    def test_a_weak_strike_back_still_deals_chip_damage(self):
        self.assertEqual(UnitControl.strike_back_damage(attacker=Mammoth, defender=Warrior), CHIP_DAMAGE)
        self.assertEqual(UnitControl.strike_back_damage(attacker=Warrior, defender=Raft), CHIP_DAMAGE)

    def test_the_power_of_a_strike_back_can_be_set_for_a_kind_of_unit(self):
        self.assertEqual(UnitControl.strike_back_damage(attacker=Warrior, defender=Hedgehog), UnitControl.mitigated(roll=Hedgehog.ATTACK.plus, armor_class=Warrior.ARMOR_CLASS))
        self.assertEqual(UnitControl.strike_back_damage(attacker=Warrior, defender=Hedgehog), UnitControl.damage(attacker=Hedgehog, defender=Warrior))

    def test_a_kind_that_does_not_strike_back_deals_nothing_when_attacked(self):
        self.assertEqual(UnitControl.strike_back_damage(attacker=Warrior, defender=Tortoise), NO_DAMAGE)
        self.assertGreater(UnitControl.damage(attacker=Tortoise, defender=Warrior), NO_DAMAGE)

    def test_land_and_sea_units_cannot_strike_back_against_air_unless_their_kind_can_hit_air(self):
        self.assertEqual(UnitControl.strike_back_damage(attacker=Pterodactyl, defender=Mammoth), NO_DAMAGE)
        self.assertEqual(UnitControl.strike_back_damage(attacker=Pterodactyl, defender=Canoe), NO_DAMAGE)
        self.assertGreater(UnitControl.strike_back_damage(attacker=Pterodactyl, defender=SpearThrower), NO_DAMAGE)
        self.assertGreater(UnitControl.strike_back_damage(attacker=Pterodactyl, defender=Harpooner), NO_DAMAGE)
        self.assertGreater(UnitControl.strike_back_damage(attacker=Warrior, defender=Pterodactyl), NO_DAMAGE)

    def test_which_class_of_unit_each_class_can_hit_by_default(self):
        expected = {
            Warrior: {Domain.LAND: True, Domain.SEA: True, Domain.AIR: False, Domain.SPACE: True},
            Canoe: {Domain.LAND: True, Domain.SEA: True, Domain.AIR: False, Domain.SPACE: True},
            Pterodactyl: {Domain.LAND: True, Domain.SEA: True, Domain.AIR: True, Domain.SPACE: True},
            Comet: {Domain.LAND: True, Domain.SEA: True, Domain.AIR: True, Domain.SPACE: True},
            SpearThrower: {Domain.LAND: True, Domain.SEA: True, Domain.AIR: True, Domain.SPACE: True},
            Harpooner: {Domain.LAND: True, Domain.SEA: True, Domain.AIR: True, Domain.SPACE: True},
        }
        targets = {Domain.LAND: Warrior, Domain.SEA: Canoe, Domain.AIR: Pterodactyl, Domain.SPACE: Comet}
        for kind, by_domain in expected.items():
            for domain, allowed in by_domain.items():
                with self.subTest(kind=kind, domain=domain):
                    self.assertEqual(targets[domain].DOMAIN, domain)
                    self.assertEqual(can_hit(kind=kind, target=targets[domain]), allowed)

    def test_a_kind_that_is_no_class_of_unit_cannot_be_a_target(self):
        self.assertEqual(self.refused(lambda: can_hit(kind=Warrior, target=Mystery)), ERR_NO_DOMAIN.format(name=saved_name(Mystery)))

    def test_a_unit_that_takes_only_chip_damage_each_turn_heals_it_back(self):
        self.assertGreaterEqual(Warrior.HEAL, CHIP_DAMAGE)

    def test_a_unit_placed_past_the_east_edge_lands_on_the_tile_around_the_world(self):
        x, y = GRASSLAND_TILE
        unit = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + WORLD_WIDTH, y=y)
        self.assertEqual(self.unit_on(GRASSLAND_TILE), unit)
        self.assertEqual(self.units.get_value(column=UnitColumn.X, unit=unit), x)
        self.assertEqual(self.refused(lambda: self.place(kind=Warrior, tile=(x - WORLD_WIDTH, y))), ERR_TILE_HAS_A_UNIT.format(x=x, y=y))

    def test_a_unit_cannot_be_placed_off_the_top_or_the_bottom(self):
        for y in (-1, WORLD_HEIGHT):
            with self.subTest(y=y):
                self.assertEqual(self.refused(lambda: self.place(kind=Warrior, tile=(0, y))), ERR_ROW_OFF_THE_MAP.format(last=WORLD_HEIGHT - 1, value=y))

    def test_a_unit_needs_a_civilization_a_world_and_a_kind_of_the_theme(self):
        x, y = GRASSLAND_TILE
        count = self.units.count()
        self.assertEqual(self.refused(lambda: self.place(kind=Warrior, tile=GRASSLAND_TILE, owner=NO_SUCH_CIVILIZATION)), ERR_NO_SUCH_CIVILIZATION.format(civilization=NO_SUCH_CIVILIZATION))
        self.assertEqual(self.refused(lambda: self.place(kind=Warrior, tile=GRASSLAND_TILE, owner=NOTHING)), ERR_NO_SUCH_CIVILIZATION.format(civilization=NOTHING))
        self.assertEqual(
            self.refused(lambda: UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=NO_SUCH_WORLD, x=x, y=y)),
            ERR_NO_SUCH_WORLD.format(world=NO_SUCH_WORLD),
        )
        theme = saved_name(self.game.get_theme())
        self.assertEqual(self.refused(lambda: self.place(kind=Phalanx, tile=GRASSLAND_TILE)), ERR_NOT_IN_THEME.format(kind=Phalanx, category=shown_category(Category.UNITS), theme=theme))
        self.assertEqual(self.units.count(), count)
        self.assertEqual(self.unit_on(GRASSLAND_TILE), NOTHING)

    def test_a_removed_unit_leaves_its_tile_empty_for_another(self):
        unit = self.place(kind=Warrior, tile=GRASSLAND_TILE)
        UnitControl.remove(game=self.game, unit=unit)
        self.assertEqual(self.unit_on(GRASSLAND_TILE), NOTHING)
        self.assertFalse(self.units.exists(unit))
        self.assertEqual(self.refused(lambda: UnitControl.remove(game=self.game, unit=unit)), ERR_NO_SUCH_UNIT.format(unit=unit))
        another = self.place(kind=Settler, tile=GRASSLAND_TILE)
        self.assertEqual(self.unit_on(GRASSLAND_TILE), another)
        self.assertNotEqual(another, unit)


if __name__ == '__main__':
    unittest.main()
