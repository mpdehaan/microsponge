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

"""The points a civilization gives orders with: Policy and Command, the two kinds of control points."""

from microsponge.engine.kinds.kind import Kind

# What something gives of a kind of control points when it says nothing about that kind.
NO_POINTS = 0


class ControlPoints(Kind):
    """A kind of points that orders take while they are in force. A theme, its city spec and its buildings say how many of each a civilization has each turn, in CONTROL_POINTS."""


class Policy(ControlPoints):
    """What policy orders take: the orders for cities, research, settlers and engineers."""


class Command(ControlPoints):
    """What command orders take: the military orders for armies, divisions and single military units. A civilization has less Command than Policy."""


CONTROL_POINTS = (Policy, Command)


def points_given(*, by, points):
    """Return how many of a kind of control points a theme, a city spec or a building gives each turn."""
    return by.CONTROL_POINTS.get(points, NO_POINTS)
