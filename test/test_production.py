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

"""Tests for what a city builds: its production queue, paying a part each turn, blocked builds, and where what is finished goes."""

import json
import unittest

from caveman_game import FLINT_TILE, SETTLER_TILES, THE_WORLD, end_rounds, end_turn_by_order, found_village, game_facts, give_building, held, learn, resource_id, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.city import City
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.levels import FIRST_LEVEL, Levels
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_ALREADY_BUILT, ERR_ALREADY_QUEUED, ERR_BUILD_NEEDS_WATER, ERR_BUILD_REQUIRES, ERR_BUILDING_ALREADY_HELD, ERR_NO_CITIZEN_TO_SPARE, ERR_NOT_YOUR_TURN, ERR_NOTHING_QUEUED, ERR_PROGRESS, ERR_UNKNOWN_ID, ERR_WONDER_BUILT,
)
from microsponge.themes.caveman.buildings import ArrangementOfRocks, Barracks, Granary, GreatCavePainting, Harbor, Watchtower
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.resources import Currency, Flint, Stone, Wood
from microsponge.themes.caveman.technologies import Agriculture, Clubs, Discipline, Fire
from microsponge.themes.caveman.theme import Caveman
from microsponge.engine.kinds.unit_kinds import LandUnit
from microsponge.themes.caveman.units import AngryBird, CaptainCaveman, CavemanUnit, Raft, Settler, Warrior, Worker

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
FIRST_NAME = 'Ugg'
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
A_THIRD_NAME = 'Uggford'
# Open grassland where the first civilization can build a second city.
A_SECOND_SITE = (20, 20)
# Open grassland beside the lake: the lake is next to the east side of the center of a city built here.
A_LAKESIDE_SITE = (20, 18)
ONE_ROUND = 1
ONE_CITIZEN = 1
TWO_CITIZENS = 2
NO_PROGRESS = 0
NOTHING_HELD = 0
WHOLE = 100
PLENTY = 1000
BARRACKS_LEVEL_BONUS = 1
STARTING_CURRENCY = Caveman.STARTS_WITH[Currency]
# The currency a city of one citizen brings in each turn.
INCOME = Village.CITIZEN_CURRENCY
A_SEED = 7
ANOTHER_SEED = 8
MANY_SEEDS = range(20)
# Ids of buildings and units, and a turn, for a city on its own.
A_BUILDING = 2
ANOTHER_BUILDING = 3
A_UNIT_KIND = 1
A_TURN = 9
A_FEW_TURNS = 2
NOT_COUNTS = (-1, 1.5, None)
LATER_BUILDINGS = {NOTHING: NOTHING, A_BUILDING: ANOTHER_BUILDING, ANOTHER_BUILDING: A_BUILDING}
LATER_UNITS = {NOTHING: NOTHING, A_UNIT_KIND: A_BUILDING}
NO_SUCH_IDS = {NOTHING: NOTHING}
# A row of open grassland, away from both settlers, the lake and the mountains.
OPEN_ROW = 2
# The tiles of the lake next to the center of a city built on the lakeside site.
WATER_BESIDE_THE_LAKESIDE_CITY = [(column, 15) for column in range(18, 22)]


class Dawdler(CavemanUnit, LandUnit):
    """A unit that takes more turns to build than it costs currency, so that its later turns cost nothing."""

    COST = {Currency: 10}
    BUILD_TURNS = 20


class Painter(CavemanUnit, LandUnit):
    """A unit that a world wonder unlocks."""

    REQUIRES = (GreatCavePainting,)
    COST = {Currency: 10}


LATER_CAVEMAN = later_caveman({Category.UNITS: (*Caveman.UNITS, Dawdler, Painter)})
# The first turn of a dawdler's build that costs nothing.
A_FREE_TURN = Dawdler.COST[Currency]


def through_json(data):
    """Return data as it comes back from a JSON file."""
    return json.loads(json.dumps(data))


