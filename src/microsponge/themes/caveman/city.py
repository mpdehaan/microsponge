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

"""What a city is to cavemen: a village."""

from microsponge.engine.kinds.city_spec import CitySpec
from microsponge.themes.caveman.resources import Food


class Village(CitySpec):
    NAME = 'village'
    NAMES = 'villages'
    PRODUCES = {Food: 2}
    GROWTH_FOOD = 5
    CITIZEN_CURRENCY = 2
    ACTION_POINTS = 2
    RESEARCH_POINTS = 1
