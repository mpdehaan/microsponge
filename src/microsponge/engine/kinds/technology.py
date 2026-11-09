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

"""The base of the technologies in a theme's tech tree."""

from microsponge.engine.kinds.kind import Kind


class Technology(Kind):
    """Something a civilization researches. REQUIRES names what must be had first."""

    # The research points it costs.
    RESEARCH = 0
    # The percent it adds to how fast each resource is harvested: each resource with its percent.
    HARVEST_BONUS = {}
    # The percent it takes off what every unit costs to support each turn.
    UNIT_SUPPORT_BONUS = 0
