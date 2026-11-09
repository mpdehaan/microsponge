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

"""The units of SciFi."""

from microsponge.engine.kinds.unit_kinds import SpaceUnit, UnitKind


class Infantry(UnitKind):
    pass


class Probe(UnitKind):
    pass


class SpaceFighter(SpaceUnit):
    """The smaller space ship, which only defends the space around a planet."""


class SpaceCarrier(SpaceUnit):
    """The giant ship that carries space fighters between planets."""
