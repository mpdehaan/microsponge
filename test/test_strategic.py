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

"""Tests for strategic resources: where they are on the map, which a civilization has within its borders, and what requires one."""

import os
import tempfile
import unittest

from caveman_game import FLINT_TILE, THE_WORLD, end_rounds, found_village, game_facts, held, started_caveman_game, terrain_id
from later_caveman import later_caveman, later_theme
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.research import Research
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.building import Building
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.improvement import Improvement
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import StrategicResource
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.kinds.terrain import Terrain
from microsponge.engine.kinds.unit_kinds import LandUnit
from microsponge.engine.saving.saved_game import load_game, save_game
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_BUILD_REQUIRES, ERR_NOT_STRATEGIC, ERR_RESOURCE_NOT_ON
from microsponge.themes.caveman.resources import Currency, Food
from microsponge.themes.caveman.terrains import Grassland
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import CavemanUnit, Settler

FIRST_CIVILIZATION = 1
SECOND_CIVILIZATION = 2
A_NAME = 'Ugghome'
ANOTHER_NAME = 'Grokstead'
A_THIRD_NAME = 'Uggford'
A_FILE_NAME = 'strategic.json'
NOTHING_HELD = 0
ONE_CITIZEN = 1
# Tiles inside the city limits of the first civilization's first city, away from the city center, as (x, y).
INSIDE = (10, 7)
ALSO_INSIDE = (9, 17)
INSIDE_AND_GRASSLAND = (8, 7)
# A tile inside the city limits of the second civilization's first city.
INSIDE_THE_SECOND = (33, 7)
# A tile no city reaches.
OUTSIDE = (15, 2)
# Open grassland where the first civilization can build a second city.
A_SECOND_SITE = (20, 20)
# A tile inside the city limits of a city built on that site, away from the city center.
INSIDE_THE_SECOND_SITE = (20, 16)
TWO_KNAPPERS = 2


class Obsidian(StrategicResource):
    """A strategic resource that two terrains can have, which caveman does not have."""


class Amber(StrategicResource):
    """A strategic resource that only a bog can have."""


class Quarry(Terrain):
    CAN_HAVE = (Obsidian,)


class Bog(Terrain):
    CAN_HAVE = (Obsidian, Amber)


class Draining(Improvement):
    """Work that turns a bog into a quarry, which cannot have amber."""

    ON = (Bog,)
    BUILD_TURNS = 2
    BECOMES = Quarry


class Digger(CavemanUnit, LandUnit):
    BUILDS = (Draining,)


class FlintKnapper(CavemanUnit, LandUnit):
    REQUIRES = (Obsidian,)
    COST = {Currency: 10}
    BUILD_TURNS = 2


class AmberShrine(Building):
    REQUIRES = (Amber,)
    COST = {Currency: 10}


class Knapping(Technology):
    REQUIRES = (Obsidian,)
    RESEARCH = 5


STRATEGIC_CAVEMAN = later_caveman({
    Category.TERRAINS: (*Caveman.TERRAINS, Quarry, Bog),
    Category.RESOURCES: (*Caveman.RESOURCES, Obsidian, Amber),
    Category.TECHNOLOGIES: (*Caveman.TECHNOLOGIES, Knapping),
    Category.UNITS: (*Caveman.UNITS, Digger, FlintKnapper),
    Category.BUILDINGS: (*Caveman.BUILDINGS, AmberShrine),
    Category.IMPROVEMENTS: (*Caveman.IMPROVEMENTS, Draining),
})
REORDERED_STRATEGIC_CAVEMAN = later_theme(theme=STRATEGIC_CAVEMAN, changes={Category.RESOURCES: tuple(reversed(STRATEGIC_CAVEMAN.RESOURCES))})
BOGS = (INSIDE, ALSO_INSIDE, INSIDE_THE_SECOND, OUTSIDE)