class TestWhatACityHolds(Refusals, unittest.TestCase):

    def setUp(self):
        self.city = City(name=A_NAME, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=5, y=12, founded=A_TURN, citizens=ONE_CITIZEN)

    def every_fact(self, city):
        return (city.get_buildings(), city.get_queue(), city.get_progress(), city.is_blocked(), city.builds_nothing())

    def a_busy_city(self):
        self.city.add_building(A_BUILDING)
        self.city.add_to_queue(category=Category.BUILDINGS, kind=ANOTHER_BUILDING)
        self.city.add_to_queue(category=Category.UNITS, kind=A_UNIT_KIND)
        self.city.set_progress(A_FEW_TURNS)
        self.city.set_blocked(True)
        return self.city

    def test_a_new_city_has_no_building_and_builds_nothing_yet(self):
        self.assertEqual(self.every_fact(self.city), ([], [], NO_PROGRESS, False, False))

    def test_a_city_has_each_building_once_in_the_order_built(self):
        self.city.add_building(ANOTHER_BUILDING)
        self.city.add_building(A_BUILDING)
        self.assertEqual(self.city.get_buildings(), [ANOTHER_BUILDING, A_BUILDING])
        self.assertTrue(self.city.has_building(A_BUILDING))
        self.assertEqual(self.refused(lambda: self.city.add_building(A_BUILDING)), ERR_BUILDING_ALREADY_HELD.format(name=A_NAME, building=A_BUILDING))
        self.assertEqual(self.city.get_buildings(), [ANOTHER_BUILDING, A_BUILDING])

    def test_taking_the_first_off_the_queue_starts_the_next_from_nothing(self):
        city = self.a_busy_city()
        city.remove_first()
        self.assertEqual(self.every_fact(city), ([A_BUILDING], [(Category.UNITS, A_UNIT_KIND)], NO_PROGRESS, False, False))
        city.remove_first()
        self.assertEqual(self.refused(city.remove_first), ERR_NOTHING_QUEUED.format(name=A_NAME))

    def test_emptying_the_queue_loses_the_progress(self):
        city = self.a_busy_city()
        city.clear_queue()
        self.assertEqual(self.every_fact(city), ([A_BUILDING], [], NO_PROGRESS, False, False))

    def test_queueing_something_ends_being_set_to_build_nothing(self):
        self.city.set_builds_nothing(True)
        self.assertTrue(self.city.builds_nothing())
        self.city.add_to_queue(category=Category.UNITS, kind=A_UNIT_KIND)
        self.assertFalse(self.city.builds_nothing())

    def test_progress_that_counts_nothing_is_refused(self):
        self.city.set_progress(A_FEW_TURNS)
        for turns in NOT_COUNTS:
            with self.subTest(turns=turns):
                self.assertEqual(self.refused(lambda: self.city.set_progress(turns)), ERR_PROGRESS.format(value=turns))
        self.assertEqual(self.city.get_progress(), A_FEW_TURNS)

    def test_the_lists_handed_out_are_copies(self):
        city = self.a_busy_city()
        city.get_buildings().clear()
        city.get_queue().clear()
        self.assertEqual((city.get_buildings(), len(city.get_queue())), ([A_BUILDING], 2))

    def test_what_a_city_builds_comes_back_from_a_saved_game_as_it_was(self):
        city = self.a_busy_city()
        loaded = City.from_data(through_json(city.to_data()))
        self.assertEqual(self.every_fact(loaded), self.every_fact(city))
        city.clear_queue()
        city.set_builds_nothing(True)
        self.assertEqual(self.every_fact(City.from_data(through_json(city.to_data()))), self.every_fact(city))

    def test_a_later_version_can_renumber_the_buildings_and_units_a_city_holds_and_builds(self):
        city = self.a_busy_city()
        city.renumber(category=Category.BUILDINGS, numbers=LATER_BUILDINGS)
        self.assertEqual((city.get_buildings(), city.get_queue()), ([ANOTHER_BUILDING], [(Category.BUILDINGS, A_BUILDING), (Category.UNITS, A_UNIT_KIND)]))
        city.renumber(category=Category.UNITS, numbers=LATER_UNITS)
        self.assertEqual((city.get_buildings(), city.get_queue()), ([ANOTHER_BUILDING], [(Category.BUILDINGS, A_BUILDING), (Category.UNITS, A_BUILDING)]))
        self.assertEqual(self.refused(lambda: city.renumber(category=Category.BUILDINGS, numbers=NO_SUCH_IDS)), ERR_UNKNOWN_ID.format(known=sorted(NO_SUCH_IDS)))


class ProductionCase(Refusals, unittest.TestCase):
    """A started game in which the first civilization has a city, knows every technology and has no units."""

    THEME = Caveman

    def setUp(self):
        self.game = started_caveman_game(theme=self.THEME)
        self.game.set_seed(A_SEED)
        self.units = self.game.get_units()
        self.first = self.game.get_civilization(FIRST_CIVILIZATION)
        self.city_id = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.city = self.game.get_city(self.city_id)
        for technology in (Clubs, Agriculture):
            learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=technology)

    def currency(self):
        return held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Currency)

    def another_city(self, *, site=A_SECOND_SITE):
        """Build a second city of the first civilization on a site, and return its id."""
        x, y = site
        settler = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        return CityControl.found(game=self.game, settler=settler, name=A_THIRD_NAME)

    def give(self, *, resource, amount):
        self.first.add(resource=resource_id(game=self.game, resource=resource), amount=amount)

    def build(self, kind):
        Orders.build(game=self.game, city=self.city_id, kind=kind)

    def rounds(self, rounds):
        end_rounds(game=self.game, rounds=rounds)

    def kinds_inside(self):
        """Return the kinds of the units inside the city."""
        return [UnitControl.kind_of(game=self.game, unit=unit) for unit in self.city.get_units()]

    def units_of_kind(self, kind):
        return [unit for unit in self.units.get_ids() if UnitControl.kind_of(game=self.game, unit=unit) is kind]

    def refused_and_unchanged(self, action):
        """Return the message an order is refused with, having checked that the refusal changed nothing in the game."""
        before = game_facts(self.game)
        message = self.refused(action)
        self.assertEqual(game_facts(self.game), before)
        return message


