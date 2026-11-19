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

"""Changing the terrain of a tile, and what goes away with the old terrain."""

from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.category import Category
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl


class TerrainControl:
    """Static: the one place a tile's terrain is changed after a world is made. It is never made into an object."""

    __slots__ = ()

    @staticmethod
    def change(*, game, world, x, y, terrain):
        """Make a tile a terrain, and take off the strategic resource and the terrain bonus that the new terrain cannot have."""
        game.get_world(world).set_value(layer=Layer.TERRAIN, x=x, y=y, value=game.get_catalog().get_id(category=Category.TERRAINS, kind=terrain))
        Strategic.terrain_changed(game=game, world=world, x=x, y=y)
        TerrainBonusControl.terrain_changed(game=game, world=world, x=x, y=y)
