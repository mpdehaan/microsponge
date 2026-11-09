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

"""What cavemen can work out."""

from microsponge.engine.kinds.technology import Technology
from microsponge.themes.caveman.resources import Food


class Clubs(Technology):
    RESEARCH = 10
    UNIT_SUPPORT_BONUS = 10


class Agriculture(Technology):
    RESEARCH = 30
    HARVEST_BONUS = {Food: 10}


class Discipline(Technology):
    RESEARCH = 40


class Fire(Technology):
    RESEARCH = 20
