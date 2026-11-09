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

"""Tests for fighting: attacking a unit, attacking the units inside a city, taking a city, and losing."""

import unittest

from caveman_game import SETTLER_TILES, THE_WORLD, end_rounds, found_village, game_facts, give_building, learn, resource_id, settler_of, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.production import Production
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.combat import ATTACK_EXPERIENCE, SURVIVAL_EXPERIENCE, Combat
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.kinds.unit_kinds import attack_dice
from microsponge.engine.units.levels import FIRST_LEVEL, LAST_LEVEL, NO_EXPERIENCE, Levels
from microsponge.engine.units.unit_control import BEST_ARMOR_CLASS, CHIP_DAMAGE, NO_BONUS, UnitControl
from microsponge.engine.units.work_control import WorkControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_ATTACK_OWN, ERR_CANNOT_HIT, ERR_CANNOT_TAKE_CITIES, ERR_CITY_DEFENDED, ERR_CITY_UNDEFENDED, ERR_NO_ACTION_POINTS, ERR_NOT_AT_WAR, ERR_NOT_NEXT_TO_UNIT,
    ERR_NOTHING_TO_ATTACK, ERR_UNIT_IN_A_CITY, ERR_UNIT_WORKING,
)
from microsponge.engine.kinds.building import Building
from microsponge.themes.caveman.buildings import Watchtower
from microsponge.themes.caveman.improvements import Farm
from microsponge.themes.caveman.resources import Currency
from microsponge.themes.caveman.technologies import Agriculture, Clubs
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import AngryBird, CaptainCaveman, Settler, SlingshotCaveman, Warrior, Worker

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
FIRST_NAME = 'Ugg'
SECOND_NAME = 'Grok'
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
VILLAGE = Caveman.CITY.NAME
WHOLE = 100
NO_DAMAGE = 0
ONE_ROUND = 1
ONE_STEP = 1
STRAIGHT = Caveman.STRAIGHT_ATTACK_COST_BASE
DIAGONAL = Caveman.DIAGONAL_ATTACK_COST_BASE
# A row of open grassland away from both settlers, the lake and the mountains, and a column on it to fight around.
OPEN_ROW = 2
OPEN_COLUMN = 20
A_SEED = 7
ONE_LEVEL = 1
# Hit points given to a unit that has to survive whatever is rolled against it.
TOUGH = 1000


def damage_range(*, attacker, defender, armor_bonus=NO_BONUS):
    """Return the least and the most damage a kind of unit deals another kind through its armor, at level 1."""
    dice = attack_dice(kind=attacker, target=defender)
    armor = UnitControl.armor_class(kind=defender, bonus=armor_bonus)
    return UnitControl.mitigated(roll=dice.least(), armor_class=armor), UnitControl.mitigated(roll=dice.most(), armor_class=armor)


def strike_back_range(*, attacker, defender):
    """Return the least and the most a kind of unit that was attacked deals its attacker by striking back, at level 1."""
    dice = attack_dice(kind=defender, target=attacker)
    least = UnitControl.strike_back_roll(attacker=attacker, defender=defender, roll=dice.least())
    most = UnitControl.strike_back_roll(attacker=attacker, defender=defender, roll=dice.most())
    armor = UnitControl.armor_class(kind=attacker)
    return UnitControl.mitigated(roll=least, armor_class=armor), UnitControl.mitigated(roll=most, armor_class=armor)


class Grunt(Warrior):
    """A warrior that does not strike back."""

    STRIKES_BACK = False


class Rockthrower(Warrior):
    """A warrior that bypasses city walls."""

    BYPASSES_WALLS = True


class Turtle(Warrior):
    """A warrior with the best armor there is."""

    ARMOR_CLASS = BEST_ARMOR_CLASS


class Palisade(Building):
    """City walls for caveman, which caveman does not have."""

    COST = {Currency: 20}
    ARMOR_BONUS = 2
    WALLS = True


MEEK_CAVEMAN = later_caveman({Category.UNITS: (*Caveman.UNITS, Grunt, Rockthrower, Turtle), Category.BUILDINGS: (*Caveman.BUILDINGS, Palisade)})