class TestBuildingUnits(ProductionCase):

    def test_the_cost_of_a_build_is_split_evenly_over_its_turns_with_what_is_left_over_paid_first(self):
        for kind in (Warrior, Settler, Worker, Granary, GreatCavePainting, ArrangementOfRocks, Dawdler):
            with self.subTest(kind=kind):
                parts = [Production.part(kind=kind, turn=turn) for turn in range(kind.BUILD_TURNS)]
                for resource, amount in kind.COST.items():
                    paid = [part[resource] for part in parts]
                    self.assertEqual(sum(paid), amount)
                    self.assertLessEqual(max(paid) - min(paid), 1)
                    self.assertEqual(paid, sorted(paid, reverse=True))

    def test_a_city_that_has_nothing_to_build_waits_to_be_told_unless_it_is_set_to_build_nothing(self):
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=FIRST_CIVILIZATION), [self.city_id])
        self.assertIsNone(Production.building(game=self.game, city=self.city_id))
        self.build(Warrior)
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=FIRST_CIVILIZATION), [])
        Orders.build_nothing(game=self.game, city=self.city_id)
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=FIRST_CIVILIZATION), [])
        self.assertTrue(self.city.builds_nothing())
        self.assertEqual(Production.queue_of(game=self.game, city=self.city_id), [])
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=SECOND_CIVILIZATION), [])

    def test_a_warrior_is_paid_for_a_part_each_turn_and_stands_inside_the_city_when_the_last_part_is_paid(self):
        pool = self.first.get_action_points()
        self.build(Warrior)
        self.assertEqual(self.first.get_action_points(), pool)
        self.assertIs(Production.building(game=self.game, city=self.city_id), Warrior)
        self.assertEqual(Production.turns_left(game=self.game, city=self.city_id), Warrior.BUILD_TURNS)
        self.rounds(ONE_ROUND)
        self.assertEqual(self.currency(), STARTING_CURRENCY + INCOME - Production.part(kind=Warrior, turn=0)[Currency])
        self.assertEqual(Production.turns_left(game=self.game, city=self.city_id), Warrior.BUILD_TURNS - ONE_ROUND)
        self.rounds(Warrior.BUILD_TURNS - ONE_ROUND - ONE_ROUND)
        self.assertEqual(self.kinds_inside(), [])
        self.rounds(ONE_ROUND)
        self.assertEqual(self.kinds_inside(), [Warrior])
        self.assertEqual(self.currency(), STARTING_CURRENCY + INCOME * Warrior.BUILD_TURNS - Warrior.COST[Currency])
        warrior, = self.city.get_units()
        self.assertEqual(self.units.get_value(column=UnitColumn.OWNER, unit=warrior), FIRST_CIVILIZATION)
        self.assertEqual(self.units.get_value(column=UnitColumn.HIT_POINTS, unit=warrior), Warrior.HIT_POINTS)
        self.assertEqual(Production.queue_of(game=self.game, city=self.city_id), [])
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=FIRST_CIVILIZATION), [self.city_id])

    def test_a_city_builds_what_is_queued_one_after_another(self):
        self.build(Warrior)
        self.build(Worker)
        self.assertEqual(Production.queue_of(game=self.game, city=self.city_id), [Warrior, Worker])
        self.rounds(Warrior.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [Warrior])
        self.assertIs(Production.building(game=self.game, city=self.city_id), Worker)
        self.rounds(Worker.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [Warrior, Worker])

    def test_a_unit_or_building_that_requires_a_technology_the_civilization_lacks_is_refused(self):
        other = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        for kind, required in ((Warrior, Clubs), (Worker, Agriculture), (Granary, Agriculture)):
            with self.subTest(kind=kind):
                message = self.refused_and_unchanged(lambda: Orders.build(game=self.game, city=other, kind=kind))
                self.assertEqual(message, ERR_BUILD_REQUIRES.format(kind=shown_name(kind), required=shown_name(required)))
                self.assertEqual(Production.problem_queueing(game=self.game, city=other, kind=kind), message)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=other, kind=AngryBird))

    def test_a_build_is_blocked_on_a_turn_when_its_part_cannot_be_paid_and_takes_a_turn_longer(self):
        self.first.pay(resource=resource_id(game=self.game, resource=Currency), amount=STARTING_CURRENCY)
        self.build(Warrior)
        first_part = Production.part(kind=Warrior, turn=0)[Currency]
        self.assertLess(INCOME, first_part)
        self.assertGreaterEqual(INCOME + INCOME, first_part)
        self.rounds(ONE_ROUND)
        self.assertTrue(self.city.is_blocked())
        self.assertEqual(Production.blocked_cities(game=self.game, civilization=FIRST_CIVILIZATION), [self.city_id])
        self.assertEqual((self.city.get_progress(), self.currency()), (NO_PROGRESS, INCOME))
        self.rounds(ONE_ROUND)
        self.assertFalse(self.city.is_blocked())
        self.assertEqual(Production.blocked_cities(game=self.game, civilization=FIRST_CIVILIZATION), [])
        self.assertEqual((self.city.get_progress(), self.currency()), (ONE_ROUND, INCOME + INCOME - first_part))

    def test_a_build_that_needs_a_second_resource_waits_for_that_resource_and_pays_nothing_meanwhile(self):
        self.build(ArrangementOfRocks)
        self.rounds(ONE_ROUND)
        self.assertTrue(self.city.is_blocked())
        self.assertEqual((self.city.get_progress(), self.currency()), (NO_PROGRESS, STARTING_CURRENCY + INCOME))
        self.give(resource=Stone, amount=PLENTY)
        self.rounds(ONE_ROUND)
        part = Production.part(kind=ArrangementOfRocks, turn=0)
        self.assertFalse(self.city.is_blocked())
        self.assertEqual(self.city.get_progress(), ONE_ROUND)
        self.assertEqual(held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Stone), PLENTY - part[Stone])
        self.assertEqual(self.currency(), STARTING_CURRENCY + INCOME + INCOME - part[Currency])

    def test_orders_about_what_a_city_builds_are_taken_only_on_the_turn_of_its_civilization(self):
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        expected = ERR_NOT_YOUR_TURN.format(name=FIRST_NAME)
        for order in (Orders.build, Orders.build_instead):
            with self.subTest(order=order):
                self.assertEqual(self.refused_and_unchanged(lambda: order(game=self.game, city=self.city_id, kind=Warrior)), expected)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.build_nothing(game=self.game, city=self.city_id)), expected)


