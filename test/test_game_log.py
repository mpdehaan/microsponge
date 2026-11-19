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

"""The detailed log of a scripted game, the report that answers questions from a log, the page with the charts, and the two tools."""

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from caveman_game import FIRST_CIVILIZATION, GRASSLAND_TILE, THE_WORLD, end_rounds, found_village, give_building, held, learn, started_caveman_game
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import StrategicResource
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.order import RetireOrder
from microsponge.engine.orders.thing import city_thing, division_thing
from microsponge.engine.players.hand import Hand
from microsponge.engine.orders.what import NoDetails
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.support.chronicle import Chronicle
from microsponge.support.game_log import NOT_GONE, Ending, GameLog, Group, Key, Series, read_log, write_log
from microsponge.support.game_log_page import (
    ALL_UNITS_CHARTS, BUILDING_CHARTS, CITY_CHARTS, CONTROL_POINT_CHARTS, MAIN_CHARTS, MILITARY_CHARTS, ORDER_SPAN_TURNS, PLACEHOLDER, SCORE_PART_CHARTS, Content, PageKey, Tab, given_in_spans,
    page_data, page_path, page_text, spans_of, write_page,
)
from microsponge.support.game_log_report import SCORE_PARTS, built_table, scores_table, forces_table, last_of, name_of, winner_line, made_table, orders_table, ranked, report_lines, series_of, strongest_turn, tables, timelines, title_of
from microsponge.support.scripted_game import play, started_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes.caveman.buildings import Granary
from microsponge.themes.caveman.improvements import Clearing, Farm
from microsponge.themes.caveman.technologies import Agriculture, Clubs
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Clubber, Worker
from microsponge.ui_strings import (
    MSG_LOG_NO_WINNER, MSG_LOG_WON_BY_CONQUEST, MSG_LOG_WON_ON_SCORE, MSG_LOG_TIMELINE_ENDED, MSG_LOG_TIMELINE_STRONGEST, MSG_LOG_UNITS_HEADING, MSG_LOG_WRITTEN, MSG_PAGE_CHART_IMPROVEMENTS_OF_KIND, MSG_PAGE_CHART_UNITS_OF_KIND, MSG_PAGE_NO_IMPROVEMENTS,
    MSG_PAGE_CHART_BANK_OF, MSG_PAGE_CHART_ORDERS_OF_KIND, MSG_PAGE_TAB_BUILDINGS, MSG_PAGE_TAB_ORDERS,
    MSG_PAGE_TAB_CITIES, MSG_PAGE_TAB_CONTROL_POINTS, MSG_PAGE_TAB_IMPROVEMENTS, MSG_PAGE_TAB_SCORE, MSG_PAGE_TAB_TABLES, MSG_PAGE_TAB_TIMELINES, MSG_PAGE_TAB_UNITS, MSG_STORY_FOUNDED,
)

ROOT = Path(__file__).resolve().parents[1]
LOG_TOOL = ROOT / 'tools' / 'game_log.py'
REPORT_TOOL = ROOT / 'tools' / 'game_report.py'
FIRST = FIRST_CIVILIZATION
SECOND = FIRST_CIVILIZATION + 1
A_NAME = 'Bedrock'
A_SEED = 5
THREE = 3
TURNS = 25
ONE_ROUND = 1
TWO_ROUNDS = 2
A_TURN = 4
A_LATER_TURN = 9
A_LAST_TURN = 12
A_FILE = 'a_log.json'
NO_FILE = 'no_such_log.json'
LOG_FILE = Path('logs') / 'caveman_seed5.json'
HTML_FLAG = '--html'
# A tile near the first civilization's first village, and a tile 3 moves east of it, as (x, y).
A_TILE = (9, 12)
A_FAR_TILE = (12, 12)
TILES_APART = 3
MADE_COLUMN = 2
FIRST_LINE = 0
ONE_UNIT = 1
TWO_UNITS = 2
NONE_AT_ALL = 0
# The tabs that show something other than charts.
NOT_CHARTS = {Tab.TIMELINES: Content.TIMELINES, Tab.TABLES: Content.TABLES}
TAB_NAMES = (MSG_PAGE_TAB_SCORE, MSG_PAGE_TAB_CITIES, MSG_PAGE_TAB_UNITS, MSG_PAGE_TAB_BUILDINGS, MSG_PAGE_TAB_IMPROVEMENTS, MSG_PAGE_TAB_ORDERS, MSG_PAGE_TAB_CONTROL_POINTS, MSG_PAGE_TAB_TIMELINES, MSG_PAGE_TAB_TABLES)