class StrategicCase(Refusals, unittest.TestCase):
    """A started game of a caveman with obsidian and amber, with a few tiles of bog, in which the first civilization builds its city first.

    Caveman's own flint is taken off the test world, so that these tests see only the
    resources they put on.
    """

    def setUp(self):
        self.game = started_caveman_game(theme=STRATEGIC_CAVEMAN)
        self.world = self.game.get_world(THE_WORLD)
        x, y = FLINT_TILE
        Strategic.remove(game=self.game, world=THE_WORLD, x=x, y=y)
        for tile in BOGS:
            self.set_terrain(tile=tile, terrain=Bog)

    def set_terrain(self, *, tile, terrain):
        x, y = tile
        self.world.set_value(layer=Layer.TERRAIN, x=x, y=y, value=terrain_id(game=self.game, terrain=terrain))

    def put(self, *, resource, tile):
        x, y = tile
        Strategic.place(game=self.game, world=THE_WORLD, x=x, y=y, resource=resource)

    def at(self, tile):
        x, y = tile
        return Strategic.resource_at(game=self.game, world=THE_WORLD, x=x, y=y)

    def has(self, civilization):
        return Strategic.held(game=self.game, civilization=civilization)

    def cities(self):
        """Build the first city of each civilization, the first civilization's first, and return their ids."""
        first = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        second = found_village(game=self.game, civilization=SECOND_CIVILIZATION, name=ANOTHER_NAME)
        return first, second


class TestWhereStrategicResourcesAre(StrategicCase):

    def test_a_strategic_resource_is_put_on_a_tile_of_a_terrain_that_can_have_it(self):
        self.assertIsNone(self.at(INSIDE))
        self.put(resource=Amber, tile=INSIDE)
        self.assertIs(self.at(INSIDE), Amber)
        self.assertIsNone(self.at(ALSO_INSIDE))

    def test_a_strategic_resource_can_be_on_more_than_one_terrain(self):
        self.set_terrain(tile=ALSO_INSIDE, terrain=Quarry)
        self.put(resource=Obsidian, tile=INSIDE)
        self.put(resource=Obsidian, tile=ALSO_INSIDE)
        self.assertEqual((self.at(INSIDE), self.at(ALSO_INSIDE)), (Obsidian, Obsidian))

    def test_a_strategic_resource_is_refused_on_a_terrain_that_cannot_have_it(self):
        self.set_terrain(tile=ALSO_INSIDE, terrain=Quarry)
        refused = self.refused(lambda: self.put(resource=Amber, tile=ALSO_INSIDE))
        self.assertEqual(refused, ERR_RESOURCE_NOT_ON.format(resource=shown_name(Amber), terrain=shown_name(Quarry)))
        refused = self.refused(lambda: self.put(resource=Obsidian, tile=INSIDE_AND_GRASSLAND))
        self.assertEqual(refused, ERR_RESOURCE_NOT_ON.format(resource=shown_name(Obsidian), terrain=shown_name(Grassland)))
        self.assertEqual((self.at(ALSO_INSIDE), self.at(INSIDE_AND_GRASSLAND)), (None, None))

    def test_a_collected_resource_is_never_on_a_tile_as_a_strategic_resource(self):
        refused = self.refused(lambda: self.put(resource=Food, tile=INSIDE))
        self.assertEqual(refused, ERR_NOT_STRATEGIC.format(resource=shown_name(Food)))
        self.assertIsNone(self.at(INSIDE))

    def test_a_tile_has_one_strategic_resource_and_one_can_be_taken_off(self):
        x, y = INSIDE
        self.put(resource=Obsidian, tile=INSIDE)
        self.put(resource=Amber, tile=INSIDE)
        self.assertIs(self.at(INSIDE), Amber)
        Strategic.remove(game=self.game, world=THE_WORLD, x=x, y=y)
        self.assertIsNone(self.at(INSIDE))


