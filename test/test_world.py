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

"""A world: layers of integers, wrapping from east to west and not from north to south."""

import json
import unittest

from refusals import Refusals
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.world.layer import LAYERS, RETIRED_LAYERS, Layer
from microsponge.engine.world.world import HEIGHT_KEY, LAYERS_KEY, WIDTH_KEY, World
from microsponge.err_messages import ERR_LAYER_SHAPE, ERR_NO_SUCH_LAYER, ERR_ROW_OFF_THE_MAP, ERR_UNKNOWN_ID, ERR_WORLD_SIZE

WIDTH = 6
HEIGHT = 4
A_TERRAIN = 3
ANOTHER_TERRAIN = 5
A_UNIT = 7
NOT_A_SIZE = 'wide'
NOT_A_LAYER = 'terrain'
# Two columns and how far apart the two are: side by side, across the edge of the world, the same column, and a whole world further on.
COLUMNS_APART = ((2, 3, 1), (0, WIDTH - 1, 1), (1, WIDTH - 2, 3), (4, 4, 0), (1, 1 + WIDTH, 0))
ONE_AROUND = 1
TWICE_AROUND = 2


def a_layer_nobody_has():
    """Return a number that is no layer, as a later version's layer or a retired one would be to this one."""
    return max(LAYERS + RETIRED_LAYERS) + 1


def through_json(data):
    """Return data as it comes back from a saved game."""
    return json.loads(json.dumps(data))


