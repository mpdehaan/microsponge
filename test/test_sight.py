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

"""The fog of war: what a civilization sees, what it remembers, and the view a player reads the map through."""

import os
import tempfile
import unittest

from caveman_game import SETTLER_TILES, THE_WORLD, end_turn_by_order, found_village, game_facts, learn, new_caveman_game, settler_of, started_caveman_game
from later_caveman import later_caveman
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.sight import Sight, vision_size
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.saving.saved_game import load_game, save_game
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_NO_MEMORY
from microsponge.themes import THEMES
from microsponge.themes.caveman.terrains import Forest, Grassland
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Clubber

FIRST = 1
SECOND = 2
SAVED_GAME = 'sight.json'
# The first settler stands at (5, 12) and sees 5 tiles each way: these tiles are just inside and just outside what it sees.
INSIDE_TILE = (10, 12)
OUTSIDE_TILE = (11, 12)
FAR_TILE = (24, 2)
# The forest column is 12: a settler that has stepped two tiles east sees it.
FOREST_TILE = (12, 12)
# A tile 7 columns east of the first settler, inside a city radius built there but outside the settler's own vision.
RADIUS_EDGE_TILE = (12, 14)
# A tile by the west edge, from which vision wraps around to the east edge.
WEST_EDGE_TILE = (1, 12)
WRAPPED_TILE = (47, 12)
# Where another civilization's clubber stands within the first settler's vision, and where it does not.
NEAR_TILE = (8, 12)
# From here a unit sees a tile of the second civilization's city radius, which starts 7 columns west of the city at (35, 12).
WATCHING_TILE = (24, 12)
AWAY_TILE = (16, 12)
VILLAGE_NAME = 'Rockbottom'
# The id of the first city founded in a game.
FIRST_CITY = 1


class SeeingRocks(Technology):
    ENDS_FOG_OF_WAR = True


SEEING_CAVEMAN = later_caveman({Category.TECHNOLOGIES: Caveman.TECHNOLOGIES + (SeeingRocks,)})
# The theme's flag that later_caveman() sets, by its name on the theme class.
LAND_STARTS_EXPLORED = 'LAND_STARTS_EXPLORED'
EXPLORED_CAVEMAN = later_caveman({LAND_STARTS_EXPLORED: True})


