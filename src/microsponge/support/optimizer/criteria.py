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

"""The criteria of a good game, which the optimizer judges a set of numbers by: each a badness from 0, as good as wanted, to 1, as bad as it gets, worked out from the logs of the games played with the numbers.

The criteria are the user's and Claude's, to be reviewed from time to time (`DEV_TOOLS.md`,
"The optimizer"). Each has a weight in `Weights`, and the score of a set of numbers is the
weighted sum, which the search makes as small as it can.
"""

from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.units.unit_control import UnitControl
from microsponge.support.game_log import Key, Series

NOTHING_BAD = 0.0
ONE = 1
ALL_BAD = 1.0
LEARNT = 'learnt'
DEFEATED = 'defeated'


def clamp(value):
    return min(max(value, NOTHING_BAD), ALL_BAD)


class Criterion:
    """The names of the criteria."""

    DEFEATS = 'civilizations exterminated'
    LAST_TECHNOLOGY = 'last technology near the end'
    EVERYTHING_USED = 'everything used'
    SHORT_FIGHTS = 'short fights'
    NO_HOARDS = 'no piles of currency'
    LATE_PEAK = 'cities peak late'
    FAIRNESS = 'fairness between places in the turn order'
    TENSION = 'the lead changes hands'

    ALL = (DEFEATS, LAST_TECHNOLOGY, EVERYTHING_USED, SHORT_FIGHTS, NO_HOARDS, LATE_PEAK, FAIRNESS, TENSION)


class Targets:
    """What each criterion aims at. A theme's optimizer run may use other targets."""

    # The share of a game's turns by which the leader should know every technology, at the soonest and at the latest.
    LAST_TECHNOLOGY_SOONEST = 0.7
    LAST_TECHNOLOGY_LATEST = 0.95
    # The most attacks a fight between two units should take on average rolls.
    MOST_ATTACKS = 4
    # A civilization's bank at the end should hold no more than this many times the currency the theme's buildings cost on average.
    MOST_BANKED_BUILDINGS = 5
    # The share of a game's turns before which cities should not reach their most citizens on average.
    PEAK_SHARE = 0.6
    # How full of citizens, as a share of the most, cities are on average when they count as at their peak.
    PEAK_FULLNESS = 0.9
    # How many times the lead in strength should change hands in a game.
    LEAD_CHANGES = 2


class Weights:
    """How much each criterion counts in the score."""

    WEIGHTS = {
        Criterion.DEFEATS: 3.0,
        Criterion.LAST_TECHNOLOGY: 1.0,
        Criterion.EVERYTHING_USED: 2.0,
        Criterion.SHORT_FIGHTS: 1.0,
        Criterion.NO_HOARDS: 1.0,
        Criterion.LATE_PEAK: 1.0,
        Criterion.FAIRNESS: 1.0,
        Criterion.TENSION: 1.0,
    }


def defeats(logs):
    """Return how far the games fall short of exterminating every civilization but one, on average."""
    shortfalls = []
    for data in logs:
        civilizations = len(data[Key.CIVILIZATIONS])
        lost = len([event for event in data[Key.EVENTS] if event[Key.WHAT] == DEFEATED])
        shortfalls.append(clamp(ONE - lost / max(civilizations - ONE, ONE)))
    return sum(shortfalls) / len(shortfalls)


def last_technology(*, logs, theme):
    """Return how far from the wanted share of the turns the first civilization to know every technology knew it, on average, counting a game where none did as the end."""
    badness = []
    for data in logs:
        learnt = {}
        for event in data[Key.EVENTS]:
            if event[Key.WHAT] == LEARNT:
                learnt.setdefault(event[Key.CIVILIZATION], []).append(event[Key.TURN])
        complete = [max(turns) for turns in learnt.values() if len(turns) == len(theme.TECHNOLOGIES)]
        share = (min(complete) if complete else data[Key.TURNS]) / max(data[Key.TURNS], ONE)
        if share < Targets.LAST_TECHNOLOGY_SOONEST:
            badness.append(clamp((Targets.LAST_TECHNOLOGY_SOONEST - share) / Targets.LAST_TECHNOLOGY_SOONEST))
        else:
            badness.append(clamp((share - Targets.LAST_TECHNOLOGY_LATEST) / (ONE - Targets.LAST_TECHNOLOGY_LATEST)))
    return sum(badness) / len(badness)


def everything_used(*, logs, theme):
    """Return the share of the theme's units, buildings and technologies that no game used."""
    made = {unit[Key.KIND] for data in logs for unit in data[Key.UNITS]}
    built = {entry[Key.BUILDING] for data in logs for entry in data[Key.BUILT]}
    learnt = {event[Key.SUBJECT] for data in logs for event in data[Key.EVENTS] if event[Key.WHAT] == LEARNT}
    kinds = [(kind, made) for kind in theme.UNITS] + [(kind, built) for kind in theme.BUILDINGS] + [(kind, learnt) for kind in theme.TECHNOLOGIES]
    return len([kind for kind, used in kinds if shown_name(kind) not in used]) / max(len(kinds), ONE)


