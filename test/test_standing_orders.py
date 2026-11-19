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

"""Standing orders: the kinds of order, giving one, what each costs in Policy and Command, armies and divisions, and the referee AI."""

import unittest

from caveman_game import FIRST_CIVILIZATION, THE_WORLD, end_rounds, found_village, give_building, settler_of, started_caveman_game
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.control_points import CONTROL_POINTS, Command, ControlPoints, Policy, points_given
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.orders.given_order import Reason
from microsponge.engine.orders.order import BuildOrder, CommandOrder, GarrisonOrder, MarchOrder, PolicyOrder, ResearchOrder, SettlerOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.referee import Referee
from microsponge.engine.orders.thing import city_thing, civilization_thing, division_thing, unit_thing
from microsponge.engine.orders.what import Buildings, CityTarget, Garrison, March, NoDetails, Technologies
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.unit_control import UnitControl
from microsponge.err_messages import (
    ERR_NO_SUCH_DIVISION, ERR_ORDER_INVALID, ERR_ORDER_NOT_IN_THEME, ERR_ORDER_RECEIVER, ERR_OVER_CONTROL_POINTS, ERR_TOO_MANY_ARMIES, ERR_TOO_MANY_DIVISIONS,
)
from microsponge.themes import THEMES
from microsponge.themes.caveman.buildings import ChieftainsHut, Watchtower
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.technologies import Clubs
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import AngryBird, Warrior
from refusals import Refusals

FIRST = FIRST_CIVILIZATION
SECOND = FIRST + 1
A_NAME = 'Bedrock'
ORDER_SUFFIX = 'Order'
DEAR = 5
ONE_ROUND = 1
A_FEW = 3
NO_DIVISION = 99
# With one group for every 5 cities, so many cities allow so many groups.
FOR_EACH = 5
CITIES_AND_GROUPS = ((0, 1), (1, 1), (5, 1), (6, 2), (10, 2), (11, 3))
# Tiles near the first civilization's first village where units can stand, as (x, y).
OPEN_TILES = ((9, 10), (9, 12), (9, 14))


def without(*, orders, kind):
    return tuple(order for order in orders if order is not kind)


class DearBuildOrder(BuildOrder):
    BASE_COST = DEAR


class NoMarching(Caveman):
    ORDERS = without(orders=Caveman.ORDERS, kind=MarchOrder)


class DearBuilding(Caveman):
    ORDERS = (*without(orders=Caveman.ORDERS, kind=BuildOrder), DearBuildOrder)


class TestOrderKinds(unittest.TestCase):

    def test_every_order_of_every_theme_ends_in_order_and_takes_policy_or_command(self):
        for theme in THEMES:
            self.assertTrue(theme.ORDERS)
            for order in theme.ORDERS:
                with self.subTest(theme=theme, order=order):
                    self.assertTrue(order.__name__.endswith(ORDER_SUFFIX))
                    self.assertNotEqual(issubclass(order, PolicyOrder), issubclass(order, CommandOrder))
                    self.assertIs(order.POINTS, Policy if issubclass(order, PolicyOrder) else Command)
                    self.assertTrue(order.RECEIVERS)

    def test_policy_and_command_are_the_two_kinds_of_control_points(self):
        self.assertEqual(CONTROL_POINTS, (Policy, Command))
        for points in CONTROL_POINTS:
            self.assertTrue(issubclass(points, ControlPoints))


class OrdersCase(Refusals, unittest.TestCase):
    """A started game of caveman in which the first civilization has its first village."""

    theme = Caveman

    def setUp(self):
        self.game = started_caveman_game(theme=self.theme)
        self.city = found_village(game=self.game, civilization=FIRST, name=A_NAME)
        self.first = self.game.get_civilization(FIRST)
        self.here = city_thing(self.city)

    def give(self, *, kind, giver, receiver, what):
        return OrderControl.give(game=self.game, civilization=FIRST, kind=kind, giver=giver, receiver=receiver, what=what)

    def build_order(self, *, kind=BuildOrder):
        return self.give(kind=kind, giver=self.here, receiver=self.here, what=Buildings(kinds=(ChieftainsHut,)))

    def division(self):
        army = OrderControl.add_army(game=self.game, civilization=FIRST)
        return OrderControl.add_division(game=self.game, civilization=FIRST, army=army)

    def warriors(self, *, division, count):
        units = [UnitControl.place(game=self.game, kind=Warrior, owner=FIRST, world=THE_WORLD, x=x, y=y) for x, y in OPEN_TILES[:count]]
        for unit in units:
            division.add_unit(unit)
        return units

    def cost(self, order):
        return OrderControl.cost(game=self.game, civilization=FIRST, order=order)

    def left(self, points):
        return OrderControl.left(game=self.game, civilization=FIRST, points=points)

    def have(self, points):
        return TurnControl.control_points(game=self.game, civilization=FIRST, points=points)


