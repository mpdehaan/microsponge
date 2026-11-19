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

"""Balance tests of caveman: the computer players play a few games, and every building, world wonder, technology and kind of unit of caveman should be used in at least one of them.

These tests are about caveman's balance, not about the engine, and a failure is a subject for
discussion with the user rather than a bug: it names what no computer player used, so that
the user and Claude can talk about why. They live apart from the suite, which discovery does
not reach in this folder, so that they never stop a commit. Run them with `make balance-test`
(`.claude/TESTING.md`, "Balance tests").
"""

import unittest

from microsponge.engine.kinds.kind import shown_name
from microsponge.support.game_log import GameLog, Key
from microsponge.support.scripted_game import play, started_game
from microsponge.themes.caveman.theme import Caveman

SEEDS = range(1, 7)
CIVILIZATIONS = 3
TURNS = 200
LEARNT = 'learnt'
# What a failure says: what no computer player used, for discussion.
UNUSED = 'no computer player used these in {games} games of {turns} turns: {kinds}'
SEPARATOR = ', '


def played_logs():
    """Return the data of the log of each game the computer players play, one for each seed."""
    logs = []
    for seed in SEEDS:
        game = started_game(theme=Caveman, seed=seed, civilizations=CIVILIZATIONS)
        log = GameLog(game)
        chronicle = play(game=game, turns=TURNS, log=log)
        logs.append(log.as_data(game=game, chronicle=chronicle, seed=seed))
    return logs


def unused(*, kinds, used):
    """Return the names of the kinds no game used."""
    return [shown_name(kind) for kind in kinds if shown_name(kind) not in used]


class TestEverythingInCavemanIsUsed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.logs = played_logs()

    def assert_all_used(self, *, kinds, used):
        missing = unused(kinds=kinds, used=used)
        self.assertEqual(missing, [], UNUSED.format(games=len(SEEDS), turns=TURNS, kinds=SEPARATOR.join(missing)))

    def test_every_building_and_world_wonder_is_built(self):
        built = {entry[Key.BUILDING] for data in self.logs for entry in data[Key.BUILT]}
        self.assert_all_used(kinds=Caveman.BUILDINGS, used=built)

    def test_every_technology_is_learnt(self):
        learnt = {event[Key.SUBJECT] for data in self.logs for event in data[Key.EVENTS] if event[Key.WHAT] == LEARNT}
        self.assert_all_used(kinds=Caveman.TECHNOLOGIES, used=learnt)

    def test_every_kind_of_unit_is_made(self):
        made = {unit[Key.KIND] for data in self.logs for unit in data[Key.UNITS]}
        self.assert_all_used(kinds=Caveman.UNITS, used=made)
