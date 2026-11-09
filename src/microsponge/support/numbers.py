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

"""Checks on numbers that several model objects share."""


def is_a_count(value):
    """Return whether a value can count something: a whole number that is not negative."""
    return type(value) is int and value >= 0


def divided_rounding_up(*, amount, by):
    """Return how many times a whole number goes into an amount, counting a part left over as one more: 10 by 4 is 3."""
    return -(-amount // by)
