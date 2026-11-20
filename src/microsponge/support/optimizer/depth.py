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

"""How deep in the tech tree each kind of a theme sits, which later kinds cost more by."""

from microsponge.engine.kinds.building import Building
from microsponge.engine.kinds.technology import Technology

NO_DEPTH = 0
ONE_DEEPER = 1


class TreeDepth:
    """Static: the depth of a theme's technologies, units, buildings and improvements.

    A technology's depth is one more than the deepest technology it requires, so a technology
    that requires none is at depth 1. A unit, a building or an improvement is as deep as the
    deepest technology it requires, and one deeper for each building on the way: caveman's
    captain caveman requires the barracks, which requires discipline. A kind that requires
    nothing is at depth 0.
    """

    __slots__ = ()

    @staticmethod
    def of_technology(technology):
        required = [kind for kind in technology.REQUIRES if issubclass(kind, Technology)]
        return ONE_DEEPER + max((TreeDepth.of_technology(kind) for kind in required), default=NO_DEPTH)

    @staticmethod
    def of_kind(kind):
        """Return the depth of a unit, a building, an improvement or a technology."""
        if issubclass(kind, Technology):
            return TreeDepth.of_technology(kind)
        depths = [NO_DEPTH]
        for required in kind.REQUIRES:
            if issubclass(required, Technology):
                depths.append(TreeDepth.of_technology(required))
            elif issubclass(required, Building):
                depths.append(TreeDepth.of_kind(required) + ONE_DEEPER)
        return max(depths)