class CombatCase(Refusals, unittest.TestCase):
    """A started game in which the two civilizations are at war, with the first playing."""

    THEME = Caveman

    def assertWithin(self, *, value, bounds):
        least, most = bounds
        self.assertTrue(least <= value <= most, (value, bounds))

    def level_of(self, unit):
        return self.units.get_value(column=UnitColumn.LEVEL, unit=unit)

    def experience_of(self, unit):
        return self.units.get_value(column=UnitColumn.EXPERIENCE, unit=unit)

    def setUp(self):
        self.game = started_caveman_game(theme=self.THEME)
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        Orders.declare_war(game=self.game, civilization=FIRST_CIVILIZATION, on=SECOND_CIVILIZATION)

    def place(self, *, kind, civilization, x, y):
        return UnitControl.place(game=self.game, kind=kind, owner=civilization, world=THE_WORLD, x=x, y=y)

    def hit_points(self, unit):
        return self.units.get_value(column=UnitColumn.HIT_POINTS, unit=unit)

    def points_of(self, unit):
        return self.units.get_value(column=UnitColumn.ACTION_POINTS, unit=unit)

    def attack(self, *, unit, x, y):
        return Orders.attack(game=self.game, unit=unit, x=x, y=y)

    def refused_and_unchanged(self, action):
        """Return the message an order is refused with, having checked that the refusal changed nothing in the game."""
        before = game_facts(self.game)
        message = self.refused(action)
        self.assertEqual(game_facts(self.game), before)
        return message

    def two_warriors(self, *, defender=Warrior):
        """Put a warrior of the first civilization and a unit of the second next to each other on the open row, and return their ids."""
        attacker = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=OPEN_ROW)
        target = self.place(kind=defender, civilization=SECOND_CIVILIZATION, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        return attacker, target


class TestAttackingAUnit(CombatCase):

    def test_an_attack_rolls_the_dice_through_the_armor_of_the_defender_and_the_defender_strikes_back_through_the_armor_of_the_attacker(self):
        attacker, target = self.two_warriors()
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual(outcome.defender, target)
        self.assertWithin(value=outcome.damage, bounds=damage_range(attacker=Warrior, defender=Warrior))
        self.assertWithin(value=outcome.strike_back, bounds=strike_back_range(attacker=Warrior, defender=Warrior))
        self.assertEqual(outcome.striker, target)
        self.assertEqual((outcome.defender_killed, outcome.attacker_killed), (False, False))
        self.assertEqual(self.hit_points(target), Warrior.HIT_POINTS - outcome.damage)
        self.assertEqual(self.hit_points(attacker), Warrior.HIT_POINTS - outcome.strike_back)
        self.assertEqual(self.points_of(attacker), Warrior.ACTION_POINTS - STRAIGHT)
        self.assertEqual(self.game.get_civilization(FIRST_CIVILIZATION).get_action_points(), Caveman.ACTION_POINTS - STRAIGHT)

    def test_the_same_seed_rolls_the_same_fight(self):
        outcomes = []
        for _ in range(2):
            self.game = started_caveman_game(theme=self.THEME)
            self.setUp_after_theme()
            self.game.set_seed(A_SEED)
            attacker, _ = self.two_warriors()
            outcomes.append([self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW) for _ in range(2)])
        self.assertEqual(outcomes[0], outcomes[1])

    def test_an_attack_always_deals_chip_damage_however_good_the_armor(self):
        self.game = started_caveman_game(theme=MEEK_CAVEMAN)
        self.setUp_after_theme()
        attacker, turtle = self.two_warriors(defender=Turtle)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual(outcome.damage, CHIP_DAMAGE)
        self.assertEqual(self.hit_points(turtle), Turtle.HIT_POINTS - CHIP_DAMAGE)
        self.assertEqual(damage_range(attacker=Warrior, defender=Turtle), (CHIP_DAMAGE, CHIP_DAMAGE))

    def test_a_land_unit_cannot_strike_back_at_an_air_unit_and_a_slingshot_caveman_can(self):
        bird = self.place(kind=AngryBird, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=OPEN_ROW)
        warrior = self.place(kind=Warrior, civilization=SECOND_CIVILIZATION, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        outcome = self.attack(unit=bird, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual(outcome.strike_back, NO_DAMAGE)
        self.assertEqual(self.hit_points(bird), AngryBird.HIT_POINTS)
        self.assertEqual(self.hit_points(warrior), Warrior.HIT_POINTS - outcome.damage)
        slingshot = self.place(kind=SlingshotCaveman, civilization=SECOND_CIVILIZATION, x=OPEN_COLUMN - ONE_STEP, y=OPEN_ROW)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=bird, value=TOUGH)
        outcome = self.attack(unit=bird, x=OPEN_COLUMN - ONE_STEP, y=OPEN_ROW)
        self.assertWithin(value=outcome.strike_back, bounds=strike_back_range(attacker=AngryBird, defender=SlingshotCaveman))
        self.assertGreater(outcome.strike_back, NO_DAMAGE)
        self.assertEqual(self.hit_points(bird), TOUGH - outcome.strike_back)
        self.assertEqual(self.hit_points(slingshot), SlingshotCaveman.HIT_POINTS - outcome.damage)

    def test_a_kind_that_does_not_strike_back_deals_nothing_back(self):
        self.game = started_caveman_game(theme=MEEK_CAVEMAN)
        self.setUp_after_theme()
        attacker, grunt = self.two_warriors(defender=Grunt)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertWithin(value=outcome.damage, bounds=damage_range(attacker=Warrior, defender=Grunt))
        self.assertEqual((outcome.strike_back, outcome.striker), (NO_DAMAGE, None))
        self.assertEqual(self.hit_points(attacker), Warrior.HIT_POINTS)

    def setUp_after_theme(self):
        """Redo the setup over a game of another theme."""
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        Orders.declare_war(game=self.game, civilization=FIRST_CIVILIZATION, on=SECOND_CIVILIZATION)

    def test_a_defender_whose_hit_points_reach_0_is_gone_and_does_not_strike_back(self):
        attacker, target = self.two_warriors()
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=target, value=CHIP_DAMAGE)
        before = self.hit_points(attacker)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual((outcome.defender_killed, outcome.strike_back, outcome.attacker_killed), (True, NO_DAMAGE, False))
        self.assertFalse(self.units.exists(target))
        self.assertEqual(self.world.get_value(layer=Layer.UNIT, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW), NOTHING)
        self.assertEqual(self.hit_points(attacker), before)

    def test_an_attacker_can_be_killed_by_the_strike_back(self):
        attacker, target = self.two_warriors()
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=attacker, value=CHIP_DAMAGE)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual((outcome.defender_killed, outcome.attacker_killed), (False, True))
        self.assertFalse(self.units.exists(attacker))
        self.assertEqual(self.world.get_value(layer=Layer.UNIT, x=OPEN_COLUMN, y=OPEN_ROW), NOTHING)
        self.assertTrue(self.units.exists(target))

    def test_attacking_diagonally_costs_the_diagonal_base(self):
        attacker = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=OPEN_ROW)
        self.place(kind=Warrior, civilization=SECOND_CIVILIZATION, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW + ONE_STEP)
        self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW + ONE_STEP)
        self.assertEqual(self.points_of(attacker), Warrior.ACTION_POINTS - DIAGONAL)


