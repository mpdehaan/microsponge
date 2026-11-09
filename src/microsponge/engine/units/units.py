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

"""Every unit of a game, as columns of integers."""

from microsponge.engine.kinds.catalog import NOTHING, renumbered
from microsponge.engine.saving.keys import text_keys
from microsponge.engine.units.unit_column import COLUMN_DEFAULTS, UNIT_COLUMNS, UnitColumn
from microsponge.err_messages import ERR_COLUMNS_DIFFER, ERR_NO_SUCH_COLUMN, ERR_NO_SUCH_UNIT


def default_of(column):
    """Return what a column holds when nothing was given for it."""
    return COLUMN_DEFAULTS.get(column, NOTHING)


def same_length(columns):
    """Return whether every column holds as many values as the others."""
    return len({len(values) for values in columns}) <= 1


class Units:
    """The units of a game. A unit is an id, and each fact about the units is a column: a list indexed by that id.

    No unit is an object, so that many units cost little. This class is the only code that
    touches the columns. Id NOTHING is never a unit, so that a tile's unit layer can say no
    unit. A unit that is removed keeps its id with kind NOTHING, and the id is not given out
    again.
    """

    __slots__ = ('_columns',)

    def __init__(self):
        self._columns = {column: [NOTHING] for column in UNIT_COLUMNS}

    def _values(self, column):
        try:
            return self._columns[column]
        except (KeyError, TypeError):
            raise ValueError(ERR_NO_SUCH_COLUMN.format(column=column)) from None

    def add(self, values):
        """Add a unit from the value of each of its columns, and return its id. A column left out holds its default, NOTHING for most."""
        for column in values:
            self._values(column)
        for column, numbers in self._columns.items():
            numbers.append(values.get(column, default_of(column)))
        return len(self._columns[UnitColumn.KIND]) - 1

    def exists(self, unit):
        kinds = self._columns[UnitColumn.KIND]
        return type(unit) is int and NOTHING < unit < len(kinds) and kinds[unit] != NOTHING

    def check(self, unit):
        """Return unit, which has to be the id of a unit that exists."""
        if not self.exists(unit):
            raise ValueError(ERR_NO_SUCH_UNIT.format(unit=unit))
        return unit

    def remove(self, unit):
        self._columns[UnitColumn.KIND][self.check(unit)] = NOTHING

    def get_ids(self):
        """Return the id of every unit that exists, in the order they were added."""
        return [unit for unit, kind in enumerate(self._columns[UnitColumn.KIND]) if kind != NOTHING]

    def count(self):
        return len(self.get_ids())

    def get_value(self, *, column, unit):
        """Return what a column holds for a unit."""
        return self._values(column)[self.check(unit)]

    def set_value(self, *, column, unit, value):
        self._values(column)[self.check(unit)] = value

    def renumber(self, *, column, numbers):
        """Replace each id in a column with its number in numbers, after loading a game saved with other ids."""
        self._columns[column] = renumbered(values=self._values(column), numbers=numbers)

    def to_data(self):
        """Return the units as a saved game holds them. The columns are the units' own lists, not copies."""
        return text_keys(self._columns)

    @classmethod
    def from_data(cls, data):
        """Return the units a saved game holds, taking its lists as the units' own.

        A column the saved game lacks, because the column was added later, holds its default for
        every unit, NOTHING for most. A column the saved game holds that is not in UNIT_COLUMNS, because it was
        retired, is left behind.
        """
        saved = {column: data[str(column)] for column in UNIT_COLUMNS if str(column) in data}
        if not same_length(saved.values()):
            raise ValueError(ERR_COLUMNS_DIFFER)
        units = cls()
        length = len(next(iter(saved.values()), units._columns[UnitColumn.KIND]))
        units._columns = {column: saved.get(column) or [default_of(column)] * length for column in UNIT_COLUMNS}
        return units