class TestABuildingAUnitRequires(ProductionCase):

    def test_a_barracks_requires_discipline(self):
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(Barracks), required=shown_name(Discipline))
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(Barracks)), expected)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Discipline)
        self.build(Barracks)
        self.rounds(Barracks.BUILD_TURNS)
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.city_id), [Barracks])

    def test_captain_caveman_is_built_only_by_a_city_that_has_a_barracks_itself(self):
        other = self.another_city()
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(CaptainCaveman), required=shown_name(Barracks))
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(CaptainCaveman)), expected)
        give_building(game=self.game, city=self.city_id, building=Barracks)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=self.city_id, kind=CaptainCaveman))
        self.assertEqual(Production.problem_queueing(game=self.game, city=other, kind=CaptainCaveman), expected)
        self.give(resource=Currency, amount=PLENTY)
        self.build(CaptainCaveman)
        self.rounds(CaptainCaveman.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [CaptainCaveman])

    def test_a_barracks_starts_the_units_built_in_its_city_at_level_2_whole_at_that_level_and_another_city_at_level_1(self):
        other = self.another_city()
        self.give(resource=Currency, amount=PLENTY)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Clubs)
        self.assertEqual(CityControl.starting_level(game=self.game, city=self.city_id), FIRST_LEVEL)
        give_building(game=self.game, city=self.city_id, building=Barracks)
        self.assertEqual(Barracks.LEVEL_BONUS, BARRACKS_LEVEL_BONUS)
        self.assertEqual(CityControl.starting_level(game=self.game, city=self.city_id), FIRST_LEVEL + BARRACKS_LEVEL_BONUS)
        self.assertEqual(CityControl.starting_level(game=self.game, city=other), FIRST_LEVEL)
        self.build(Warrior)
        Orders.build(game=self.game, city=other, kind=Warrior)
        self.rounds(Warrior.BUILD_TURNS)
        trained, raw = self.units_of_kind(Warrior)
        self.assertEqual(UnitControl.level_of(game=self.game, unit=trained), FIRST_LEVEL + BARRACKS_LEVEL_BONUS)
        self.assertEqual(self.units.get_value(column=UnitColumn.EXPERIENCE, unit=trained), Levels.experience_for(level=FIRST_LEVEL + BARRACKS_LEVEL_BONUS))
        self.assertEqual(self.units.get_value(column=UnitColumn.HIT_POINTS, unit=trained), Levels.hit_points(theme=Caveman, kind=Warrior, level=FIRST_LEVEL + BARRACKS_LEVEL_BONUS))
        self.assertEqual(UnitControl.level_of(game=self.game, unit=raw), FIRST_LEVEL)
        self.assertEqual(self.units.get_value(column=UnitColumn.HIT_POINTS, unit=raw), Warrior.HIT_POINTS)
        for _ in range(Village.MOST_UNITS):
            self.build(Warrior)
            self.rounds(Warrior.BUILD_TURNS)
        outside = self.units_of_kind(Warrior)[-1]
        self.assertEqual(self.units.get_value(column=UnitColumn.CITY, unit=outside), NOTHING)
        self.assertEqual(UnitControl.level_of(game=self.game, unit=outside), FIRST_LEVEL + BARRACKS_LEVEL_BONUS)

    def test_a_harbor_is_built_only_by_a_city_with_water_next_to_its_center(self):
        lakeside = self.another_city(site=A_LAKESIDE_SITE)
        self.assertFalse(CityControl.is_beside_water(game=self.game, city=self.city_id))
        self.assertTrue(CityControl.is_beside_water(game=self.game, city=lakeside))
        expected = ERR_BUILD_NEEDS_WATER.format(building=shown_name(Harbor), city=Village.NAME)
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(Harbor)), expected)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.build_instead(game=self.game, city=self.city_id, kind=Harbor)), expected)
        Orders.build(game=self.game, city=lakeside, kind=Harbor)
        self.rounds(Harbor.BUILD_TURNS)
        self.assertEqual(CityControl.buildings_of(game=self.game, city=lakeside), [Harbor])

    def test_a_watchtower_is_built_with_fire_known_and_flint_within_the_borders(self):
        other = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        x, y = FLINT_TILE
        self.assertIs(Strategic.resource_at(game=self.game, world=THE_WORLD, x=x, y=y), Flint)
        self.assertEqual(Strategic.held(game=self.game, civilization=SECOND_CIVILIZATION), [Flint])
        self.assertNotIn(Flint, Strategic.held(game=self.game, civilization=FIRST_CIVILIZATION))
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Fire)
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(Watchtower), required=shown_name(Flint))
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(Watchtower)), expected)
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(Watchtower), required=shown_name(Fire))
        self.assertEqual(Production.problem_queueing(game=self.game, city=other, kind=Watchtower), expected)
        learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=Fire)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=other, kind=Watchtower))

    def test_a_raft_is_built_only_by_a_city_that_has_a_harbor(self):
        lakeside = self.another_city(site=A_LAKESIDE_SITE)
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(Raft), required=shown_name(Harbor))
        self.assertEqual(Production.problem_queueing(game=self.game, city=lakeside, kind=Raft), expected)
        give_building(game=self.game, city=lakeside, building=Harbor)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=lakeside, kind=Raft))
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(Raft)), expected)

    def harbor_city(self):
        """Build a city of the first civilization beside the lake, with a harbor, and return its id."""
        lakeside = self.another_city(site=A_LAKESIDE_SITE)
        give_building(game=self.game, city=lakeside, building=Harbor)
        return lakeside

    def test_a_raft_is_paid_for_in_currency_and_wood_and_can_leave_its_city_onto_the_water(self):
        lakeside = self.harbor_city()
        self.give(resource=Wood, amount=Raft.COST[Wood])
        self.give(resource=Currency, amount=PLENTY)
        before = self.currency()
        Orders.build(game=self.game, city=lakeside, kind=Raft)
        self.rounds(Raft.BUILD_TURNS)
        raft, = self.game.get_city(lakeside).get_units()
        self.assertIs(UnitControl.kind_of(game=self.game, unit=raft), Raft)
        self.assertEqual(held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Wood), NOTHING_HELD)
        self.assertLess(self.currency(), before + INCOME * 2 * Raft.BUILD_TURNS)
        self.assertEqual(CityControl.free_ring_tiles(game=self.game, city=lakeside, kind=Raft), WATER_BESIDE_THE_LAKESIDE_CITY)
        x, y = WATER_BESIDE_THE_LAKESIDE_CITY[0]
        Orders.leave_city(game=self.game, unit=raft, x=x, y=y)
        self.assertEqual(UnitControl.tile_of(game=self.game, unit=raft), (THE_WORLD, x, y))

    def test_a_raft_waits_while_the_civilization_holds_no_wood(self):
        lakeside = self.harbor_city()
        Orders.build(game=self.game, city=lakeside, kind=Raft)
        self.rounds(Raft.BUILD_TURNS)
        self.assertEqual(self.game.get_city(lakeside).get_units(), [])
        self.assertTrue(self.game.get_city(lakeside).is_blocked())
        self.assertEqual(self.game.get_city(lakeside).get_progress(), NO_PROGRESS)


