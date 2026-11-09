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

"""The categories of kind a theme lists, each named after the Theme constant that lists it."""


class Category:
    """A category's value is the name of the Theme constant holding its kinds, and is what a saved game calls the category."""

    TERRAINS = 'TERRAINS'
    RESOURCES = 'RESOURCES'
    TECHNOLOGIES = 'TECHNOLOGIES'
    UNITS = 'UNITS'
    BUILDINGS = 'BUILDINGS'
    IMPROVEMENTS = 'IMPROVEMENTS'
    TERRAIN_BONUSES = 'TERRAIN_BONUSES'


CATEGORIES = (Category.TERRAINS, Category.RESOURCES, Category.TECHNOLOGIES, Category.UNITS, Category.BUILDINGS, Category.IMPROVEMENTS, Category.TERRAIN_BONUSES)


def shown_category(category):
    """Return a category as an error message words it, like units."""
    return category.lower()
