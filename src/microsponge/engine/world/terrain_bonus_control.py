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

"""Terrain bonuses: where they are on the map, and what they add to a tile."""

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_BONUS_NOT_ON


class TerrainBonusControl:
    """The rules for terrain bonuses, as static methods over a game. It is never made into an object."""

    __slots__ = ()

    @staticmethod
    def bonus_at(*, game, world, x, y):
        """Return the terrain bonus on a tile, as the theme's class, or None."""
        bonus = game.get_world(world).get_value(layer=Layer.TERRAIN_BONUS, x=x, y=y)
        return None if bonus == NOTHING else game.get_catalog().get_kind(category=Category.TERRAIN_BONUSES, kind_id=bonus)

    @staticmethod
    def problem_placing(*, game, world, x, y, bonus):
        """Return why a terrain bonus cannot be put on a tile, as an error message, or None when it can: the tile has to be of a compatible terrain."""
        terrain = game.get_terrain(world=world, x=x, y=y)
        if terrain not in bonus.ON:
            return ERR_BONUS_NOT_ON.format(bonus=shown_name(bonus), terrain=shown_name(terrain))
        return None

    @staticmethod
    def place(*, game, world, x, y, bonus):
        """Put a terrain bonus on a tile, in place of any the tile had."""
        problem = TerrainBonusControl.problem_placing(game=game, world=world, x=x, y=y, bonus=bonus)
        if problem is not None:
            raise ValueError(problem)
        bonus_id = game.get_catalog().get_id(category=Category.TERRAIN_BONUSES, kind=bonus)
        game.get_world(world).set_value(layer=Layer.TERRAIN_BONUS, x=x, y=y, value=bonus_id)

    @staticmethod
    def remove(*, game, world, x, y):
        """Take the terrain bonus off a tile, for good."""
        game.get_world(world).set_value(layer=Layer.TERRAIN_BONUS, x=x, y=y, value=NOTHING)

    @staticmethod
    def terrain_changed(*, game, world, x, y):
        """Take the terrain bonus off a tile whose terrain has changed to one the bonus is not compatible with."""
        bonus = TerrainBonusControl.bonus_at(game=game, world=world, x=x, y=y)
        if bonus is not None and game.get_terrain(world=world, x=x, y=y) not in bonus.ON:
            TerrainBonusControl.remove(game=game, world=world, x=x, y=y)

    @staticmethod
    def gives(*, game, world, x, y):
        """Return what the terrain bonus on a tile adds to what the tile gives: each resource with its amount, and nothing when the tile has no bonus."""
        bonus = TerrainBonusControl.bonus_at(game=game, world=world, x=x, y=y)
        return {} if bonus is None else bonus.GIVES
