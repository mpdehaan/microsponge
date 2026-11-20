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

"""Judging a set of the optimizer's numbers: playing games of a theme with the numbers applied, side by side in worker processes, and scoring the logs against the criteria."""

import json
from multiprocessing import get_context

from microsponge.engine.kinds.kind import shown_name
from microsponge.support.game_log import GameLog
from microsponge.support.optimizer.criteria import badness, score
from microsponge.support.optimizer.parameters import Tuning
from microsponge.support.scripted_game import play, started_game
from microsponge.support.theme_tools import theme_called

# Worker processes start fresh, so that a theme changed in one never leaks into another.
START_METHOD = 'spawn'


def played(job):
    """Return the log of one game, as data read back from JSON, from a job of (the theme's name, the numbers or None for the theme as it is, the seed, how many civilizations and how many turns). Runs in a worker process."""
    name, values, seed, civilizations, turns = job
    theme = theme_called(name)
    if values is None:
        return played_as_is(theme=theme, seed=seed, civilizations=civilizations, turns=turns)
    with Tuning.applied(theme=theme, values=values):
        return played_as_is(theme=theme, seed=seed, civilizations=civilizations, turns=turns)


def played_as_is(*, theme, seed, civilizations, turns):
    game = started_game(theme=theme, seed=seed, civilizations=civilizations)
    log = GameLog(game)
    chronicle = play(game=game, turns=turns, log=log)
    return json.loads(json.dumps(log.as_data(game=game, chronicle=chronicle, seed=seed)))


class Judge:
    """Plays the games that judge a set of numbers for a theme, on given seeds, in a pool of worker processes it owns until closed."""

    __slots__ = ('theme', 'civilizations', 'turns', 'pool', 'played_games')

    def __init__(self, *, theme, civilizations, turns, processes):
        self.theme = theme
        self.civilizations = civilizations
        self.turns = turns
        self.pool = get_context(START_METHOD).Pool(processes=processes)
        self.played_games = 0

    def close(self):
        self.pool.close()
        self.pool.join()

    def get_played_games(self):
        return self.played_games

    def logs(self, *, values, seeds):
        """Return the logs of the games played with some numbers, None for the theme as it is, one game on each seed."""
        jobs = [(shown_name(self.theme), values, seed, self.civilizations, self.turns) for seed in seeds]
        self.played_games += len(jobs)
        return self.pool.map(played, jobs)

    def badness(self, *, values, seeds):
        """Return the badness of every criterion for the games played with some numbers on some seeds; the criteria that read the theme read it with the numbers applied."""
        logs = self.logs(values=values, seeds=seeds)
        if values is None:
            return badness(logs=logs, theme=self.theme)
        with Tuning.applied(theme=self.theme, values=values):
            return badness(logs=logs, theme=self.theme)

    def scorer(self, seeds):
        """Return a function that scores a set of numbers by the games played on some seeds, for the search."""
        return lambda values: score(self.badness(values=values, seeds=seeds))
