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

"""The themes: every theme can be numbered, and each holds what the user has said it holds."""

import unittest

from microsponge.engine.kinds.bonuses import FREE, WHOLE, harvest_percent, unit_support_percent
from microsponge.engine.kinds.building import Building, Wonder
from microsponge.engine.kinds.catalog import Catalog
from microsponge.engine.kinds.category import CATEGORIES, Category
from microsponge.engine.kinds.city_spec import CitySpec
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.improvement import Improvement
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import Resource, StrategicResource
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.kinds.terrain import Terrain
from microsponge.engine.kinds.terrain_bonus import TerrainBonus
from microsponge.engine.kinds.theme import LEAST_COST, Theme, underpriced
from microsponge.engine.kinds.unit_kinds import SettlerUnit, UnitKind, can_hit
from microsponge.themes import THEMES
from microsponge.themes.caveman import buildings as caveman_buildings
from microsponge.themes.caveman import city as caveman_city
from microsponge.themes.caveman import improvements as caveman_improvements
from microsponge.themes.caveman import resources as caveman_resources
from microsponge.themes.caveman import technologies as caveman_technologies
from microsponge.themes.caveman import terrain_bonuses as caveman_terrain_bonuses
from microsponge.themes.caveman import terrains as caveman_terrains
from microsponge.themes.caveman import units as caveman_units
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.classic import buildings as classic_buildings
from microsponge.themes.classic import improvements as classic_improvements
from microsponge.themes.classic import resources as classic_resources
from microsponge.themes.classic import technologies as classic_technologies
from microsponge.themes.classic import terrain_bonuses as classic_terrain_bonuses
from microsponge.themes.classic import terrains as classic_terrains
from microsponge.themes.classic import units as classic_units
from microsponge.themes.classic.theme import Classic
from microsponge.themes.fantasy import technologies as fantasy_technologies
from microsponge.themes.fantasy import units as fantasy_units
from microsponge.themes.fantasy.theme import Fantasy
from microsponge.themes.scifi import buildings as scifi_buildings
from microsponge.themes.scifi import units as scifi_units
from microsponge.themes.planetwars import units as planetwars_units
from microsponge.themes.planetwars.theme import PlanetWars
from microsponge.themes.scifi.theme import SciFi
from microsponge.ui_strings import MSG_CITIES, MSG_CITY

# The base every kind of a category is built on.
BASES = {
    Category.TERRAINS: Terrain,
    Category.RESOURCES: Resource,
    Category.TECHNOLOGIES: Technology,
    Category.UNITS: UnitKind,
    Category.BUILDINGS: Building,
    Category.IMPROVEMENTS: Improvement,
    Category.TERRAIN_BONUSES: TerrainBonus,
}


class Ploughing(Technology):
    """A second technology that speeds up the harvest of food, to add to agriculture's."""

    HARVEST_BONUS = {caveman_resources.Food: 5}


class Feasting(Technology):
    """A technology that takes most of the cost off supporting units, so that two of it would take off more than all."""

    UNIT_SUPPORT_BONUS = 75


class Bargain(caveman_units.CavemanUnit):
    """A unit that costs less currency than every unit must."""

    COST = {caveman_resources.Currency: 9}


class FoodOnly(Building):
    """A building that costs no currency at all."""

    COST = {caveman_resources.Food: 100}


class CheapCaveman(Caveman):
    """Caveman with a unit and a building that cost too little."""

    UNITS = (*Caveman.UNITS, Bargain)
    BUILDINGS = (*Caveman.BUILDINGS, FoodOnly)


class LaterPlatform(classic_units.AntiAirPlatform):
    """A kind built on one that names itself, which goes by its own class name again."""


LATER_PLATFORM = 'later platform'
ONE_WORLD = 1
GRANARY_FOOD = 1
GRANARY_TURNS_SOONER = 1
WATCHTOWER_DEFENSE_BONUS = 25
SIEGE_DEFENSE = 1
SIEGE_HIT_POINTS = 1
SIEGE_STEP = 3
EVERY_COST_BASE = 1
VILLAGE = 'village'
VILLAGES = 'villages'
ANTI_MISSILE_PLATFORM = 'anti-missile platform'
ANTI_AIR_PLATFORM = 'anti-air platform'
FIGHTER_PLANE = 'fighter plane'
SCIFI = 'SciFi'
PLANETWARS = 'PlanetWars'
THE_LEAST_COST = 10
TWICE = 2
CAPTAIN_CAVEMAN = 'captain caveman'
SLINGSHOT_CAVEMAN = 'slingshot caveman'
ANGRY_BIRD = 'angry bird'
NO_ATTACK = 0
# Caveman has land units, one sea unit and one air unit.
CAVEMAN_DOMAINS = (Domain.LAND, Domain.SEA, Domain.AIR)
MOST_CITIZENS = 10
GROWTH_TURNS = (5, 10)
BANK_INCOME_BONUS = 20
BANKRUPTCY_HARVEST_PENALTY = 50
BANKRUPTCY_TURNS = 50
COST = 'COST'
# What the model says of hit points: about 10 for the weakest unit, and up to 500.
WEAKEST_HIT_POINTS = 10
MOST_HIT_POINTS = 500
# What the model says of every city.
CENTER_SIZE = 5
RADIUS_SIZE = 15
MOST_UNITS_IN_A_CITY = 3
CITY_DISBAND_PERCENT = 10
UNIT_DISBAND_PERCENT = 20
MOST_PLANETS = 50