class TestWhatCannotBeAttacked(CombatCase):

    def test_an_empty_tile_a_far_tile_and_an_own_unit_cannot_be_attacked(self):
        attacker = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=OPEN_ROW)
        own = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN - ONE_STEP, y=OPEN_ROW)
        self.place(kind=Warrior, civilization=SECOND_CIVILIZATION, x=OPEN_COLUMN + 2, y=OPEN_ROW)
        message = self.refused_and_unchanged(lambda: self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW))
        self.assertEqual(message, ERR_NOTHING_TO_ATTACK.format(x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW))
        message = self.refused_and_unchanged(lambda: self.attack(unit=attacker, x=OPEN_COLUMN + 2, y=OPEN_ROW))
        self.assertEqual(message, ERR_NOT_NEXT_TO_UNIT.format(x=OPEN_COLUMN + 2, y=OPEN_ROW, unit=attacker))
        message = self.refused_and_unchanged(lambda: self.attack(unit=attacker, x=OPEN_COLUMN - ONE_STEP, y=OPEN_ROW))
        self.assertEqual(message, ERR_ATTACK_OWN.format(unit=attacker))
        self.assertTrue(self.units.exists(own))

    def test_a_unit_of_a_civilization_not_at_war_cannot_be_attacked(self):
        self.game = started_caveman_game()
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        attacker, target = self.two_warriors()
        message = self.refused_and_unchanged(lambda: self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW))
        self.assertEqual(message, ERR_NOT_AT_WAR.format(name=SECOND_NAME))

    def test_a_kind_that_cannot_hit_the_target_cannot_attack_it(self):
        attacker = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=OPEN_ROW)
        self.place(kind=AngryBird, civilization=SECOND_CIVILIZATION, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        message = self.refused_and_unchanged(lambda: self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW))
        self.assertEqual(message, ERR_CANNOT_HIT.format(unit=shown_name(Warrior), target=shown_name(AngryBird)))

    def test_a_unit_with_no_action_points_a_working_unit_and_a_unit_inside_a_city_cannot_attack(self):
        attacker, target = self.two_warriors()
        self.units.set_value(column=UnitColumn.ACTION_POINTS, unit=attacker, value=NOTHING)
        message = self.refused_and_unchanged(lambda: self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW))
        self.assertEqual(message, ERR_NO_ACTION_POINTS.format(unit=attacker, left=NOTHING, cost=STRAIGHT))
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Agriculture)
        worker = self.place(kind=Worker, civilization=FIRST_CIVILIZATION, x=OPEN_COLUMN, y=OPEN_ROW + ONE_STEP)
        WorkControl.start(game=self.game, unit=worker, improvement=Farm)
        message = self.refused_and_unchanged(lambda: self.attack(unit=worker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW))
        self.assertEqual(message, ERR_UNIT_WORKING.format(unit=worker, improvement=shown_name(Farm)))
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        x, y = SETTLER_TILES[0]
        inside = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=x + 3, y=y)
        Orders.enter_city(game=self.game, unit=inside, city=city)
        self.place(kind=Warrior, civilization=SECOND_CIVILIZATION, x=x + 3, y=y)
        message = self.refused_and_unchanged(lambda: self.attack(unit=inside, x=x + 3, y=y))
        self.assertEqual(message, ERR_UNIT_IN_A_CITY.format(unit=inside, city=VILLAGE))


