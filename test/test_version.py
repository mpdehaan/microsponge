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

"""microsponge's version: three whole numbers separated by dots, compared number by number."""

import unittest

from microsponge.support.version import VERSION, VERSION_PARTS, is_version, version_numbers

# Pairs of versions where the first comes after the second, though as decimals or as text it wouldn't.
LATER_THEN_EARLIER = [('1.0.10', '1.0.9'), ('2.0.0', '1.99.99'), ('0.10.0', '0.9.9')]
# Things that aren't versions: too few numbers, too many, a letter, a sign, nothing, a space, and values that aren't text.
NOT_VERSIONS = ['1.0', '1.0.2.3', '1.0.x', '1.0.-2', '', ' 1.0.2', 1.02, None]
TOO_SHORT = '1.0'


class TestVersion(unittest.TestCase):

    def test_the_version_is_three_whole_numbers(self):
        self.assertTrue(is_version(VERSION))
        self.assertEqual(len(version_numbers(VERSION)), VERSION_PARTS)

    def test_versions_compare_number_by_number_not_as_decimals(self):
        for later, earlier in LATER_THEN_EARLIER:
            with self.subTest(later=later, earlier=earlier):
                self.assertGreater(version_numbers(later), version_numbers(earlier))

    def test_anything_else_is_not_a_version(self):
        for text in NOT_VERSIONS:
            with self.subTest(text=text):
                self.assertFalse(is_version(text))

    def test_the_numbers_of_something_that_is_not_a_version_are_refused(self):
        with self.assertRaises(ValueError):
            version_numbers(TOO_SHORT)


if __name__ == '__main__':
    unittest.main()