class TestEveryTheme(unittest.TestCase):

    def test_the_themes_are_caveman_classic_scifi_fantasy_and_planetwars(self):
        self.assertEqual(THEMES, (Caveman, Classic, SciFi, Fantasy, PlanetWars))
        self.assertEqual((shown_name(SciFi), shown_name(PlanetWars)), (SCIFI, PLANETWARS))

    def test_every_theme_can_be_numbered(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertTrue(issubclass(theme, Theme))
                self.assertIs(Catalog(theme).get_theme(), theme)

    def test_every_kind_is_built_on_the_base_of_its_category(self):
        self.assertEqual(set(BASES), set(CATEGORIES))
        for theme in THEMES:
            for category in CATEGORIES:
                for kind in getattr(theme, category):
                    with self.subTest(theme=theme, kind=kind):
                        self.assertTrue(issubclass(kind, BASES[category]))

    def test_every_theme_says_the_fewest_and_the_most_worlds_a_game_has(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertLessEqual(ONE_WORLD, theme.MIN_WORLDS)
                self.assertLessEqual(theme.MIN_WORLDS, theme.MAX_WORLDS)
        for theme in (Caveman, Classic):
            with self.subTest(theme=theme):
                self.assertEqual((theme.MIN_WORLDS, theme.MAX_WORLDS), (ONE_WORLD, ONE_WORLD))
        self.assertEqual((SciFi.MIN_WORLDS, SciFi.MAX_WORLDS), (ONE_WORLD, MOST_PLANETS))
        self.assertEqual((Fantasy.MIN_WORLDS, Fantasy.MAX_WORLDS), (ONE_WORLD, ONE_WORLD))
        self.assertEqual((PlanetWars.MIN_WORLDS, PlanetWars.MAX_WORLDS), (ONE_WORLD, MOST_PLANETS))

    def test_every_theme_has_a_city_spec_of_its_own_that_produces_its_own_resources(self):
        specs = [theme.CITY for theme in THEMES]
        self.assertEqual(len(set(specs)), len(THEMES))
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertTrue(issubclass(theme.CITY, CitySpec))
                self.assertIsNot(theme.CITY, CitySpec)
                self.assertLessEqual(set(theme.CITY.PRODUCES), set(theme.RESOURCES))

    def test_a_city_is_a_center_inside_a_radius_and_holds_a_few_units(self):
        self.assertEqual((CitySpec.CENTER_SIZE, CitySpec.RADIUS_SIZE, CitySpec.MOST_UNITS), (CENTER_SIZE, RADIUS_SIZE, MOST_UNITS_IN_A_CITY))
        self.assertEqual((CitySpec.DISBAND_PERCENT, CitySpec.UNIT_DISBAND_PERCENT), (CITY_DISBAND_PERCENT, UNIT_DISBAND_PERCENT))

    def test_moving_and_attacking_straight_and_diagonally_each_cost_a_base_of_one_for_now(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                bases = (theme.STRAIGHT_MOVE_COST_BASE, theme.DIAGONAL_MOVE_COST_BASE, theme.STRAIGHT_ATTACK_COST_BASE, theme.DIAGONAL_ATTACK_COST_BASE)
                self.assertEqual(bases, (EVERY_COST_BASE,) * len(bases))

    def test_every_theme_has_the_same_default_penalty_and_limit_for_bankruptcy(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertEqual((theme.BANKRUPTCY_HARVEST_PENALTY, theme.BANKRUPTCY_TURNS), (BANKRUPTCY_HARVEST_PENALTY, BANKRUPTCY_TURNS))

    def test_the_primary_resource_of_a_theme_is_one_of_its_resources(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                if theme.RESOURCES:
                    self.assertIn(theme.PRIMARY_RESOURCE, theme.RESOURCES)
                else:
                    self.assertIsNone(theme.PRIMARY_RESOURCE)

    def test_what_a_kind_costs_holds_and_requires_is_in_its_own_theme(self):
        for theme in THEMES:
            strategic = {resource for resource in theme.RESOURCES if issubclass(resource, StrategicResource)}
            collected = set(theme.RESOURCES) - strategic
            known = set(theme.TECHNOLOGIES) | set(theme.BUILDINGS) | strategic
            for unit in theme.UNITS:
                with self.subTest(theme=theme, unit=unit):
                    self.assertLessEqual(set(unit.BUILDS), set(theme.IMPROVEMENTS))
            for improvement in theme.IMPROVEMENTS:
                with self.subTest(theme=theme, improvement=improvement):
                    self.assertLessEqual(set(improvement.ON), set(theme.TERRAINS))
                    self.assertLessEqual(set(improvement.TILE_BONUS), collected)
            for kind in theme.UNITS + theme.BUILDINGS + theme.TECHNOLOGIES + theme.IMPROVEMENTS:
                with self.subTest(theme=theme, kind=kind):
                    self.assertLessEqual(set(kind.REQUIRES), known)
            for kind in theme.UNITS + theme.BUILDINGS:
                with self.subTest(theme=theme, kind=kind):
                    self.assertLessEqual(set(kind.COST), collected)
                    self.assertLessEqual(set(kind.SUPPORT), collected)
            for technology in theme.TECHNOLOGIES:
                with self.subTest(theme=theme, technology=technology):
                    self.assertLessEqual(set(technology.HARVEST_BONUS), set(theme.RESOURCES))
                    self.assertTrue(FREE <= technology.UNIT_SUPPORT_BONUS <= WHOLE)
            for bonus in theme.TERRAIN_BONUSES:
                with self.subTest(theme=theme, bonus=bonus):
                    self.assertLessEqual(set(bonus.ON), set(theme.TERRAINS))
                    self.assertLessEqual(set(bonus.GIVES), collected)
            for terrain in theme.TERRAINS:
                with self.subTest(theme=theme, terrain=terrain):
                    self.assertLessEqual(set(terrain.GIVES), collected)
                    self.assertLessEqual(set(terrain.CAN_HAVE), strategic)


class TestCaveman(unittest.TestCase):

    def test_caveman_has_a_settler_a_warrior_a_worker_and_captain_caveman(self):
        units = caveman_units
        self.assertEqual(Caveman.UNITS, (units.Settler, units.Warrior, units.Worker, units.CaptainCaveman, units.SlingshotCaveman, units.Raft, units.AngryBird))

    def test_the_raft_is_a_weak_sea_unit_that_costs_wood_and_wood_comes_from_forest(self):
        raft = caveman_units.Raft
        self.assertEqual(raft.DOMAIN, Domain.SEA)
        self.assertIn(caveman_resources.Wood, raft.COST)
        self.assertEqual([terrain for terrain in Caveman.TERRAINS if caveman_resources.Wood in terrain.GIVES], [caveman_terrains.Forest])
        self.assertTrue(NO_ATTACK < raft.ATTACK < caveman_units.Warrior.ATTACK)

    def test_the_raft_requires_a_harbor_and_only_the_harbor_requires_water_next_to_the_city_center(self):
        self.assertEqual(caveman_units.Raft.REQUIRES, (caveman_buildings.Harbor,))
        self.assertEqual([building for building in Caveman.BUILDINGS if building.BESIDE_WATER], [caveman_buildings.Harbor])
        self.assertFalse(Building.BESIDE_WATER)

    def test_the_raft_can_hit_units_on_water_and_on_land_and_no_unit_in_the_air(self):
        raft = caveman_units.Raft
        for target in (raft, caveman_units.Warrior, caveman_units.Settler):
            with self.subTest(target=target):
                self.assertTrue(can_hit(kind=raft, target=target))
        self.assertFalse(can_hit(kind=raft, target=caveman_units.AngryBird))
        self.assertTrue(can_hit(kind=caveman_units.Warrior, target=raft))

    def test_the_angry_bird_is_a_weak_air_unit_and_no_unit_is_cheaper_or_sooner_built(self):
        bird = caveman_units.AngryBird
        self.assertEqual(bird.DOMAIN, Domain.AIR)
        self.assertEqual(shown_name(bird), ANGRY_BIRD)
        self.assertTrue(NO_ATTACK < bird.ATTACK < caveman_units.Warrior.ATTACK)
        self.assertEqual(bird.COST, {caveman_resources.Currency: min(unit.COST[caveman_resources.Currency] for unit in Caveman.UNITS)})
        self.assertEqual(bird.BUILD_TURNS, min(unit.BUILD_TURNS for unit in Caveman.UNITS))

    def test_the_angry_bird_is_the_unit_that_cannot_take_a_city(self):
        self.assertEqual([unit for unit in Caveman.UNITS if not unit.TAKES_CITIES], [caveman_units.AngryBird])
        self.assertTrue(UnitKind.TAKES_CITIES)

    def test_slingshot_caveman_is_the_land_unit_that_can_hit_air_and_is_strong_against_air_and_weak_against_land(self):
        slingshot = caveman_units.SlingshotCaveman
        self.assertEqual([unit for unit in Caveman.UNITS if unit.DOMAIN == Domain.LAND and unit.CAN_HIT_AIR], [slingshot])
        self.assertTrue(slingshot.ATTACK < caveman_units.Warrior.ATTACK < slingshot.AIR_ATTACK)
        self.assertEqual([unit for unit in Caveman.UNITS if unit.AIR_ATTACK is not None], [slingshot])
        self.assertEqual(shown_name(slingshot), SLINGSHOT_CAVEMAN)

    def test_captain_caveman_is_twice_the_warrior_and_requires_the_barracks_which_requires_discipline(self):
        captain = caveman_units.CaptainCaveman
        warrior = caveman_units.Warrior
        self.assertEqual(captain.ATTACK, warrior.ATTACK * TWICE)
        self.assertEqual(captain.HIT_POINTS, warrior.HIT_POINTS * TWICE)
        self.assertEqual(captain.COST[caveman_resources.Currency], warrior.COST[caveman_resources.Currency] * TWICE)
        self.assertEqual(captain.REQUIRES, (caveman_buildings.Barracks,))
        self.assertEqual(caveman_buildings.Barracks.REQUIRES, (caveman_technologies.Discipline,))
        self.assertIn(caveman_buildings.Barracks, Caveman.BUILDINGS)
        self.assertEqual(shown_name(captain), CAPTAIN_CAVEMAN)

    def test_a_caveman_city_is_called_a_village_and_the_other_themes_say_city(self):
        self.assertEqual((Caveman.CITY.NAME, Caveman.CITY.NAMES), (VILLAGE, VILLAGES))
        for theme in (Classic, SciFi, Fantasy, PlanetWars):
            self.assertEqual((theme.CITY.NAME, theme.CITY.NAMES), (MSG_CITY, MSG_CITIES))

    def test_the_worker_builds_the_farm_on_grassland_once_agriculture_is_known_and_the_settler_builds_no_improvement(self):
        farm = caveman_improvements.Farm
        clearing = caveman_improvements.Clearing
        self.assertEqual(Caveman.IMPROVEMENTS, (farm, clearing))
        self.assertEqual(caveman_units.Worker.BUILDS, (farm, clearing))
        self.assertEqual((clearing.ON, clearing.BECOMES), ((caveman_terrains.Forest,), caveman_terrains.Grassland))
        self.assertIsNone(farm.BECOMES)
        self.assertEqual(caveman_units.Settler.BUILDS, ())
        self.assertEqual(caveman_units.Warrior.BUILDS, ())
        self.assertEqual(farm.REQUIRES, (caveman_technologies.Agriculture,))
        self.assertEqual(caveman_units.Worker.REQUIRES, farm.REQUIRES)
        self.assertEqual(farm.ON, (caveman_terrains.Grassland,))
        self.assertGreater(farm.TILE_BONUS[caveman_resources.Food], 0)
        self.assertGreater(farm.BUILD_TURNS, 0)
        self.assertEqual(farm.COST if hasattr(farm, COST) else {}, {})

    def test_the_settler_costs_currency_time_and_a_citizen_and_needs_no_technology(self):
        settler = caveman_units.Settler
        self.assertTrue(issubclass(settler, SettlerUnit))
        self.assertEqual(settler.REQUIRES, ())
        self.assertGreaterEqual(settler.COST[caveman_resources.Currency], LEAST_COST)
        self.assertEqual(settler.CITIZENS, 1)
        self.assertGreater(settler.BUILD_TURNS, 0)
        self.assertEqual(caveman_units.Warrior.CITIZENS, 0)

    def test_a_caveman_city_produces_food_and_its_working_citizens_generate_currency(self):
        self.assertIs(Caveman.CITY, caveman_city.Village)
        self.assertGreater(Caveman.CITY.PRODUCES[caveman_resources.Food], 0)
        self.assertGreater(Caveman.CITY.CITIZEN_CURRENCY, 0)
        self.assertIs(Caveman.FOOD, caveman_resources.Food)
        self.assertGreater(Caveman.STARTS_WITH[caveman_resources.Currency], 0)

    def test_each_citizen_eats_food_in_every_theme(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertGreater(theme.CITY.CITIZEN_FOOD, 0)

    def test_a_city_grows_to_10_citizens_at_most_after_5_turns_and_then_10(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertEqual(theme.CITY.MAX_CITIZENS, MOST_CITIZENS)
                self.assertEqual(theme.CITY.GROWTH_TURNS, GROWTH_TURNS)

    def test_the_bank_of_classic_adds_20_percent_to_the_income_of_its_city(self):
        self.assertIn(classic_buildings.Bank, Classic.BUILDINGS)
        self.assertEqual(classic_buildings.Bank.INCOME_BONUS, BANK_INCOME_BONUS)

    def test_every_caveman_unit_and_building_costs_at_least_10_currency(self):
        self.assertEqual(LEAST_COST, THE_LEAST_COST)
        self.assertIs(Caveman.PRIMARY_RESOURCE, caveman_resources.Currency)
        self.assertEqual(underpriced(Caveman), [])

    def test_every_caveman_unit_is_supported_with_currency_and_food_and_every_building_with_currency(self):
        for unit in Caveman.UNITS:
            with self.subTest(unit=unit):
                self.assertEqual(set(unit.SUPPORT), {caveman_resources.Currency, caveman_resources.Food})
        for building in Caveman.BUILDINGS:
            with self.subTest(building=building):
                self.assertEqual(set(building.SUPPORT), {caveman_resources.Currency})

    def test_a_unit_or_building_that_costs_less_than_10_currency_is_found(self):
        self.assertEqual(underpriced(CheapCaveman), [Bargain, FoodOnly])

    def test_every_caveman_unit_defines_its_attack_defense_and_hit_points_and_heals_faster_in_a_city(self):
        for unit in Caveman.UNITS:
            with self.subTest(unit=unit):
                self.assertTrue(issubclass(unit, caveman_units.CavemanUnit))
                self.assertTrue(WEAKEST_HIT_POINTS <= unit.HIT_POINTS <= MOST_HIT_POINTS)
                self.assertTrue(unit.STRIKES_BACK)
                self.assertIn(unit.DOMAIN, CAVEMAN_DOMAINS)
                self.assertGreaterEqual(unit.ATTACK, 0)
                self.assertGreaterEqual(unit.DEFENSE, 0)
                self.assertEqual((unit.HEAL, unit.CITY_HEAL), (caveman_units.CavemanUnit.HEAL, caveman_units.CavemanUnit.CITY_HEAL))
        self.assertGreater(caveman_units.CavemanUnit.HEAL, 0)
        self.assertGreater(caveman_units.CavemanUnit.CITY_HEAL, caveman_units.CavemanUnit.HEAL)
        self.assertGreater(caveman_units.Warrior.ATTACK, caveman_units.Settler.ATTACK)

    def test_every_caveman_unit_and_building_costs_something_to_support(self):
        for kind in Caveman.UNITS + Caveman.BUILDINGS:
            with self.subTest(kind=kind):
                self.assertTrue(kind.SUPPORT)
                self.assertTrue(all(amount > 0 for amount in kind.SUPPORT.values()))

    def test_harvest_bonuses_are_percentages_that_add_up(self):
        technologies = caveman_technologies
        food = caveman_resources.Food
        stone = caveman_resources.Stone
        self.assertEqual(harvest_percent(technologies=(), resource=food), WHOLE)
        self.assertEqual(harvest_percent(technologies=(technologies.Clubs,), resource=food), WHOLE)
        self.assertEqual(harvest_percent(technologies=(technologies.Agriculture,), resource=food), WHOLE + technologies.Agriculture.HARVEST_BONUS[food])
        self.assertEqual(harvest_percent(technologies=(technologies.Agriculture,), resource=stone), WHOLE)
        self.assertEqual(harvest_percent(technologies=(technologies.Agriculture, Ploughing), resource=food), WHOLE + technologies.Agriculture.HARVEST_BONUS[food] + Ploughing.HARVEST_BONUS[food])
        self.assertGreater(technologies.Agriculture.HARVEST_BONUS[food], 0)

    def test_support_bonuses_add_up_and_make_units_cheaper_but_never_less_than_free(self):
        technologies = caveman_technologies
        self.assertEqual(unit_support_percent(()), WHOLE)
        self.assertEqual(unit_support_percent((technologies.Agriculture,)), WHOLE)
        self.assertEqual(unit_support_percent((technologies.Clubs,)), WHOLE - technologies.Clubs.UNIT_SUPPORT_BONUS)
        both = technologies.Clubs.UNIT_SUPPORT_BONUS + Feasting.UNIT_SUPPORT_BONUS
        self.assertEqual(unit_support_percent((technologies.Clubs, Feasting)), WHOLE - both)
        self.assertGreater(both, technologies.Clubs.UNIT_SUPPORT_BONUS)
        self.assertEqual(unit_support_percent((Feasting, Feasting)), FREE)

    def test_a_technology_allows_the_warrior(self):
        self.assertEqual(caveman_units.Warrior.REQUIRES, (caveman_technologies.Clubs,))
        self.assertIn(caveman_technologies.Clubs, Caveman.TECHNOLOGIES)

    def test_the_granary_requires_agriculture_feeds_the_city_from_grassland_and_grows_it_sooner(self):
        granary = caveman_buildings.Granary
        self.assertIn(granary, Caveman.BUILDINGS)
        self.assertIn(caveman_technologies.Agriculture, Caveman.TECHNOLOGIES)
        self.assertEqual(granary.REQUIRES, (caveman_technologies.Agriculture,))
        self.assertEqual(granary.WORKED_TILE_BONUS, {caveman_terrains.Grassland: {caveman_resources.Food: GRANARY_FOOD}})
        self.assertEqual(granary.GROWS_SOONER, GRANARY_TURNS_SOONER)
        self.assertFalse(issubclass(granary, Wonder))

    def test_caveman_has_clubs_agriculture_discipline_and_fire_and_none_requires_anything(self):
        technologies = caveman_technologies
        self.assertEqual(Caveman.TECHNOLOGIES, (technologies.Clubs, technologies.Agriculture, technologies.Discipline, technologies.Fire))
        for technology in Caveman.TECHNOLOGIES:
            self.assertEqual(technology.REQUIRES, ())

    def test_stone_comes_from_mountains(self):
        giving_stone = [terrain for terrain in Caveman.TERRAINS if caveman_resources.Stone in terrain.GIVES]
        self.assertEqual(giving_stone, [caveman_terrains.Mountains])

    def test_the_tarpit_gives_nothing_and_no_land_unit_crosses_it_and_nothing_is_built_on_it(self):
        tarpit = caveman_terrains.Tarpit
        self.assertEqual(tarpit.GIVES, {})
        self.assertEqual([terrain for terrain in Caveman.TERRAINS if not terrain.CROSSED_BY_LAND_UNITS], [tarpit])
        self.assertEqual([terrain for terrain in Caveman.TERRAINS if not terrain.BUILDABLE], [tarpit])
        self.assertTrue(tarpit.LAND)
        for improvement in Caveman.IMPROVEMENTS:
            self.assertNotIn(tarpit, improvement.ON)

    def test_the_world_has_land_water_mountains_forest_and_tarpit(self):
        terrains = caveman_terrains
        self.assertEqual(Caveman.TERRAINS, (terrains.Grassland, terrains.Mountains, terrains.Water, terrains.Forest, terrains.Tarpit))
        self.assertTrue(caveman_terrains.Forest.LAND)
        self.assertTrue(caveman_terrains.Grassland.LAND)
        self.assertTrue(caveman_terrains.Mountains.LAND)
        self.assertFalse(caveman_terrains.Water.LAND)
        self.assertGreater(caveman_terrains.Mountains.MOVE_COST, caveman_terrains.Grassland.MOVE_COST)

    def test_the_world_wonders_are_the_great_cave_painting_and_the_arrangement_of_rocks_each_with_a_bonus(self):
        wonders = (caveman_buildings.GreatCavePainting, caveman_buildings.ArrangementOfRocks)
        self.assertEqual([building for building in Caveman.BUILDINGS if issubclass(building, Wonder)], list(wonders))
        for wonder in wonders:
            with self.subTest(wonder=wonder):
                self.assertTrue(issubclass(wonder, Wonder))
                self.assertGreater(wonder.RESEARCH_POINTS + wonder.ACTION_POINTS, 0)


class TestClassic(unittest.TestCase):

    def test_classic_has_the_resources_the_user_named_with_currency_first(self):
        resources = classic_resources
        collected = {resources.Currency, resources.Food, resources.Wood, resources.Stone, resources.Metal}
        placeholders = {resources.Iron, resources.Gold, resources.Uranium, resources.Silk}
        self.assertEqual(set(Classic.RESOURCES), collected | placeholders)
        self.assertIs(Classic.PRIMARY_RESOURCE, resources.Currency)
        self.assertIs(Classic.FOOD, resources.Food)

    def test_iron_gold_uranium_and_silk_are_strategic_and_the_other_resources_of_classic_are_collected(self):
        resources = classic_resources
        strategic = [resource for resource in Classic.RESOURCES if issubclass(resource, StrategicResource)]
        self.assertEqual(strategic, [resources.Iron, resources.Gold, resources.Uranium, resources.Silk])

    def test_the_legion_of_classic_requires_iron_and_no_other_unit_named_so_far_requires_a_strategic_resource(self):
        requiring = [unit for unit in Classic.UNITS if any(issubclass(required, StrategicResource) for required in unit.REQUIRES)]
        self.assertEqual(requiring, [classic_units.Legion])
        self.assertEqual(classic_units.Legion.REQUIRES, (classic_resources.Iron,))

    def test_the_mountains_that_have_metal_in_classic_are_marked_by_a_terrain_bonus(self):
        self.assertEqual(Classic.TERRAIN_BONUSES, (classic_terrain_bonuses.MetalDeposit,))
        self.assertEqual(classic_terrain_bonuses.MetalDeposit.ON, (classic_terrains.Mountains,))
        self.assertEqual([improvement for improvement in Classic.IMPROVEMENTS if improvement.BECOMES is not None], [])

    def test_the_mountains_of_classic_can_have_iron_gold_and_uranium(self):
        self.assertEqual(classic_terrains.Mountains.CAN_HAVE, (classic_resources.Iron, classic_resources.Gold, classic_resources.Uranium))
        self.assertEqual([terrain for terrain in Classic.TERRAINS if terrain.CAN_HAVE], [classic_terrains.Mountains])

    def test_caveman_has_flint_in_the_mountains_as_its_one_strategic_resource(self):
        strategic = [resource for resource in Caveman.RESOURCES if issubclass(resource, StrategicResource)]
        self.assertEqual(strategic, [caveman_resources.Flint])
        self.assertEqual(caveman_terrains.Mountains.CAN_HAVE, (caveman_resources.Flint,))
        self.assertEqual([terrain for terrain in Caveman.TERRAINS if terrain.CAN_HAVE], [caveman_terrains.Mountains])

    def test_caveman_has_bison_and_elephants_as_terrain_bonuses_on_grassland_that_give_more_food(self):
        bonuses = caveman_terrain_bonuses
        self.assertEqual(Caveman.TERRAIN_BONUSES, (bonuses.Bison, bonuses.Elephants))
        for bonus in Caveman.TERRAIN_BONUSES:
            self.assertEqual(bonus.ON, (caveman_terrains.Grassland,))
            self.assertEqual(set(bonus.GIVES), {caveman_resources.Food})
        self.assertLess(bonuses.Bison.GIVES[caveman_resources.Food], bonuses.Elephants.GIVES[caveman_resources.Food])

    def test_the_watchtower_requires_fire_and_flint_and_boosts_the_defenses_of_its_city_by_a_quarter(self):
        watchtower = caveman_buildings.Watchtower
        self.assertEqual(watchtower.REQUIRES, (caveman_technologies.Fire, caveman_resources.Flint))
        self.assertEqual(watchtower.DEFENSE_BONUS, WATCHTOWER_DEFENSE_BONUS)
        self.assertEqual([building for building in Caveman.BUILDINGS if building.DEFENSE_BONUS], [watchtower])
        self.assertEqual(Building.DEFENSE_BONUS, 0)
        self.assertIn(caveman_technologies.Fire, Caveman.TECHNOLOGIES)

    def test_classic_has_the_terrains_the_user_named_and_only_rivers_and_lakes_are_fresh_water(self):
        terrains = classic_terrains
        self.assertEqual(set(Classic.TERRAINS), {terrains.Grassland, terrains.Desert, terrains.Mountains, terrains.River, terrains.Lake, terrains.Ocean})
        self.assertEqual({terrain for terrain in Classic.TERRAINS if terrain.FRESH_WATER}, {terrains.River, terrains.Lake})
        self.assertEqual({terrain for terrain in Classic.TERRAINS if not terrain.LAND}, {terrains.River, terrains.Lake, terrains.Ocean})

    def test_classic_has_the_mine(self):
        self.assertIn(classic_improvements.Mine, Classic.IMPROVEMENTS)

    def test_a_kind_can_be_called_something_its_class_name_cannot_say(self):
        self.assertEqual(shown_name(classic_units.AntiMissilePlatform), ANTI_MISSILE_PLATFORM)
        self.assertEqual(shown_name(classic_units.AntiAirPlatform), ANTI_AIR_PLATFORM)
        self.assertEqual(shown_name(classic_units.FighterPlane), FIGHTER_PLANE)
        self.assertEqual(shown_name(LaterPlatform), LATER_PLATFORM)

    def test_classic_has_the_technologies_the_user_named(self):
        technologies = classic_technologies
        named = {
            technologies.IronWorking, technologies.Literacy, technologies.BronzeWorking, technologies.Computers,
            technologies.Industrialization, technologies.Sanitation, technologies.TheInternet, technologies.Irrigation, technologies.Fortification,
        }
        self.assertLessEqual(named, set(Classic.TECHNOLOGIES))

    def test_classic_has_the_units_the_user_named(self):
        units = classic_units
        named = {
            units.Settler, units.Scout, units.Phalanx, units.Legion, units.Catapult, units.Knights, units.Cannon, units.FighterPlane,
            units.Bomber, units.StealthBomber, units.CruiseMissile, units.NuclearMissile, units.Drone, units.AntiMissilePlatform, units.AntiAirPlatform,
            units.Musketeer, units.Infantry, units.Warrior, units.Howitzer,
        }
        self.assertLessEqual(named, set(Classic.UNITS))
        self.assertTrue(issubclass(units.Settler, SettlerUnit))

    def test_classic_has_the_buildings_that_add_research_points(self):
        buildings = classic_buildings
        self.assertLessEqual({buildings.Library, buildings.College, buildings.ResearchCenter}, set(Classic.BUILDINGS))

    def test_the_world_wonders_of_classic_are_the_ones_the_user_named_and_no_more(self):
        buildings = classic_buildings
        named = {
            buildings.ThePyramids, buildings.TheGreatWall, buildings.TheManhattanProject, buildings.TheLibraryOfAlexandria,
            buildings.TheHangingGardensOfBabylon, buildings.TheStatueOfZeusAtOlympia, buildings.TheTempleOfArtemisAtEphesus,
            buildings.TheMausoleumAtHalicarnassus, buildings.TheColossusOfRhodes, buildings.TheLighthouseOfAlexandria,
        }
        self.assertEqual({building for building in Classic.BUILDINGS if issubclass(building, Wonder)}, named)

    def test_the_manhattan_project_unlocks_the_nuclear_missile(self):
        self.assertEqual(classic_units.NuclearMissile.REQUIRES, (classic_buildings.TheManhattanProject,))

    def test_the_siege_units_of_classic_do_not_strike_back_bypass_city_walls_and_every_other_unit_does_neither(self):
        siege = {classic_units.Catapult, classic_units.Cannon, classic_units.Howitzer}
        self.assertEqual({unit for unit in Classic.UNITS if not unit.STRIKES_BACK}, siege)
        self.assertEqual({unit for unit in Classic.UNITS if unit.BYPASSES_WALLS}, siege)
        for unit in siege:
            self.assertEqual((unit.DEFENSE, unit.HIT_POINTS), (SIEGE_DEFENSE, SIEGE_HIT_POINTS))

    def test_a_cannon_is_3_times_a_catapult_and_a_howitzer_3_times_a_cannon(self):
        self.assertEqual(classic_units.Cannon.ATTACK, classic_units.Catapult.ATTACK * SIEGE_STEP)
        self.assertEqual(classic_units.Howitzer.ATTACK, classic_units.Cannon.ATTACK * SIEGE_STEP)
        self.assertGreater(classic_units.Catapult.ATTACK, 0)

    def test_city_walls_require_fortification_cost_stone_and_are_the_walls_of_classic(self):
        walls = classic_buildings.CityWalls
        self.assertEqual(walls.REQUIRES, (classic_technologies.Fortification,))
        self.assertEqual(set(walls.COST), {classic_resources.Stone})
        self.assertGreater(walls.DEFENSE_BONUS, 0)
        self.assertEqual([building for building in Classic.BUILDINGS if building.WALLS], [walls])
        self.assertFalse(Building.WALLS)


class TestSciFi(unittest.TestCase):

    def test_scifi_has_infantry_the_probe_the_space_fighter_the_space_carrier_and_the_stargate(self):
        self.assertLessEqual({scifi_units.Infantry, scifi_units.Probe, scifi_units.SpaceFighter, scifi_units.SpaceCarrier}, set(SciFi.UNITS))
        self.assertEqual({unit for unit in SciFi.UNITS if unit.DOMAIN == Domain.SPACE}, {scifi_units.SpaceFighter, scifi_units.SpaceCarrier})
        self.assertIn(scifi_buildings.Stargate, SciFi.BUILDINGS)


class TestPlanetWars(unittest.TestCase):

    def test_planetwars_has_the_settler_the_colony_ship_and_the_space_transport(self):
        units = planetwars_units
        self.assertEqual(set(PlanetWars.UNITS), {units.Settler, units.ColonyShip, units.SpaceTransport})
        self.assertTrue(issubclass(units.Settler, SettlerUnit))
        self.assertEqual({unit for unit in PlanetWars.UNITS if unit.DOMAIN == Domain.SPACE}, {units.ColonyShip, units.SpaceTransport})


class TestFantasy(unittest.TestCase):

    def test_fantasy_has_the_units_the_user_named(self):
        units = fantasy_units
        named = {
            units.Dragon, units.Knight, units.Wyvern, units.Monk, units.Cleric, units.Ranger, units.Sorcerer, units.Wizard, units.Elemental,
            units.Soldier, units.Scout, units.Settler, units.Worker, units.Ogre, units.Goblin, units.Blimp,
        }
        self.assertEqual(set(Fantasy.UNITS), named)
        self.assertTrue(issubclass(units.Settler, SettlerUnit))
        self.assertEqual({unit for unit in Fantasy.UNITS if unit.DOMAIN == Domain.AIR}, {units.Dragon, units.Wyvern, units.Blimp})

    def test_fantasy_has_the_technologies_the_user_named_and_none_requires_anything_yet(self):
        technologies = fantasy_technologies
        named = {
            technologies.DragonHusbandry, technologies.DragonRiding, technologies.Chivalry, technologies.WyvernHusbandry, technologies.Magic,
            technologies.FireMagic, technologies.WaterMagic, technologies.EarthMagic, technologies.AirMagic, technologies.Elementals,
            technologies.Necromancy, technologies.Psionics, technologies.Teleportation, technologies.Spirituality, technologies.NatureAttunement,
            technologies.Guilds, technologies.Summoning, technologies.Telepathy, technologies.Blimps,
        }
        self.assertEqual(set(Fantasy.TECHNOLOGIES), named)
        for technology in Fantasy.TECHNOLOGIES:
            self.assertEqual(technology.REQUIRES, ())


if __name__ == '__main__':
    unittest.main()