class TestGivingOrders(OrdersCase):

    def test_an_order_given_is_in_the_table_active_with_its_giver_its_receiver_and_what_it_says(self):
        what = Buildings(kinds=(ChieftainsHut,))
        order = self.give(kind=BuildOrder, giver=self.here, receiver=self.here, what=what)
        self.assertEqual(self.first.get_orders().get_orders(), [order])
        self.assertEqual((order.get_kind(), order.get_giver(), order.get_receiver(), order.get_what()), (BuildOrder, self.here, self.here, what))
        self.assertTrue(order.is_active())
        self.assertIsNone(order.get_reason())
        self.assertEqual(self.game.get_civilization(SECOND).get_orders().get_orders(), [])

    def test_an_order_cannot_be_given_to_a_type_of_thing_its_kind_does_not_take(self):
        settler = unit_thing(settler_of(game=self.game, civilization=SECOND))
        message = self.refused(lambda: self.give(kind=BuildOrder, giver=self.here, receiver=settler, what=Buildings(kinds=())))
        self.assertEqual(message, ERR_ORDER_RECEIVER.format(order=shown_name(BuildOrder)))
        self.assertEqual(self.first.get_orders().get_all(), [])

    def test_an_order_is_completed_disabled_and_made_active_again_and_an_invalid_order_stays_invalid(self):
        order = self.build_order()
        for change, reason in ((order.disable, Reason.DISABLED), (order.complete, Reason.COMPLETED)):
            change()
            self.assertEqual((order.is_active(), order.get_reason()), (False, reason))
            order.activate()
            self.assertTrue(order.is_active())
        order.invalidate()
        self.assertEqual(order.get_reason(), Reason.INVALID)
        for change in (order.activate, order.disable, order.complete, lambda: order.set_what(Buildings(kinds=()))):
            self.assertEqual(self.refused(change), ERR_ORDER_INVALID)
        self.assertEqual(order.get_reason(), Reason.INVALID)

    def test_the_orders_the_helper_ai_realized_are_kept_apart_from_the_orders_the_player_gave(self):
        given = self.build_order()
        settler = unit_thing(settler_of(game=self.game, civilization=SECOND))
        realized = OrderControl.give(game=self.game, civilization=FIRST, kind=SettlerOrder, giver=self.here, receiver=settler, what=NoDetails(), realized=True)
        table = self.first.get_orders()
        self.assertEqual((table.get_orders(), table.get_realized(), table.get_all()), ([given], [realized], [given, realized]))
        self.assertEqual(table.active(SettlerOrder), [realized])
        self.assertEqual(self.cost(realized), 0)
        table.remove(given)
        self.assertEqual(table.get_orders(), [])


class TestAThemeWithoutAnOrder(OrdersCase):
    theme = NoMarching

    def test_an_order_the_theme_does_not_have_cannot_be_given(self):
        me = division_thing(self.division().get_id())
        message = self.refused(lambda: self.give(kind=MarchOrder, giver=me, receiver=me, what=March(target=CityTarget(city=self.city))))
        self.assertEqual(message, ERR_ORDER_NOT_IN_THEME.format(theme=shown_name(NoMarching), order=shown_name(MarchOrder)))
        self.assertEqual(self.first.get_orders().get_all(), [])


class TestAThemeWithItsOwnOrder(OrdersCase):
    theme = DearBuilding

    def test_a_theme_subclasses_an_order_to_change_what_the_order_costs(self):
        order = self.build_order(kind=DearBuildOrder)
        self.assertTrue(order.is_a(BuildOrder))
        self.assertEqual(self.cost(order), DEAR)
        self.assertEqual(self.first.get_orders().active(BuildOrder), [order])


