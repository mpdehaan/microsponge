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

"""The Hand: the helper AI carrying out standing orders for research, cities, settlers and divisions, and doing nothing no order asks for."""

import unittest

from caveman_game import FIRST_CIVILIZATION, THE_WORLD, WATER_TILE, end_rounds, found_village, learn, settler_of, started_caveman_game
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.research import Research
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.orders.given_order import NEVER, Reason
from microsponge.engine.orders.order import BuildOrder, ExpandOrder, GarrisonOrder, MarchOrder, RaiseOrder, ResearchOrder, RetireOrder, SettlerOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.thing import army_thing, city_thing, civilization_thing, division_thing, unit_thing
from microsponge.engine.orders.what import BuildTarget, Buildings, CityTarget, Garrison, March, NoDetails, Technologies, Units
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.players.hand import Hand
from microsponge.themes.caveman.theme import Caveman
from microsponge.engine.players.knowledge import Knowledge
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.unit_control import UnitControl
from microsponge.themes.caveman.buildings import Barracks, ChieftainsHut
from microsponge.themes.caveman.technologies import Clubs, Fire, Leadership
from microsponge.themes.caveman.terrains import Water
from microsponge.themes.caveman.units import CaptainCaveman, Settler, Clubber

FIRST = FIRST_CIVILIZATION
SECOND = FIRST + 1
A_NAME = 'Bedrock'
ANOTHER_NAME = 'Gravel'
A_SEED = 3
ONE_ROUND = 1
ENOUGH_CITIZENS = 3
# Currency enough that a test is not about whether the theme's prices can be paid.
PLENTY = 10000
# Rounds enough for a unit to walk a few tiles, and for a settler to find a site and build a village.
A_SHORT_WALK = 6
A_LONG_WALK = 60
FIGHTERS = (CaptainCaveman, Clubber)
# A kind of unit that cannot attack, which no division takes in.
NOT_A_FIGHTER = next(kind for kind in Caveman.UNITS if kind.ATTACK is NO_DICE and not issubclass(kind, SettlerUnit))
# A tile a few steps east of the first civilization's first village, and tiles on each side of the lake in the same row, as (x, y).
NEAR_TILE = (10, 12)
WEST_OF_LAKE = (16, 11)
EAST_OF_LAKE = (23, 11)
# A tile a few steps west of the second civilization's first village, and the tile next to it.
NEAR_SECOND = (30, 14)
NEXT_TO_NEAR_SECOND = (29, 14)


class HandCase(unittest.TestCase):
    """A started game of caveman in which the first civilization has its first village, one army and one division."""

    def setUp(self):
        self.game = started_caveman_game()
        self.game.set_seed(A_SEED)
        self.city = found_village(game=self.game, civilization=FIRST, name=A_NAME)
        self.first = self.game.get_civilization(FIRST)
        self.here = city_thing(self.city)
        army = OrderControl.add_army(game=self.game, civilization=FIRST)
        self.division = OrderControl.add_division(game=self.game, civilization=FIRST, army=army)
        self.me = division_thing(self.division.get_id())

    def give(self, *, kind, giver, receiver, what):
        return OrderControl.give(game=self.game, civilization=FIRST, kind=kind, giver=giver, receiver=receiver, what=what)

    def carry_out(self):
        Hand.carry_out(game=self.game, civilization=FIRST)

    def rounds(self, count):
        """Have the Hand carry out the first civilization's orders and end a round, so many times over, stopping when the game is over."""
        for _ in range(count):
            self.carry_out()
            if self.game.is_over():
                return
            end_rounds(game=self.game, rounds=ONE_ROUND)

    def queue(self):
        return Production.queue_of(game=self.game, city=self.city)

    def clubber(self, *, tile, owner=FIRST, kind=Clubber):
        unit = UnitControl.place(game=self.game, kind=kind, owner=owner, world=THE_WORLD, x=tile[0], y=tile[1])
        if owner == FIRST:
            self.division.add_unit(unit)
        return unit

    def tile_of(self, unit):
        _, x, y = UnitControl.tile_of(game=self.game, unit=unit)
        return (x, y)

    def raise_order(self, count):
        return self.give(kind=RaiseOrder, giver=self.me, receiver=self.here, what=Units(targets=(BuildTarget(kinds=FIGHTERS, count=count),)))


