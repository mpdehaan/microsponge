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

"""The base of a theme's resources."""

from microsponge.engine.kinds.kind import Kind


class Resource(Kind):
    """Something a civilization collects and holds, like food or stone."""


class StrategicResource(Resource):
    """A strategic resource, like iron: one that is not collected and not used up.

    One is on a tile, of a terrain that can have it. A civilization with such a tile within
    its borders has what every kind that requires the resource needs, and one tile is enough.
    """