class TestWhatOrdersCost(OrdersCase):

    def test_a_policy_order_costs_its_base_cost_and_an_order_for_one_unit_alone_costs_more(self):
        settler = unit_thing(settler_of(game=self.game, civilization=SECOND))
        me = civilization_thing(FIRST)
        research = self.give(kind=ResearchOrder, giver=me, receiver=me, what=Technologies(kinds=(Clubs,)))
        alone = self.give(kind=SettlerOrder, giver=settler, receiver=settler, what=NoDetails())
        self.assertEqual(self.cost(self.build_order()), BuildOrder.BASE_COST)
        self.assertEqual(self.cost(research), ResearchOrder.BASE_COST)
        self.assertEqual(self.cost(alone), SettlerOrder.BASE_COST + SettlerOrder.LONE_UNIT_COST)
        self.assertGreater(self.cost(alone), self.cost(research))

    def test_a_command_order_costs_for_each_unit_it_leads_and_a_garrison_order_leads_only_the_units_it_keeps(self):
        division = self.division()
        self.warriors(division=division, count=A_FEW)
        me = division_thing(division.get_id())
        march = self.give(kind=MarchOrder, giver=me, receiver=me, what=March(target=CityTarget(city=self.city)))
        garrison = self.give(kind=GarrisonOrder, giver=self.here, receiver=me, what=Garrison(place=CityTarget(city=self.city), count=1))
        self.assertEqual(self.cost(march), A_FEW * MarchOrder.UNIT_COST)
        self.assertEqual(self.cost(garrison), GarrisonOrder.UNIT_COST)
        self.assertEqual(OrderControl.taken(game=self.game, civilization=FIRST, points=Command), self.cost(march) + self.cost(garrison))
        self.assertEqual(OrderControl.taken(game=self.game, civilization=FIRST, points=Policy), 0)

    def test_an_inactive_order_costs_nothing(self):
        order = self.build_order()
        before = self.left(Policy)
        order.disable()
        self.assertEqual(self.cost(order), 0)
        self.assertEqual(self.left(Policy), before + BuildOrder.BASE_COST)

    def test_a_turn_cannot_end_while_the_active_orders_take_more_points_than_the_civilization_has(self):
        orders = [self.build_order() for _ in range(self.have(Policy) + 1)]
        self.assertIsNone(Orders.research(game=self.game, civilization=FIRST, technology=Clubs))
        expected = ERR_OVER_CONTROL_POINTS.format(name=self.first.get_name(), have=self.have(Policy), points=shown_name(Policy), cost=len(orders) * BuildOrder.BASE_COST)
        self.assertEqual(OrderControl.problem_ending_turn(game=self.game, civilization=FIRST), expected)
        self.assertEqual(self.refused(lambda: Orders.end_turn(game=self.game, civilization=FIRST)), expected)
        self.assertEqual(self.game.get_playing(), FIRST)
        orders[0].disable()
        self.assertIsNone(OrderControl.problem_ending_turn(game=self.game, civilization=FIRST))
        Orders.end_turn(game=self.game, civilization=FIRST)
        self.assertEqual(self.game.get_playing(), SECOND)


class TestControlPoints(OrdersCase):

    def test_a_civilization_has_the_command_of_its_theme_its_cities_and_its_buildings(self):
        idle = Village.IDLE_CONTROL_POINTS[Command]
        expected = points_given(by=Caveman, points=Command) + points_given(by=Village, points=Command) + idle
        self.assertEqual(self.have(Command), expected)
        give_building(game=self.game, city=self.city, building=Watchtower)
        self.assertEqual(self.have(Command), expected + points_given(by=Watchtower, points=Command))
        self.assertGreater(points_given(by=Watchtower, points=Command), 0)
        self.assertEqual(points_given(by=Watchtower, points=Policy), 0)
        self.assertLess(points_given(by=Caveman, points=Command), points_given(by=Caveman, points=Policy))

    def test_a_city_that_builds_nothing_adds_policy_and_command_and_a_city_that_builds_does_not(self):
        idle = {points: self.have(points) for points in CONTROL_POINTS}
        Orders.build(game=self.game, city=self.city, kind=AngryBird)
        for points in CONTROL_POINTS:
            with self.subTest(points=points):
                self.assertGreater(Village.IDLE_CONTROL_POINTS[points], 0)
                self.assertEqual(self.have(points), idle[points] - Village.IDLE_CONTROL_POINTS[points])
        Orders.build_nothing(game=self.game, city=self.city)
        self.assertEqual(self.have(Policy), idle[Policy])