def titles_of(charts):
    return [title for _, title in charts]


def had_some(*, data, key):
    """Return the kinds counted under a key of a log that some civilization had on some turn."""
    return [kind for kind, counts in data[key].items() if any(count > 0 for turns in counts.values() for count in turns)]


def expected_titles(data):
    """Return, for each tab of the page of a log, the titles of its charts in order."""
    city = data[Key.CITY_WORD]
    units = [MSG_PAGE_CHART_UNITS_OF_KIND.format(kind=kind) for kind in had_some(data=data, key=Key.UNIT_KINDS)]
    improvements = [MSG_PAGE_CHART_IMPROVEMENTS_OF_KIND.format(kind=kind, city=city) for kind in had_some(data=data, key=Key.IMPROVEMENTS)]
    return {
        Tab.SCORE: titles_of(MAIN_CHARTS) + titles_of(SCORE_PART_CHARTS),
        Tab.CITIES: titles_of(CITY_CHARTS) + [MSG_PAGE_CHART_BANK_OF.format(kind=kind) for kind in had_some(data=data, key=Key.BANKS)],
        Tab.UNITS: titles_of(ALL_UNITS_CHARTS) + units + titles_of(MILITARY_CHARTS),
        Tab.BUILDINGS: titles_of(BUILDING_CHARTS),
        Tab.IMPROVEMENTS: improvements,
        Tab.ORDERS: [MSG_PAGE_CHART_ORDERS_OF_KIND.format(kind=kind, turns=ORDER_SPAN_TURNS) for kind in dict.fromkeys(record[Key.KIND] for record in data[Key.ORDERS] if record[Key.GIVEN])],
        Tab.CONTROL_POINTS: titles_of(CONTROL_POINT_CHARTS),
        Tab.TIMELINES: [],
        Tab.TABLES: [],
    }


def tab_called(*, page, tab):
    return next(entry for entry in page[PageKey.TABS] if entry[PageKey.ID] == tab)


def chart_titles(tab):
    return [chart[PageKey.TITLE] for chart in tab[PageKey.CHARTS]]


def played():
    """Return the data of the log of a game of caveman the computer players played."""
    game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
    log = GameLog(game)
    chronicle = play(game=game, turns=TURNS, log=log)
    return log.as_data(game=game, chronicle=chronicle, seed=A_SEED)