class TestBorders(StrategicCase):

    def test_a_civilization_has_a_resource_within_the_city_limits_of_its_city_though_no_citizen_works_the_tile(self):
        self.put(resource=Obsidian, tile=INSIDE)
        self.assertEqual(self.has(FIRST_CIVILIZATION), [])
        first, _ = self.cities()
        self.assertEqual(self.game.get_city(first).get_citizens(), ONE_CITIZEN)
        worked = [(tile.x, tile.y) for tile in Harvest.assignments(game=self.game, city=first)]
        self.assertNotIn(INSIDE, worked)
        self.assertEqual(self.has(FIRST_CIVILIZATION), [Obsidian])
        self.assertEqual(self.has(SECOND_CIVILIZATION), [])
        self.assertEqual(Strategic.of_city(game=self.game, city=first), [Obsidian])

    def test_a_resource_outside_every_city_limit_is_nobodys(self):
        self.put(resource=Obsidian, tile=OUTSIDE)
        self.cities()
        self.assertEqual((self.has(FIRST_CIVILIZATION), self.has(SECOND_CIVILIZATION)), ([], []))

    def test_each_civilization_has_what_is_within_its_own_city_limits(self):
        self.put(resource=Obsidian, tile=INSIDE)
        self.put(resource=Amber, tile=INSIDE_THE_SECOND)
        self.cities()
        self.assertEqual((self.has(FIRST_CIVILIZATION), self.has(SECOND_CIVILIZATION)), ([Obsidian], [Amber]))

    def test_a_resource_counts_once_however_many_tiles_have_it(self):
        self.put(resource=Obsidian, tile=INSIDE)
        self.put(resource=Obsidian, tile=ALSO_INSIDE)
        self.cities()
        self.assertEqual(self.has(FIRST_CIVILIZATION), [Obsidian])

    def test_the_resources_of_every_city_of_a_civilization_are_the_civilizations(self):
        self.put(resource=Obsidian, tile=INSIDE)
        self.set_terrain(tile=INSIDE_THE_SECOND_SITE, terrain=Bog)
        self.put(resource=Amber, tile=INSIDE_THE_SECOND_SITE)
        self.cities()
        x, y = A_SECOND_SITE
        settler = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        CityControl.found(game=self.game, settler=settler, name=A_THIRD_NAME)
        self.assertEqual(self.has(FIRST_CIVILIZATION), [Obsidian, Amber])


class TestRequiringAStrategicResource(StrategicCase):

    def setUp(self):
        super().setUp()
        self.city, self.other = self.cities()

    def test_a_unit_that_requires_a_strategic_resource_is_built_only_with_the_resource_within_the_borders(self):
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(FlintKnapper), required=shown_name(Obsidian))
        self.assertEqual(self.refused(lambda: Orders.build(game=self.game, city=self.city, kind=FlintKnapper)), expected)
        self.put(resource=Obsidian, tile=INSIDE)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=self.city, kind=FlintKnapper))
        self.assertEqual(Production.problem_queueing(game=self.game, city=self.other, kind=FlintKnapper), expected)

    def test_one_tile_of_a_strategic_resource_builds_any_number_of_units_and_is_not_used_up(self):
        self.put(resource=Obsidian, tile=INSIDE)
        for _ in range(TWO_KNAPPERS):
            Orders.build(game=self.game, city=self.city, kind=FlintKnapper)
        end_rounds(game=self.game, rounds=FlintKnapper.BUILD_TURNS * TWO_KNAPPERS)
        kinds = [UnitControl.kind_of(game=self.game, unit=unit) for unit in self.game.get_city(self.city).get_units()]
        self.assertEqual(kinds, [FlintKnapper] * TWO_KNAPPERS)
        self.assertIs(self.at(INSIDE), Obsidian)
        self.assertEqual(self.has(FIRST_CIVILIZATION), [Obsidian])
        self.assertEqual(held(game=self.game, civilization=FIRST_CIVILIZATION, resource=Obsidian), NOTHING_HELD)

    def test_every_city_of_a_civilization_builds_with_a_resource_in_the_city_limits_of_one_of_them(self):
        self.put(resource=Obsidian, tile=INSIDE)
        x, y = A_SECOND_SITE
        settler = UnitControl.place(game=self.game, kind=Settler, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        far_city = CityControl.found(game=self.game, settler=settler, name=A_THIRD_NAME)
        self.assertEqual(Strategic.of_city(game=self.game, city=far_city), [])
        self.assertIsNone(Production.problem_queueing(game=self.game, city=far_city, kind=FlintKnapper))

    def test_a_building_can_require_a_strategic_resource(self):
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(AmberShrine), required=shown_name(Amber))
        self.assertEqual(Production.problem_queueing(game=self.game, city=self.city, kind=AmberShrine), expected)
        self.put(resource=Amber, tile=INSIDE)
        self.assertIsNone(Production.problem_queueing(game=self.game, city=self.city, kind=AmberShrine))

    def test_a_technology_can_require_a_strategic_resource(self):
        self.assertNotIn(Knapping, Research.available(game=self.game, civilization=FIRST_CIVILIZATION))
        self.put(resource=Obsidian, tile=INSIDE)
        self.assertIn(Knapping, Research.available(game=self.game, civilization=FIRST_CIVILIZATION))
        self.assertNotIn(Knapping, Research.available(game=self.game, civilization=SECOND_CIVILIZATION))


