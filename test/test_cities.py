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

"""Cities in a game of caveman, where a city is a village: building one, the tiles it covers, and the units inside."""

import json
import os
import tempfile
import unittest

from caveman_game import OVERLAPPING_TILE, SETTLER_TILES, THE_WORLD, WORLD_HEIGHT, WORLD_WIDTH, game_facts, new_caveman_game, terrain_id
from refusals import Refusals
from microsponge.engine.cities.city import City
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.city_spec import CitySpec
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.saving.saved_game import load_game, save_game
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_CANNOT_BE_ON, ERR_CITIZENS, ERR_CITY_COVERS_A_UNIT, ERR_CITY_COVERS_TERRAIN, ERR_CITY_FULL, ERR_CITY_NAME, ERR_CITY_NEEDS_LAND, ERR_CITY_OFF_THE_MAP,
    ERR_CITY_TOO_CLOSE, ERR_NO_SUCH_CITY, ERR_NO_SUCH_UNIT, ERR_NOT_A_SETTLER, ERR_NOT_AT_WAR, ERR_NOT_NEXT_TO_CENTER, ERR_NOT_NEXT_TO_CITY,
    ERR_TILE_HAS_A_UNIT, ERR_TILE_IN_A_CITY_CENTER, ERR_UNIT_ALREADY_HELD, ERR_UNIT_IN_A_CITY, ERR_UNIT_NOT_HELD, ERR_UNIT_NOT_IN_A_CITY,
)
from microsponge.themes import THEMES
from microsponge.themes.caveman.terrains import Mountains, Tarpit, Water
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Warrior

VILLAGE = Caveman.CITY.NAME
FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
FIRST_CITY = 1
FIRST_NAME = 'Ugg'
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
A_THIRD_NAME = 'Lakeside'
BLANK = '  '
A_TURN = 9
FILE_NAME = 'game.json'
# How far the city center and the city radius reach from the middle tile, and one tile further.
CENTER_REACH = CitySpec.CENTER_SIZE // 2
RADIUS_REACH = CitySpec.RADIUS_SIZE // 2
JUST_PAST_CENTER = CENTER_REACH + 1
JUST_PAST_RADIUS = RADIUS_REACH + 1
CENTER_TILES = CitySpec.CENTER_SIZE * CitySpec.CENTER_SIZE
RADIUS_TILES = CitySpec.RADIUS_SIZE * CitySpec.RADIUS_SIZE
# A tile far from both settlers with only grassland around, as (x, y).
OPEN_TILE = (20, 20)
# A row with only grassland, where a city radius built past the first city's reaches off the bottom of the world.
OPEN_ROW = 20
MIDDLE_ROW = 12


class TestCity(Refusals, unittest.TestCase):

    def setUp(self):
        self.city = City(name=A_NAME, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=5, y=MIDDLE_ROW, founded=A_TURN, citizens=1)

    def test_a_city_keeps_what_it_was_built_with(self):
        facts = (self.city.get_name(), self.city.get_owner(), self.city.get_world(), self.city.get_x(), self.city.get_y(), self.city.get_founded(), self.city.get_citizens())
        self.assertEqual(facts, (A_NAME, FIRST_CIVILIZATION, THE_WORLD, 5, MIDDLE_ROW, A_TURN, 1))
        self.assertEqual(self.city.get_units(), [])

    def test_the_name_the_owner_and_the_citizens_can_change(self):
        self.city.set_name(ANOTHER_NAME)
        self.city.set_owner(SECOND_CIVILIZATION)
        self.city.set_citizens(4)
        self.assertEqual((self.city.get_name(), self.city.get_owner(), self.city.get_citizens()), (ANOTHER_NAME, SECOND_CIVILIZATION, 4))

    def test_a_blank_name_or_a_negative_number_of_citizens_is_refused(self):
        for name in (BLANK, None, 3):
            with self.subTest(name=name):
                self.assertEqual(self.refused(lambda: self.city.set_name(name)), ERR_CITY_NAME.format(value=name))
        for citizens in (-1, None, 1.5):
            with self.subTest(citizens=citizens):
                self.assertEqual(self.refused(lambda: self.city.set_citizens(citizens)), ERR_CITIZENS.format(value=citizens))
        self.assertEqual((self.city.get_name(), self.city.get_citizens()), (A_NAME, 1))

    def test_a_city_holds_units_in_the_order_they_entered(self):
        self.city.add_unit(7)
        self.city.add_unit(3)
        self.assertEqual(self.city.get_units(), [7, 3])
        self.assertTrue(self.city.holds(7))
        self.assertFalse(self.city.holds(4))
        self.assertEqual(self.refused(lambda: self.city.add_unit(7)), ERR_UNIT_ALREADY_HELD.format(unit=7, name=A_NAME))
        self.city.remove_unit(7)
        self.assertEqual(self.city.get_units(), [3])
        self.assertEqual(self.refused(lambda: self.city.remove_unit(7)), ERR_UNIT_NOT_HELD.format(unit=7, name=A_NAME))
        self.city.get_units().clear()
        self.assertEqual(self.city.get_units(), [3])

    def test_a_city_comes_back_from_a_saved_game_as_it_was(self):
        self.city.add_unit(7)
        loaded = City.from_data(json.loads(json.dumps(self.city.to_data())))
        self.assertEqual(loaded.to_data(), self.city.to_data())
        self.assertEqual(loaded.get_units(), [7])


