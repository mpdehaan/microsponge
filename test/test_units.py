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

"""The units of a game: columns of integers, indexed by the unit's id."""

import json
import unittest

from refusals import Refusals
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.units.levels import FIRST_LEVEL
from microsponge.engine.units.unit_column import COLUMN_DEFAULTS, RETIRED_UNIT_COLUMNS, UNIT_COLUMNS, UnitColumn
from microsponge.engine.units.units import Units, default_of
from microsponge.err_messages import ERR_COLUMNS_DIFFER, ERR_NO_SUCH_COLUMN, ERR_NO_SUCH_UNIT, ERR_UNKNOWN_ID

FIRST_UNIT = 1
A_KIND = 2
ANOTHER_KIND = 4
A_CIVILIZATION = 3
FULL_HEALTH = 10
HURT = 6
A_CITY = 2
NOT_A_UNIT = 'first'
NOT_A_COLUMN = 'kind'
A_UNIT = {UnitColumn.KIND: A_KIND, UnitColumn.OWNER: A_CIVILIZATION, UnitColumn.WORLD: 0, UnitColumn.X: 8, UnitColumn.Y: 9, UnitColumn.HIT_POINTS: FULL_HEALTH, UnitColumn.CITY: NOTHING}
ANOTHER_UNIT = {UnitColumn.KIND: ANOTHER_KIND, UnitColumn.OWNER: A_CIVILIZATION, UnitColumn.WORLD: 1, UnitColumn.X: 1, UnitColumn.Y: 2, UnitColumn.HIT_POINTS: HURT, UnitColumn.CITY: A_CITY}


def in_every_column(values):
    """Return what a unit added with some columns holds in every column: the column's default, nothing for most, in the columns it was not given."""
    return {column: values.get(column, default_of(column)) for column in UNIT_COLUMNS}


def a_column_nobody_has():
    return max(UNIT_COLUMNS + RETIRED_UNIT_COLUMNS) + 1


def through_json(data):
    """Return data as it comes back from a saved game."""
    return json.loads(json.dumps(data))


