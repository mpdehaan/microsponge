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

"""The weight classes of units, which a theme gives each kind of unit, and what an extra die or an armor bonus can be versus beside a class of unit."""


class Weight:
    """How heavy a kind of unit is, which bonuses can be versus. Light is the default."""

    LIGHT = 'light'
    MEDIUM = 'medium'
    HEAVY = 'heavy'

    ALL = (LIGHT, MEDIUM, HEAVY)


class Versus:
    """What an extra die can be versus beside a class of unit and a weight class: a unit inside a city."""

    IN_CITY = 'in a city'