class CityCombatCase(CombatCase):
    """The first civilization's village with the second civilization's warrior next to its center, to the east."""

    def setUp(self):
        super().setUp()
        self.city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        x, y = SETTLER_TILES[0]
        self.middle = (x, y)
        self.east = (x + 3, y)
        self.south = (x, y + 3)
        self.game.set_playing(SECOND_CIVILIZATION)
        self.raider = self.place(kind=Warrior, civilization=SECOND_CIVILIZATION, x=self.east[0], y=self.east[1])

    def put_inside(self, kind):
        """Put a unit of the first civilization inside the village, and return its id."""
        x, y = self.south
        unit = self.place(kind=kind, civilization=FIRST_CIVILIZATION, x=x, y=y)
        CityControl.enter(game=self.game, unit=unit, city=self.city)
        return unit

    def raid(self):
        """Have the raider attack the city center tile next to it, and return the outcome."""
        x, y = self.east
        return Orders.attack(game=self.game, unit=self.raider, x=x - ONE_STEP, y=y)


class TestAttackingACity(CityCombatCase):

    def test_the_unit_with_the_strongest_defense_is_hit_and_the_strongest_attacker_able_to_hit_strikes_back(self):
        bird = self.put_inside(AngryBird)
        captain = self.put_inside(CaptainCaveman)
        slingshot = self.put_inside(SlingshotCaveman)
        self.assertEqual(Combat.defender_of_city(game=self.game, city=self.city), captain)
        self.assertEqual(Combat.striker_of_city(game=self.game, city=self.city, attacker=self.raider), captain)
        outcome = self.raid()
        self.assertEqual(outcome.defender, captain)
        self.assertWithin(value=outcome.damage, bounds=damage_range(attacker=Warrior, defender=CaptainCaveman))
        self.assertWithin(value=outcome.strike_back, bounds=strike_back_range(attacker=Warrior, defender=CaptainCaveman))
        self.assertEqual(outcome.striker, captain)
        self.assertEqual(self.hit_points(bird), AngryBird.HIT_POINTS)
        self.assertEqual(self.hit_points(slingshot), SlingshotCaveman.HIT_POINTS)
        self.assertEqual(self.hit_points(self.raider), Warrior.HIT_POINTS - outcome.strike_back)

    def test_the_striker_can_be_another_unit_than_the_one_hit(self):
        self.put_inside(Settler)
        warrior = self.put_inside(Warrior)
        self.assertGreater(Settler.ARMOR_CLASS, Warrior.ARMOR_CLASS)
        self.assertEqual(Combat.defender_of_city(game=self.game, city=self.city), warrior)
        self.assertEqual(Combat.striker_of_city(game=self.game, city=self.city, attacker=self.raider), warrior)
        bird = self.put_inside(AngryBird)
        raider = self.place(kind=AngryBird, civilization=SECOND_CIVILIZATION, x=self.east[0], y=self.east[1] + ONE_STEP)
        self.assertEqual(Combat.striker_of_city(game=self.game, city=self.city, attacker=raider), bird)
        x, y = self.middle
        outcome = Orders.attack(game=self.game, unit=raider, x=x + 2, y=y + 1)
        self.assertEqual((outcome.defender, outcome.striker), (warrior, bird))
        self.assertWithin(value=outcome.strike_back, bounds=strike_back_range(attacker=AngryBird, defender=AngryBird))
        self.assertEqual(self.hit_points(raider), AngryBird.HIT_POINTS - outcome.strike_back)

    def test_a_watchtower_makes_the_armor_class_of_every_unit_inside_better(self):
        warrior = self.put_inside(Warrior)
        give_building(game=self.game, city=self.city, building=Watchtower)
        self.assertEqual(CityControl.armor_bonus(game=self.game, city=self.city, against=Warrior), Watchtower.ARMOR_BONUS)
        self.assertEqual(UnitControl.armor_class_of(game=self.game, unit=warrior, bonus=Watchtower.ARMOR_BONUS), Warrior.ARMOR_CLASS - Watchtower.ARMOR_BONUS)
        self.game.set_seed(A_SEED)
        outcome = self.raid()
        self.assertWithin(value=outcome.damage, bounds=damage_range(attacker=Warrior, defender=Warrior, armor_bonus=Watchtower.ARMOR_BONUS))
        self.assertEqual(self.hit_points(warrior), Warrior.HIT_POINTS - outcome.damage)
        self.assertLess(damage_range(attacker=Warrior, defender=Warrior, armor_bonus=Watchtower.ARMOR_BONUS)[1], damage_range(attacker=Warrior, defender=Warrior)[1])

    def test_a_city_with_no_unit_inside_cannot_be_attacked_but_taken(self):
        message = self.refused_and_unchanged(self.raid)
        self.assertEqual(message, ERR_CITY_UNDEFENDED.format(name=A_NAME, city=VILLAGE))

    def test_attacking_any_tile_of_the_city_center_attacks_the_city(self):
        warrior = self.put_inside(Warrior)
        x, y = self.east
        outcome = Orders.attack(game=self.game, unit=self.raider, x=x - ONE_STEP, y=y + ONE_STEP)
        self.assertEqual(outcome.defender, warrior)


