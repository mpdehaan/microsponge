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

"""The scripted game: the chronicle kept of a game, the game the computer players play, the report with its story, and the tool."""

import subprocess
import sys
import unittest
from pathlib import Path

from caveman_game import FIRST_CIVILIZATION, THE_WORLD, found_village, give_building, learn, settler_of, started_caveman_game
from refusals import Refusals
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.unit_control import UnitControl
from microsponge.err_messages import ERR_NO_PLAYER
from microsponge.support.chronicle import Chronicle, Measure, What
from microsponge.support.game_story import DECLINE_PERCENT, curve_lines, decline_turn, report_lines, story_lines
from microsponge.support.scripted_game import play, started_game
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes.caveman.buildings import Granary, GreatCavePainting
from microsponge.themes.caveman.city import Village
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.units import Settler, Warrior
from microsponge.themes.classic.theme import Classic
from microsponge.ui_strings import (
    MSG_CHART_CITIZENS, MSG_CURVE_AFTER_OPEN, MSG_CURVE_DEFEATS, MSG_CURVE_KNEW_EVERYTHING, MSG_CURVE_NEVER_KNEW_EVERYTHING, MSG_CURVE_NO_DEFEATS, MSG_LIST_SEPARATOR, MSG_STORY_DEFEATED, MSG_STORY_FOUNDED, MSG_STORY_STALLED,
    MSG_STORY_TITLE, MSG_STORY_TOOK, MSG_STORY_UNFINISHED, MSG_STORY_WON, MSG_TALLY, MSG_TRAITS_TITLE,
)

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'scripted_game.py'
SECOND_CIVILIZATION = 2
A_SEED = 5
THREE = 3
TURNS = 25
A_TURN = 4
A_LATER_TURN = 9
A_NAME = 'Bedrock'
ONE_TURN = 1
NOT_A_NUMBER = 'seven'
FIRST_NAME = 0


def whats(chronicle):
    return [event.what for event in chronicle.get_events()]


