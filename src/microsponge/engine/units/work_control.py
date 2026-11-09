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

"""The rules for a unit that builds an improvement on the tile it stands on."""

from microsponge.engine.civilizations.requirements import missing_requirements
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.terrain_bonus_control import TerrainBonusControl
from microsponge.err_messages import (
    ERR_CANNOT_BUILD_IMPROVEMENT, ERR_IMPROVEMENT_NOT_ON, ERR_IMPROVEMENT_REQUIRES, ERR_TILE_IMPROVED, ERR_UNIT_IN_A_CITY, ERR_UNIT_NOT_WORKING, ERR_UNIT_WORKING,
)

DONE = 0


class WorkControl:
    """Building improvements, as static methods over a game. It is never made into an object.

    A unit builds an improvement on the tile it stands on, over the turns the improvement
    takes, and cannot move until the improvement is done. The unit can abandon the effort, and
    then nothing comes of the turns already spent. Building costs nothing, for now.
    """

    __slots__ = ()

    @staticmethod
    def improvement_of(*, game, unit):
        """Return the improvement a unit is building, as the theme's class, or None when the unit is building nothing."""
        improvement = game.get_units().get_value(column=UnitColumn.IMPROVEMENT, unit=unit)
        if improvement == NOTHING:
            return None
        return game.get_catalog().get_kind(category=Category.IMPROVEMENTS, kind_id=improvement)

    @staticmethod
    def turns_left(*, game, unit):
        """Return how many more turns the improvement a unit is building takes."""
        return game.get_units().get_value(column=UnitColumn.BUILD_TURNS, unit=unit)

    @staticmethod
    def check_idle(*, game, unit):
        """Check that a unit is building nothing, and so is free to move."""
        improvement = WorkControl.improvement_of(game=game, unit=unit)
        if improvement is not None:
            raise ValueError(ERR_UNIT_WORKING.format(unit=unit, improvement=shown_name(improvement)))

    @staticmethod
    def problem_starting(*, game, unit, improvement):
        """Return why a unit cannot start building an improvement where it stands, as an error message, or None when it can.

        The unit's kind has to build the improvement, the unit has to stand on a tile of its
        own and be building nothing, its civilization has to have what the improvement
        requires, and the tile has to be of a terrain the improvement goes on, with no
        improvement yet.
        """
        units = game.get_units()
        kind = UnitControl.kind_of(game=game, unit=unit)
        if improvement not in kind.BUILDS:
            return ERR_CANNOT_BUILD_IMPROVEMENT.format(unit=shown_name(kind), improvement=shown_name(improvement))
        if units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING:
            return ERR_UNIT_IN_A_CITY.format(unit=unit, city=game.get_theme().CITY.NAME)
        already = WorkControl.improvement_of(game=game, unit=unit)
        if already is not None:
            return ERR_UNIT_WORKING.format(unit=unit, improvement=shown_name(already))
        missing = missing_requirements(game=game, civilization=units.get_value(column=UnitColumn.OWNER, unit=unit), kind=improvement)
        if missing:
            return ERR_IMPROVEMENT_REQUIRES.format(improvement=shown_name(improvement), required=shown_name(missing[0]))
        world_id, x, y = UnitControl.tile_of(game=game, unit=unit)
        world = game.get_world(world_id)
        terrain = game.get_terrain(world=world_id, x=x, y=y)
        if terrain not in improvement.ON or not terrain.BUILDABLE:
            return ERR_IMPROVEMENT_NOT_ON.format(improvement=shown_name(improvement), terrain=shown_name(terrain))
        built = world.get_value(layer=Layer.IMPROVEMENT, x=x, y=y)
        if built != NOTHING:
            return ERR_TILE_IMPROVED.format(x=x, y=y, improvement=shown_name(game.get_catalog().get_kind(category=Category.IMPROVEMENTS, kind_id=built)))
        return None

    @staticmethod
    def start(*, game, unit, improvement):
        """Set a unit to building an improvement on the tile it stands on."""
        problem = WorkControl.problem_starting(game=game, unit=unit, improvement=improvement)
        if problem is not None:
            raise ValueError(problem)
        units = game.get_units()
        units.set_value(column=UnitColumn.IMPROVEMENT, unit=unit, value=game.get_catalog().get_id(category=Category.IMPROVEMENTS, kind=improvement))
        units.set_value(column=UnitColumn.BUILD_TURNS, unit=unit, value=improvement.BUILD_TURNS)

    @staticmethod
    def abandon(*, game, unit):
        """Stop a unit building its improvement. Nothing comes of the turns already spent."""
        if WorkControl.improvement_of(game=game, unit=unit) is None:
            raise ValueError(ERR_UNIT_NOT_WORKING.format(unit=unit))
        WorkControl._stop(game=game, unit=unit)

    @staticmethod
    def _stop(*, game, unit):
        units = game.get_units()
        units.set_value(column=UnitColumn.IMPROVEMENT, unit=unit, value=NOTHING)
        units.set_value(column=UnitColumn.BUILD_TURNS, unit=unit, value=DONE)

    @staticmethod
    def advance(*, game, civilization):
        """Take a turn off what each building unit of a civilization still has to do, and put what is done on its unit's tile."""
        units = game.get_units()
        for unit in UnitControl.units_of(game=game, civilization=civilization):
            improvement = units.get_value(column=UnitColumn.IMPROVEMENT, unit=unit)
            if improvement == NOTHING:
                continue
            left = units.get_value(column=UnitColumn.BUILD_TURNS, unit=unit) - 1
            units.set_value(column=UnitColumn.BUILD_TURNS, unit=unit, value=left)
            if left <= DONE:
                WorkControl._finish(game=game, unit=unit)
                WorkControl._stop(game=game, unit=unit)

    @staticmethod
    def _finish(*, game, unit):
        """Put what a unit has built on the unit's tile: the improvement, or the terrain the work turns the tile into, which can make a strategic resource or a terrain bonus go away."""
        catalog = game.get_catalog()
        improvement = WorkControl.improvement_of(game=game, unit=unit)
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        tiles = game.get_world(world)
        if improvement.BECOMES is None:
            tiles.set_value(layer=Layer.IMPROVEMENT, x=x, y=y, value=catalog.get_id(category=Category.IMPROVEMENTS, kind=improvement))
        else:
            tiles.set_value(layer=Layer.TERRAIN, x=x, y=y, value=catalog.get_id(category=Category.TERRAINS, kind=improvement.BECOMES))
            Strategic.terrain_changed(game=game, world=world, x=x, y=y)
            TerrainBonusControl.terrain_changed(game=game, world=world, x=x, y=y)