class TestExperienceAndLevels(CombatCase):

    def test_a_new_unit_is_at_the_first_level_with_no_experience(self):
        attacker, _ = self.two_warriors()
        self.assertEqual((self.level_of(attacker), self.experience_of(attacker)), (FIRST_LEVEL, NO_EXPERIENCE))
        self.assertEqual(UnitControl.max_hit_points(game=self.game, unit=attacker), Warrior.HIT_POINTS)

    def test_an_attack_gives_the_attacker_and_a_surviving_defender_a_little_experience(self):
        attacker, target = self.two_warriors()
        self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual(self.experience_of(attacker), ATTACK_EXPERIENCE)
        self.assertEqual(self.experience_of(target), SURVIVAL_EXPERIENCE)

    def test_a_kill_gives_the_worth_of_the_kind_killed_plus_its_level_and_a_dead_defender_gains_nothing(self):
        attacker, target = self.two_warriors()
        self.units.set_value(column=UnitColumn.LEVEL, unit=target, value=FIRST_LEVEL + ONE_LEVEL)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=target, value=CHIP_DAMAGE)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertTrue(outcome.defender_killed)
        self.assertEqual(self.experience_of(attacker), ATTACK_EXPERIENCE + Warrior.EXPERIENCE_WORTH + FIRST_LEVEL + ONE_LEVEL)
        self.assertEqual(Levels.kill_experience(killed=Warrior, level=FIRST_LEVEL), Warrior.EXPERIENCE_WORTH + FIRST_LEVEL)
        self.assertLess(Levels.kill_experience(killed=Settler, level=FIRST_LEVEL), Levels.kill_experience(killed=CaptainCaveman, level=FIRST_LEVEL))

    def test_a_striker_that_kills_the_attacker_gets_the_prize_and_the_dead_attacker_gets_nothing(self):
        attacker, target = self.two_warriors()
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=attacker, value=CHIP_DAMAGE)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertTrue(outcome.attacker_killed)
        self.assertEqual(self.experience_of(target), SURVIVAL_EXPERIENCE + Warrior.EXPERIENCE_WORTH + FIRST_LEVEL)

    def test_experience_that_reaches_a_level_raises_the_level_and_adds_the_hit_points_on_top_of_the_wounds(self):
        attacker, target = self.two_warriors()
        needed = Levels.experience_for(level=FIRST_LEVEL + ONE_LEVEL)
        self.units.set_value(column=UnitColumn.EXPERIENCE, unit=attacker, value=needed - ATTACK_EXPERIENCE)
        outcome = self.attack(unit=attacker, x=OPEN_COLUMN + ONE_STEP, y=OPEN_ROW)
        self.assertEqual(self.level_of(attacker), FIRST_LEVEL + ONE_LEVEL)
        whole = Levels.hit_points(theme=Caveman, kind=Warrior, level=FIRST_LEVEL + ONE_LEVEL)
        self.assertEqual(UnitControl.max_hit_points(game=self.game, unit=attacker), whole)
        self.assertEqual(self.hit_points(attacker), Warrior.HIT_POINTS - outcome.strike_back + whole - Warrior.HIT_POINTS)
        self.assertEqual(self.level_of(target), FIRST_LEVEL)

    def test_the_experience_a_level_takes_and_what_a_level_adds(self):
        self.assertEqual([Levels.experience_for(level=level) for level in range(FIRST_LEVEL, FIRST_LEVEL + 4)], [0, 10, 30, 60])
        self.assertEqual(Levels.experience_for(level=LAST_LEVEL), 1900)
        self.assertEqual(Levels.level_for(experience=NO_EXPERIENCE), FIRST_LEVEL)
        self.assertEqual(Levels.level_for(experience=29), FIRST_LEVEL + ONE_LEVEL)
        self.assertEqual(Levels.level_for(experience=30), FIRST_LEVEL + 2 * ONE_LEVEL)
        self.assertEqual(Levels.level_for(experience=1900 * 2), LAST_LEVEL)
        self.assertEqual([Levels.damage_bonus(level=level) for level in (1, 9, 10, 19, 20)], [0, 0, 1, 1, 2])
        self.assertEqual([Levels.armor_bonus(level=level) for level in (1, 4, 5, 14, 15, 20)], [0, 0, 1, 1, 2, 2])
        self.assertEqual(Levels.hit_points(theme=Caveman, kind=Warrior, level=FIRST_LEVEL), Warrior.HIT_POINTS)
        self.assertEqual(Levels.hit_points(theme=Caveman, kind=Warrior, level=LAST_LEVEL), Warrior.HIT_POINTS + Warrior.HIT_POINTS * Caveman.LEVEL_HIT_POINTS_PERCENT * (LAST_LEVEL - FIRST_LEVEL) // WHOLE)

    def test_a_unit_heals_up_to_the_hit_points_of_its_level(self):
        attacker, _ = self.two_warriors()
        self.units.set_value(column=UnitColumn.LEVEL, unit=attacker, value=LAST_LEVEL)
        whole = Levels.hit_points(theme=Caveman, kind=Warrior, level=LAST_LEVEL)
        self.assertGreater(whole, Warrior.HIT_POINTS)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=attacker, value=whole - CHIP_DAMAGE)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.assertEqual(self.hit_points(attacker), whole)