class TestNothingWithoutOrders(HandCase):

    def test_with_no_orders_a_city_builds_nothing_and_a_unit_stays_where_it_is(self):
        learn(game=self.game, civilization=FIRST, technology=Clubs)
        unit = self.clubber(tile=NEAR_TILE)
        self.rounds(A_SHORT_WALK)
        self.assertEqual(self.queue(), [])
        self.assertEqual(self.tile_of(unit), NEAR_TILE)
        self.assertEqual(self.first.get_orders().get_all(), [])

    def test_with_no_research_order_a_technology_is_picked_at_random_so_that_the_turn_can_end(self):
        self.assertTrue(Research.must_choose(game=self.game, civilization=FIRST))
        self.carry_out()
        self.assertIn(Research.researching(game=self.game, civilization=FIRST), Research.available(game=self.game, civilization=FIRST))
        Orders.end_turn(game=self.game, civilization=FIRST)
        self.assertEqual(self.game.get_playing(), SECOND)


class TestResearchAndBuilding(HandCase):

    def test_a_research_order_is_followed_in_its_order_past_what_cannot_be_researched(self):
        me = civilization_thing(FIRST)
        learn(game=self.game, civilization=FIRST, technology=Fire)
        self.give(kind=ResearchOrder, giver=me, receiver=me, what=Technologies(kinds=(Fire, Leadership, Clubs)))
        self.carry_out()
        self.assertIs(Research.researching(game=self.game, civilization=FIRST), Leadership)

    def test_a_build_order_builds_the_first_building_the_city_can_build(self):
        learn(game=self.game, civilization=FIRST, technology=Leadership)
        order = self.give(kind=BuildOrder, giver=self.here, receiver=self.here, what=Buildings(kinds=(Barracks, ChieftainsHut)))
        self.assertEqual(order.get_served(), NEVER)
        self.carry_out()
        self.assertEqual(self.queue(), [ChieftainsHut])
        self.assertEqual(order.get_served(), self.game.get_turn())

    def test_a_disabled_order_does_nothing(self):
        learn(game=self.game, civilization=FIRST, technology=Leadership)
        self.give(kind=BuildOrder, giver=self.here, receiver=self.here, what=Buildings(kinds=(ChieftainsHut,))).disable()
        self.carry_out()
        self.assertEqual(self.queue(), [])

    def test_a_raise_order_has_a_city_build_units_that_join_the_division_and_is_completed_when_the_division_has_them(self):
        learn(game=self.game, civilization=FIRST, technology=Clubs)
        order = self.raise_order(1)
        self.carry_out()
        self.assertEqual(self.queue(), [Clubber])
        self.rounds(Clubber.BUILD_TURNS + ONE_ROUND)
        self.assertEqual(len(self.division.get_units()), 1)
        self.assertIs(UnitControl.kind_of(game=self.game, unit=self.division.get_units()[0]), Clubber)
        self.assertEqual(order.get_reason(), Reason.COMPLETED)
        self.assertEqual(self.queue(), [])

    def test_a_city_that_cannot_build_the_first_target_of_a_raise_order_builds_from_a_later_one(self):
        learn(game=self.game, civilization=FIRST, technology=Clubs)
        theme = self.game.get_theme()
        out_of_reach = next(kind for kind in theme.UNITS if any(required in theme.BUILDINGS for required in kind.REQUIRES))
        targets = (BuildTarget(kinds=(out_of_reach,), count=1), BuildTarget(kinds=FIGHTERS, count=1))
        self.give(kind=RaiseOrder, giver=self.me, receiver=self.here, what=Units(targets=targets))
        self.carry_out()
        self.assertEqual(len(self.queue()), 1)
        self.assertIn(self.queue()[0], FIGHTERS)

    def test_the_order_that_has_waited_longest_is_served_first(self):
        learn(game=self.game, civilization=FIRST, technology=Clubs)
        learn(game=self.game, civilization=FIRST, technology=Leadership)
        self.first.add(resource=self.game.get_catalog().get_id(category=Category.RESOURCES, kind=self.game.get_theme().PRIMARY_RESOURCE), amount=PLENTY)
        build = self.give(kind=BuildOrder, giver=self.here, receiver=self.here, what=Buildings(kinds=(ChieftainsHut,)))
        raising = self.raise_order(1)
        self.carry_out()
        self.assertEqual(self.queue(), [ChieftainsHut])
        self.rounds(ChieftainsHut.BUILD_TURNS + ONE_ROUND)
        self.assertEqual(self.queue(), [Clubber])
        self.assertLess(build.get_served(), raising.get_served())


