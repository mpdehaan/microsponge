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

"""The keys of a saved game. JSON only has text for keys, so numbers that are keys are written as text."""


def text_keys(numbered):
    """Return a dictionary whose keys are numbers with each key as text, the way JSON writes it."""
    return {str(number): value for number, value in numbered.items()}


def number_keys(texted):
    """Return a dictionary read from JSON with each key as the number it was."""
    return {int(text): value for text, value in texted.items()}
