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
    RESEARCH = 15
    UNIT_SUPPORT_BONUS = 10


class Fire(Technology):
    RESEARCH = 15


class Agriculture(Technology):
    RESEARCH = 20
    HARVEST_BONUS = {Food: 10}


class Sewing(Technology):
    REQUIRES = (Agriculture,)
    RESEARCH = 50
    GROWS_SOONER = 2


class Carpentry(Technology):
    RESEARCH = 50


class Leadership(Technology):
    REQUIRES = (Fire,)
    RESEARCH = 50


class Discipline(Technology):
    REQUIRES = (Leadership,)
    RESEARCH = 90


class ChurchOfTheCaveBear(Technology):
    NAME = 'church of the cave bear'
    REQUIRES = (Fire, Leadership)
    RESEARCH = 90


class Barter(Technology):
    REQUIRES = (Sewing, Leadership)
    RESEARCH = 100


class Astrology(Technology):
    REQUIRES = (ChurchOfTheCaveBear, Leadership)
    RESEARCH = 200
