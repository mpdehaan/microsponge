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

"""Armies and divisions: the groups a civilization's military units belong to."""

from microsponge.err_messages import ERR_NO_SUCH_DIVISION

FIRST_ID = 1


class Division:
    """A group of units inside an army, with the cities that can build for it, which are its bases."""

    __slots__ = ('_id', '_army', '_units', '_bases')

    def __init__(self, *, id, army):
        self._id = id
        self._army = army
        self._units = []
        self._bases = []

    def get_id(self):
        return self._id

    def get_army(self):
        return self._army

    def get_units(self):
        return list(self._units)

    def add_unit(self, unit):
        if unit not in self._units:
            self._units.append(unit)

    def remove_unit(self, unit):
        self._units.remove(unit)

    def get_bases(self):
        return list(self._bases)

    def set_bases(self, cities):
        self._bases = list(cities)


class Forces:
    """The armies of a civilization and the divisions each is made of. An army is a number, and its divisions say which army they are in."""

    __slots__ = ('_armies', '_divisions')

    def __init__(self):
        self._armies = []
        self._divisions = []

    def get_armies(self):
        return list(self._armies)

    def add_army(self):
        """Add an army and return its id."""
        self._armies.append(len(self._armies) + FIRST_ID)
        return self._armies[-1]

    def get_divisions(self):
        return list(self._divisions)

    def add_division(self, army):
        """Add a division to an army and return the division."""
        division = Division(id=len(self._divisions) + FIRST_ID, army=army)
        self._divisions.append(division)
        return division

    def get_division(self, id):
        if not FIRST_ID <= id <= len(self._divisions):
            raise ValueError(ERR_NO_SUCH_DIVISION.format(division=id))
        return self._divisions[id - FIRST_ID]

    def has_division(self, id):
        return FIRST_ID <= id <= len(self._divisions)

    def division_of(self, unit):
        """Return the division a unit is in, or None."""
        for division in self._divisions:
            if unit in division.get_units():
                return division
        return None
