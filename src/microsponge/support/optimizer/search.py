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

"""The search the optimizer makes: simulated annealing with restarts over the numbers in `parameters.py`.

The search takes a step by moving one or two numbers a little, keeps the step when the score
is better, and sometimes keeps a worse one on purpose, more often early than late, so that it
can climb out of a local best. After a run of steps with no new best, it restarts from the best
found. It stops after a set number of steps or a set time, whichever comes first. What a score
is comes from outside, so that the tests can search a cheap function.
"""

from dataclasses import dataclass, field
from math import exp
from time import monotonic

# How far one step moves a number at most, as a share of the number's range, at the start of the search.
STEP_SHARE = 0.15
# The least the step shrinks to by the end of the search, as a share of where it started.
LEAST_STEP = 0.2
# The temperature at the start: how much worse a step can be and still be kept, often enough.
START_TEMPERATURE = 0.5
# Steps with no new best before the search starts again from the best.
RESTART_AFTER = 12
# The chance that a step moves two numbers rather than one.
TWO_NUMBERS = 0.3
ONE = 1
NO_TIME = 0.0


@dataclass(slots=True, kw_only=True)
class Step:
    """One set of numbers the search tried, with its score and whether it was kept."""

    number: int
    values: dict
    score: float
    kept: bool
    best: bool


@dataclass(slots=True, kw_only=True)
class Result:
    """What a search found: the numbers it started from and their score, the best numbers and their score, and every step."""

    start: dict
    start_score: float
    best: dict
    best_score: float
    steps: list = field(default_factory=list)
    restarts: int = 0


class Anneal:
    """Static: simulated annealing with restarts over a set of parameters."""

    __slots__ = ()

    @staticmethod
    def neighbor(*, values, parameters, random, share):
        """Return a copy of some numbers with one or two of them moved by up to a share of their range."""
        moved = dict(values)
        count = 2 if random.random() < TWO_NUMBERS and len(parameters) > ONE else ONE
        for parameter in random.sample(list(parameters), count):
            span = parameter.high - parameter.low
            moved[parameter.name] = parameter.clipped(values[parameter.name] + random.uniform(-share, share) * span)
        return moved

    @staticmethod
    def accepts(*, worse_by, temperature, random):
        """Return whether to keep a step that is worse by some amount, at a temperature."""
        if worse_by <= 0:
            return True
        return temperature > 0 and random.random() < exp(-worse_by / temperature)

    @staticmethod
    def search(*, start, parameters, evaluate, random, steps, seconds=None, on_step=None):
        """Return the Result of searching from some numbers, scoring each set with evaluate(values), for at most a number of steps and, when given, a number of seconds."""
        began = monotonic()
        current = dict(start)
        current_score = evaluate(current)
        result = Result(start=dict(start), start_score=current_score, best=dict(start), best_score=current_score)
        since_best = 0
        for number in range(ONE, steps + ONE):
            elapsed = monotonic() - began
            if seconds is not None and elapsed >= seconds:
                break
            progress = max(number / steps, elapsed / seconds if seconds else NO_TIME)
            share = STEP_SHARE * (ONE - (ONE - LEAST_STEP) * progress)
            candidate = Anneal.neighbor(values=current, parameters=parameters, random=random, share=share)
            score = evaluate(candidate)
            kept = Anneal.accepts(worse_by=score - current_score, temperature=START_TEMPERATURE * (ONE - progress), random=random)
            best = score < result.best_score
            if kept:
                current, current_score = candidate, score
            if best:
                result.best, result.best_score = dict(candidate), score
                since_best = 0
            else:
                since_best += ONE
            if since_best >= RESTART_AFTER:
                current, current_score = dict(result.best), result.best_score
                result.restarts += ONE
                since_best = 0
            step = Step(number=number, values=candidate, score=score, kept=kept, best=best)
            result.steps.append(step)
            if on_step is not None:
                on_step(step)
        return result