class TestSwitchingWhatACityBuilds(ProductionCase):

    def refund_after(self, *, kind, turns):
        """Return the currency that comes back for a build of a kind given up after some turns: the theme's percent of what was paid, rounded down."""
        return sum(Production.part(kind=kind, turn=turn)[Currency] for turn in range(turns)) * Caveman.SWITCH_REFUND_PERCENT // WHOLE

    def test_building_something_instead_refunds_a_part_of_what_was_paid_and_empties_the_rest_of_the_queue(self):
        self.build(Warrior)
        self.build(AngryBird)
        self.rounds(A_FEW_TURNS)
        paid = self.currency()
        refund = self.refund_after(kind=Warrior, turns=A_FEW_TURNS)
        self.assertEqual(Production.refund(game=self.game, city=self.city_id), {Currency: refund})
        self.assertGreater(refund, NOTHING_HELD)
        self.assertLess(refund, Production.paid(kind=Warrior, turns=A_FEW_TURNS)[Currency])
        Orders.build_instead(game=self.game, city=self.city_id, kind=Worker)
        self.assertEqual(Production.queue_of(game=self.game, city=self.city_id), [Worker])
        self.assertEqual((self.city.get_progress(), self.currency()), (NO_PROGRESS, paid + refund))
        self.assertEqual(Production.refund(game=self.game, city=self.city_id), {})
        self.rounds(Worker.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [Worker])

    def test_what_a_build_has_paid_so_far_is_the_parts_of_the_turns_paid_for(self):
        self.assertEqual(Production.paid(kind=Warrior, turns=NO_PROGRESS), {})
        self.assertEqual(Production.paid(kind=Warrior, turns=Warrior.BUILD_TURNS), Warrior.COST)
        self.assertEqual(Production.paid(kind=Raft, turns=Raft.BUILD_TURNS), Raft.COST)
        self.assertEqual(Production.refund(game=self.game, city=self.city_id), {})

    def test_a_refund_rounds_down_and_a_switch_before_any_part_is_paid_refunds_nothing(self):
        self.build(Warrior)
        paid = self.currency()
        Orders.build_instead(game=self.game, city=self.city_id, kind=Worker)
        self.assertEqual(self.currency(), paid)
        self.rounds(ONE_ROUND)
        paid = self.currency()
        self.assertEqual(self.refund_after(kind=Worker, turns=ONE_ROUND), NOTHING_HELD)
        Orders.build_instead(game=self.game, city=self.city_id, kind=Warrior)
        self.assertEqual(self.currency(), paid)

    def test_a_refused_switch_leaves_the_build_under_way_as_it_was(self):
        self.build(Granary)
        self.rounds(Granary.BUILD_TURNS)
        self.build(Warrior)
        self.rounds(A_FEW_TURNS)
        message = self.refused_and_unchanged(lambda: Orders.build_instead(game=self.game, city=self.city_id, kind=Granary))
        self.assertEqual(message, ERR_ALREADY_BUILT.format(name=A_NAME, building=shown_name(Granary)))
        self.assertEqual((Production.queue_of(game=self.game, city=self.city_id), self.city.get_progress()), ([Warrior], A_FEW_TURNS))

    def test_setting_a_city_to_build_nothing_refunds_a_part_of_what_was_paid(self):
        self.build(Warrior)
        self.rounds(A_FEW_TURNS)
        paid = self.currency()
        Orders.build_nothing(game=self.game, city=self.city_id)
        self.assertEqual(self.currency(), paid + self.refund_after(kind=Warrior, turns=A_FEW_TURNS))
        self.assertEqual((self.city.get_queue(), self.city.get_progress()), ([], NO_PROGRESS))
        self.rounds(Warrior.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [])


