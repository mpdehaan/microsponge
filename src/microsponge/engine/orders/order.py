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

"""The kinds of standing order. Each is a definition, a class of constants, that a theme lists in ORDERS and may subclass to change what the order costs."""

from microsponge.engine.kinds.control_points import Command, Policy
from microsponge.engine.kinds.kind import Kind
from microsponge.engine.orders.thing import ThingType


class Order(Kind):
    """A kind of standing order: what points the order takes while it is in force, what it costs, and what can receive it.

    The name of every order class ends in Order. An order that takes Policy is a PolicyOrder
    and one that takes Command is a CommandOrder.
    """

    # The kind of control points the order takes each turn while it is active.
    POINTS = None
    # What the order costs each turn whatever it leads, and what it costs for each unit it leads.
    BASE_COST = 0
    UNIT_COST = 0
    # What an order given to a single unit costs beyond that, so that ordering every unit alone is the dear way.
    LONE_UNIT_COST = 2
    # The types of thing that can receive the order.
    RECEIVERS = ()


class PolicyOrder(Order):
    POINTS = Policy
    BASE_COST = 1


class CommandOrder(Order):
    """A military order, for an army, a division or one military unit."""

    POINTS = Command
    UNIT_COST = 1
    RECEIVERS = (ThingType.ARMY, ThingType.DIVISION, ThingType.UNIT)


class BuildTargetOrder(PolicyOrder):
    """An order that aims at things being built by the city that receives it. The order holds a list, and a long list costs no more."""

    RECEIVERS = (ThingType.CITY,)


class BuildOrder(BuildTargetOrder):
    """The buildings a city builds, in order of priority."""


class RaiseOrder(BuildTargetOrder):
    """The units a city builds for the division that gives the order."""


class ExpandOrder(BuildTargetOrder):
    """A city builds a settler, which the helper AI sends to build a city."""


class ImproveOrder(BuildTargetOrder):
    """A city builds an engineer, which the helper AI sends to build improvements on the city's tiles."""


class CivilOrder(PolicyOrder):
    """An order for one unit that is not military."""

    RECEIVERS = (ThingType.UNIT,)


class SettlerOrder(CivilOrder):
    """A settler finds a site and builds a city."""


class WorkOrder(CivilOrder):
    """An engineer builds improvements on the tiles of a city."""


class ResourcesPolicyOrder(PolicyOrder):
    """What a city's citizens look for first, like stone first, and how many of them do."""

    RECEIVERS = (ThingType.CITY,)


class ResearchOrder(PolicyOrder):
    """The technologies a civilization aims for, in order."""

    RECEIVERS = (ThingType.CIVILIZATION,)


class GarrisonOrder(CommandOrder):
    """A division keeps so many of its units inside a city. The order leads only the units it keeps."""

    RECEIVERS = (ThingType.DIVISION,)


class MarchOrder(CommandOrder):
    """A division goes to a target and attacks it."""

    RECEIVERS = (ThingType.DIVISION,)


class RetireOrder(PolicyOrder):
    """A unit, or every unit of a division or of an army, is taken out of the game for good, which can save a civilization's income from upkeep. The order is free, and gives nothing back."""

    BASE_COST = 0
    LONE_UNIT_COST = 0
    RECEIVERS = (ThingType.ARMY, ThingType.DIVISION, ThingType.UNIT)


# The orders every theme has unless the theme lists its own.
ORDERS = (BuildOrder, RaiseOrder, ExpandOrder, ImproveOrder, SettlerOrder, WorkOrder, ResourcesPolicyOrder, ResearchOrder, GarrisonOrder, MarchOrder, RetireOrder)
