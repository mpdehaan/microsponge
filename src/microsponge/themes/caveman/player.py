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

"""The computer player of caveman: which of caveman's kinds the player researches, defends with, attacks with and builds for the economy."""

from microsponge.engine.players.computer_player import ComputerPlayer
from microsponge.themes.caveman.buildings import ArrangementOfRocks, Barracks, ChieftainsHut, Granary, GreatCavePainting
from microsponge.themes.caveman.technologies import Agriculture, Clubs, Discipline, Fire, Leadership
from microsponge.themes.caveman.units import CaptainCaveman, Warrior


class CavemanPlayer(ComputerPlayer):
    __slots__ = ()
    SCIENCE_RESEARCH = (Agriculture, Clubs, Leadership, Discipline, Fire)
    MILITARY_RESEARCH = (Clubs, Discipline, Fire, Leadership, Agriculture)
    DEFENDERS = (CaptainCaveman, Warrior)
    ATTACKERS = (CaptainCaveman, Warrior)
    ECONOMY = (Granary, ChieftainsHut, GreatCavePainting, Barracks, ArrangementOfRocks)