def short_fights(theme):
    """Return the share of pairs of units, among those that can hit each other, where a fight takes more than the most attacks wanted on average rolls."""
    pairs = [UnitControl.attacks_to_kill(theme=theme, attacker=attacker, defender=defender) for attacker in theme.UNITS for defender in theme.UNITS]
    counted = [attacks for attacks in pairs if attacks is not None]
    return len([attacks for attacks in counted if attacks > Targets.MOST_ATTACKS]) / max(len(counted), ONE)


def no_hoards(*, logs, theme):
    """Return how far the civilizations' banks at the end go past what the theme's buildings cost several times over, on average, as a share of that."""
    primary = theme.PRIMARY_RESOURCE
    costs = [kind.COST.get(primary, 0) for kind in theme.BUILDINGS]
    limit = Targets.MOST_BANKED_BUILDINGS * max(sum(costs) / max(len(costs), ONE), ONE)
    banks = [counts[-1] for data in logs for counts in data[Key.BANKS].get(shown_name(primary), {}).values() if counts]
    return clamp(sum(banks) / max(len(banks), ONE) / limit - ONE) if banks else NOTHING_BAD


def late_peak(*, logs, theme):
    """Return how far before the wanted share of the turns the cities of a civilization are, on average, at their peak of citizens."""
    badness = []
    full = Targets.PEAK_FULLNESS * theme.CITY.MAX_CITIZENS
    for data in logs:
        for civilization in data[Key.SERIES][Series.CITIES]:
            cities = data[Key.SERIES][Series.CITIES][civilization]
            citizens = data[Key.SERIES][Series.CITIZENS][civilization]
            peak = next((turn for turn, (count, people) in enumerate(zip(cities, citizens)) if count and people / count >= full), data[Key.TURNS])
            share = peak / max(data[Key.TURNS], ONE)
            badness.append(clamp((Targets.PEAK_SHARE - share) / Targets.PEAK_SHARE))
    return sum(badness) / max(len(badness), ONE)


def winner_of(data):
    """Return the civilization a log names as the winner: the only one left, or the highest score among those left."""
    left = [entry[Key.ID] for entry in data[Key.CIVILIZATIONS] if not entry[Key.LOST]]
    scores = data[Key.SERIES][Series.SCORE]
    return max(left, key=lambda civilization: scores[str(civilization)][-1] if scores[str(civilization)] else 0, default=None)


def fairness(logs):
    """Return how much more often than an even share one place in the turn order won, as a share of the most it could."""
    wins = {}
    for data in logs:
        winner = winner_of(data)
        if winner is not None:
            wins[winner] = wins.get(winner, 0) + 1
    places = max((len(data[Key.CIVILIZATIONS]) for data in logs), default=ONE)
    games = sum(wins.values())
    if not games or places <= ONE:
        return NOTHING_BAD
    even = ONE / places
    return clamp((max(wins.values()) / games - even) / (ONE - even))


def tension(logs):
    """Return how far the games fall short of the lead in strength changing hands as often as wanted, on average."""
    badness = []
    for data in logs:
        strength = data[Key.SERIES][Series.STRENGTH]
        turns = max((len(counts) for counts in strength.values()), default=0)
        leaders = []
        for turn in range(turns):
            alive = {civilization: counts[turn] for civilization, counts in strength.items() if turn < len(counts)}
            leaders.append(max(alive, key=alive.get))
        changes = len([turn for turn in range(ONE, len(leaders)) if leaders[turn] != leaders[turn - ONE]])
        badness.append(clamp(ONE - changes / Targets.LEAD_CHANGES))
    return sum(badness) / max(len(badness), ONE)


def badness(*, logs, theme):
    """Return the badness of every criterion for the logs of some games of a theme."""
    return {
        Criterion.DEFEATS: defeats(logs),
        Criterion.LAST_TECHNOLOGY: last_technology(logs=logs, theme=theme),
        Criterion.EVERYTHING_USED: everything_used(logs=logs, theme=theme),
        Criterion.SHORT_FIGHTS: short_fights(theme),
        Criterion.NO_HOARDS: no_hoards(logs=logs, theme=theme),
        Criterion.LATE_PEAK: late_peak(logs=logs, theme=theme),
        Criterion.FAIRNESS: fairness(logs),
        Criterion.TENSION: tension(logs),
    }


def score(found):
    """Return the score of some criteria's badness: their weighted sum, which the search makes as small as it can."""
    return sum(Weights.WEIGHTS[criterion] * value for criterion, value in found.items())