class TestChangingTheTerrainUnderAResource(StrategicCase):

    def setUp(self):
        super().setUp()
        self.city, _ = self.cities()

    def drain(self, tile):
        """Have a digger of the first civilization turn a tile of bog into a quarry."""
        x, y = tile
        digger = UnitControl.place(game=self.game, kind=Digger, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x, y=y)
        Orders.build_improvement(game=self.game, unit=digger, improvement=Draining)
        end_rounds(game=self.game, rounds=Draining.BUILD_TURNS)
        self.assertIs(self.game.get_terrain(world=THE_WORLD, x=x, y=y), Quarry)

    def test_a_resource_goes_away_for_good_when_its_tile_becomes_a_terrain_that_cannot_have_it(self):
        self.put(resource=Amber, tile=INSIDE)
        self.assertEqual(self.has(FIRST_CIVILIZATION), [Amber])
        self.drain(INSIDE)
        self.assertIsNone(self.at(INSIDE))
        self.assertEqual(self.has(FIRST_CIVILIZATION), [])
        expected = ERR_BUILD_REQUIRES.format(kind=shown_name(AmberShrine), required=shown_name(Amber))
        self.assertEqual(Production.problem_queueing(game=self.game, city=self.city, kind=AmberShrine), expected)

    def test_a_resource_stays_when_its_tile_becomes_a_terrain_that_can_have_it(self):
        self.put(resource=Obsidian, tile=INSIDE)
        self.drain(INSIDE)
        self.assertIs(self.at(INSIDE), Obsidian)
        self.assertEqual(self.has(FIRST_CIVILIZATION), [Obsidian])

    def test_changing_the_terrain_of_a_tile_with_no_resource_changes_no_other_tile(self):
        self.put(resource=Amber, tile=ALSO_INSIDE)
        self.drain(INSIDE)
        self.assertIs(self.at(ALSO_INSIDE), Amber)


class TestSavingStrategicResources(StrategicCase):

    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, A_FILE_NAME)
        self.cities()
        self.put(resource=Obsidian, tile=INSIDE)
        self.put(resource=Amber, tile=OUTSIDE)

    def test_the_strategic_resources_on_the_map_come_back_from_a_saved_game(self):
        save_game(game=self.game, path=self.path)
        loaded = load_game(path=self.path, themes=(STRATEGIC_CAVEMAN,))
        self.assertEqual(game_facts(loaded), game_facts(self.game))
        self.assertEqual(Strategic.held(game=loaded, civilization=FIRST_CIVILIZATION), [Obsidian])

    def test_they_come_back_in_a_later_theme_whose_resources_have_other_ids(self):
        save_game(game=self.game, path=self.path)
        loaded = load_game(path=self.path, themes=(REORDERED_STRATEGIC_CAVEMAN,))
        x, y = INSIDE
        self.assertIs(Strategic.resource_at(game=loaded, world=THE_WORLD, x=x, y=y), Obsidian)
        x, y = OUTSIDE
        self.assertIs(Strategic.resource_at(game=loaded, world=THE_WORLD, x=x, y=y), Amber)
        self.assertNotEqual(
            loaded.get_world(THE_WORLD).get_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y),
            self.world.get_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y),
        )
        self.assertEqual(game_facts(loaded), game_facts(self.game))

