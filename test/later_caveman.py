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

"""The caveman theme as later versions of the game might have it, to load games saved by this one."""

from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.improvement import Improvement
from microsponge.engine.kinds.kind import saved_name
from microsponge.engine.kinds.unit_kinds import LandUnit
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler


class Hunter(LandUnit):
    """A kind of unit that a later version adds."""


class Fence(Improvement):
    """A kind of improvement that a later version adds."""


def later_theme(*, theme, changes):
    """Return a theme with caveman's name, and the kinds of a theme made from caveman but for the categories in changes."""
    return type(saved_name(Caveman), (theme,), changes)


def later_caveman(changes):
    """Return a theme with caveman's name, and caveman's kinds but for the categories in changes."""
    return later_theme(theme=Caveman, changes=changes)


def without(*, kinds, kind):
    return tuple(other for other in kinds if other is not kind)


# The same kinds in another order, and one more unit and one more improvement first: every id of a unit and of an
# improvement differs, the first and last terrain, resource, technology and building swap ids, and the terrain
# bonuses swap ids.
REORDERED_CAVEMAN = later_caveman({
    Category.TERRAINS: tuple(reversed(Caveman.TERRAINS)),
    Category.RESOURCES: tuple(reversed(Caveman.RESOURCES)),
    Category.TECHNOLOGIES: tuple(reversed(Caveman.TECHNOLOGIES)),
    Category.UNITS: (Hunter, *Caveman.UNITS),
    Category.BUILDINGS: tuple(reversed(Caveman.BUILDINGS)),
    Category.IMPROVEMENTS: (Fence, *Caveman.IMPROVEMENTS),
    Category.TERRAIN_BONUSES: tuple(reversed(Caveman.TERRAIN_BONUSES)),
})
# A kind added at the end: no id differs.
EXTENDED_CAVEMAN = later_caveman({Category.UNITS: (*Caveman.UNITS, Hunter)})
# The settler taken out.
SETTLERLESS_CAVEMAN = later_caveman({Category.UNITS: without(kinds=Caveman.UNITS, kind=Settler)})