class TestWhereAFinishedUnitGoes(ProductionCase):

    def fill_the_city(self):
        """Put as many warriors inside the city as a city holds."""
        x, y = CityControl.ring_tiles(game=self.game, city=self.city_id)[0]
        for _ in range(Village.MOST_UNITS):
            warrior = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
            CityControl.enter(game=self.game, unit=warrior, city=self.city_id)

    def fill_the_ring(self):
        """Put a warrior on every tile next to the city center, and return the tiles."""
        ring = CityControl.ring_tiles(game=self.game, city=self.city_id)
        for x, y in ring:
            UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        return ring

    def place_of(self, unit):
        _, x, y = UnitControl.tile_of(game=self.game, unit=unit)
        return (x, y)

    def test_a_unit_finished_by_a_full_city_stands_on_a_tile_next_to_the_city_center(self):
        self.fill_the_city()
        self.give(resource=Currency, amount=PLENTY)
        self.build(Worker)
        self.rounds(Worker.BUILD_TURNS)
        worker, = self.units_of_kind(Worker)
        self.assertEqual(self.kinds_inside(), [Warrior] * Village.MOST_UNITS)
        self.assertEqual(self.units.get_value(column=UnitColumn.CITY, unit=worker), NOTHING)
        self.assertIn(self.place_of(worker), CityControl.ring_tiles(game=self.game, city=self.city_id))

    def test_the_tile_is_chosen_at_random_and_the_same_seed_chooses_the_same_tile(self):
        self.fill_the_city()
        chosen = {seed: self.chosen_tile(seed) for seed in MANY_SEEDS}
        self.assertGreater(len(set(chosen.values())), 1)
        self.assertEqual(self.chosen_tile(A_SEED), chosen[A_SEED])
        self.assertEqual(self.chosen_tile(ANOTHER_SEED), chosen[ANOTHER_SEED])

    def chosen_tile(self, seed):
        """Return the tile a new unit of the full city is put on with a seed, having taken the unit away again."""
        self.game.set_seed(seed)
        unit = CityControl.muster(game=self.game, city=self.city_id, kind=Worker)
        place = self.place_of(unit)
        UnitControl.remove(game=self.game, unit=unit)
        return place

    def test_a_unit_with_nowhere_to_go_waits_until_there_is_room(self):
        self.fill_the_city()
        ring = self.fill_the_ring()
        self.give(resource=Currency, amount=PLENTY)
        self.build(Worker)
        self.rounds(Worker.BUILD_TURNS + ONE_ROUND)
        self.assertEqual(self.units_of_kind(Worker), [])
        self.assertTrue(self.city.is_blocked())
        self.assertEqual(self.city.get_progress(), Worker.BUILD_TURNS)
        paid = self.currency()
        x, y = ring[0]
        UnitControl.remove(game=self.game, unit=self.game.get_world(THE_WORLD).get_value(layer=Layer.UNIT, x=x, y=y))
        self.rounds(ONE_ROUND)
        worker, = self.units_of_kind(Worker)
        self.assertEqual(self.place_of(worker), (x, y))
        self.assertFalse(self.city.is_blocked())
        self.assertEqual(Production.queue_of(game=self.game, city=self.city_id), [])
        self.assertLess(self.currency(), paid + INCOME)

    def test_a_settler_uses_up_a_citizen_of_the_city_that_builds_the_settler(self):
        self.city.set_citizens(TWO_CITIZENS)
        self.build(Settler)
        self.rounds(Settler.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [Settler])
        self.assertEqual(self.city.get_citizens(), ONE_CITIZEN)

    def test_a_warrior_uses_up_no_citizen(self):
        self.city.set_citizens(TWO_CITIZENS)
        self.build(Warrior)
        self.rounds(Warrior.BUILD_TURNS)
        self.assertEqual((self.kinds_inside(), self.city.get_citizens()), ([Warrior], TWO_CITIZENS))

    def test_a_city_cannot_build_a_settler_that_would_leave_it_with_no_citizens(self):
        expected = ERR_NO_CITIZEN_TO_SPARE.format(unit=shown_name(Settler), name=A_NAME, citizens=ONE_CITIZEN, uses=Settler.CITIZENS)
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(Settler)), expected)
        self.assertEqual(Production.problem_queueing(game=self.game, city=self.city_id, kind=Settler), expected)
        self.city.set_citizens(TWO_CITIZENS)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=self.city_id, kind=Settler))

    def test_a_second_settler_queued_while_there_were_citizens_waits_for_another_citizen(self):
        self.city.set_citizens(TWO_CITIZENS)
        self.build(Settler)
        self.build(Settler)
        self.rounds(Settler.BUILD_TURNS)
        self.assertEqual(self.kinds_inside(), [Settler])
        self.rounds(Settler.BUILD_TURNS - ONE_ROUND)
        # The city may have grown meanwhile: the second settler must find one citizen, and the city may grow again after the wait.
        self.city.set_citizens(ONE_CITIZEN)
        self.rounds(ONE_ROUND)
        self.assertEqual(self.kinds_inside(), [Settler])
        self.assertTrue(self.city.is_blocked())
        self.city.set_citizens(TWO_CITIZENS)
        self.rounds(ONE_ROUND)
        self.assertEqual(self.kinds_inside(), [Settler, Settler])
        self.assertGreaterEqual(self.city.get_citizens(), ONE_CITIZEN)
        self.assertFalse(self.city.is_blocked())


