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

"""Running the optimizer from start to end: the theme as it is, the search, and the check of the best numbers on seeds held out."""

from dataclasses import dataclass
from random import Random
from time import monotonic

from microsponge.support.optimizer.judge import Judge
from microsponge.support.optimizer.parameters import PARAMETERS, Tuning
from microsponge.support.optimizer.search import Anneal, Result

# Far more steps than a run has time for, so that the time is what stops the search.
MOST_STEPS = 100000
FIRST_SEED = 1


@dataclass(slots=True, kw_only=True)
class Found:
    """What a run of the optimizer found: the search's Result, and the badness of every criterion for the theme as it is and for the best numbers, on the seeds searched and on those held out."""

    result: Result
    now_searched: dict
    best_searched: dict
    now_held_out: dict
    best_held_out: dict
    games: int
    seconds: float
    random_seed: int


def seeds(*, searched, held_out):
    """Return (the seeds searched, the seeds held out): the first from 1, and the rest after them."""
    search = list(range(FIRST_SEED, FIRST_SEED + searched))
    return search, list(range(FIRST_SEED + searched, FIRST_SEED + searched + held_out))


def optimize(*, theme, seconds, searched, held_out, civilizations, turns, processes, random_seed, on_step=None):
    """Return what a run of the optimizer Found for a theme in about a number of seconds, leaving the theme as it was."""
    began = monotonic()
    search_seeds, held_out_seeds = seeds(searched=searched, held_out=held_out)
    judge = Judge(theme=theme, civilizations=civilizations, turns=turns, processes=processes)
    try:
        now_searched = judge.badness(values=None, seeds=search_seeds)
        result = Anneal.search(start=Tuning.start(theme), parameters=PARAMETERS, evaluate=judge.scorer(search_seeds), random=Random(random_seed), steps=MOST_STEPS, seconds=max(seconds - (monotonic() - began), 0), on_step=on_step)
        best_searched = judge.badness(values=result.best, seeds=search_seeds)
        now_held_out = judge.badness(values=None, seeds=held_out_seeds)
        best_held_out = judge.badness(values=result.best, seeds=held_out_seeds)
        games = judge.get_played_games()
    finally:
        judge.close()
    return Found(result=result, now_searched=now_searched, best_searched=best_searched, now_held_out=now_held_out, best_held_out=best_held_out, games=games, seconds=monotonic() - began, random_seed=random_seed)