class TestSight(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        self.world = self.game.get_world(THE_WORLD)

    def view(self, civilization):
        return Sight.view(game=self.game, civilization=civilization)

    def terrain_remembered(self, *, civilization, tile):
        x, y = tile
        return self.view(civilization).remembered(world=THE_WORLD, layer=Layer.TERRAIN, x=x, y=y)

    def has_seen(self, *, civilization, tile):
        x, y = tile
        return self.view(civilization).has_seen(world=THE_WORLD, x=x, y=y)

    def can_see(self, *, civilization, tile):
        x, y = tile
        return self.view(civilization).can_see(world=THE_WORLD, x=x, y=y)

    def place(self, *, kind, owner, tile):
        x, y = tile
        unit = UnitControl.place(game=self.game, kind=kind, owner=owner, world=THE_WORLD, x=x, y=y)
        Sight.look_around_unit(game=self.game, unit=unit)
        return unit

    def test_at_the_start_a_civilization_has_seen_the_square_around_its_settler_and_nothing_else(self):
        self.assertEqual(vision_size(Settler), 2 * Settler.VISION + 1)
        self.assertTrue(self.has_seen(civilization=FIRST, tile=INSIDE_TILE))
        self.assertFalse(self.has_seen(civilization=FIRST, tile=OUTSIDE_TILE))
        self.assertFalse(self.has_seen(civilization=FIRST, tile=FAR_TILE))
        self.assertFalse(self.has_seen(civilization=FIRST, tile=SETTLER_TILES[SECOND - 1]))
        self.assertTrue(self.has_seen(civilization=SECOND, tile=SETTLER_TILES[SECOND - 1]))
        self.assertEqual(self.terrain_remembered(civilization=FIRST, tile=OUTSIDE_TILE), NOTHING)
        self.assertEqual(self.terrain_remembered(civilization=FIRST, tile=INSIDE_TILE), self.game.get_catalog().get_id(category=Category.TERRAINS, kind=Grassland))
        self.assertFalse(Caveman.LAND_STARTS_EXPLORED)

    def test_in_a_theme_whose_land_starts_explored_every_tile_is_remembered_from_the_start(self):
        game = started_caveman_game(theme=EXPLORED_CAVEMAN)
        self.assertTrue(EXPLORED_CAVEMAN.LAND_STARTS_EXPLORED)
        view = Sight.view(game=game, civilization=FIRST)
        for tile in (INSIDE_TILE, OUTSIDE_TILE, FAR_TILE, SETTLER_TILES[SECOND - 1]):
            with self.subTest(tile=tile):
                x, y = tile
                self.assertTrue(view.has_seen(world=THE_WORLD, x=x, y=y))
        x, y = FAR_TILE
        self.assertFalse(view.can_see(world=THE_WORLD, x=x, y=y))

    def test_moving_a_unit_by_order_adds_what_it_sees_and_the_tiles_left_behind_stay_remembered(self):
        settler = settler_of(game=self.game, civilization=FIRST)
        x, y = SETTLER_TILES[FIRST - 1]
        Orders.move(game=self.game, unit=settler, x=x + 1, y=y)
        self.assertTrue(self.has_seen(civilization=FIRST, tile=OUTSIDE_TILE))
        self.assertTrue(self.can_see(civilization=FIRST, tile=OUTSIDE_TILE))
        self.assertTrue(self.has_seen(civilization=FIRST, tile=(x - Settler.VISION, y)))
        self.assertFalse(self.can_see(civilization=FIRST, tile=(x - Settler.VISION, y)))

    def test_vision_wraps_around_the_world_from_west_to_east(self):
        self.place(kind=Clubber, owner=FIRST, tile=WEST_EDGE_TILE)
        self.assertTrue(self.can_see(civilization=FIRST, tile=WRAPPED_TILE))
        self.assertTrue(self.has_seen(civilization=FIRST, tile=WRAPPED_TILE))
        x, y = WEST_EDGE_TILE
        self.assertTrue(self.view(FIRST).can_see(world=THE_WORLD, x=x - 2, y=y))

    def test_a_city_sees_its_whole_city_radius_which_is_wider_than_a_unit_sees(self):
        self.assertFalse(self.has_seen(civilization=FIRST, tile=RADIUS_EDGE_TILE))
        city = Orders.found_city(game=self.game, settler=settler_of(game=self.game, civilization=FIRST), name=VILLAGE_NAME)
        self.assertTrue(self.has_seen(civilization=FIRST, tile=RADIUS_EDGE_TILE))
        self.assertTrue(self.can_see(civilization=FIRST, tile=RADIUS_EDGE_TILE))
        radius = {(THE_WORLD, x, y) for x, y in CityControl.radius_tiles(game=self.game, city=city)}
        self.assertEqual(Sight.vision(game=self.game, civilization=FIRST), radius)

    def test_a_tile_is_remembered_as_last_seen_until_it_is_seen_again(self):
        settler = settler_of(game=self.game, civilization=FIRST)
        x, y = SETTLER_TILES[FIRST - 1]
        forest = self.game.get_catalog().get_id(category=Category.TERRAINS, kind=Forest)
        grassland = self.game.get_catalog().get_id(category=Category.TERRAINS, kind=Grassland)
        UnitControl.move_to(game=self.game, unit=settler, x=x + 2, y=y)
        Sight.look_around_unit(game=self.game, unit=settler)
        self.assertEqual(self.terrain_remembered(civilization=FIRST, tile=FOREST_TILE), forest)
        UnitControl.move_to(game=self.game, unit=settler, x=x, y=y)
        Sight.look_around_unit(game=self.game, unit=settler)
        forest_x, forest_y = FOREST_TILE
        self.world.set_value(layer=Layer.TERRAIN, x=forest_x, y=forest_y, value=grassland)
        self.assertFalse(self.can_see(civilization=FIRST, tile=FOREST_TILE))
        self.assertEqual(self.terrain_remembered(civilization=FIRST, tile=FOREST_TILE), forest)
        UnitControl.move_to(game=self.game, unit=settler, x=x + 2, y=y)
        Sight.look_around_unit(game=self.game, unit=settler)
        self.assertEqual(self.terrain_remembered(civilization=FIRST, tile=FOREST_TILE), grassland)

    def test_what_changes_in_vision_while_others_play_is_recorded_when_the_turn_comes_back(self):
        grassland = self.game.get_catalog().get_id(category=Category.TERRAINS, kind=Grassland)
        forest = self.game.get_catalog().get_id(category=Category.TERRAINS, kind=Forest)
        x, y = INSIDE_TILE
        memory = self.game.get_civilization(FIRST).get_memory(THE_WORLD)
        self.assertEqual(memory.get_value(layer=Layer.TERRAIN, x=x, y=y), grassland)
        end_turn_by_order(game=self.game, civilization=FIRST)
        self.world.set_value(layer=Layer.TERRAIN, x=x, y=y, value=forest)
        self.assertEqual(memory.get_value(layer=Layer.TERRAIN, x=x, y=y), grassland)
        end_turn_by_order(game=self.game, civilization=SECOND)
        self.assertEqual(memory.get_value(layer=Layer.TERRAIN, x=x, y=y), forest)

    def test_another_civilizations_unit_is_seen_only_in_vision_and_its_own_always(self):
        settler = settler_of(game=self.game, civilization=FIRST)
        near = self.place(kind=Clubber, owner=SECOND, tile=NEAR_TILE)
        far = self.place(kind=Clubber, owner=SECOND, tile=FAR_TILE)
        view = self.view(FIRST)
        self.assertEqual(view.units_seen(), [near])
        x, y = NEAR_TILE
        self.assertEqual(view.unit_on(world=THE_WORLD, x=x, y=y), near)
        x, y = FAR_TILE
        self.assertEqual(view.unit_on(world=THE_WORLD, x=x, y=y), NOTHING)
        x, y = SETTLER_TILES[FIRST - 1]
        self.assertEqual(view.unit_on(world=THE_WORLD, x=x, y=y), settler)
        self.assertNotIn(far, view.units_seen())
        self.assertIn(settler_of(game=self.game, civilization=FIRST), Sight.units_of(game=self.game, civilization=FIRST))
        self.assertEqual(self.view(SECOND).units_seen(), [settler])

    def test_a_technology_that_ends_the_fog_of_war_shows_every_unit_but_reveals_no_land(self):
        game = started_caveman_game(theme=SEEING_CAVEMAN)
        x, y = FAR_TILE
        far = UnitControl.place(game=game, kind=Clubber, owner=SECOND, world=THE_WORLD, x=x, y=y)
        self.assertFalse(Sight.sees_every_unit(game=game, civilization=FIRST))
        self.assertNotIn(far, Sight.view(game=game, civilization=FIRST).units_seen())
        learn(game=game, civilization=FIRST, technology=SeeingRocks)
        self.assertTrue(Sight.sees_every_unit(game=game, civilization=FIRST))
        view = Sight.view(game=game, civilization=FIRST)
        self.assertEqual(view.units_seen(), [settler_of(game=game, civilization=SECOND), far])
        self.assertEqual(view.unit_on(world=THE_WORLD, x=x, y=y), far)
        self.assertFalse(view.has_seen(world=THE_WORLD, x=x, y=y))
        self.assertFalse(Sight.sees_every_unit(game=game, civilization=SECOND))

    def test_a_unit_inside_a_city_is_on_no_tile_and_is_not_seen_even_when_the_fog_of_war_has_ended(self):
        game = started_caveman_game(theme=SEEING_CAVEMAN)
        learn(game=game, civilization=FIRST, technology=SeeingRocks)
        city = found_village(game=game, civilization=SECOND, name=VILLAGE_NAME)
        x, y = CityControl.ring_tiles(game=game, city=city)[0]
        clubber = UnitControl.place(game=game, kind=Clubber, owner=SECOND, world=THE_WORLD, x=x, y=y)
        self.assertIn(clubber, Sight.view(game=game, civilization=FIRST).units_seen())
        CityControl.enter(game=game, unit=clubber, city=city)
        self.assertNotIn(clubber, Sight.view(game=game, civilization=FIRST).units_seen())

    def test_a_city_seen_once_stays_on_the_map_with_the_owner_it_had_until_seen_again(self):
        city = found_village(game=self.game, civilization=SECOND, name=VILLAGE_NAME)
        Sight.look_around_city(game=self.game, city=city)
        self.assertEqual(self.view(FIRST).owner_of(city), NOTHING)
        self.assertEqual(self.view(SECOND).owner_of(city), SECOND)
        watcher = self.place(kind=Clubber, owner=FIRST, tile=WATCHING_TILE)
        self.assertEqual(self.view(FIRST).owner_of(city), SECOND)
        x, y = AWAY_TILE
        UnitControl.move_to(game=self.game, unit=watcher, x=x, y=y)
        Sight.look_around_unit(game=self.game, unit=watcher)
        # The city changes hands while the second civilization, whose settler built it, has nothing left to see it with.
        self.game.get_city(city).set_owner(FIRST)
        self.assertEqual(self.view(SECOND).owner_of(city), SECOND)
        self.assertEqual(self.view(FIRST).owner_of(city), FIRST)
        self.place(kind=Clubber, owner=SECOND, tile=WATCHING_TILE)
        self.assertEqual(self.view(SECOND).owner_of(city), FIRST)
        radius_x, radius_y = CityControl.radius_tiles(game=self.game, city=city)[0]
        self.assertEqual(self.view(FIRST).remembered(world=THE_WORLD, layer=Layer.CITY, x=radius_x, y=radius_y), city)

    def test_a_game_that_has_not_started_has_no_memories_and_says_so(self):
        game = new_caveman_game()
        self.assertEqual(game.get_civilization(FIRST).get_memories(), [])
        self.assertEqual(self.refused(lambda: game.get_civilization(FIRST).get_memory(THE_WORLD)), ERR_NO_MEMORY.format(name=game.get_civilization(FIRST).get_name(), world=THE_WORLD))
        self.assertEqual(len(self.game.get_civilization(FIRST).get_memories()), len(self.game.get_worlds()))

    def test_memories_are_saved_and_loaded_with_what_was_seen_and_the_owners_of_the_cities_seen(self):
        settler = settler_of(game=self.game, civilization=FIRST)
        x, y = SETTLER_TILES[FIRST - 1]
        Orders.move(game=self.game, unit=settler, x=x + 1, y=y)
        found_village(game=self.game, civilization=SECOND, name=VILLAGE_NAME)
        Sight.refresh(game=self.game, civilization=SECOND)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, SAVED_GAME)
            save_game(game=self.game, path=path)
            loaded = load_game(path=path, themes=THEMES)
            self.assertEqual(game_facts(loaded), game_facts(self.game))
        # The settler stepped east, so the tile at the west edge of where it started is remembered, and only remembered.
        behind = (x - Settler.VISION, y)
        view = Sight.view(game=loaded, civilization=FIRST)
        self.assertTrue(view.has_seen(world=THE_WORLD, x=behind[0], y=behind[1]))
        self.assertFalse(view.can_see(world=THE_WORLD, x=behind[0], y=behind[1]))
        self.assertEqual(loaded.get_civilization(FIRST).get_memory(THE_WORLD).get_owner(FIRST_CITY), NOTHING)
        self.assertEqual(loaded.get_civilization(SECOND).get_memory(THE_WORLD).get_owner(FIRST_CITY), SECOND)