class TestBuildingBuildings(ProductionCase):

    def setUp(self):
        super().setUp()
        self.other_id = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        self.other = self.game.get_city(self.other_id)

    def test_a_building_stands_in_its_city_when_the_last_part_is_paid(self):
        self.build(Granary)
        self.rounds(Granary.BUILD_TURNS - ONE_ROUND)
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.city_id), [])
        self.rounds(ONE_ROUND)
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.city_id), [Granary])
        self.assertEqual(self.currency(), STARTING_CURRENCY + INCOME * Granary.BUILD_TURNS - Granary.COST[Currency])
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.other_id), [])

    def test_a_city_has_one_of_each_building(self):
        self.build(Granary)
        message = self.refused_and_unchanged(lambda: self.build(Granary))
        self.assertEqual(message, ERR_ALREADY_QUEUED.format(name=A_NAME, building=shown_name(Granary)))
        self.rounds(Granary.BUILD_TURNS)
        message = self.refused_and_unchanged(lambda: self.build(Granary))
        self.assertEqual(message, ERR_ALREADY_BUILT.format(name=A_NAME, building=shown_name(Granary)))

    def test_a_world_wonder_that_stands_somewhere_cannot_be_built_again_by_anyone(self):
        self.build(GreatCavePainting)
        self.rounds(GreatCavePainting.BUILD_TURNS)
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.city_id), [GreatCavePainting])
        self.assertTrue(Production.wonder_is_built(game=self.game, wonder=GreatCavePainting))
        self.assertFalse(Production.wonder_is_built(game=self.game, wonder=ArrangementOfRocks))
        expected = ERR_WONDER_BUILT.format(wonder=shown_name(GreatCavePainting))
        self.assertEqual(Production.problem_queueing(game=self.game, city=self.other_id, kind=GreatCavePainting), expected)
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        self.assertEqual(self.refused_and_unchanged(lambda: Orders.build(game=self.game, city=self.other_id, kind=GreatCavePainting)), expected)

    def test_when_two_civilizations_build_the_same_world_wonder_the_first_to_finish_has_it_and_the_other_loses_what_it_paid(self):
        self.assertEqual(Production.wonder_builders(game=self.game, wonder=GreatCavePainting), [])
        self.build(GreatCavePainting)
        end_turn_by_order(game=self.game, civilization=FIRST_CIVILIZATION)
        self.assertEqual(Production.wonder_builders(game=self.game, wonder=GreatCavePainting), [self.city_id])
        Orders.build(game=self.game, city=self.other_id, kind=GreatCavePainting)
        end_turn_by_order(game=self.game, civilization=SECOND_CIVILIZATION)
        self.assertEqual(Production.wonder_builders(game=self.game, wonder=GreatCavePainting), [self.city_id, self.other_id])
        self.assertEqual(Production.wonder_builders(game=self.game, wonder=ArrangementOfRocks), [])
        self.rounds(GreatCavePainting.BUILD_TURNS - ONE_ROUND)
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.city_id), [GreatCavePainting])
        self.assertEqual(CityControl.buildings_of(game=self.game, city=self.other_id), [])
        self.assertEqual((self.other.get_queue(), self.other.get_progress()), ([], NO_PROGRESS))
        self.assertEqual(Production.waiting_cities(game=self.game, civilization=SECOND_CIVILIZATION), [self.other_id])
        self.assertLess(held(game=self.game, civilization=SECOND_CIVILIZATION, resource=Currency), STARTING_CURRENCY)
        self.assertEqual(Production.wonder_builders(game=self.game, wonder=GreatCavePainting), [])