class TestSettling(HandCase):

    def test_an_expand_order_builds_a_settler_that_the_hand_sends_to_build_a_city_by_an_order_no_player_sees(self):
        self.game.get_city(self.city).set_citizens(ENOUGH_CITIZENS)
        found_village(game=self.game, civilization=SECOND, name=ANOTHER_NAME)
        expand = self.give(kind=ExpandOrder, giver=self.here, receiver=self.here, what=NoDetails())
        self.carry_out()
        self.assertEqual(self.queue(), [Settler])
        self.rounds(Settler.BUILD_TURNS + ONE_ROUND)
        settlers = Knowledge.settlers_of(game=self.game, civilization=FIRST)
        table = self.first.get_orders()
        self.assertEqual(len(settlers), 1)
        self.assertEqual([order.get_receiver() for order in table.get_realized()], [unit_thing(settlers[0])])
        self.assertEqual(table.get_orders(), [expand])
        self.assertEqual(table.get_realized()[0].get_giver(), self.here)
        expand.disable()
        self.rounds(A_LONG_WALK)
        self.assertEqual(len(self.game.get_cities_of(FIRST)), 2)
        self.assertEqual(table.get_realized(), [])
        self.assertEqual(Knowledge.settlers_of(game=self.game, civilization=FIRST), [])

    def test_a_settler_with_no_order_and_no_city_ordered_to_expand_waits(self):
        settler = settler_of(game=self.game, civilization=SECOND)
        before = self.tile_of(settler)
        TurnControl.end_turn(self.game)
        self.assertEqual(self.game.get_playing(), SECOND)
        Hand.carry_out(game=self.game, civilization=SECOND)
        self.assertEqual(self.tile_of(settler), before)
        self.assertEqual(self.game.get_cities_of(SECOND), [])
        order = OrderControl.give(game=self.game, civilization=SECOND, kind=SettlerOrder, giver=unit_thing(settler), receiver=unit_thing(settler), what=NoDetails())
        Hand.carry_out(game=self.game, civilization=SECOND)
        self.assertEqual(len(self.game.get_cities_of(SECOND)), 1)
        self.assertEqual(order.get_reason(), Reason.COMPLETED)


class TestDivisions(HandCase):

    def test_a_garrison_order_brings_the_nearest_unit_inside_the_city_and_keeps_it_there_and_leaves_the_others(self):
        near = self.clubber(tile=NEAR_TILE)
        far = self.clubber(tile=WEST_OF_LAKE)
        pool = self.first.get_policy_points()
        self.give(kind=GarrisonOrder, giver=self.here, receiver=self.me, what=Garrison(place=CityTarget(city=self.city), count=1))
        self.carry_out()
        self.assertNotEqual(self.tile_of(near), NEAR_TILE)
        self.assertEqual(self.first.get_policy_points(), pool)
        self.rounds(A_SHORT_WALK)
        self.assertEqual(Knowledge.city_of(game=self.game, unit=near), self.city)
        self.assertEqual(self.tile_of(far), WEST_OF_LAKE)

    def test_a_march_order_takes_an_empty_enemy_city_which_wins_the_game_and_is_then_completed_and_a_garrisoned_unit_does_not_march(self):
        target = found_village(game=self.game, civilization=SECOND, name=ANOTHER_NAME)
        Orders.declare_war(game=self.game, civilization=FIRST, on=SECOND)
        guard = self.clubber(tile=NEAR_TILE)
        self.give(kind=GarrisonOrder, giver=self.here, receiver=self.me, what=Garrison(place=CityTarget(city=self.city), count=1))
        self.rounds(A_SHORT_WALK)
        marcher = self.clubber(tile=NEAR_SECOND)
        march = self.give(kind=MarchOrder, giver=self.me, receiver=self.me, what=March(target=CityTarget(city=target)))
        self.rounds(A_SHORT_WALK)
        self.assertEqual(self.game.get_city(target).get_owner(), FIRST)
        self.assertEqual(Knowledge.city_of(game=self.game, unit=marcher), target)
        self.assertEqual(Knowledge.city_of(game=self.game, unit=guard), self.city)
        self.assertTrue(self.game.is_over())
        self.carry_out()
        self.assertEqual(march.get_reason(), Reason.COMPLETED)

    def test_a_march_order_says_whether_a_unit_attacks_a_stronger_enemy_next_to_it_or_leaves_enemy_units_alone(self):
        target = found_village(game=self.game, civilization=SECOND, name=ANOTHER_NAME)
        Orders.declare_war(game=self.game, civilization=FIRST, on=SECOND)
        unit = self.clubber(tile=NEXT_TO_NEAR_SECOND)
        self.clubber(tile=NEAR_SECOND, owner=SECOND, kind=CaptainCaveman)
        careful = March(target=CityTarget(city=target))
        bold = March(target=CityTarget(city=target), bold=True)
        blinkered = March(target=CityTarget(city=target), bold=True, ignore_units=True)
        self.assertFalse(Hand.fight_next_to(game=self.game, unit=unit, civilization=FIRST, what=careful))
        self.assertFalse(Hand.fight_next_to(game=self.game, unit=unit, civilization=FIRST, what=blinkered))
        self.assertTrue(Hand.fight_next_to(game=self.game, unit=unit, civilization=FIRST, what=bold))

    def test_a_dead_unit_leaves_its_division(self):
        unit = self.clubber(tile=NEAR_TILE)
        UnitControl.remove(game=self.game, unit=unit)
        self.carry_out()
        self.assertEqual(self.division.get_units(), [])