class TestCityWalls(CityCombatCase):
    """The village has a palisade and a watchtower, and a warrior inside."""

    THEME = MEEK_CAVEMAN

    def setUp(self):
        super().setUp()
        self.warrior = self.put_inside(Warrior)
        give_building(game=self.game, city=self.city, building=Palisade)
        give_building(game=self.game, city=self.city, building=Watchtower)

    def test_city_walls_add_their_armor_against_a_unit_that_does_not_bypass_them(self):
        bonus = CityControl.armor_bonus(game=self.game, city=self.city, against=Warrior)
        self.assertEqual(bonus, Palisade.ARMOR_BONUS + Watchtower.ARMOR_BONUS)
        outcome = self.raid()
        self.assertWithin(value=outcome.damage, bounds=damage_range(attacker=Warrior, defender=Warrior, armor_bonus=bonus))
        self.assertLess(damage_range(attacker=Warrior, defender=Warrior, armor_bonus=bonus)[1], damage_range(attacker=Warrior, defender=Warrior, armor_bonus=Watchtower.ARMOR_BONUS)[1])

    def test_a_unit_that_bypasses_city_walls_ignores_the_walls_but_not_the_other_buildings(self):
        self.assertEqual(CityControl.armor_bonus(game=self.game, city=self.city, against=Rockthrower), Watchtower.ARMOR_BONUS)
        x, y = self.east
        thrower = self.place(kind=Rockthrower, civilization=SECOND_CIVILIZATION, x=x, y=y + ONE_STEP)
        outcome = Orders.attack(game=self.game, unit=thrower, x=x - ONE_STEP, y=y + ONE_STEP)
        self.assertWithin(value=outcome.damage, bounds=damage_range(attacker=Rockthrower, defender=Warrior, armor_bonus=Watchtower.ARMOR_BONUS))


