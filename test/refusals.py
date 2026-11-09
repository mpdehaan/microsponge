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

"""What the tests share for checking that the program refuses something."""


class Refusals:
    """Gives a test class refused(), to read the message the program refuses something with. It goes before unittest.TestCase in the bases."""

    __slots__ = ()

    def refused(self, action):
        """Return the message of the ValueError that calling action raises."""
        with self.assertRaises(ValueError) as refusal:
            action()
        return str(refusal.exception)
