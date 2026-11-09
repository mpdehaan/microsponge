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

"""The fantasy theme."""

from microsponge.engine.kinds.theme import Theme
from microsponge.themes.fantasy.city import FantasyCity
from microsponge.themes.fantasy.technologies import (
    AirMagic, Blimps, Chivalry, DragonHusbandry, DragonRiding, EarthMagic, Elementals, FireMagic, Guilds, Magic, NatureAttunement, Necromancy,
    Psionics, Spirituality, Summoning, Telepathy, Teleportation, WaterMagic, WyvernHusbandry,
)
from microsponge.themes.fantasy.units import (
    Blimp, Cleric, Dragon, Elemental, Goblin, Knight, Monk, Ogre, Ranger, Scout, Settler, Soldier, Sorcerer, Wizard, Worker, Wyvern,
)


class Fantasy(Theme):
    CITY = FantasyCity
    TECHNOLOGIES = (
        DragonHusbandry, DragonRiding, Chivalry, WyvernHusbandry, Magic, FireMagic, WaterMagic, EarthMagic, AirMagic, Elementals, Necromancy,
        Psionics, Teleportation, Spirituality, NatureAttunement, Guilds, Summoning, Telepathy, Blimps,
    )
    UNITS = (Settler, Worker, Scout, Soldier, Knight, Ranger, Monk, Cleric, Sorcerer, Wizard, Elemental, Ogre, Goblin, Dragon, Wyvern, Blimp)