class TestBuildingACity(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = new_caveman_game()
        self.game.set_turn(A_TURN)
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        self.first_settler = self.unit_on(SETTLER_TILES[0])
        self.second_settler = self.unit_on(SETTLER_TILES[1])

    def unit_on(self, tile):
        x, y = tile
        return self.world.get_value(layer=Layer.UNIT, x=x, y=y)

    def place(self, *, kind, tile, owner=FIRST_CIVILIZATION):
        x, y = tile
        return UnitControl.place(game=self.game, kind=kind, owner=owner, world=THE_WORLD, x=x, y=y)

    def tiles_of(self, *, layer, city):
        """Return every tile of the world that a layer gives to a city, as a set of (x, y)."""
        return {(x, y) for y in range(WORLD_HEIGHT) for x in range(WORLD_WIDTH) if self.world.get_value(layer=layer, x=x, y=y) == city}

    def set_terrain(self, *, tile, terrain):
        x, y = tile
        self.world.set_value(layer=Layer.TERRAIN, x=x, y=y, value=terrain_id(game=self.game, terrain=terrain))

    def center_around(self, tile):
        """Return the tiles of a city center around a tile, but for the tile itself."""
        x, y = tile
        reach = range(-CENTER_REACH, CENTER_REACH + 1)
        return [(x + across, y + down) for down in reach for across in reach if (across, down) != (0, 0)]

    def test_a_settler_builds_a_city_where_it_stands_and_is_gone(self):
        count = self.units.count()
        city = CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        self.assertEqual(city, FIRST_CITY)
        self.assertFalse(self.units.exists(self.first_settler))
        self.assertEqual(self.units.count(), count - 1)
        self.assertEqual(self.unit_on(SETTLER_TILES[0]), NOTHING)
        built = self.game.get_city(city)
        x, y = SETTLER_TILES[0]
        facts = (built.get_name(), built.get_owner(), built.get_world(), built.get_x(), built.get_y(), built.get_founded(), built.get_citizens())
        self.assertEqual(facts, (A_NAME, FIRST_CIVILIZATION, THE_WORLD, x, y, A_TURN, Caveman.CITY.STARTING_CITIZENS))
        self.assertEqual(built.get_units(), [])
        self.assertEqual(self.game.get_cities(), [built])

    def test_the_city_center_is_5_by_5_tiles_inside_a_city_radius_of_15_by_15(self):
        city = CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        center = self.tiles_of(layer=Layer.CITY_CENTER, city=city)
        radius = self.tiles_of(layer=Layer.CITY, city=city)
        self.assertEqual(len(center), CENTER_TILES)
        self.assertEqual(len(radius), RADIUS_TILES)
        self.assertLess(center, radius)
        self.assertEqual(center, set(CityControl.center_tiles(game=self.game, city=city)))
        self.assertEqual(radius, set(CityControl.radius_tiles(game=self.game, city=city)))
        self.assertIn((x + CENTER_REACH, y - CENTER_REACH), center)
        self.assertNotIn((x + JUST_PAST_CENTER, y), center)
        self.assertNotIn((x, y + JUST_PAST_CENTER), center)
        self.assertIn((x + RADIUS_REACH, y + RADIUS_REACH), radius)
        self.assertNotIn((x + JUST_PAST_RADIUS, y), radius)
        self.assertNotIn((x, y - JUST_PAST_RADIUS), radius)

    def test_the_tiles_next_to_the_city_center_are_the_24_around_it(self):
        city = CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        ring = CityControl.ring_tiles(game=self.game, city=city)
        self.assertEqual(len(ring), (CitySpec.CENTER_SIZE + 2) ** 2 - CENTER_TILES)
        self.assertEqual(len(set(ring)), len(ring))
        self.assertIn((x + JUST_PAST_CENTER, y), ring)
        self.assertIn((x - JUST_PAST_CENTER, y + JUST_PAST_CENTER), ring)
        self.assertNotIn((x + CENTER_REACH, y), ring)
        self.assertNotIn((x + JUST_PAST_CENTER + 1, y), ring)

    def test_the_city_radius_goes_around_the_edge_of_the_world(self):
        city = CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        self.assertLess(x - RADIUS_REACH, 0)
        self.assertEqual(self.world.get_value(layer=Layer.CITY, x=WORLD_WIDTH + x - RADIUS_REACH, y=y), city)
        self.assertEqual(self.world.get_value(layer=Layer.CITY, x=WORLD_WIDTH - 1, y=y), city)
        self.assertEqual(self.world.get_value(layer=Layer.CITY, x=WORLD_WIDTH + x - JUST_PAST_RADIUS, y=y), NOTHING)

    def test_two_city_radii_never_overlap_and_a_tile_belongs_to_one_city_at_most(self):
        first = CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        second = CityControl.found(game=self.game, settler=self.second_settler, name=ANOTHER_NAME)
        self.assertFalse(set(CityControl.radius_tiles(game=self.game, city=first)) & set(CityControl.radius_tiles(game=self.game, city=second)))
        for city in (first, second):
            self.assertEqual(len(self.tiles_of(layer=Layer.CITY, city=city)), RADIUS_TILES)
            self.assertEqual(len(self.tiles_of(layer=Layer.CITY_CENTER, city=city)), CENTER_TILES)

    def test_a_city_radius_may_not_overlap_another_city_radius_whoever_owns_it(self):
        CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        x, y = SETTLER_TILES[0]
        edge = x + RADIUS_REACH
        expected = ERR_CITY_TOO_CLOSE.format(city=VILLAGE, name=A_NAME)
        for owner in (FIRST_CIVILIZATION, SECOND_CIVILIZATION):
            for tile in ((edge + CENTER_REACH, y), (edge + RADIUS_REACH, OPEN_ROW), OVERLAPPING_TILE):
                with self.subTest(owner=owner, tile=tile):
                    overlapping = self.place(kind=Settler, tile=tile, owner=owner)
                    self.assertEqual(CityControl.problem_founding(game=self.game, settler=overlapping), expected)
                    self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=overlapping, name=ANOTHER_NAME)), expected)
                    self.assertTrue(self.units.exists(overlapping))
                    UnitControl.remove(game=self.game, unit=overlapping)
        clear = self.place(kind=Settler, tile=(edge + JUST_PAST_RADIUS, OPEN_ROW), owner=SECOND_CIVILIZATION)
        self.assertIsNone(CityControl.problem_founding(game=self.game, settler=clear))
        second = CityControl.found(game=self.game, settler=clear, name=ANOTHER_NAME)
        self.assertEqual(len(self.tiles_of(layer=Layer.CITY_CENTER, city=second)), CENTER_TILES)
        self.assertLess(len(self.tiles_of(layer=Layer.CITY, city=second)), RADIUS_TILES)
        self.assertEqual(len(self.game.get_cities()), 2)

    def test_the_whole_city_center_has_to_be_on_the_map_and_the_city_radius_is_cut_off_at_the_edge(self):
        expected = ERR_CITY_OFF_THE_MAP.format(city=VILLAGE)
        x, _ = OPEN_TILE
        for y in (CENTER_REACH - 1, WORLD_HEIGHT - CENTER_REACH):
            with self.subTest(y=y):
                settler = self.place(kind=Settler, tile=(x, y))
                self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=settler, name=A_NAME)), expected)
                self.assertTrue(self.units.exists(settler))
                UnitControl.remove(game=self.game, unit=settler)
        settler = self.place(kind=Settler, tile=(x, CENTER_REACH))
        city = CityControl.found(game=self.game, settler=settler, name=A_NAME)
        self.assertEqual(len(self.tiles_of(layer=Layer.CITY_CENTER, city=city)), CENTER_TILES)
        rows_on_the_map = CENTER_REACH + RADIUS_REACH + 1
        self.assertEqual(len(self.tiles_of(layer=Layer.CITY, city=city)), CitySpec.RADIUS_SIZE * rows_on_the_map)
        self.assertEqual(self.game.get_cities(), [self.game.get_city(city)])

    def test_a_city_center_cannot_cover_a_tarpit_and_can_cover_mountains(self):
        settler = self.place(kind=Settler, tile=OPEN_TILE)
        corner = self.center_around(OPEN_TILE)[0]
        self.set_terrain(tile=corner, terrain=Tarpit)
        x, y = corner
        expected = ERR_CITY_COVERS_TERRAIN.format(city=VILLAGE, terrain=shown_name(Tarpit), x=x, y=y)
        self.assertEqual(CityControl.problem_founding(game=self.game, settler=settler), expected)
        self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=settler, name=A_NAME)), expected)
        self.assertEqual(self.game.get_cities(), [])
        self.set_terrain(tile=corner, terrain=Mountains)
        self.assertIsNone(CityControl.problem_founding(game=self.game, settler=settler))

    def test_at_least_13_tiles_of_the_city_center_have_to_be_land_and_mountains_are_land(self):
        settler = self.place(kind=Settler, tile=OPEN_TILE)
        around = self.center_around(OPEN_TILE)
        most_water = CENTER_TILES - Caveman.CITY.CENTER_LAND
        for tile in around[:most_water]:
            self.set_terrain(tile=tile, terrain=Water)
        for tile in around[most_water:most_water + 3]:
            self.set_terrain(tile=tile, terrain=Mountains)
        self.assertIsNone(CityControl.problem_founding(game=self.game, settler=settler))
        self.set_terrain(tile=around[most_water], terrain=Water)
        expected = ERR_CITY_NEEDS_LAND.format(city=VILLAGE, least=Caveman.CITY.CENTER_LAND, land=Caveman.CITY.CENTER_LAND - 1)
        self.assertEqual(CityControl.problem_founding(game=self.game, settler=settler), expected)
        self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=settler, name=A_NAME)), expected)
        self.assertEqual(self.game.get_cities(), [])
        self.set_terrain(tile=around[most_water], terrain=Mountains)
        CityControl.found(game=self.game, settler=settler, name=A_NAME)
        self.assertEqual(len(self.game.get_cities()), 1)

    def test_a_city_center_may_not_cover_another_unit(self):
        x, y = SETTLER_TILES[0]
        corner = (x + CENTER_REACH, y + CENTER_REACH)
        warrior = self.place(kind=Warrior, tile=corner, owner=SECOND_CIVILIZATION)
        expected = ERR_CITY_COVERS_A_UNIT.format(city=VILLAGE, x=corner[0], y=corner[1])
        self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)), expected)
        UnitControl.remove(game=self.game, unit=warrior)
        self.place(kind=Warrior, tile=(x + JUST_PAST_CENTER, y), owner=SECOND_CIVILIZATION)
        CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        self.assertEqual(len(self.game.get_cities()), 1)

    def test_only_a_settler_builds_a_city(self):
        warrior = self.place(kind=Warrior, tile=OPEN_TILE)
        expected = ERR_NOT_A_SETTLER.format(unit=shown_name(Warrior), city=VILLAGE)
        self.assertEqual(CityControl.problem_founding(game=self.game, settler=warrior), expected)
        self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=warrior, name=A_NAME)), expected)
        self.assertTrue(self.units.exists(warrior))
        gone = self.units.count() + 10
        self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=gone, name=A_NAME)), ERR_NO_SUCH_UNIT.format(unit=gone))
        self.assertEqual(self.game.get_cities(), [])

    def test_a_city_without_a_name_is_not_built_and_the_settler_stays(self):
        for name in (BLANK, None):
            with self.subTest(name=name):
                self.assertEqual(self.refused(lambda: CityControl.found(game=self.game, settler=self.first_settler, name=name)), ERR_CITY_NAME.format(value=name))
        self.assertTrue(self.units.exists(self.first_settler))
        self.assertEqual(self.unit_on(SETTLER_TILES[0]), self.first_settler)
        self.assertEqual(self.game.get_cities(), [])
        self.assertEqual(self.tiles_of(layer=Layer.CITY, city=FIRST_CITY), set())

    def test_an_id_that_is_no_city_is_refused(self):
        CityControl.found(game=self.game, settler=self.first_settler, name=A_NAME)
        for city in (NOTHING, FIRST_CITY + 1, -1, A_NAME, None):
            with self.subTest(city=city):
                self.assertEqual(self.refused(lambda: self.game.get_city(city)), ERR_NO_SUCH_CITY.format(city=city))