class TestUnits(Refusals, unittest.TestCase):

    def setUp(self):
        self.units = Units()

    def every_value(self, *, units, unit):
        return {column: units.get_value(column=column, unit=unit) for column in UNIT_COLUMNS}

    def test_there_are_no_units_to_start_with(self):
        self.assertEqual(self.units.get_ids(), [])
        self.assertEqual(self.units.count(), 0)
        self.assertFalse(self.units.exists(FIRST_UNIT))

    def test_units_are_numbered_from_one_as_they_are_added(self):
        first = self.units.add(A_UNIT)
        second = self.units.add(ANOTHER_UNIT)
        self.assertEqual((first, second), (FIRST_UNIT, FIRST_UNIT + 1))
        self.assertEqual(self.units.get_ids(), [first, second])
        self.assertEqual(self.every_value(units=self.units, unit=first), in_every_column(A_UNIT))
        self.assertEqual(self.every_value(units=self.units, unit=second), in_every_column(ANOTHER_UNIT))

    def test_a_column_left_out_when_adding_holds_its_default_which_is_nothing_for_most_and_the_first_level_for_the_level(self):
        unit = self.units.add({UnitColumn.KIND: A_KIND})
        self.assertEqual(self.units.get_value(column=UnitColumn.OWNER, unit=unit), NOTHING)
        self.assertEqual(self.units.get_value(column=UnitColumn.KIND, unit=unit), A_KIND)
        self.assertEqual(self.units.get_value(column=UnitColumn.LEVEL, unit=unit), FIRST_LEVEL)
        self.assertEqual(self.units.get_value(column=UnitColumn.EXPERIENCE, unit=unit), NOTHING)
        self.assertEqual(COLUMN_DEFAULTS, {UnitColumn.LEVEL: FIRST_LEVEL})

    def test_a_value_can_be_changed_for_one_unit(self):
        first = self.units.add(A_UNIT)
        second = self.units.add(A_UNIT)
        self.units.set_value(column=UnitColumn.HIT_POINTS, unit=first, value=HURT)
        self.assertEqual(self.units.get_value(column=UnitColumn.HIT_POINTS, unit=first), HURT)
        self.assertEqual(self.units.get_value(column=UnitColumn.HIT_POINTS, unit=second), FULL_HEALTH)

    def test_a_removed_unit_is_gone_and_its_id_is_not_given_out_again(self):
        first = self.units.add(A_UNIT)
        second = self.units.add(ANOTHER_UNIT)
        self.units.remove(first)
        self.assertFalse(self.units.exists(first))
        self.assertTrue(self.units.exists(second))
        self.assertEqual(self.units.get_ids(), [second])
        self.assertEqual(self.units.count(), 1)
        self.assertEqual(self.refused(lambda: self.units.remove(first)), ERR_NO_SUCH_UNIT.format(unit=first))
        self.assertEqual(self.units.add(A_UNIT), second + 1)

    def test_an_id_that_is_no_unit_is_refused(self):
        self.units.add(A_UNIT)
        for unit in (NOTHING, FIRST_UNIT + 1, -1, NOT_A_UNIT, None, True):
            with self.subTest(unit=unit):
                expected = ERR_NO_SUCH_UNIT.format(unit=unit)
                self.assertFalse(self.units.exists(unit))
                self.assertEqual(self.refused(lambda: self.units.check(unit)), expected)
                self.assertEqual(self.refused(lambda: self.units.get_value(column=UnitColumn.KIND, unit=unit)), expected)
                self.assertEqual(self.refused(lambda: self.units.set_value(column=UnitColumn.KIND, unit=unit, value=A_KIND)), expected)
        self.assertEqual(self.units.check(FIRST_UNIT), FIRST_UNIT)

    def test_a_column_the_units_do_not_have_is_refused(self):
        unit = self.units.add(A_UNIT)
        for column in (a_column_nobody_has(), NOTHING, NOT_A_COLUMN, None):
            with self.subTest(column=column):
                expected = ERR_NO_SUCH_COLUMN.format(column=column)
                self.assertEqual(self.refused(lambda: self.units.get_value(column=column, unit=unit)), expected)
                self.assertEqual(self.refused(lambda: self.units.set_value(column=column, unit=unit, value=A_KIND)), expected)
                self.assertEqual(self.refused(lambda: self.units.add({column: A_KIND})), expected)
        self.assertEqual(self.units.count(), 1)

    def test_renumbering_a_column_replaces_each_id(self):
        first = self.units.add(A_UNIT)
        second = self.units.add(ANOTHER_UNIT)
        numbers = {NOTHING: NOTHING, A_KIND: ANOTHER_KIND, ANOTHER_KIND: A_KIND}
        self.units.renumber(column=UnitColumn.KIND, numbers=numbers)
        self.assertEqual(self.units.get_value(column=UnitColumn.KIND, unit=first), ANOTHER_KIND)
        self.assertEqual(self.units.get_value(column=UnitColumn.KIND, unit=second), A_KIND)
        self.assertEqual(self.units.get_value(column=UnitColumn.OWNER, unit=first), A_CIVILIZATION)
        numbers = {NOTHING: NOTHING}
        self.assertEqual(self.refused(lambda: self.units.renumber(column=UnitColumn.KIND, numbers=numbers)), ERR_UNKNOWN_ID.format(known=sorted(numbers)))

    def test_units_come_back_from_a_saved_game_as_they_were(self):
        first = self.units.add(A_UNIT)
        second = self.units.add(ANOTHER_UNIT)
        third = self.units.add(A_UNIT)
        self.units.remove(second)
        loaded = Units.from_data(through_json(self.units.to_data()))
        self.assertEqual(loaded.get_ids(), [first, third])
        for unit in loaded.get_ids():
            self.assertEqual(self.every_value(units=loaded, unit=unit), self.every_value(units=self.units, unit=unit))
        self.assertEqual(loaded.add(A_UNIT), third + 1)

    def test_no_units_come_back_from_a_saved_game_as_no_units(self):
        loaded = Units.from_data(through_json(self.units.to_data()))
        self.assertEqual(loaded.get_ids(), [])
        self.assertEqual(loaded.add(A_UNIT), FIRST_UNIT)

    def test_a_saved_game_calls_each_column_by_its_number(self):
        self.assertEqual(set(through_json(self.units.to_data())), {str(column) for column in UNIT_COLUMNS})

    def test_a_column_the_saved_game_lacks_holds_its_default_for_every_unit(self):
        first = self.units.add(A_UNIT)
        second = self.units.add(ANOTHER_UNIT)
        data = through_json(self.units.to_data())
        del data[str(UnitColumn.HIT_POINTS)]
        del data[str(UnitColumn.LEVEL)]
        loaded = Units.from_data(data)
        for unit in (first, second):
            self.assertEqual(loaded.get_value(column=UnitColumn.HIT_POINTS, unit=unit), NOTHING)
            self.assertEqual(loaded.get_value(column=UnitColumn.LEVEL, unit=unit), FIRST_LEVEL)
            self.assertEqual(loaded.get_value(column=UnitColumn.KIND, unit=unit), self.units.get_value(column=UnitColumn.KIND, unit=unit))

    def test_a_column_this_version_does_not_have_is_left_behind(self):
        unit = self.units.add(A_UNIT)
        data = through_json(self.units.to_data())
        data[str(a_column_nobody_has())] = [NOTHING, A_KIND]
        loaded = Units.from_data(data)
        self.assertEqual(set(through_json(loaded.to_data())), {str(column) for column in UNIT_COLUMNS})
        self.assertEqual(self.every_value(units=loaded, unit=unit), in_every_column(A_UNIT))

    def test_saved_columns_of_different_lengths_are_refused(self):
        self.units.add(A_UNIT)
        data = through_json(self.units.to_data())
        data[str(UnitColumn.X)].append(NOTHING)
        self.assertEqual(self.refused(lambda: Units.from_data(data)), ERR_COLUMNS_DIFFER)

    def test_no_column_number_is_used_twice_or_brought_back(self):
        self.assertEqual(len(set(UNIT_COLUMNS)), len(UNIT_COLUMNS))
        self.assertFalse(set(UNIT_COLUMNS) & set(RETIRED_UNIT_COLUMNS))
        self.assertNotIn(NOTHING, UNIT_COLUMNS + RETIRED_UNIT_COLUMNS)


if __name__ == '__main__':
    unittest.main()
