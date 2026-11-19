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

"""The table of a civilization's orders."""


class OrderTable:
    """The orders a civilization has given, in the order they were given, and the orders its helper AI realized from them.

    A player reads and changes only the orders the player gave. The realized orders are how the
    helper AI interprets those, and neither a person nor a main AI reads them: tests may.
    """

    __slots__ = ('_orders',)

    def __init__(self):
        self._orders = []

    def add(self, order):
        self._orders.append(order)

    def remove(self, order):
        self._orders.remove(order)

    def get_orders(self):
        """Return the orders the player gave."""
        return [order for order in self._orders if not order.is_realized()]

    def get_realized(self):
        """Return the orders the helper AI made itself."""
        return [order for order in self._orders if order.is_realized()]

    def active(self, kind):
        """Return every active order of a kind, given or realized, in the order they were added."""
        return [order for order in self._orders if order.is_active() and order.is_a(kind)]

    def get_all(self):
        return list(self._orders)
