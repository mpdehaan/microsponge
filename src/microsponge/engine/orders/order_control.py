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

"""The rules for standing orders: giving one, what each costs, what a civilization can afford, and the limits on armies and divisions."""

from microsponge.engine.kinds.control_points import CONTROL_POINTS
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.orders.given_order import GivenOrder
from microsponge.engine.orders.order import GarrisonOrder
from microsponge.engine.orders.thing import ThingType
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.err_messages import ERR_ORDER_NOT_IN_THEME, ERR_ORDER_RECEIVER, ERR_OVER_CONTROL_POINTS, ERR_TOO_MANY_ARMIES, ERR_TOO_MANY_DIVISIONS

# An order that leads no group of units leads this many.
NO_UNITS = 0
ONE_UNIT = 1
# A civilization always may have this many armies and this many divisions.
AT_LEAST = 1


class OrderControl:
    """Static: the rules for the orders in a civilization's table. It is never made into an object."""

    __slots__ = ()

    @staticmethod
    def give(*, game, civilization, kind, giver, receiver, what, realized=False):
        """Add an order to a civilization's table and return it. The theme has to have the kind of order, and the receiver has to be a type of thing the kind can be given to."""
        theme = game.get_theme()
        if not any(issubclass(kind, known) for known in theme.ORDERS):
            raise ValueError(ERR_ORDER_NOT_IN_THEME.format(theme=shown_name(theme), order=shown_name(kind)))
        if receiver.type not in kind.RECEIVERS:
            raise ValueError(ERR_ORDER_RECEIVER.format(order=shown_name(kind)))
        order = GivenOrder(kind=kind, giver=giver, receiver=receiver, what=what, realized=realized)
        game.get_civilization(civilization).get_orders().add(order)
        return order

    @staticmethod
    def units_led(*, game, civilization, order):
        """Return how many units an order leads: one for a single unit, the units a garrison order keeps, and every unit of a division."""
        receiver = order.get_receiver()
        if receiver.type is ThingType.UNIT:
            return ONE_UNIT
        if receiver.type is not ThingType.DIVISION:
            return NO_UNITS
        if order.is_a(GarrisonOrder):
            return order.get_what().count
        return len(game.get_civilization(civilization).get_forces().get_division(receiver.id).get_units())

    @staticmethod
    def cost(*, game, civilization, order):
        """Return the points an order takes this turn: nothing when it is inactive or the helper AI made it, else its base cost, its cost for each unit it leads, and more when it is for one unit alone."""
        if not order.is_active() or order.is_realized():
            return 0
        kind = order.get_kind()
        alone = kind.LONE_UNIT_COST if order.get_receiver().type is ThingType.UNIT else 0
        return kind.BASE_COST + kind.UNIT_COST * OrderControl.units_led(game=game, civilization=civilization, order=order) + alone

    @staticmethod
    def taken(*, game, civilization, points):
        """Return how many of a kind of control points the civilization's active orders take each turn."""
        orders = game.get_civilization(civilization).get_orders().get_orders()
        return sum(OrderControl.cost(game=game, civilization=civilization, order=order) for order in orders if order.get_kind().POINTS is points)

    @staticmethod
    def left(*, game, civilization, points):
        """Return how many of a kind of control points a civilization has beyond what its active orders take, which is below 0 when they take too many."""
        return TurnControl.control_points(game=game, civilization=civilization, points=points) - OrderControl.taken(game=game, civilization=civilization, points=points)

    @staticmethod
    def problem_ending_turn(*, game, civilization):
        """Return why a civilization cannot end its turn as far as orders go, or None: its active orders may not take more of either kind of control points than it has."""
        for points in CONTROL_POINTS:
            if OrderControl.left(game=game, civilization=civilization, points=points) < 0:
                have = TurnControl.control_points(game=game, civilization=civilization, points=points)
                cost = OrderControl.taken(game=game, civilization=civilization, points=points)
                return ERR_OVER_CONTROL_POINTS.format(name=game.get_civilization(civilization).get_name(), have=have, points=shown_name(points), cost=cost)
        return None

    @staticmethod
    def most(*, game, civilization, cities_for_each):
        """Return how many armies or divisions a civilization may have: one for every so many cities, rounding up, and always one."""
        return OrderControl.allowed(cities=len(game.get_cities_of(civilization)), cities_for_each=cities_for_each)

    @staticmethod
    def allowed(*, cities, cities_for_each):
        """Return how many groups so many cities allow at one group for every so many cities: the count rounds up and is never below one."""
        return max(AT_LEAST, -(-cities // cities_for_each))

    @staticmethod
    def add_army(*, game, civilization):
        """Give a civilization another army and return the army's id, which is refused past the theme's limit."""
        holder = game.get_civilization(civilization)
        most = OrderControl.most(game=game, civilization=civilization, cities_for_each=game.get_theme().CITIES_PER_ARMY)
        if len(holder.get_forces().get_armies()) >= most:
            raise ValueError(ERR_TOO_MANY_ARMIES.format(name=holder.get_name(), most=most))
        return holder.get_forces().add_army()

    @staticmethod
    def add_division(*, game, civilization, army):
        """Give an army of a civilization another division and return the division, which is refused past the theme's limit."""
        holder = game.get_civilization(civilization)
        most = OrderControl.most(game=game, civilization=civilization, cities_for_each=game.get_theme().CITIES_PER_DIVISION)
        if len(holder.get_forces().get_divisions()) >= most:
            raise ValueError(ERR_TOO_MANY_DIVISIONS.format(name=holder.get_name(), most=most))
        return holder.get_forces().add_division(army)