class TestWorld(Refusals, unittest.TestCase):

    def setUp(self):
        self.world = World(width=WIDTH, height=HEIGHT)

    def every_value(self, *, world, layer):
        return [[world.get_value(layer=layer, x=x, y=y) for x in range(world.get_width())] for y in range(world.get_height())]

    def test_a_new_world_has_its_size_and_nothing_on_any_layer(self):
        self.assertEqual(self.world.get_width(), WIDTH)
        self.assertEqual(self.world.get_height(), HEIGHT)
        for layer in LAYERS:
            self.assertEqual(self.every_value(world=self.world, layer=layer), [[NOTHING] * WIDTH] * HEIGHT)

    def test_a_size_that_is_not_a_whole_number_of_at_least_one_is_refused(self):
        for value in (0, -1, NOT_A_SIZE, None, 1.5, True):
            with self.subTest(value=value):
                self.assertEqual(self.refused(lambda: World(width=value, height=HEIGHT)), ERR_WORLD_SIZE.format(name=WIDTH_KEY, value=value))
                self.assertEqual(self.refused(lambda: World(width=WIDTH, height=value)), ERR_WORLD_SIZE.format(name=HEIGHT_KEY, value=value))

    def test_each_layer_holds_its_own_value_for_a_tile(self):
        self.world.set_value(layer=Layer.TERRAIN, x=2, y=1, value=A_TERRAIN)
        self.world.set_value(layer=Layer.UNIT, x=2, y=1, value=A_UNIT)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=2, y=1), A_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.UNIT, x=2, y=1), A_UNIT)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=3, y=1), NOTHING)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=2, y=2), NOTHING)

    def test_the_world_wraps_from_east_to_west(self):
        self.world.set_value(layer=Layer.TERRAIN, x=0, y=1, value=A_TERRAIN)
        self.world.set_value(layer=Layer.TERRAIN, x=WIDTH - 1, y=1, value=ANOTHER_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=WIDTH * ONE_AROUND, y=1), A_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=WIDTH * TWICE_AROUND, y=1), A_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=-1, y=1), ANOTHER_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=-1 - WIDTH, y=1), ANOTHER_TERRAIN)
        self.world.set_value(layer=Layer.TERRAIN, x=WIDTH + 2, y=1, value=A_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=2, y=1), A_TERRAIN)
        self.assertEqual(self.world.column(WIDTH + 2), 2)
        self.assertEqual(self.world.column(-1), WIDTH - 1)

    def test_two_columns_are_as_far_apart_as_the_shorter_way_around_the_world(self):
        for first, second, apart in COLUMNS_APART:
            with self.subTest(first=first, second=second):
                self.assertEqual(self.world.columns_apart(first=first, second=second), apart)
                self.assertEqual(self.world.columns_apart(first=second, second=first), apart)

    def test_the_world_does_not_wrap_from_north_to_south(self):
        for y in (-1, HEIGHT, HEIGHT * TWICE_AROUND, None, 1.0):
            with self.subTest(y=y):
                expected = ERR_ROW_OFF_THE_MAP.format(last=HEIGHT - 1, value=y)
                self.assertEqual(self.refused(lambda: self.world.get_value(layer=Layer.TERRAIN, x=0, y=y)), expected)
                self.assertEqual(self.refused(lambda: self.world.set_value(layer=Layer.TERRAIN, x=0, y=y, value=A_TERRAIN)), expected)
        self.assertEqual(self.world.row(HEIGHT - 1), HEIGHT - 1)

    def test_a_layer_the_world_does_not_have_is_refused(self):
        for layer in (a_layer_nobody_has(), NOTHING, NOT_A_LAYER, None):
            with self.subTest(layer=layer):
                expected = ERR_NO_SUCH_LAYER.format(layer=layer)
                self.assertEqual(self.refused(lambda: self.world.get_value(layer=layer, x=0, y=0)), expected)
                self.assertEqual(self.refused(lambda: self.world.set_value(layer=layer, x=0, y=0, value=A_TERRAIN)), expected)
                self.assertEqual(self.refused(lambda: self.world.fill(layer=layer, value=A_TERRAIN)), expected)

    def test_filling_a_layer_gives_every_tile_the_value_and_keeps_the_rows_apart(self):
        self.world.fill(layer=Layer.TERRAIN, value=A_TERRAIN)
        self.assertEqual(self.every_value(world=self.world, layer=Layer.TERRAIN), [[A_TERRAIN] * WIDTH] * HEIGHT)
        self.assertEqual(self.every_value(world=self.world, layer=Layer.UNIT), [[NOTHING] * WIDTH] * HEIGHT)
        self.world.set_value(layer=Layer.TERRAIN, x=0, y=0, value=ANOTHER_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=0, y=1), A_TERRAIN)

    def test_renumbering_a_layer_replaces_each_id_and_leaves_the_other_layers(self):
        self.world.fill(layer=Layer.TERRAIN, value=A_TERRAIN)
        self.world.set_value(layer=Layer.TERRAIN, x=1, y=1, value=ANOTHER_TERRAIN)
        self.world.set_value(layer=Layer.UNIT, x=1, y=1, value=A_TERRAIN)
        self.world.renumber(layer=Layer.TERRAIN, numbers={A_TERRAIN: ANOTHER_TERRAIN, ANOTHER_TERRAIN: A_TERRAIN})
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=1, y=1), A_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.TERRAIN, x=0, y=0), ANOTHER_TERRAIN)
        self.assertEqual(self.world.get_value(layer=Layer.UNIT, x=1, y=1), A_TERRAIN)
        numbers = {ANOTHER_TERRAIN: A_TERRAIN}
        self.assertEqual(self.refused(lambda: self.world.renumber(layer=Layer.TERRAIN, numbers=numbers)), ERR_UNKNOWN_ID.format(known=sorted(numbers)))

    def test_a_world_comes_back_from_a_saved_game_as_it_was(self):
        self.world.fill(layer=Layer.TERRAIN, value=A_TERRAIN)
        self.world.set_value(layer=Layer.TERRAIN, x=WIDTH - 1, y=HEIGHT - 1, value=ANOTHER_TERRAIN)
        self.world.set_value(layer=Layer.UNIT, x=0, y=HEIGHT - 1, value=A_UNIT)
        loaded = World.from_data(through_json(self.world.to_data()))
        self.assertEqual(loaded.get_width(), WIDTH)
        self.assertEqual(loaded.get_height(), HEIGHT)
        for layer in LAYERS:
            self.assertEqual(self.every_value(world=loaded, layer=layer), self.every_value(world=self.world, layer=layer))

    def test_a_saved_game_calls_each_layer_by_its_number(self):
        data = through_json(self.world.to_data())
        self.assertEqual(set(data[LAYERS_KEY]), {str(layer) for layer in LAYERS})

    def test_a_layer_the_saved_game_lacks_has_nothing_on_every_tile(self):
        self.world.fill(layer=Layer.TERRAIN, value=A_TERRAIN)
        self.world.fill(layer=Layer.UNIT, value=A_UNIT)
        data = through_json(self.world.to_data())
        del data[LAYERS_KEY][str(Layer.UNIT)]
        loaded = World.from_data(data)
        self.assertEqual(self.every_value(world=loaded, layer=Layer.UNIT), [[NOTHING] * WIDTH] * HEIGHT)
        self.assertEqual(self.every_value(world=loaded, layer=Layer.TERRAIN), [[A_TERRAIN] * WIDTH] * HEIGHT)

    def test_a_layer_this_version_does_not_have_is_left_behind(self):
        self.world.fill(layer=Layer.TERRAIN, value=A_TERRAIN)
        data = through_json(self.world.to_data())
        data[LAYERS_KEY][str(a_layer_nobody_has())] = [[A_UNIT] * WIDTH] * HEIGHT
        loaded = World.from_data(data)
        self.assertEqual(set(through_json(loaded.to_data())[LAYERS_KEY]), {str(layer) for layer in LAYERS})
        self.assertEqual(self.every_value(world=loaded, layer=Layer.TERRAIN), [[A_TERRAIN] * WIDTH] * HEIGHT)

    def test_a_saved_layer_of_the_wrong_shape_is_refused(self):
        expected = ERR_LAYER_SHAPE.format(layer=Layer.TERRAIN, height=HEIGHT, width=WIDTH)
        for rows in ([[NOTHING] * WIDTH] * (HEIGHT - 1), [[NOTHING] * (WIDTH + 1)] * HEIGHT, []):
            with self.subTest(rows=rows):
                data = through_json(self.world.to_data())
                data[LAYERS_KEY][str(Layer.TERRAIN)] = rows
                self.assertEqual(self.refused(lambda: World.from_data(data)), expected)

    def test_no_layer_number_is_used_twice_or_brought_back(self):
        self.assertEqual(len(set(LAYERS)), len(LAYERS))
        self.assertFalse(set(LAYERS) & set(RETIRED_LAYERS))
        self.assertNotIn(NOTHING, LAYERS + RETIRED_LAYERS)


if __name__ == '__main__':
    unittest.main()
