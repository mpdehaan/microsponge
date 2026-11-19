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

"""Revising a world around a chosen starting site, so that the site has what the theme asks of a start."""

from microsponge.engine.cities.city_control import on_the_map, square
from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.engine.world.start_survey import StartSurvey, strategic_square_size
from microsponge.engine.world.terrain_control import TerrainControl

# The layers that hold something special on a tile. The generator only changes the terrain of a tile that has nothing in any of them.
SPECIAL_LAYERS = (Layer.STRATEGIC_RESOURCE, Layer.TERRAIN_BONUS, Layer.IMPROVEMENT)


class StartImprover:
    """Static: changes a few tiles around a starting site that lacks something. It is never made into an object.

    It works from what the theme's MAP spec asks of a start and from what the theme's terrains
    give and can have, and names no kind of any theme. It never changes a tile of the city
    center, a tile the starting unit cannot be on, or a tile with something special on it.
    """

    __slots__ = ()

    @staticmethod
    def improve(*, game, world_id, kind, x, y):
        """Change tiles around a starting site until the first city radius gives what it must and the strategic resources of a start are near, as far as the theme's terrains allow."""
        survey = StartSurvey(game=game, world_id=world_id, kind=kind)
        StartImprover.add_giving(game=game, world_id=world_id, kind=kind, x=x, y=y, gives=survey.radius_gives(x=x, y=y))
        for resource in survey.misses(x=x, y=y):
            StartImprover.add_strategic(game=game, world_id=world_id, kind=kind, x=x, y=y, resource=resource)

    @staticmethod
    def add_giving(*, game, world_id, kind, x, y, gives):
        """Turn tiles of the first city radius into terrains that give the resources the radius is short of, never taking a tile another needed resource cannot spare.

        gives is how many tiles of the radius give each needed resource now, and is kept up to
        date as tiles change.
        """
        needs = game.get_theme().MAP.START_NEEDS
        tiles = StartImprover.shuffled(game=game, tiles=StartImprover.plain_tiles(game=game, world_id=world_id, kind=kind, tiles=StartImprover.radius_outside_center(game=game, world_id=world_id, x=x, y=y)))
        for resource, need in needs.items():
            terrain = StartImprover.terrain_giving(game=game, kind=kind, resource=resource)
            for tile_x, tile_y in tiles:
                if gives[resource] >= need or terrain is None:
                    break
                given = Harvest.tile_gives(game=game, world=world_id, x=tile_x, y=tile_y)
                if resource not in given and StartImprover.can_spare(gives=gives, needs=needs, given=given):
                    TerrainControl.change(game=game, world=world_id, x=tile_x, y=tile_y, terrain=terrain)
                    for lost in given:
                        if lost in gives:
                            gives[lost] -= 1
                    for gained in terrain.GIVES:
                        if gained in gives:
                            gives[gained] += 1

    @staticmethod
    def can_spare(*, gives, needs, given):
        """Return whether a tile can stop giving what it gives without leaving the radius short of a needed resource."""
        return all(gives[resource] > needs[resource] for resource in given if resource in needs)

    @staticmethod
    def add_strategic(*, game, world_id, kind, x, y, resource):
        """Put a strategic resource near a starting site: on a tile whose terrain can have the resource, or else on a tile outside the first city radius turned into such a terrain."""
        random = game.get_random()
        world = game.get_world(world_id)
        near = on_the_map(tiles=square(x=x, y=y, size=strategic_square_size(game.get_theme())), world=world)
        able = [(tile_x, tile_y) for tile_x, tile_y in near if Strategic.resource_at(game=game, world=world_id, x=tile_x, y=tile_y) is None and resource in game.get_terrain(world=world_id, x=tile_x, y=tile_y).CAN_HAVE]
        if not able:
            terrain = StartImprover.terrain_having(game=game, kind=kind, resource=resource)
            radius = set(on_the_map(tiles=square(x=x, y=y, size=game.get_theme().CITY.RADIUS_SIZE), world=world))
            spare = StartImprover.plain_tiles(game=game, world_id=world_id, kind=kind, tiles=[tile for tile in near if tile not in radius])
            if terrain is None or not spare:
                return
            able = [random.choice(spare)]
            TerrainControl.change(game=game, world=world_id, x=able[0][0], y=able[0][1], terrain=terrain)
        tile_x, tile_y = random.choice(able)
        Strategic.place(game=game, world=world_id, x=tile_x, y=tile_y, resource=resource)

    @staticmethod
    def radius_outside_center(*, game, world_id, x, y):
        """Return the tiles of the radius of a city founded on a tile that are outside the city center, which are the tiles citizens work."""
        city = game.get_theme().CITY
        world = game.get_world(world_id)
        center = set(on_the_map(tiles=square(x=x, y=y, size=city.CENTER_SIZE), world=world))
        return [tile for tile in on_the_map(tiles=square(x=x, y=y, size=city.RADIUS_SIZE), world=world) if tile not in center]

    @staticmethod
    def plain_tiles(*, game, world_id, kind, tiles):
        """Return the tiles the generator may change: of a terrain the starting unit can be on and that can be built on, with nothing special on the tile."""
        world = game.get_world(world_id)
        return [(x, y) for x, y in tiles if StartImprover.is_changeable(kind=kind, terrain=game.get_terrain(world=world_id, x=x, y=y)) and all(world.get_value(layer=layer, x=x, y=y) == NOTHING for layer in SPECIAL_LAYERS)]

    @staticmethod
    def is_changeable(*, kind, terrain):
        """Return whether a terrain is one the generator changes tiles from and to: the starting unit can be on it, and it can be built on."""
        return terrain.BUILDABLE and UnitControl.can_be_on(kind=kind, terrain=terrain)

    @staticmethod
    def shuffled(*, game, tiles):
        """Return tiles in a random order, from the game's random source."""
        return game.get_random().sample(tiles, len(tiles))

    @staticmethod
    def terrain_giving(*, game, kind, resource):
        """Return the changeable terrain of the theme that gives the most of a resource, or None when none gives any."""
        giving = [terrain for terrain in game.get_theme().TERRAINS if resource in terrain.GIVES and StartImprover.is_changeable(kind=kind, terrain=terrain)]
        return max(giving, key=lambda terrain: terrain.GIVES[resource], default=None)

    @staticmethod
    def terrain_having(*, game, kind, resource):
        """Return the first changeable terrain of the theme that can have a strategic resource, or None when none can."""
        return next((terrain for terrain in game.get_theme().TERRAINS if resource in terrain.CAN_HAVE and StartImprover.is_changeable(kind=kind, terrain=terrain)), None)