class TestForces(OrdersCase):

    def test_a_civilization_has_one_army_and_one_division_for_so_many_cities_and_always_one_of_each(self):
        self.assertEqual(len(self.game.get_cities_of(SECOND)), 0)
        for civilization in (FIRST, SECOND):
            with self.subTest(civilization=civilization):
                name = self.game.get_civilization(civilization).get_name()
                army = OrderControl.add_army(game=self.game, civilization=civilization)
                division = OrderControl.add_division(game=self.game, civilization=civilization, army=army)
                forces = self.game.get_civilization(civilization).get_forces()
                self.assertEqual((forces.get_armies(), forces.get_divisions(), division.get_army()), ([army], [division], army))
                self.assertEqual(self.refused(lambda: OrderControl.add_army(game=self.game, civilization=civilization)), ERR_TOO_MANY_ARMIES.format(name=name, most=1))
                message = self.refused(lambda: OrderControl.add_division(game=self.game, civilization=civilization, army=army))
                self.assertEqual(message, ERR_TOO_MANY_DIVISIONS.format(name=name, most=1))
                self.assertEqual(len(forces.get_divisions()), 1)

    def test_the_limits_round_up(self):
        for cities, allowed in CITIES_AND_GROUPS:
            with self.subTest(cities=cities):
                self.assertEqual(OrderControl.allowed(cities=cities, cities_for_each=FOR_EACH), allowed)
        self.assertEqual(OrderControl.most(game=self.game, civilization=FIRST, cities_for_each=Caveman.CITIES_PER_DIVISION), 1)
        self.assertLess(Caveman.CITIES_PER_DIVISION, Caveman.CITIES_PER_ARMY)

    def test_a_division_holds_its_units_and_its_bases_and_a_unit_is_found_by_its_division(self):
        division = self.division()
        units = self.warriors(division=division, count=A_FEW)
        division.add_unit(units[0])
        division.set_bases([self.city])
        forces = self.first.get_forces()
        self.assertEqual((division.get_units(), division.get_bases()), (units, [self.city]))
        self.assertIs(forces.division_of(units[0]), division)
        division.remove_unit(units[0])
        self.assertIsNone(forces.division_of(units[0]))
        self.assertIs(forces.get_division(division.get_id()), division)
        self.assertEqual(self.refused(lambda: forces.get_division(NO_DIVISION)), ERR_NO_SUCH_DIVISION.format(division=NO_DIVISION))


class TestReferee(OrdersCase):

    def test_an_order_for_a_unit_that_is_gone_is_invalid_and_costs_nothing(self):
        unit = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST, world=THE_WORLD, x=OPEN_TILES[0][0], y=OPEN_TILES[0][1])
        order = self.give(kind=SettlerOrder, giver=unit_thing(unit), receiver=unit_thing(unit), what=NoDetails())
        kept = self.build_order()
        Referee.review(game=self.game, civilization=FIRST)
        self.assertTrue(order.is_active())
        UnitControl.remove(game=self.game, unit=unit)
        Referee.review(game=self.game, civilization=FIRST)
        self.assertEqual((order.get_reason(), self.cost(order)), (Reason.INVALID, 0))
        self.assertTrue(kept.is_active())

    def test_the_orders_about_a_city_that_was_taken_are_invalid(self):
        division = self.division()
        me = division_thing(division.get_id())
        build = self.build_order()
        garrison = self.give(kind=GarrisonOrder, giver=me, receiver=me, what=Garrison(place=CityTarget(city=self.city), count=1))
        march = self.give(kind=MarchOrder, giver=me, receiver=me, what=March(target=CityTarget(city=self.city)))
        CityControl.capture(game=self.game, city=self.city, by=SECOND)
        end_rounds(game=self.game, rounds=ONE_ROUND)
        Referee.review(game=self.game, civilization=FIRST)
        self.assertEqual((build.get_reason(), garrison.get_reason()), (Reason.INVALID, Reason.INVALID))
        self.assertTrue(march.is_active())