class TestGameLog(unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        self.city = found_village(game=self.game, civilization=FIRST, name=A_NAME)
        self.log = GameLog(self.game)
        self.chronicle = Chronicle(self.game)

    def data(self):
        return self.log.as_data(game=self.game, chronicle=self.chronicle, seed=A_SEED)

    def unit_logged(self, unit):
        return next(record for record in self.data()[Key.UNITS] if record[Key.ID] == unit)

    def look(self):
        self.log.note(game=self.game, turn=self.game.get_turn())

    def test_a_unit_is_logged_with_how_far_it_moved_how_long_it_lived_and_that_it_was_lost(self):
        unit = UnitControl.place(game=self.game, kind=Clubber, owner=FIRST, world=THE_WORLD, x=A_TILE[0], y=A_TILE[1])
        self.look()
        UnitControl.move_to(game=self.game, unit=unit, x=A_FAR_TILE[0], y=A_FAR_TILE[1])
        self.look()
        self.log.count(self.game)
        logged = self.unit_logged(unit)
        self.assertEqual((logged[Key.KIND], logged[Key.CIVILIZATION], logged[Key.MILITARY]), (shown_name(Clubber), FIRST, True))
        self.assertEqual((logged[Key.MOVED], logged[Key.LIVED], logged[Key.INSIDE], logged[Key.ENDING], logged[Key.GONE]), (TILES_APART, 1, 0, Ending.ALIVE, NOT_GONE))
        UnitControl.remove(game=self.game, unit=unit)
        self.look()
        logged = self.unit_logged(unit)
        self.assertEqual((logged[Key.ENDING], logged[Key.GONE]), (Ending.LOST, self.game.get_turn()))

    def test_a_settler_that_built_a_city_is_not_lost_and_the_city_is_logged_with_its_founder_and_its_buildings(self):
        game = started_caveman_game()
        log = GameLog(game)
        found_village(game=game, civilization=FIRST, name=A_NAME)
        log.note(game=game, turn=game.get_turn())
        give_building(game=game, city=game.get_cities_of(FIRST)[0], building=Granary)
        data = log.as_data(game=game, chronicle=Chronicle(game), seed=A_SEED)
        settlers = [record for record in data[Key.UNITS] if record[Key.KIND] == shown_name(Settler) and record[Key.CIVILIZATION] == FIRST]
        self.assertEqual([record[Key.ENDING] for record in settlers], [Ending.SETTLED])
        self.assertFalse(settlers[0][Key.MILITARY])
        city = data[Key.CITIES][0]
        self.assertEqual((city[Key.NAME], city[Key.FOUNDER], city[Key.OWNER], city[Key.BUILDINGS]), (A_NAME, FIRST, FIRST, [shown_name(Granary)]))

    def test_strength_is_counted_each_turn_and_each_part_of_the_score_adds_up_over_the_turns(self):
        learn(game=self.game, civilization=FIRST, technology=Clubs)
        give_building(game=self.game, city=self.city, building=Granary)
        UnitControl.place(game=self.game, kind=Clubber, owner=FIRST, world=THE_WORLD, x=A_TILE[0], y=A_TILE[1])
        self.look()
        self.log.count(self.game)
        self.log.count(self.game)
        data = self.data()
        citizens = self.game.get_city(self.city).get_citizens()
        expected = {Series.MILITARY_SCORE: Clubber.HIT_POINTS, Series.SCIENCE_SCORE: 1, Series.POPULATION_SCORE: citizens, Series.DEVELOPMENT_SCORE: 1}
        for part in SCORE_PARTS:
            with self.subTest(part=part):
                self.assertEqual(series_of(data=data, civilization=FIRST, series=part), [expected[part], expected[part] * TWO_ROUNDS])
        strength = sum(expected.values())
        self.assertEqual(series_of(data=data, civilization=FIRST, series=Series.STRENGTH), [strength, strength])
        self.assertEqual(series_of(data=data, civilization=FIRST, series=Series.SCORE), [strength, strength * TWO_ROUNDS])
        self.assertEqual(series_of(data=data, civilization=FIRST, series=Series.HIT_POINTS), [Clubber.HIT_POINTS, Clubber.HIT_POINTS])

    def counts_of(self, *, key, kind, civilization):
        return self.data()[key][shown_name(kind)][str(civilization)]

    def test_the_units_of_each_kind_each_civilization_has_are_counted_each_turn(self):
        clubber = UnitControl.place(game=self.game, kind=Clubber, owner=FIRST, world=THE_WORLD, x=A_TILE[0], y=A_TILE[1])
        UnitControl.place(game=self.game, kind=Clubber, owner=FIRST, world=THE_WORLD, x=A_FAR_TILE[0], y=A_FAR_TILE[1])
        self.look()
        self.log.count(self.game)
        UnitControl.remove(game=self.game, unit=clubber)
        self.look()
        self.log.count(self.game)
        self.assertEqual(self.counts_of(key=Key.UNIT_KINDS, kind=Clubber, civilization=FIRST), [TWO_UNITS, ONE_UNIT])
        self.assertEqual(self.counts_of(key=Key.UNIT_KINDS, kind=Settler, civilization=FIRST), [NONE_AT_ALL, NONE_AT_ALL])
        self.assertEqual(self.counts_of(key=Key.UNIT_KINDS, kind=Settler, civilization=SECOND), [ONE_UNIT, ONE_UNIT])
        self.assertEqual(self.counts_of(key=Key.UNIT_KINDS, kind=Clubber, civilization=SECOND), [NONE_AT_ALL, NONE_AT_ALL])

    def test_every_kind_of_unit_and_every_kind_of_improvement_that_stays_on_a_tile_is_in_the_log_even_with_none(self):
        self.log.count(self.game)
        data = self.data()
        self.assertEqual(list(data[Key.UNIT_KINDS]), [shown_name(kind) for kind in Caveman.UNITS])
        self.assertEqual(list(data[Key.IMPROVEMENTS]), [shown_name(Farm)])
        self.assertNotIn(shown_name(Clearing), data[Key.IMPROVEMENTS])
        for counts in (*data[Key.UNIT_KINDS].values(), *data[Key.IMPROVEMENTS].values()):
            self.assertEqual(set(counts), {str(FIRST), str(SECOND)})

    def test_an_improvement_on_a_tile_of_a_city_radius_is_counted_for_its_civilization_and_one_outside_every_radius_is_not(self):
        radius = CityControl.radius_tiles(game=self.game, city=self.city)
        self.assertIn(A_TILE, radius)
        self.assertTrue(all(GRASSLAND_TILE not in CityControl.radius_tiles(game=self.game, city=city) for city in self.game.get_city_ids()))
        learn(game=self.game, civilization=FIRST, technology=Agriculture)
        for x, y in (A_TILE, GRASSLAND_TILE):
            worker = UnitControl.place(game=self.game, kind=Worker, owner=FIRST, world=THE_WORLD, x=x, y=y)
            Orders.build_improvement(game=self.game, unit=worker, improvement=Farm)
        self.look()
        self.log.count(self.game)
        end_rounds(game=self.game, rounds=Farm.BUILD_TURNS)
        self.look()
        self.log.count(self.game)
        world = self.game.get_world(THE_WORLD)
        for x, y in (A_TILE, GRASSLAND_TILE):
            self.assertNotEqual(world.get_value(layer=Layer.IMPROVEMENT, x=x, y=y), NOTHING)
        self.assertEqual(self.counts_of(key=Key.IMPROVEMENTS, kind=Farm, civilization=FIRST), [NONE_AT_ALL, ONE_UNIT])
        self.assertEqual(self.counts_of(key=Key.IMPROVEMENTS, kind=Farm, civilization=SECOND), [NONE_AT_ALL, NONE_AT_ALL])

    def test_policy_and_command_are_counted_each_turn_and_a_log_is_read_back_as_it_was_written(self):
        end_rounds(game=self.game, rounds=ONE_ROUND)
        self.log.count(self.game)
        data = self.data()
        for series in (Series.POLICY, Series.COMMAND):
            self.assertGreater(last_of(data=data, civilization=FIRST, series=series), 0)
        for series in (Series.POLICY_TAKEN, Series.COMMAND_TAKEN, Series.INSIDE, Series.LEVEL):
            self.assertEqual(series_of(data=data, civilization=FIRST, series=series), [0])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / A_FILE
            write_log(data=data, path=path)
            self.assertEqual(read_log(path), data)


class TestGameLogReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = played()

    def test_a_played_game_logs_every_turn_of_every_series_for_every_civilization(self):
        self.assertEqual(self.data[Key.TURNS], TURNS)
        self.assertEqual(len(self.data[Key.CIVILIZATIONS]), THREE)
        for series in (*Series.OWN, Series.CITIES, Series.WEALTH):
            for civilization in self.data[Key.CIVILIZATIONS]:
                with self.subTest(series=series):
                    self.assertEqual(len(series_of(data=self.data, civilization=civilization[Key.ID], series=series)), TURNS)
        for key in (Key.UNIT_KINDS, Key.IMPROVEMENTS):
            for kind, counts in self.data[key].items():
                with self.subTest(kind=kind):
                    self.assertEqual([len(turns) for turns in counts.values()], [TURNS] * THREE)

    def test_the_same_seed_writes_the_same_log(self):
        self.assertEqual(played(), self.data)

    def test_the_civilizations_are_ranked_by_score_and_the_strongest_turn_is_found(self):
        scores = [last_of(data=self.data, civilization=civilization, series=Series.SCORE) for civilization in ranked(self.data)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        turn, most = strongest_turn(data=self.data, civilization=FIRST)
        strength = series_of(data=self.data, civilization=FIRST, series=Series.STRENGTH)
        self.assertEqual((most, strength[turn]), (max(strength), max(strength)))

    def test_the_tables_count_every_unit_once_and_each_table_has_a_cell_for_every_heading(self):
        made = 0
        for table in tables(self.data):
            with self.subTest(table=table.title):
                self.assertTrue(all(len(row) == len(table.heading) for row in table.rows))
            if table.heading == MSG_LOG_UNITS_HEADING:
                made = sum(int(row[MADE_COLUMN]) for row in table.rows)
        self.assertEqual(made, len(self.data[Key.UNITS]))
        self.assertEqual(len(scores_table(self.data).rows), THREE)

    def test_each_civilization_has_a_timeline_of_its_high_points_in_order_that_ends_with_its_place(self):
        told = timelines(self.data)
        self.assertEqual(len(told), THREE)
        first = told[FIRST - 1]
        name = self.data[Key.CIVILIZATIONS][FIRST - 1][Key.NAME]
        self.assertTrue(first.lines[FIRST_LINE].startswith(MSG_STORY_FOUNDED.split('{subject}')[0].format(turn=0, name=name, city=self.data[Key.CITY_WORD])))
        turn, most = strongest_turn(data=self.data, civilization=FIRST)
        self.assertIn(MSG_LOG_TIMELINE_STRONGEST.format(turn=turn, name=name, strength=most), first.lines)
        place = ranked(self.data).index(FIRST) + 1
        score = last_of(data=self.data, civilization=FIRST, series=Series.SCORE)
        self.assertEqual(first.lines[-1], MSG_LOG_TIMELINE_ENDED.format(turn=TURNS, name=name, place=place, of=THREE, score=score))

    def test_the_winner_is_the_only_civilization_remaining_or_else_the_highest_score_among_those_remaining(self):
        data = copy.deepcopy(self.data)
        for entry in data[Key.CIVILIZATIONS]:
            entry[Key.LOST] = False
        last_place = ranked(data)[-1]
        for entry in data[Key.CIVILIZATIONS]:
            entry[Key.LOST] = entry[Key.ID] != last_place
        self.assertEqual(winner_line(data), MSG_LOG_WON_BY_CONQUEST.format(turn=TURNS, name=name_of(data=data, civilization=last_place)))
        for entry in data[Key.CIVILIZATIONS]:
            entry[Key.LOST] = entry[Key.ID] == ranked(data)[0]
        remaining = [civilization for civilization in ranked(data) if civilization != ranked(data)[0]]
        best = remaining[0]
        expected = MSG_LOG_WON_ON_SCORE.format(turn=TURNS, count=len(remaining), name=name_of(data=data, civilization=best), score=last_of(data=data, civilization=best, series=Series.SCORE))
        self.assertEqual(winner_line(data), expected)
        for entry in data[Key.CIVILIZATIONS]:
            entry[Key.LOST] = True
        self.assertEqual(winner_line(data), MSG_LOG_NO_WINNER)

    def test_the_report_starts_with_the_title_and_the_winner_and_holds_every_timeline_and_table(self):
        lines = report_lines(data=self.data)
        self.assertEqual(lines[:2], [title_of(self.data), winner_line(self.data)])
        for part in (*timelines(self.data), *tables(self.data)):
            self.assertIn(part.title, lines)

    def test_the_page_has_its_tabs_in_order_each_with_its_charts_and_a_line_for_each_civilization(self):
        page = page_data(self.data)
        self.assertEqual([tab[PageKey.ID] for tab in page[PageKey.TABS]], list(Tab.ORDER))
        self.assertEqual([tab[PageKey.NAME] for tab in page[PageKey.TABS]], list(TAB_NAMES))
        self.assertEqual({tab[PageKey.ID]: chart_titles(tab) for tab in page[PageKey.TABS]}, expected_titles(self.data))
        self.assertEqual({tab[PageKey.ID]: tab[PageKey.CONTENT] for tab in page[PageKey.TABS]}, {tab: NOT_CHARTS.get(tab, Content.CHARTS) for tab in Tab.ORDER})
        charted = (*MAIN_CHARTS, *SCORE_PART_CHARTS, *CITY_CHARTS, *BUILDING_CHARTS, *ALL_UNITS_CHARTS, *MILITARY_CHARTS, *CONTROL_POINT_CHARTS)
        self.assertEqual({series for series, _ in charted} | {Series.WEALTH}, set(self.data[Key.SERIES]))
        self.assertEqual([chart[PageKey.WIDE] for chart in tab_called(page=page, tab=Tab.SCORE)[PageKey.CHARTS]][:len(MAIN_CHARTS)], [True] * len(MAIN_CHARTS))
        for tab in page[PageKey.TABS]:
            for chart in tab[PageKey.CHARTS]:
                self.assertEqual(len(chart[PageKey.SERIES]), THREE)
        self.assertEqual(len(page[PageKey.TABLES]), len(tables(self.data)))
        expected = {Tab.UNITS: (made_table(self.data), forces_table(self.data)), Tab.BUILDINGS: (built_table(self.data),), Tab.ORDERS: (orders_table(self.data),)}
        for tab, shown_tables in expected.items():
            self.assertEqual([shown[PageKey.TITLE] for shown in tab_called(page=page, tab=tab)[PageKey.TABLES]], [table.title for table in shown_tables])
        made = made_table(self.data)
        self.assertEqual(sum(int(row[MADE_COLUMN]) for row in made.rows), len(self.data[Key.UNITS]))

    def test_a_kind_no_civilization_ever_had_has_no_chart_and_with_no_improvement_the_tab_says_so(self):
        data = copy.deepcopy(self.data)
        for counts in (data[Key.UNIT_KINDS][shown_name(Clubber)], data[Key.IMPROVEMENTS][shown_name(Farm)]):
            for civilization in counts:
                counts[civilization] = [NONE_AT_ALL] * len(counts[civilization])
        page = page_data(data)
        self.assertNotIn(MSG_PAGE_CHART_UNITS_OF_KIND.format(kind=shown_name(Clubber)), chart_titles(tab_called(page=page, tab=Tab.UNITS)))
        improvements = tab_called(page=page, tab=Tab.IMPROVEMENTS)
        self.assertEqual((improvements[PageKey.CHARTS], improvements[PageKey.NOTE]), ([], MSG_PAGE_NO_IMPROVEMENTS.format(city=data[Key.CITY_WORD])))
        data[Key.UNIT_KINDS][shown_name(Clubber)][str(SECOND)][-1] = ONE_UNIT
        data[Key.IMPROVEMENTS][shown_name(Farm)][str(FIRST)][-1] = ONE_UNIT
        page = page_data(data)
        self.assertIn(MSG_PAGE_CHART_UNITS_OF_KIND.format(kind=shown_name(Clubber)), chart_titles(tab_called(page=page, tab=Tab.UNITS)))
        improvements = tab_called(page=page, tab=Tab.IMPROVEMENTS)
        self.assertEqual(chart_titles(improvements), [MSG_PAGE_CHART_IMPROVEMENTS_OF_KIND.format(kind=shown_name(Farm), city=data[Key.CITY_WORD])])
        self.assertIsNone(improvements[PageKey.NOTE])
        text = page_text(self.data)
        self.assertNotIn(PLACEHOLDER, text)
        self.assertIn(title_of(self.data), text)
        with tempfile.TemporaryDirectory() as folder:
            path = page_path(Path(folder) / A_FILE)
            write_page(data=self.data, path=path)
            self.assertEqual(path.read_text(encoding='utf-8'), text)


class TestWhatTheLogCountsOfBuildingsBanksAndOrders(unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        self.city = found_village(game=self.game, civilization=FIRST, name=A_NAME)
        self.log = GameLog(self.game)

    def data(self):
        return self.log.as_data(game=self.game, chronicle=Chronicle(self.game), seed=A_SEED)

    def test_a_building_a_city_gains_is_built_once_by_the_owner_on_that_turn(self):
        building = self.game.get_theme().BUILDINGS[0]
        give_building(game=self.game, city=self.city, building=building)
        self.log.note(game=self.game, turn=A_TURN)
        self.log.note(game=self.game, turn=A_LATER_TURN)
        built = self.data()[Key.BUILT]
        self.assertEqual(built, [{Key.TURN: A_TURN, Key.CIVILIZATION: FIRST, Key.BUILDING: shown_name(building), Key.CITY: A_NAME}])
        table = built_table(self.data())
        self.assertEqual(table.rows, [[self.data()[Key.CIVILIZATIONS][FIRST - 1][Key.NAME], shown_name(building), str(len(built)), str(A_TURN), str(A_TURN)]])

    def test_the_bank_of_every_collected_resource_is_counted_each_turn_and_the_food_the_cities_store(self):
        self.log.count(self.game)
        banks = self.data()[Key.BANKS]
        collected = [resource for resource in self.game.get_theme().RESOURCES if not issubclass(resource, StrategicResource) and resource is not self.game.get_theme().FOOD]
        self.assertEqual(list(banks), [shown_name(resource) for resource in collected])
        primary = self.game.get_theme().PRIMARY_RESOURCE
        self.assertEqual(banks[shown_name(primary)][str(FIRST)], [held(game=self.game, civilization=FIRST, resource=primary)])
        self.assertNotIn(shown_name(self.game.get_theme().FOOD), banks)
        self.assertEqual(series_of(data=self.data(), civilization=FIRST, series=Series.FOOD_STORED), [self.game.get_city(self.city).get_food()])

    def test_an_order_is_counted_once_when_given_and_the_turns_its_kind_was_in_use_are_kept(self):
        here = city_thing(self.city)
        kind = next(kind for kind in self.game.get_theme().ORDERS if here.type in kind.RECEIVERS)
        order = OrderControl.give(game=self.game, civilization=FIRST, kind=kind, giver=here, receiver=here, what=NoDetails())
        self.log.note(game=self.game, turn=A_TURN)
        self.log.note(game=self.game, turn=A_LATER_TURN)
        order.disable()
        self.log.note(game=self.game, turn=A_LAST_TURN)
        record, = [record for record in self.data()[Key.ORDERS] if record[Key.CIVILIZATION] == FIRST]
        self.assertEqual((record[Key.KIND], record[Key.GIVEN], record[Key.FIRST_IN_USE], record[Key.LAST_IN_USE]), (shown_name(kind), [A_TURN], A_TURN, A_LATER_TURN))
        name = self.data()[Key.CIVILIZATIONS][FIRST - 1][Key.NAME]
        self.assertEqual(orders_table(self.data()).rows, [[name, shown_name(kind), str(1), str(A_TURN), str(A_LATER_TURN)]])

    def test_orders_are_counted_in_spans_of_turns_and_a_turn_past_the_last_span_falls_in_the_last(self):
        self.assertEqual(given_in_spans(turns=[0, ORDER_SPAN_TURNS - 1, ORDER_SPAN_TURNS, ORDER_SPAN_TURNS * THREE], spans=THREE), [2, 1, 1])
        data = {Key.TURNS: ORDER_SPAN_TURNS * THREE - 1}
        self.assertEqual(len(spans_of(data)), THREE)


class TestWhatTheLogCountsOfForces(unittest.TestCase):

    def test_divisions_and_armies_made_and_units_and_groups_retired_are_counted_with_their_turns(self):
        game = started_caveman_game()
        city = found_village(game=game, civilization=FIRST, name=A_NAME)
        log = GameLog(game)
        army = OrderControl.add_army(game=game, civilization=FIRST)
        division = OrderControl.add_division(game=game, civilization=FIRST, army=army)
        log.note(game=game, turn=A_TURN)
        unit = UnitControl.place(game=game, kind=game.get_theme().PLAYER.FIGHTERS[-1], owner=FIRST, world=THE_WORLD, x=A_TILE[0], y=A_TILE[1])
        division.add_unit(unit)
        log.note(game=game, turn=A_TURN)
        OrderControl.give(game=game, civilization=FIRST, kind=RetireOrder, giver=city_thing(city), receiver=division_thing(division.get_id()), what=NoDetails())
        Hand.retire(game=game, civilization=FIRST)
        log.note(game=game, turn=A_LATER_TURN)
        data = log.as_data(game=game, chronicle=Chronicle(game), seed=A_SEED)
        groups = {record[Key.GROUP]: record for record in data[Key.FORCES] if record[Key.CIVILIZATION] == FIRST}
        self.assertEqual(groups[Group.DIVISION][Key.MADE_TURNS], [A_TURN])
        self.assertEqual(groups[Group.ARMY][Key.MADE_TURNS], [A_TURN])
        self.assertEqual(groups[Group.DIVISION][Key.RETIRED_TURNS], [A_LATER_TURN])
        self.assertEqual(groups[Group.UNIT][Key.RETIRED_TURNS], [A_LATER_TURN])
        self.assertEqual(groups[Group.ARMY][Key.RETIRED_TURNS], [])
        logged, = [record for record in data[Key.UNITS] if record[Key.ID] == unit]
        self.assertEqual(logged[Key.ENDING], Ending.RETIRED)
        row = forces_table(data).rows[FIRST - 1]
        self.assertEqual(len(row), len(forces_table(data).heading))


class TestGameLogTools(unittest.TestCase):

    def run_tool(self, *, tool, arguments, folder):
        return subprocess.run([sys.executable, str(tool), *arguments], capture_output=True, text=True, cwd=folder, check=False)

    def test_the_log_tool_writes_the_log_and_the_report_tool_prints_its_report_and_writes_its_page(self):
        with tempfile.TemporaryDirectory() as folder:
            run = self.run_tool(tool=LOG_TOOL, arguments=[shown_name(Caveman), str(A_SEED), str(THREE), str(TURNS)], folder=folder)
            self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
            self.assertEqual(run.stdout.splitlines(), [MSG_LOG_WRITTEN.format(path=LOG_FILE)])
            data = read_log(Path(folder) / LOG_FILE)
            self.assertEqual(data, played())
            run = self.run_tool(tool=REPORT_TOOL, arguments=[str(LOG_FILE)], folder=folder)
            self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
            self.assertEqual(run.stdout.splitlines(), report_lines(data=data))
            run = self.run_tool(tool=REPORT_TOOL, arguments=[str(LOG_FILE), HTML_FLAG], folder=folder)
            self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
            self.assertEqual(page_path(Path(folder) / LOG_FILE).read_text(encoding='utf-8'), page_text(data))

    def test_each_tool_refuses_a_bad_command_line(self):
        with tempfile.TemporaryDirectory() as folder:
            for tool, arguments in ((LOG_TOOL, []), (LOG_TOOL, [A_NAME]), (REPORT_TOOL, []), (REPORT_TOOL, [NO_FILE])):
                with self.subTest(tool=tool.name, arguments=arguments):
                    self.assertEqual(self.run_tool(tool=tool, arguments=arguments, folder=folder).returncode, FAILED)