class TestUnitsInACity(Refusals, unittest.TestCase):

    def setUp(self):
        self.game = new_caveman_game()
        self.units = self.game.get_units()
        self.world = self.game.get_world(THE_WORLD)
        x, y = SETTLER_TILES[0]
        self.city = CityControl.found(game=self.game, settler=self.world.get_value(layer=Layer.UNIT, x=x, y=y), name=A_NAME)
        self.middle = (x, y)
        self.east = (x + JUST_PAST_CENTER, y)
        self.west = (x - JUST_PAST_CENTER, y)
        self.north = (x, y - JUST_PAST_CENTER)
        self.corner = (x + JUST_PAST_CENTER, y + JUST_PAST_CENTER)
        self.further_east = (x + JUST_PAST_CENTER + 1, y)

    def place(self, *, tile, owner=FIRST_CIVILIZATION):
        x, y = tile
        return UnitControl.place(game=self.game, kind=Warrior, owner=owner, world=THE_WORLD, x=x, y=y)

    def unit_on(self, tile):
        x, y = tile
        return self.world.get_value(layer=Layer.UNIT, x=x, y=y)

    def inside(self, tile):
        """Place a warrior on a tile next to the city center, move it into the city and return it."""
        unit = self.place(tile=tile)
        CityControl.enter(game=self.game, unit=unit, city=self.city)
        return unit

    def test_no_unit_stands_on_a_tile_of_a_city_center(self):
        x, y = self.middle
        for tile in (self.middle, (x + CENTER_REACH, y - CENTER_REACH)):
            with self.subTest(tile=tile):
                self.assertEqual(self.refused(lambda: self.place(tile=tile)), ERR_TILE_IN_A_CITY_CENTER.format(city=VILLAGE, x=tile[0], y=tile[1]))
        self.assertEqual(self.unit_on(self.east), NOTHING)
        self.place(tile=self.east)

    def test_a_unit_next_to_the_city_center_of_its_own_city_goes_inside_and_leaves_its_tile(self):
        for tile in (self.east, self.corner):
            with self.subTest(tile=tile):
                unit = self.inside(tile)
                self.assertEqual(self.unit_on(tile), NOTHING)
                self.assertEqual(self.units.get_value(column=UnitColumn.CITY, unit=unit), self.city)
                self.assertEqual(UnitControl.tile_of(game=self.game, unit=unit), (THE_WORLD, *self.middle))
                self.assertTrue(self.game.get_city(self.city).holds(unit))
        self.assertEqual(len(self.game.get_city(self.city).get_units()), 2)

    def test_a_unit_that_is_not_next_to_the_city_center_cannot_go_inside(self):
        unit = self.place(tile=self.further_east)
        self.assertEqual(self.refused(lambda: CityControl.enter(game=self.game, unit=unit, city=self.city)), ERR_NOT_NEXT_TO_CITY.format(unit=unit, city=VILLAGE, name=A_NAME))
        self.assertEqual(self.unit_on(self.further_east), unit)
        self.assertEqual(self.game.get_city(self.city).get_units(), [])

    def test_a_unit_of_another_civilization_cannot_go_inside_without_a_war(self):
        unit = self.place(tile=self.east, owner=SECOND_CIVILIZATION)
        self.assertEqual(self.refused(lambda: CityControl.enter(game=self.game, unit=unit, city=self.city)), ERR_NOT_AT_WAR.format(name=FIRST_NAME))
        self.assertEqual(self.unit_on(self.east), unit)

    def test_a_city_holds_3_units_and_no_more(self):
        most = Caveman.CITY.MOST_UNITS
        tiles = (self.east, self.west, self.north)
        self.assertEqual(len(tiles), most)
        for tile in tiles:
            self.inside(tile)
        one_too_many = self.place(tile=self.corner)
        self.assertEqual(self.refused(lambda: CityControl.enter(game=self.game, unit=one_too_many, city=self.city)), ERR_CITY_FULL.format(city=VILLAGE, name=A_NAME, most=most))
        self.assertEqual(self.unit_on(self.corner), one_too_many)
        self.assertEqual(len(self.game.get_city(self.city).get_units()), most)

    def test_a_unit_inside_a_city_cannot_go_inside_again(self):
        unit = self.inside(self.east)
        self.assertEqual(self.refused(lambda: CityControl.enter(game=self.game, unit=unit, city=self.city)), ERR_UNIT_IN_A_CITY.format(unit=unit, city=VILLAGE))
        self.assertEqual(self.game.get_city(self.city).get_units(), [unit])

    def test_a_unit_leaves_a_city_onto_an_empty_tile_next_to_the_city_center(self):
        unit = self.inside(self.east)
        x, y = self.north
        CityControl.leave(game=self.game, unit=unit, x=x, y=y)
        self.assertEqual(self.unit_on(self.north), unit)
        self.assertEqual(self.units.get_value(column=UnitColumn.CITY, unit=unit), NOTHING)
        self.assertEqual(UnitControl.tile_of(game=self.game, unit=unit), (THE_WORLD, x, y))
        self.assertEqual(self.game.get_city(self.city).get_units(), [])
        self.assertEqual(self.refused(lambda: CityControl.leave(game=self.game, unit=unit, x=x, y=y)), ERR_UNIT_NOT_IN_A_CITY.format(unit=unit, city=VILLAGE))

    def test_a_unit_cannot_leave_a_city_onto_a_tile_it_cannot_stand_on(self):
        unit = self.inside(self.east)
        blocker = self.place(tile=self.east)
        water = self.west
        self.world.set_value(layer=Layer.TERRAIN, x=water[0], y=water[1], value=terrain_id(game=self.game, terrain=Water))
        refusals = {
            self.east: ERR_TILE_HAS_A_UNIT.format(x=self.east[0], y=self.east[1]),
            water: ERR_CANNOT_BE_ON.format(unit=shown_name(Warrior), terrain=shown_name(Water)),
            self.further_east: ERR_NOT_NEXT_TO_CENTER.format(x=self.further_east[0], y=self.further_east[1], city=VILLAGE, name=A_NAME),
            self.middle: ERR_NOT_NEXT_TO_CENTER.format(x=self.middle[0], y=self.middle[1], city=VILLAGE, name=A_NAME),
            (self.east[0], None): ERR_NOT_NEXT_TO_CENTER.format(x=self.east[0], y=None, city=VILLAGE, name=A_NAME),
        }
        for (x, y), expected in refusals.items():
            with self.subTest(x=x, y=y):
                self.assertEqual(self.refused(lambda: CityControl.leave(game=self.game, unit=unit, x=x, y=y)), expected)
        self.assertEqual(self.game.get_city(self.city).get_units(), [unit])
        self.assertEqual(self.units.get_value(column=UnitColumn.CITY, unit=unit), self.city)
        self.assertEqual(self.unit_on(self.east), blocker)

    def test_a_unit_removed_while_inside_a_city_leaves_the_city(self):
        unit = self.inside(self.east)
        other = self.inside(self.west)
        UnitControl.remove(game=self.game, unit=unit)
        self.assertFalse(self.units.exists(unit))
        self.assertEqual(self.game.get_city(self.city).get_units(), [other])

    def test_a_settler_inside_a_city_cannot_build_a_city(self):
        x, y = self.east
        settler = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        CityControl.enter(game=self.game, unit=settler, city=self.city)
        self.assertEqual(CityControl.problem_founding(game=self.game, settler=settler), ERR_UNIT_IN_A_CITY.format(unit=settler, city=VILLAGE))

    def test_a_game_with_cities_and_a_unit_inside_one_comes_back_from_its_file_as_it_was(self):
        inside = self.inside(self.east)
        outside = self.place(tile=self.corner)
        x, y = SETTLER_TILES[1]
        second = CityControl.found(game=self.game, settler=self.unit_on((x, y)), name=ANOTHER_NAME)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, FILE_NAME)
            save_game(game=self.game, path=path)
            loaded = load_game(path=path, themes=THEMES)
        self.assertEqual(game_facts(loaded), game_facts(self.game))
        self.assertEqual(loaded.get_city(self.city).get_units(), [inside])
        self.assertEqual(loaded.get_city(second).get_name(), ANOTHER_NAME)
        self.assertEqual(loaded.get_units().get_value(column=UnitColumn.CITY, unit=inside), self.city)
        self.assertEqual(loaded.get_units().get_value(column=UnitColumn.CITY, unit=outside), NOTHING)
        CityControl.leave(game=loaded, unit=inside, x=self.east[0], y=self.east[1])
        self.assertEqual(loaded.get_world(THE_WORLD).get_value(layer=Layer.UNIT, x=self.east[0], y=self.east[1]), inside)
        third = UnitControl.place(game=loaded, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=OPEN_TILE[0], y=OPEN_TILE[1])
        self.assertEqual(CityControl.found(game=loaded, settler=third, name=A_THIRD_NAME), second + 1)


if __name__ == '__main__':
    unittest.main()
