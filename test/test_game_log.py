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

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from caveman_game import FIRST_CIVILIZATION, THE_WORLD, end_rounds, found_village, give_building, learn, started_caveman_game
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.units.unit_control import UnitControl
from microsponge.support.chronicle import Chronicle
from microsponge.support.game_log import NOT_GONE, Ending, GameLog, Key, Series, read_log, write_log
from microsponge.support.game_log_page import CHARTS, MAIN_CHARTS, PLACEHOLDER, PageKey, page_data, page_path, page_text, write_page
from microsponge.support.game_log_report import SCORE_PARTS, last_of, ranked, report_lines, series_of, strongest_turn, tables, timelines, title_of
from microsponge.support.scripted_game import play, started_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes.caveman.buildings import Granary
from microsponge.themes.caveman.technologies import Clubs
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Warrior
from microsponge.ui_strings import MSG_LOG_TIMELINE_ENDED, MSG_LOG_TIMELINE_STRONGEST, MSG_LOG_UNITS_HEADING, MSG_LOG_WRITTEN, MSG_STORY_FOUNDED

ROOT = Path(__file__).resolve().parents[1]
LOG_TOOL = ROOT / 'tools' / 'game_log.py'
REPORT_TOOL = ROOT / 'tools' / 'game_report.py'
FIRST = FIRST_CIVILIZATION
A_NAME = 'Bedrock'
A_SEED = 5
THREE = 3
TURNS = 25
ONE_ROUND = 1
TWO_ROUNDS = 2
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
        unit = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST, world=THE_WORLD, x=A_TILE[0], y=A_TILE[1])
        self.look()
        UnitControl.move_to(game=self.game, unit=unit, x=A_FAR_TILE[0], y=A_FAR_TILE[1])
        self.look()
        self.log.count(self.game)
        logged = self.unit_logged(unit)
        self.assertEqual((logged[Key.KIND], logged[Key.CIVILIZATION], logged[Key.MILITARY]), (shown_name(Warrior), FIRST, True))
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
        UnitControl.place(game=self.game, kind=Warrior, owner=FIRST, world=THE_WORLD, x=A_TILE[0], y=A_TILE[1])
        self.look()
        self.log.count(self.game)
        self.log.count(self.game)
        data = self.data()
        citizens = self.game.get_city(self.city).get_citizens()
        expected = {Series.MILITARY_SCORE: Warrior.HIT_POINTS, Series.SCIENCE_SCORE: 1, Series.POPULATION_SCORE: citizens, Series.DEVELOPMENT_SCORE: 1}
        for part in SCORE_PARTS:
            with self.subTest(part=part):
                self.assertEqual(series_of(data=data, civilization=FIRST, series=part), [expected[part], expected[part] * TWO_ROUNDS])
        strength = sum(expected.values())
        self.assertEqual(series_of(data=data, civilization=FIRST, series=Series.STRENGTH), [strength, strength])
        self.assertEqual(series_of(data=data, civilization=FIRST, series=Series.SCORE), [strength, strength * TWO_ROUNDS])
        self.assertEqual(series_of(data=data, civilization=FIRST, series=Series.HIT_POINTS), [Warrior.HIT_POINTS, Warrior.HIT_POINTS])

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
                self.assertTrue(table.rows)
                self.assertTrue(all(len(row) == len(table.heading) for row in table.rows))
            if table.heading == MSG_LOG_UNITS_HEADING:
                made = sum(int(row[MADE_COLUMN]) for row in table.rows)
        self.assertEqual(made, len(self.data[Key.UNITS]))

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

    def test_the_report_starts_with_the_title_and_holds_every_timeline_and_table(self):
        lines = report_lines(data=self.data)
        self.assertEqual(lines[FIRST_LINE], title_of(self.data))
        for part in (*timelines(self.data), *tables(self.data)):
            self.assertIn(part.title, lines)

    def test_the_page_has_a_chart_of_every_series_with_a_line_for_each_civilization_and_the_data_put_in(self):
        page = page_data(self.data)
        self.assertEqual(len(page[PageKey.MAIN_CHARTS]), len(MAIN_CHARTS))
        self.assertEqual(len(page[PageKey.CHARTS]), len(CHARTS))
        self.assertEqual({series for series, _ in (*MAIN_CHARTS, *CHARTS)}, set(self.data[Key.SERIES]))
        for chart in (*page[PageKey.MAIN_CHARTS], *page[PageKey.CHARTS]):
            self.assertEqual(len(chart[PageKey.SERIES]), THREE)
        self.assertEqual(len(page[PageKey.TABLES]), len(tables(self.data)))
        text = page_text(self.data)
        self.assertNotIn(PLACEHOLDER, text)
        self.assertIn(title_of(self.data), text)
        with tempfile.TemporaryDirectory() as folder:
            path = page_path(Path(folder) / A_FILE)
            write_page(data=self.data, path=path)
            self.assertEqual(path.read_text(encoding='utf-8'), text)


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
