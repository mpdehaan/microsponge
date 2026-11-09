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

"""The base of every kind of thing a theme defines."""

import re

# Where a new word starts inside a class name like GreatCavePainting: before each capital but the first.
WORD_START = re.compile(r'(?<!^)(?=[A-Z])')
WORD_SEPARATOR = ' '
# The constant a kind sets to be called something its class name can't say.
NAME = 'NAME'


class Kind:
    """A kind of thing in a theme, like a kind of unit, a terrain or a technology.

    A kind is a class that only holds constants and is never made into an object. A theme
    subclasses one of the base kinds and sets the constants that differ, so a kind that changes
    nothing is one line. While a game runs a kind is known by a number, its id, which the game's
    Catalog gives it.
    """

    # What the theme calls this kind, when the words of its class name aren't right, like anti-missile platform. It is not inherited.
    NAME = None
    # What a civilization must have before it can have this kind: technologies it has researched, buildings and world wonders it has built,
    # and strategic resources within its borders.
    REQUIRES = ()


def saved_name(kind):
    """Return what a saved game calls a kind: its class name, like GreatCavePainting."""
    return kind.__name__


def shown_name(kind):
    """Return a kind's name as people read it: the name the kind sets for itself, or else the words of its class name, so GreatCavePainting is great cave painting."""
    return vars(kind).get(NAME) or WORD_START.sub(WORD_SEPARATOR, kind.__name__).lower()
