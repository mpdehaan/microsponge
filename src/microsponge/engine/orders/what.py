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

"""What an order says: the configuration of each kind of order, and the targets an order mentions."""

from dataclasses import dataclass


@dataclass(slots=True, kw_only=True, frozen=True)
class BuildTarget:
    """So many units of the first of some kinds a city can build, the best first."""

    kinds: tuple
    count: int


@dataclass(slots=True, kw_only=True, frozen=True)
class Buildings:
    """What a BuildOrder says: the buildings to build, in order of priority."""

    kinds: tuple


@dataclass(slots=True, kw_only=True, frozen=True)
class Units:
    """What a RaiseOrder says: the build targets the giving division should reach, met from the top."""

    targets: tuple


@dataclass(slots=True, kw_only=True, frozen=True)
class Priority:
    """What a ResourcesPolicyOrder says: the resource a city's citizens look for first, and how many citizens do."""

    resource: type
    citizens: int


@dataclass(slots=True, kw_only=True, frozen=True)
class Technologies:
    """What a ResearchOrder says: the technologies to research, in order."""

    kinds: tuple


@dataclass(slots=True, kw_only=True, frozen=True)
class Target:
    """Something on the map that an order mentions. A target is never an order."""


@dataclass(slots=True, kw_only=True, frozen=True)
class CityTarget(Target):
    city: int


@dataclass(slots=True, kw_only=True, frozen=True)
class Garrison:
    """What a GarrisonOrder says: the city, and how many units are kept inside."""

    place: CityTarget
    count: int


@dataclass(slots=True, kw_only=True, frozen=True)
class March:
    """What a MarchOrder says: the military target, a location to attack, and how the units behave on the way.

    Bold units attack an enemy unit next to them even when the numbers are against them, and
    units that ignore units leave enemy units alone and attack only the target.
    """

    target: Target
    bold: bool = False
    ignore_units: bool = False


@dataclass(slots=True, kw_only=True, frozen=True)
class NoDetails:
    """What an order says that needs no configuration, like an ExpandOrder with no target."""
