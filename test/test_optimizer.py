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

"""The optimizer: the depth of kinds in the tech tree, the numbers it searches and applying them to a theme, the criteria, the search, the judge that plays games side by side, the report and the tool."""

import subprocess
import sys
import unittest
from pathlib import Path
from random import Random

from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.technology import Technology
from microsponge.support.optimizer.criteria import ALL_BAD, NOTHING_BAD, Criterion, Weights, badness, score
from microsponge.support.optimizer.depth import NO_DEPTH, ONE_DEEPER, TreeDepth
from microsponge.support.optimizer.judge import Judge, played_as_is
from microsponge.support.optimizer.parameters import PARAMETERS, Name, Parameter, Tuning, scaled
from microsponge.support.optimizer.report import changed_constants, report_lines
from microsponge.support.optimizer.run import optimize, seeds
from microsponge.support.optimizer.search import RESTART_AFTER, Anneal
from microsponge.themes.caveman.theme import Caveman
from microsponge.ui_strings import MSG_OPTIMIZER_CHANGES_TITLE, MSG_OPTIMIZER_CRITERIA_TITLE, MSG_OPTIMIZER_NUMBERS_TITLE

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / 'tools' / 'optimize.py'
FAILED = 1
SHORT_TURNS = 8
TWO_CIVILIZATIONS = 2
ONE_PROCESS = 1
STEPS = 40
RANDOM_SEED = 3
NOT_A_NUMBER = 'many'
TARGET_SHARE = 0.25
# With one seed of each set and no time: the theme as it is, the starting numbers and the best on the seed searched, and the theme as it is and the best on the seed held out.
GAMES_WITH_NO_TIME = 5


def constants_of(theme):
    """Return every constant the optimizer can change, as it reads now, to compare before and after."""
    return [(kind, name, repr(getattr(kind, name))) for kind, name, _ in Tuning.changes(theme=theme, values=Tuning.start(theme))]


def distance_from_target(values):
    """A cheap score for the search: how far each number is from a quarter of its range, added up."""
    return sum(abs(values[parameter.name] - (parameter.low + TARGET_SHARE * (parameter.high - parameter.low))) / (parameter.high - parameter.low) for parameter in PARAMETERS)


class TestTreeDepth(unittest.TestCase):

    def test_a_technology_is_one_deeper_than_the_deepest_technology_it_requires(self):
        for technology in Caveman.TECHNOLOGIES:
            required = [TreeDepth.of_technology(kind) for kind in technology.REQUIRES if issubclass(kind, Technology)]
            self.assertEqual(TreeDepth.of_technology(technology), ONE_DEEPER + max(required, default=NO_DEPTH))

    def test_a_unit_or_building_is_as_deep_as_what_it_requires_and_one_deeper_for_a_building_on_the_way(self):
        for kind in (*Caveman.UNITS, *Caveman.BUILDINGS):
            depth = TreeDepth.of_kind(kind)
            for required in kind.REQUIRES:
                if issubclass(required, Technology):
                    self.assertGreaterEqual(depth, TreeDepth.of_technology(required))
                elif required in Caveman.BUILDINGS:
                    self.assertGreaterEqual(depth, TreeDepth.of_kind(required) + ONE_DEEPER)
            if not kind.REQUIRES:
                self.assertEqual(depth, NO_DEPTH)


class TestTuning(unittest.TestCase):

    def test_a_number_is_kept_within_its_bounds_and_whole_numbers_are_rounded(self):
        parameter = Parameter(name=Name.STORE_FOOD, low=5, high=40, whole=True)
        self.assertEqual(parameter.clipped(1), parameter.low)
        self.assertEqual(parameter.clipped(99), parameter.high)
        self.assertEqual(parameter.clipped(12.6), 13)

    def test_the_starting_numbers_are_within_bounds_and_later_kinds_cost_at_least_as_much(self):
        values = Tuning.start(Caveman)
        for parameter in PARAMETERS:
            self.assertTrue(parameter.low <= values[parameter.name] <= parameter.high)
        self.assertGreaterEqual(scaled(base=values[Name.UNIT_COST], growth=values[Name.UNIT_GROWTH], depth=ONE_DEEPER), scaled(base=values[Name.UNIT_COST], growth=values[Name.UNIT_GROWTH], depth=NO_DEPTH))

    def test_applied_numbers_change_the_theme_inside_the_block_and_every_constant_is_put_back_after_even_on_an_error(self):
        before = constants_of(Caveman)
        values = {parameter.name: parameter.high for parameter in PARAMETERS}
        primary = Caveman.PRIMARY_RESOURCE
        with Tuning.applied(theme=Caveman, values=values):
            for kind in Caveman.UNITS:
                self.assertEqual(kind.COST[primary], Tuning.currency_cost(theme=Caveman, kind=kind, values=values))
            for technology in Caveman.TECHNOLOGIES:
                self.assertEqual(technology.RESEARCH, Tuning.research(technology=technology, values=values))
            self.assertEqual(Caveman.CITY.STORE_FOOD, values[Name.STORE_FOOD])
        self.assertEqual(constants_of(Caveman), before)
        with self.assertRaises(KeyError):
            with Tuning.applied(theme=Caveman, values=values):
                raise KeyError(Name.STORE_FOOD)
        self.assertEqual(constants_of(Caveman), before)

    def test_a_world_wonder_costs_the_wonder_factor_times_a_building_as_deep(self):
        values = Tuning.start(Caveman)
        for kind in Caveman.BUILDINGS:
            building = scaled(base=values[Name.BUILDING_COST], growth=values[Name.BUILDING_GROWTH], depth=TreeDepth.of_kind(kind))
            expected = round(building * values[Name.WONDER_FACTOR]) if issubclass(kind, Wonder) else building
            self.assertEqual(Tuning.currency_cost(theme=Caveman, kind=kind, values=values), expected)