class TestChronicle(unittest.TestCase):

    def setUp(self):
        self.game = started_caveman_game()
        self.chronicle = Chronicle(self.game)

    def test_a_city_founded_is_an_event_and_the_settler_that_built_it_is_not_lost(self):
        found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.chronicle.note(game=self.game, turn=A_TURN)
        event = self.chronicle.get_events()[0]
        self.assertEqual((event.turn, event.what, event.civilization, event.subject), (A_TURN, What.FOUNDED, FIRST_CIVILIZATION, A_NAME))
        self.assertEqual(self.chronicle.get_lost(civilization=FIRST_CIVILIZATION, kind=Settler), 0)
        self.chronicle.note(game=self.game, turn=A_LATER_TURN)
        self.assertEqual(whats(self.chronicle), [What.FOUNDED])

    def test_a_unit_that_appears_is_made_and_a_unit_that_is_gone_is_lost(self):
        _, x, y = UnitControl.tile_of(game=self.game, unit=settler_of(game=self.game, civilization=FIRST_CIVILIZATION))
        warrior = UnitControl.place(game=self.game, kind=Warrior, owner=FIRST_CIVILIZATION, world=THE_WORLD, x=x + 1, y=y)
        self.chronicle.note(game=self.game, turn=A_TURN)
        self.assertEqual((self.chronicle.get_made(civilization=FIRST_CIVILIZATION, kind=Warrior), self.chronicle.get_lost(civilization=FIRST_CIVILIZATION, kind=Warrior)), (1, 0))
        UnitControl.remove(game=self.game, unit=warrior)
        UnitControl.remove(game=self.game, unit=settler_of(game=self.game, civilization=SECOND_CIVILIZATION))
        self.chronicle.note(game=self.game, turn=A_LATER_TURN)
        self.assertEqual(self.chronicle.get_lost(civilization=FIRST_CIVILIZATION, kind=Warrior), 1)
        self.assertEqual(self.chronicle.get_lost(civilization=SECOND_CIVILIZATION, kind=Settler), 1)
        self.assertEqual(self.chronicle.get_made(civilization=SECOND_CIVILIZATION, kind=Warrior), 0)

    def test_technologies_a_war_a_world_wonder_a_city_taken_and_a_defeat_are_events_each_noted_once(self):
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.chronicle.note(game=self.game, turn=A_TURN)
        for technology in Caveman.TECHNOLOGIES:
            learn(game=self.game, civilization=SECOND_CIVILIZATION, technology=technology)
        self.game.get_civilization(SECOND_CIVILIZATION).declare_war(FIRST_CIVILIZATION)
        give_building(game=self.game, city=city, building=Granary)
        give_building(game=self.game, city=city, building=GreatCavePainting)
        self.chronicle.note(game=self.game, turn=A_TURN)
        CityControl.capture(game=self.game, city=city, by=SECOND_CIVILIZATION)
        self.game.get_civilization(FIRST_CIVILIZATION).lose()
        self.chronicle.note(game=self.game, turn=A_LATER_TURN)
        self.chronicle.note(game=self.game, turn=A_LATER_TURN)
        expected = [What.FOUNDED, What.FINISHED_WONDER, *[What.LEARNT] * len(Caveman.TECHNOLOGIES), What.KNEW_EVERYTHING, What.DECLARED_WAR, What.TOOK, What.DEFEATED]
        self.assertEqual(whats(self.chronicle), expected)
        learnt = [event.subject for event in self.chronicle.events_of(What.LEARNT)]
        self.assertEqual(learnt, [shown_name(technology) for technology in Caveman.TECHNOLOGIES])
        took = self.chronicle.events_of(What.TOOK)[0]
        self.assertEqual((took.civilization, took.other, took.subject, took.turn), (SECOND_CIVILIZATION, FIRST_CIVILIZATION, A_NAME, A_LATER_TURN))
        self.assertEqual(self.chronicle.events_of(What.FINISHED_WONDER)[0].subject, shown_name(GreatCavePainting))

    def test_a_civilization_defeated_while_bankrupt_went_bankrupt(self):
        holder = self.game.get_civilization(FIRST_CIVILIZATION)
        holder.set_bankrupt_turns(Caveman.BANKRUPTCY_TURNS)
        holder.lose()
        self.chronicle.note(game=self.game, turn=A_TURN)
        self.assertEqual(whats(self.chronicle), [What.WENT_BANKRUPT])

    def test_every_measure_is_counted_at_the_end_of_a_turn_for_the_civilizations_still_playing(self):
        found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.chronicle.count(self.game)
        self.game.get_civilization(SECOND_CIVILIZATION).lose()
        self.chronicle.count(self.game)
        self.assertEqual(self.chronicle.get_counts(civilization=FIRST_CIVILIZATION, measure=Measure.CITIES), [1, 1])
        self.assertEqual(self.chronicle.get_counts(civilization=FIRST_CIVILIZATION, measure=Measure.CITIZENS), [Village.STARTING_CITIZENS] * 2)
        self.assertEqual(self.chronicle.get_counts(civilization=FIRST_CIVILIZATION, measure=Measure.UNITS), [0, 0])
        self.assertEqual(self.chronicle.get_counts(civilization=SECOND_CIVILIZATION, measure=Measure.UNITS), [1])
        self.assertEqual(self.chronicle.get_counts(civilization=SECOND_CIVILIZATION, measure=Measure.CITIES), [0])
        self.assertEqual(self.chronicle.get_counts(civilization=FIRST_CIVILIZATION, measure=Measure.TECHNOLOGIES), [0, 0])
        self.assertEqual(len(self.chronicle.get_counts(civilization=FIRST_CIVILIZATION, measure=Measure.WEALTH)), 2)

    def test_progress_is_a_unit_a_building_or_a_city_and_the_turns_without_any_are_counted(self):
        self.assertEqual(self.chronicle.turns_without_progress(A_TURN), A_TURN)
        city = found_village(game=self.game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        self.chronicle.note(game=self.game, turn=A_TURN)
        self.assertEqual(self.chronicle.turns_without_progress(A_LATER_TURN), A_LATER_TURN - A_TURN)
        learn(game=self.game, civilization=FIRST_CIVILIZATION, technology=Caveman.TECHNOLOGIES[0])
        self.chronicle.note(game=self.game, turn=A_LATER_TURN)
        self.assertEqual(self.chronicle.turns_without_progress(A_LATER_TURN), A_LATER_TURN - A_TURN)
        give_building(game=self.game, city=city, building=Granary)
        self.chronicle.note(game=self.game, turn=A_LATER_TURN)
        self.assertEqual(self.chronicle.turns_without_progress(A_LATER_TURN), 0)


class TestScriptedGame(Refusals, unittest.TestCase):

    def test_the_computer_players_play_to_the_turn_limit_and_the_chronicle_holds_every_turn(self):
        game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
        self.assertTrue(all(holder.is_computer_played() for holder in game.get_civilizations()))
        chronicle = play(game=game, turns=TURNS)
        self.assertEqual(game.get_turn(), TURNS)
        self.assertFalse(chronicle.is_stalled())
        for civilization in chronicle.get_civilizations():
            self.assertEqual(len(chronicle.get_counts(civilization=civilization, measure=Measure.CITIZENS)), TURNS)
        self.assertEqual(len(chronicle.events_of(What.FOUNDED)), THREE)

    def test_a_game_that_reaches_its_turn_limit_says_who_was_still_playing(self):
        game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
        chronicle = play(game=game, turns=ONE_TURN)
        names = MSG_LIST_SEPARATOR.join(holder.get_name() for holder in game.get_civilizations())
        self.assertEqual(story_lines(game=game, chronicle=chronicle)[-1], MSG_STORY_UNFINISHED.format(turn=ONE_TURN, names=names))

    def test_the_same_seed_plays_the_same_game(self):
        reports = []
        for _ in range(2):
            game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
            reports.append(report_lines(game=game, chronicle=play(game=game, turns=TURNS), seed=A_SEED))
        self.assertEqual(reports[0], reports[1])

    def test_a_game_in_which_nothing_is_built_for_too_long_is_stopped_and_says_so(self):
        game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
        chronicle = play(game=game, turns=TURNS, stall_turns=ONE_TURN)
        self.assertTrue(chronicle.is_stalled())
        self.assertLess(game.get_turn(), TURNS)
        self.assertTrue(story_lines(game=game, chronicle=chronicle)[-1].startswith(MSG_STORY_STALLED.split('{turns}')[0].format(turn=game.get_turn())))

    def test_a_theme_with_no_computer_player_cannot_play_a_scripted_game(self):
        self.assertIsNone(Classic.PLAYER)
        self.assertEqual(self.refused(lambda: started_game(theme=Classic, seed=A_SEED, civilizations=THREE)), ERR_NO_PLAYER.format(theme=shown_name(Classic)))


class TestGameStory(unittest.TestCase):

    def test_a_civilization_started_to_lose_on_the_last_turn_it_was_at_its_strongest_when_it_ended_far_weaker(self):
        self.assertEqual(decline_turn([1, 3, 5, 5, 2, 0]), 3)
        self.assertEqual(decline_turn([4, 8, 3]), 1)
        self.assertIsNone(decline_turn([1, 2, 3, 4]))
        self.assertIsNone(decline_turn([10, 10 * DECLINE_PERCENT // 100]))
        self.assertEqual(decline_turn([10, 10 * DECLINE_PERCENT // 100 - 1]), 0)
        self.assertIsNone(decline_turn([]))
        self.assertIsNone(decline_turn([0, 0]))

    def test_the_story_tells_each_event_in_order_with_the_themes_word_for_a_city_and_how_the_game_ended(self):
        game = started_caveman_game()
        chronicle = Chronicle(game)
        names = [holder.get_name() for holder in game.get_civilizations()]
        city = found_village(game=game, civilization=FIRST_CIVILIZATION, name=A_NAME)
        chronicle.note(game=game, turn=A_TURN)
        CityControl.capture(game=game, city=city, by=SECOND_CIVILIZATION)
        game.get_civilization(FIRST_CIVILIZATION).lose()
        chronicle.note(game=game, turn=A_LATER_TURN)
        lines = story_lines(game=game, chronicle=chronicle)
        self.assertEqual(lines[1], MSG_STORY_FOUNDED.format(turn=A_TURN, name=names[FIRST_NAME], city=Village.NAME, subject=A_NAME))
        self.assertEqual(lines[2], MSG_STORY_TOOK.format(turn=A_LATER_TURN, name=names[1], city=Village.NAME, subject=A_NAME, other=names[FIRST_NAME]))
        self.assertEqual(lines[3], MSG_STORY_DEFEATED.format(turn=A_LATER_TURN, name=names[FIRST_NAME]))
        self.assertEqual(lines[-1], MSG_STORY_WON.format(turn=game.get_turn(), name=names[1]))
        curve = curve_lines(game=game, chronicle=chronicle)
        self.assertEqual(curve[1:], [MSG_CURVE_NEVER_KNEW_EVERYTHING, MSG_CURVE_DEFEATS.format(turns=A_LATER_TURN)])

    def test_the_curve_says_when_the_tech_tree_was_exhausted_and_how_long_the_game_went_on_after(self):
        game = started_caveman_game()
        chronicle = Chronicle(game)
        for technology in Caveman.TECHNOLOGIES:
            learn(game=game, civilization=FIRST_CIVILIZATION, technology=technology)
        chronicle.note(game=game, turn=game.get_turn())
        for _ in range(A_TURN * len(game.get_civilizations())):
            TurnControl.end_turn(game)
        name = game.get_civilization(FIRST_CIVILIZATION).get_name()
        expected = [MSG_CURVE_KNEW_EVERYTHING.format(name=name, turn=0), MSG_CURVE_AFTER_OPEN.format(turns=A_TURN), MSG_CURVE_NO_DEFEATS]
        self.assertEqual(curve_lines(game=game, chronicle=chronicle)[1:], expected)

    def test_the_report_has_the_title_the_story_the_tables_and_a_chart_of_each_measure(self):
        game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
        chronicle = play(game=game, turns=TURNS)
        lines = report_lines(game=game, chronicle=chronicle, seed=A_SEED)
        world = game.get_worlds()[0]
        self.assertEqual(lines[0], MSG_STORY_TITLE.format(theme=shown_name(Caveman), seed=A_SEED, civilizations=THREE, width=world.get_width(), height=world.get_height()))
        for expected in (MSG_TRAITS_TITLE, MSG_CHART_CITIZENS):
            self.assertIn(expected, lines)
        settlers = next(line for line in lines if line.startswith(shown_name(Settler)))
        for civilization in chronicle.get_civilizations():
            self.assertIn(MSG_TALLY.format(made=chronicle.get_made(civilization=civilization, kind=Settler), lost=chronicle.get_lost(civilization=civilization, kind=Settler)), settlers)

    def test_the_tool_prints_the_report_of_the_game_asked_for_and_refuses_a_bad_command_line(self):
        run = subprocess.run([sys.executable, str(TOOL), shown_name(Caveman), str(A_SEED), str(THREE), str(TURNS)], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
        game = started_game(theme=Caveman, seed=A_SEED, civilizations=THREE)
        self.assertEqual(run.stdout.splitlines(), report_lines(game=game, chronicle=play(game=game, turns=TURNS), seed=A_SEED))
        for arguments in ([], [shown_name(Caveman), NOT_A_NUMBER], [shown_name(Classic)]):
            with self.subTest(arguments=arguments):
                run = subprocess.run([sys.executable, str(TOOL), *arguments], capture_output=True, text=True, cwd=ROOT, check=False)
                self.assertEqual(run.returncode, FAILED)