class TestTakingACity(CityCombatCase):

    def test_a_unit_takes_a_city_of_a_civilization_at_war_with_no_unit_inside_by_going_in(self):
        give_building(game=self.game, city=self.city, building=Watchtower)
        self.game.set_playing(FIRST_CIVILIZATION)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Clubs)
        Orders.build(game=self.game, city=self.city, kind=Warrior)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.game.set_playing(SECOND_CIVILIZATION)
        currency = self.game.get_civilization(FIRST_CIVILIZATION).get_amount(resource_id(game=self.game, resource=Currency))
        self.assertGreater(self.game.get_city(self.city).get_progress(), NOTHING)
        self.assertIsNone(CityControl.problem_taking(game=self.game, unit=self.raider, city=self.city))
        Orders.enter_city(game=self.game, unit=self.raider, city=self.city)
        target = self.game.get_city(self.city)
        self.assertEqual(target.get_owner(), SECOND_CIVILIZATION)
        self.assertEqual(target.get_units(), [self.raider])
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.city), [Watchtower])
        self.assertEqual((target.get_queue(), target.get_progress(), target.builds_nothing()), ([], NOTHING, False))
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=SECOND_CIVILIZATION), [self.city])
        self.assertEqual(self.game.get_civilization(FIRST_CIVILIZATION).get_amount(resource_id(game=self.game, resource=Currency)), currency)
        self.assertEqual(self.game.get_cities_of(SECOND_CIVILIZATION), [self.city])
        self.assertEqual(self.game.get_cities_of(FIRST_CIVILIZATION), [])
        self.assertEqual(self.points_of(self.raider), Warrior.ACTION_POINTS - Caveman.STRAIGHT_MOVE_COST_BASE)

    def test_a_city_with_a_unit_inside_is_not_taken(self):
        self.put_inside(Warrior)
        message = self.refused_and_unchanged(lambda: Orders.enter_city(game=self.game, unit=self.raider, city=self.city))
        self.assertEqual(message, ERR_CITY_DEFENDED.format(name=A_NAME))

    def test_a_kind_that_cannot_take_cities_does_not_take_one(self):
        x, y = self.east
        bird = self.place(kind=AngryBird, civilization=SECOND_CIVILIZATION, x=x, y=y + ONE_STEP)
        message = self.refused_and_unchanged(lambda: Orders.enter_city(game=self.game, unit=bird, city=self.city))
        self.assertEqual(message, ERR_CANNOT_TAKE_CITIES.format(unit=shown_name(AngryBird), city=VILLAGE))
        self.assertEqual(self.game.get_city(self.city).get_owner(), FIRST_CIVILIZATION)

    def test_a_city_is_not_taken_without_a_war(self):
        self.game = started_caveman_game()
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.game.set_playing(SECOND_CIVILIZATION)
        x, y = self.east
        raider = self.place(kind=Warrior, civilization=SECOND_CIVILIZATION, x=x, y=y)
        message = self.refused_and_unchanged(lambda: Orders.enter_city(game=self.game, unit=raider, city=city))
        self.assertEqual(message, ERR_NOT_AT_WAR.format(name=FIRST_NAME))