class TestSearch(unittest.TestCase):

    def test_the_search_finds_better_numbers_within_bounds_in_the_steps_it_is_given(self):
        start = Tuning.start(Caveman)
        result = Anneal.search(start=start, parameters=PARAMETERS, evaluate=distance_from_target, random=Random(RANDOM_SEED), steps=STEPS)
        self.assertEqual(len(result.steps), STEPS)
        self.assertLess(result.best_score, result.start_score)
        self.assertEqual(result.best_score, distance_from_target(result.best))
        for parameter in PARAMETERS:
            self.assertTrue(parameter.low <= result.best[parameter.name] <= parameter.high)

    def test_the_search_starts_again_from_the_best_after_steps_with_no_new_best(self):
        result = Anneal.search(start=Tuning.start(Caveman), parameters=PARAMETERS, evaluate=lambda values: ALL_BAD, random=Random(RANDOM_SEED), steps=STEPS)
        self.assertEqual(result.restarts, STEPS // RESTART_AFTER)

    def test_a_better_step_is_always_kept_and_a_worse_one_never_once_cold(self):
        random = Random(RANDOM_SEED)
        self.assertTrue(Anneal.accepts(worse_by=-ALL_BAD, temperature=NOTHING_BAD, random=random))
        self.assertFalse(Anneal.accepts(worse_by=ALL_BAD, temperature=NOTHING_BAD, random=random))

    def test_the_search_stops_when_its_time_is_up(self):
        result = Anneal.search(start=Tuning.start(Caveman), parameters=PARAMETERS, evaluate=distance_from_target, random=Random(RANDOM_SEED), steps=STEPS, seconds=NOTHING_BAD)
        self.assertEqual(result.steps, [])
        self.assertEqual(result.best, result.start)


class TestCriteria(unittest.TestCase):

    def test_every_criterion_is_a_badness_from_0_to_1_and_the_score_is_their_weighted_sum(self):
        logs = [played_as_is(theme=Caveman, seed=seed, civilizations=TWO_CIVILIZATIONS, turns=SHORT_TURNS) for seed in seeds(searched=TWO_CIVILIZATIONS, held_out=0)[0]]
        found = badness(logs=logs, theme=Caveman)
        self.assertEqual(set(found), set(Criterion.ALL))
        for value in found.values():
            self.assertTrue(NOTHING_BAD <= value <= ALL_BAD)
        self.assertEqual(score(found), sum(Weights.WEIGHTS[criterion] * found[criterion] for criterion in Criterion.ALL))
        self.assertEqual(found[Criterion.DEFEATS], ALL_BAD)


class TestRunning(unittest.TestCase):

    def test_the_judge_plays_a_game_on_each_seed_in_worker_processes_and_leaves_the_theme_as_it_was(self):
        before = constants_of(Caveman)
        judge = Judge(theme=Caveman, civilizations=TWO_CIVILIZATIONS, turns=SHORT_TURNS, processes=ONE_PROCESS)
        try:
            searched, _ = seeds(searched=TWO_CIVILIZATIONS, held_out=0)
            logs = judge.logs(values=Tuning.start(Caveman), seeds=searched)
            self.assertEqual(len(logs), len(searched))
            self.assertEqual(judge.get_played_games(), len(searched))
        finally:
            judge.close()
        self.assertEqual(constants_of(Caveman), before)

    def test_a_run_with_no_time_judges_the_theme_as_it_is_on_both_sets_of_seeds_and_reports(self):
        searched, held_out = seeds(searched=ONE_PROCESS, held_out=ONE_PROCESS)
        self.assertFalse(set(searched) & set(held_out))
        found = optimize(theme=Caveman, seconds=0, searched=ONE_PROCESS, held_out=ONE_PROCESS, civilizations=TWO_CIVILIZATIONS, turns=SHORT_TURNS, processes=ONE_PROCESS, random_seed=RANDOM_SEED)
        self.assertEqual(found.result.best, Tuning.start(Caveman))
        self.assertEqual(found.games, GAMES_WITH_NO_TIME)
        lines = report_lines(theme=Caveman, found=found)
        for title in (MSG_OPTIMIZER_CRITERIA_TITLE, MSG_OPTIMIZER_NUMBERS_TITLE, MSG_OPTIMIZER_CHANGES_TITLE):
            self.assertIn(title, lines)
        for kind, name, now, value in changed_constants(theme=Caveman, values=found.result.best):
            self.assertEqual(getattr(kind, name), now)
            self.assertNotEqual(now, value)

    def test_the_tool_refuses_a_command_line_it_cannot_read(self):
        run = subprocess.run([sys.executable, str(TOOL), Caveman.__name__.lower(), NOT_A_NUMBER], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(run.returncode, FAILED)
