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

"""An order given in a game: which kind, who gave it, who received it, what it says and whether it is active."""

from enum import Enum

from microsponge.err_messages import ERR_ORDER_INVALID

# The turn an order was last served before it has been served at all.
NEVER = -1


class Reason(Enum):
    """Why an order is inactive. An inactive order costs nothing and does nothing."""

    COMPLETED = 1
    INVALID = 2
    DISABLED = 3


class GivenOrder:
    """One order in a civilization's table.

    The giver is the thing the order comes from and the receiver the thing ordered to do
    something. An order is active, or inactive with a reason: completed, disabled by the
    player, or invalid because something the order refers to is gone, which cannot be undone.
    """

    __slots__ = ('_kind', '_giver', '_receiver', '_what', '_reason', '_realized', '_served')

    def __init__(self, *, kind, giver, receiver, what, realized=False):
        self._kind = kind
        self._giver = giver
        self._receiver = receiver
        self._what = what
        self._reason = None
        self._realized = realized
        self._served = NEVER

    def get_kind(self):
        return self._kind

    def is_a(self, kind):
        """Return whether the order is of a kind, or of a theme's subclass of it."""
        return issubclass(self._kind, kind)

    def get_giver(self):
        return self._giver

    def get_receiver(self):
        return self._receiver

    def get_what(self):
        return self._what

    def set_what(self, what):
        """Change what the order says, which a player may do to any order that is not invalid."""
        self.check_valid()
        self._what = what

    def is_active(self):
        return self._reason is None

    def get_reason(self):
        """Return why the order is inactive, or None for an active order."""
        return self._reason

    def is_realized(self):
        """Return whether the helper AI made this order itself, to carry out an order it was given. Such an order costs nothing."""
        return self._realized

    def check_valid(self):
        if self._reason is Reason.INVALID:
            raise ValueError(ERR_ORDER_INVALID)

    def activate(self):
        """Make a completed or disabled order active again."""
        self.check_valid()
        self._reason = None

    def disable(self):
        self.check_valid()
        self._reason = Reason.DISABLED

    def complete(self):
        self.check_valid()
        self._reason = Reason.COMPLETED

    def invalidate(self):
        self._reason = Reason.INVALID

    def get_served(self):
        """Return the turn the order last had something done for it, which decides who has waited longest."""
        return self._served

    def set_served(self, turn):
        self._served = turn
