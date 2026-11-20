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

"""The effectiveness report: the notes on units, buildings, technologies and resources that do nothing or too little, its tables, and its tool."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from later_caveman import later_caveman
from microsponge.engine.kinds.building import Building
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import Resource
from microsponge.engine.kinds.technology import Technology
from microsponge.engine.units.combat import Tally
from microsponge.support.effectiveness import LOSSES_PER_KILL, all_notes, is_fighter, report_lines, unit_notes
from microsponge.support.game_log import Key, write_log
from microsponge.support.optimizer.judge import played_as_is
from microsponge.themes.caveman.theme import Caveman
from microsponge.ui_strings import (
    MSG_EFFECTIVENESS_BUILDINGS_TITLE, MSG_EFFECTIVENESS_RESOURCES_TITLE, MSG_EFFECTIVENESS_TECHNOLOGIES_TITLE, MSG_EFFECTIVENESS_UNITS_TITLE,
    MSG_NOTE_DOES_NOTHING, MSG_NOTE_LOSES_MORE, MSG_NOTE_NEVER_ATTACKED, MSG_NOTE_NEVER_BUILT, MSG_NOTE_NEVER_LEARNT, MSG_NOTE_NEVER_MADE, MSG_NOTE_NOTHING_GIVES,
    MSG_NOTE_NOTHING_USES, MSG_NOTE_RARELY_MADE,
)

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / 'tools' / 'effectiveness_report.py'
SUCCEEDED = 0
FAILED = 1
SHORT_TURNS = 8
TWO_CIVILIZATIONS = 2
SEED = 1
KILLS = 1
LOG_NAME = 'game.json'
NOT_A_THEME = 'no such theme'
FIRST_CIVILIZATION = 1


class Shed(Building):
    """A building that does nothing and that nothing requires."""

    COST = {Caveman.PRIMARY_RESOURCE: 10}


class Navel(Technology):
    """A technology that allows nothing and gives nothing."""

    RESEARCH = 10


class Lint(Resource):
    """A resource that nothing gives and nothing uses."""


IDLE_CAVEMAN = later_caveman({Category.BUILDINGS: (*Caveman.BUILDINGS, Shed), Category.TECHNOLOGIES: (*Caveman.TECHNOLOGIES, Navel), Category.RESOURCES: (*Caveman.RESOURCES, Lint)})


def empty_log():
    """Return a log of a game in which nothing was made, built or learnt."""
    return {Key.CIVILIZATIONS: [], Key.UNITS: [], Key.BUILT: [], Key.EVENTS: []}


def log_of_fights(*, kind, made, attacks, kills, losses):
    """Return a log in which one civilization made units of a kind, which attacked, killed and were lost defending in the field so many times."""
    tallies = {Tally.ATTACKS: {shown_name(kind): attacks}, Tally.KILLS: {shown_name(kind): kills}, Tally.LOST_DEFENDING_FIELD: {shown_name(kind): losses}}
    return {**empty_log(), Key.CIVILIZATIONS: [{Key.ID: FIRST_CIVILIZATION, Key.TALLIES: tallies}], Key.UNITS: [{Key.KIND: shown_name(kind)}] * made}


class TestNotes(unittest.TestCase):

    def test_with_no_games_played_everything_is_never_made_built_or_learnt(self):
        notes = dict(all_notes(theme=Caveman, logs=[empty_log()]))
        for kind in Caveman.UNITS:
            self.assertEqual(notes[kind], [MSG_NOTE_NEVER_MADE])
        for kind in Caveman.BUILDINGS:
            self.assertIn(MSG_NOTE_NEVER_BUILT, notes[kind])
        for kind in Caveman.TECHNOLOGIES:
            self.assertIn(MSG_NOTE_NEVER_LEARNT, notes[kind])

    def test_a_building_a_technology_and_a_resource_that_do_nothing_are_noted(self):
        notes = dict(all_notes(theme=IDLE_CAVEMAN, logs=[empty_log()]))
        self.assertIn(MSG_NOTE_DOES_NOTHING, notes[Shed])
        self.assertIn(MSG_NOTE_DOES_NOTHING, notes[Navel])
        self.assertEqual(notes[Lint], [MSG_NOTE_NOTHING_USES, MSG_NOTE_NOTHING_GIVES])
        for kind in Caveman.BUILDINGS + Caveman.TECHNOLOGIES:
            self.assertNotIn(MSG_NOTE_DOES_NOTHING, notes.get(kind, []))

    def test_a_fighter_that_never_attacks_or_loses_more_than_it_kills_is_noted_and_one_made_in_few_games_too(self):
        fighter = next(kind for kind in Caveman.UNITS if is_fighter(kind))
        self.assertEqual(unit_notes(kind=fighter, logs=[log_of_fights(kind=fighter, made=1, attacks=0, kills=0, losses=0)]), [MSG_NOTE_NEVER_ATTACKED])
        losing = log_of_fights(kind=fighter, made=1, attacks=1, kills=KILLS, losses=LOSSES_PER_KILL * KILLS + 1)
        self.assertEqual(unit_notes(kind=fighter, logs=[losing]), [MSG_NOTE_LOSES_MORE])
        even = log_of_fights(kind=fighter, made=1, attacks=1, kills=KILLS, losses=LOSSES_PER_KILL * KILLS)
        self.assertEqual(unit_notes(kind=fighter, logs=[even]), [])
        self.assertEqual(unit_notes(kind=fighter, logs=[even, empty_log(), empty_log()]), [MSG_NOTE_RARELY_MADE])


class TestReport(unittest.TestCase):

    def test_the_report_of_a_played_game_has_a_table_of_each_category_with_a_row_for_each_kind(self):
        logs = [played_as_is(theme=Caveman, seed=SEED, civilizations=TWO_CIVILIZATIONS, turns=SHORT_TURNS)]
        lines = report_lines(theme=Caveman, logs=logs)
        for title in (MSG_EFFECTIVENESS_UNITS_TITLE, MSG_EFFECTIVENESS_BUILDINGS_TITLE, MSG_EFFECTIVENESS_TECHNOLOGIES_TITLE, MSG_EFFECTIVENESS_RESOURCES_TITLE):
            self.assertIn(title, lines)
        for kind in (*Caveman.UNITS, *Caveman.BUILDINGS, *Caveman.TECHNOLOGIES, *Caveman.RESOURCES):
            self.assertTrue(any(line.startswith(shown_name(kind)) for line in lines))

    def test_the_tool_reads_the_logs_named_and_refuses_an_unknown_theme(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / LOG_NAME
            write_log(data=played_as_is(theme=Caveman, seed=SEED, civilizations=TWO_CIVILIZATIONS, turns=SHORT_TURNS), path=path)
            run = subprocess.run([sys.executable, str(TOOL), shown_name(Caveman), str(path)], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(run.returncode, SUCCEEDED)
        self.assertIn(MSG_EFFECTIVENESS_UNITS_TITLE, run.stdout)
        refused = subprocess.run([sys.executable, str(TOOL), NOT_A_THEME], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(refused.returncode, FAILED)