class TestKindsOfALaterTheme(ProductionCase):

    THEME = LATER_CAVEMAN

    def test_a_world_wonder_in_any_city_of_a_civilization_unlocks_a_unit_for_every_city_of_that_civilization_only(self):
        other = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(Painter), required=shown_name(GreatCavePainting))
        self.assertEqual(self.refused_and_unchanged(lambda: self.build(Painter)), expected)
        give_building(game=self.game, city=self.another_city(), building=GreatCavePainting)
        self.build(Painter)
        self.assertEqual(Production.queue_of(game=self.game, city=self.city_id), [Painter])
        self.assertEqual(Production.problem_queueing(game=self.game, city=other, kind=Painter), expected)

    def bankrupting_warriors(self):
        """Put warriors of the first civilization on tiles, until supporting them costs all the currency the city brings in each turn."""
        x, _ = SETTLER_TILES[0]
        currency = resource_id(game=self.game, resource=Currency)
        while TurnControl.support_cost(game=self.game, civilization=FIRST_CIVILIZATION).get(currency, NOTHING_HELD) < INCOME:
            UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=OPEN_ROW)
            x += 1

    def test_a_bankrupt_civilization_builds_nothing_even_on_a_turn_that_costs_nothing(self):
        self.bankrupting_warriors()
        self.first.pay(resource=resource_id(game=self.game, resource=Currency), amount=STARTING_CURRENCY)
        self.build(Dawdler)
        self.city.set_progress(A_FREE_TURN)
        self.assertEqual(Production.part(kind=Dawdler, turn=A_FREE_TURN), {Currency: NOTHING_HELD})
        self.rounds(ONE_ROUND)
        self.assertTrue(self.first.is_bankrupt())
        self.assertTrue(self.city.is_blocked())
        self.assertEqual(self.city.get_progress(), A_FREE_TURN)

    def test_a_civilization_that_is_not_bankrupt_goes_on_building_on_a_turn_that_costs_nothing(self):
        self.bankrupting_warriors()
        self.build(Dawdler)
        self.city.set_progress(A_FREE_TURN)
        self.rounds(ONE_ROUND)
        self.assertFalse(self.first.is_bankrupt())
        self.assertFalse(self.city.is_blocked())
        self.assertEqual(self.city.get_progress(), A_FREE_TURN + ONE_ROUND)
        self.assertEqual(self.currency(), STARTING_CURRENCY)