class TestRoutes(HandCase):

    def test_a_unit_walks_around_a_lake_it_has_seen_and_not_into_it(self):
        unit = self.clubber(tile=WEST_OF_LAKE)
        self.first.get_memory(THE_WORLD).remember_all(self.game.get_world(THE_WORLD))
        self.assertIs(self.game.get_terrain(world=THE_WORLD, x=WATER_TILE[0], y=WEST_OF_LAKE[1]), Water)
        for _ in range(A_LONG_WALK):
            step = Hand.first_step(game=self.game, unit=unit, civilization=FIRST, arrived=lambda x, y: (x, y) == EAST_OF_LAKE)
            if step is None:
                break
            self.assertIsNot(self.game.get_terrain(world=THE_WORLD, x=step[0], y=step[1]), Water)
            UnitControl.move_to(game=self.game, unit=unit, x=step[0], y=step[1])
            if self.tile_of(unit) == EAST_OF_LAKE:
                break
        self.assertEqual(self.tile_of(unit), EAST_OF_LAKE)

    def test_no_route_is_found_to_a_tile_that_cannot_be_reached(self):
        unit = self.clubber(tile=WEST_OF_LAKE)
        self.first.get_memory(THE_WORLD).remember_all(self.game.get_world(THE_WORLD))
        self.assertIsNone(Hand.first_step(game=self.game, unit=unit, civilization=FIRST, arrived=lambda x, y: False))
        self.assertEqual(Knowledge.city_of(game=self.game, unit=unit), NOTHING)


class TestRetiring(HandCase):

    def test_an_order_to_retire_a_unit_takes_the_unit_out_of_the_game_for_nothing_and_gives_nothing_back(self):
        unit = self.clubber(tile=NEAR_TILE)
        holdings = dict(self.first.get_holdings())
        order = self.give(kind=RetireOrder, giver=self.me, receiver=unit_thing(unit), what=NoDetails())
        self.assertEqual(OrderControl.cost(game=self.game, civilization=FIRST, order=order), 0)
        self.carry_out()
        self.assertNotIn(unit, Knowledge.units_of(game=self.game, civilization=FIRST))
        self.assertEqual(self.division.get_units(), [])
        self.assertEqual(order.get_reason(), Reason.COMPLETED)
        self.assertEqual(self.first.get_holdings(), holdings)

    def test_an_order_to_retire_a_division_or_an_army_retires_every_unit_of_it_and_no_other(self):
        for receiver in (self.me, army_thing(self.division.get_army())):
            with self.subTest(receiver=receiver):
                units = [self.clubber(tile=tile) for tile in (NEAR_TILE, NEAR_SECOND)]
                other = self.clubber(tile=WEST_OF_LAKE, kind=NOT_A_FIGHTER)
                self.division.remove_unit(other)
                order = self.give(kind=RetireOrder, giver=self.me, receiver=receiver, what=NoDetails())
                self.assertEqual(OrderControl.cost(game=self.game, civilization=FIRST, order=order), 0)
                self.carry_out()
                alive = Knowledge.units_of(game=self.game, civilization=FIRST)
                self.assertEqual([unit for unit in units if unit in alive], [])
                self.assertIn(other, alive)
                UnitControl.remove(game=self.game, unit=other)


class TestAUnitAlreadyGone(HandCase):

    def test_a_unit_killed_earlier_in_the_turn_does_nothing_when_its_turn_to_act_comes(self):
        unit = self.clubber(tile=NEAR_TILE)
        UnitControl.remove(game=self.game, unit=unit)
        acted = []
        Hand.repeat(game=self.game, unit=unit, action=lambda: acted.append(unit))
        self.assertEqual(acted, [])