class TestLosing(CityCombatCase):

    def test_a_civilization_that_founded_cities_loses_when_its_last_city_is_taken_and_its_units_are_gone(self):
        first = self.game.get_civilization(FIRST_CIVILIZATION)
        x, y = self.south
        stray = self.place(kind=Warrior, civilization=FIRST_CIVILIZATION, x=x, y=y + ONE_STEP)
        self.assertEqual(first.get_cities_founded(), 1)
        self.assertFalse(first.has_lost())
        Orders.enter_city(game=self.game, unit=self.raider, city=self.city)
        Combat.settle_losses(self.game)
        self.assertTrue(first.has_lost())
        self.assertFalse(self.units.exists(stray))
        self.assertEqual(self.game.get_still_playing(), [SECOND_CIVILIZATION])
        self.assertTrue(self.game.is_over())

    def test_a_civilization_that_founded_no_city_loses_when_its_last_unit_is_killed(self):
        second = self.game.get_civilization(SECOND_CIVILIZATION)
        settler = settler_of(game=self.game, civilization=SECOND_CIVILIZATION)
        UnitControl.remove(game=self.game, unit=settler)
        self.assertEqual(second.get_cities_founded(), NOTHING)
        self.game.set_playing(FIRST_CIVILIZATION)
        x, y = self.east
        captain = self.place(kind=CaptainCaveman, civilization=FIRST_CIVILIZATION, x=x + ONE_STEP, y=y)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=self.raider, value=CHIP_DAMAGE)
        outcome = Orders.attack(game=self.game, unit=captain, x=x, y=y)
        self.assertTrue(outcome.defender_killed)
        self.assertTrue(second.has_lost())
        self.assertTrue(self.game.is_over())

    def test_a_civilization_with_a_city_left_has_not_lost_though_its_units_are_gone(self):
        self.game.set_playing(FIRST_CIVILIZATION)
        first = self.game.get_civilization(FIRST_CIVILIZATION)
        for unit in UnitControl.units_of(game=self.game, civilization=FIRST_CIVILIZATION):
            UnitControl.remove(game=self.game, unit=unit)
        Combat.settle_losses(self.game)
        self.assertFalse(first.has_lost())

    def test_an_attacker_whose_civilization_has_no_city_loses_by_dying_in_its_own_attack(self):
        settler = settler_of(game=self.game, civilization=SECOND_CIVILIZATION)
        UnitControl.remove(game=self.game, unit=settler)
        self.put_inside(CaptainCaveman)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=self.raider, value=CHIP_DAMAGE)
        outcome = self.raid()
        self.assertTrue(outcome.attacker_killed)
        self.assertTrue(self.game.get_civilization(SECOND_CIVILIZATION).has_lost())


if __name__ == '__main__':
    unittest.main()
