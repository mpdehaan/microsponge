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

"""The detailed log of a scripted game: what became of every unit, every city and every civilization, turn by turn, as data that is written to a JSON file.

The log watches a game only through its getters, beside the chronicle (`chronicle.py`), which
keeps the events. The log does not hold every move: for each unit the log keeps totals, like
how many tiles the unit moved and how many turns the unit spent inside a city, and for each
civilization one number a turn of each thing worth a chart. `game_log_report.py` reads the
file back and answers questions about the game, and `game_log_page.py` draws the charts.
"""

import json

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.control_points import Command, Policy
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.players.knowledge import distance
from microsponge.engine.players.traits import TRAITS
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.support.chronicle import FIRST_CIVILIZATION, Measure, What

# A unit that is still alive when the log is written has no turn on which the unit was gone.
NOT_GONE = -1
FILE_ENCODING = 'utf-8'
WRITE_MODE = 'w'
READ_MODE = 'r'


class Key:
    """The names of what a log file holds."""

    THEME = 'theme'
    SEED = 'seed'
    WIDTH = 'width'
    HEIGHT = 'height'
    TURNS = 'turns'
    CITY_WORD = 'city_word'
    RESOURCE_WORD = 'resource_word'
    CIVILIZATIONS = 'civilizations'
    EVENTS = 'events'
    SERIES = 'series'
    UNITS = 'units'
    CITIES = 'cities'
    ID = 'id'
    NAME = 'name'
    LOST = 'lost'
    TRAITS = 'traits'
    TURN = 'turn'
    WHAT = 'what'
    CIVILIZATION = 'civilization'
    SUBJECT = 'subject'
    OTHER = 'other'
    KIND = 'kind'
    MILITARY = 'military'
    MADE = 'made'
    GONE = 'gone'
    ENDING = 'ending'
    FIRST_LEVEL = 'first_level'
    LEVEL = 'level'
    MOVED = 'moved'
    LIVED = 'lived'
    INSIDE = 'inside'
    FOUNDER = 'founder'
    FOUNDED = 'founded'
    OWNER = 'owner'
    CITIZENS = 'citizens'
    BUILDINGS = 'buildings'
    PLACE = 'place'
    SETTLER = 'settler'


class Ending:
    """What became of a unit."""

    ALIVE = 'alive'
    LOST = 'lost'
    SETTLED = 'settled'


class Series:
    """The names of the numbers a log keeps for each civilization at the end of each turn."""

    CITIES = 'cities'
    CITIZENS = 'citizens'
    WEALTH = 'wealth'
    UNITS = 'units'
    TECHNOLOGIES = 'technologies'
    POLICY = 'policy'
    POLICY_TAKEN = 'policy_taken'
    COMMAND = 'command'
    COMMAND_TAKEN = 'command_taken'
    INSIDE = 'units_inside'
    LEVEL = 'average_level'
    BUILDINGS = 'buildings'
    MILITARY_SCORE = 'military_score'
    SCIENCE_SCORE = 'science_score'
    POPULATION_SCORE = 'population_score'
    DEVELOPMENT_SCORE = 'development_score'
    SCORE = 'score'
    HIT_POINTS = 'military_hit_points'
    STRENGTH = 'strength'

    OWN = (HIT_POINTS, STRENGTH, POLICY, POLICY_TAKEN, COMMAND, COMMAND_TAKEN, INSIDE, LEVEL, BUILDINGS, MILITARY_SCORE, SCIENCE_SCORE, POPULATION_SCORE, DEVELOPMENT_SCORE, SCORE)


# What the chronicle counts, by the name the log gives each.
MEASURES = {
    Series.CITIES: Measure.CITIES,
    Series.CITIZENS: Measure.CITIZENS,
    Series.WEALTH: Measure.WEALTH,
    Series.UNITS: Measure.UNITS,
    Series.TECHNOLOGIES: Measure.TECHNOLOGIES,
}
# What the chronicle calls each event, by the name the log gives the event.
WHATS = {
    'founded': What.FOUNDED,
    'took': What.TOOK,
    'learnt': What.LEARNT,
    'knew_everything': What.KNEW_EVERYTHING,
    'declared_war': What.DECLARED_WAR,
    'finished_wonder': What.FINISHED_WONDER,
    'defeated': What.DEFEATED,
    'went_bankrupt': What.WENT_BANKRUPT,
}
HIT_POINTS = 'hit_points'
TECHNOLOGIES = 'technologies'
CITIZENS = 'citizens'
BUILDINGS = 'buildings'
# Each part of a civilization's score grows by what it counts on each turn, by the number the score adds.
SCORES = {
    Series.MILITARY_SCORE: HIT_POINTS,
    Series.SCIENCE_SCORE: TECHNOLOGIES,
    Series.POPULATION_SCORE: CITIZENS,
    Series.DEVELOPMENT_SCORE: BUILDINGS,
}
ONE_PLACE = 1


def name_of_what(what):
    """Return the name the log gives one of the chronicle's kinds of event."""
    return next(name for name, known in WHATS.items() if known == what)


def is_military(kind):
    """Return whether a kind of unit can attack, which is what makes a unit count toward the military score."""
    return kind.ATTACK is not NO_DICE


class GameLog:

    __slots__ = ('_units', '_cities', '_series', '_scores')

    def __init__(self, game):
        civilizations = range(FIRST_CIVILIZATION, len(game.get_civilizations()) + FIRST_CIVILIZATION)
        self._units = {}
        self._cities = {}
        self._series = {civilization: {name: [] for name in Series.OWN} for civilization in civilizations}
        self._scores = {civilization: {name: 0 for name in SCORES} for civilization in civilizations}
        self.note(game=game, turn=game.get_turn())

    def note(self, *, game, turn):
        """Look at the game after a civilization's turn: the cities that are new, the units that are new, how far each unit moved, and the units that are gone."""
        founded = self._note_cities(game=game, turn=turn)
        units = game.get_units()
        alive = set(units.get_ids())
        for unit in alive:
            if unit not in self._units:
                self._units[unit] = self._new_unit(game=game, unit=unit, turn=turn)
            self._follow(game=game, unit=unit)
        for unit, record in self._units.items():
            if unit not in alive and record[Key.ENDING] == Ending.ALIVE:
                self._end(record=record, turn=turn, founded=founded)

    def _note_cities(self, *, game, turn):
        """Record each new city, and return how many cities each civilization founded since the last look."""
        founded = {}
        for city_id in game.get_city_ids():
            if city_id not in self._cities:
                owner = game.get_city(city_id).get_owner()
                self._cities[city_id] = {Key.FOUNDER: owner, Key.FOUNDED: turn}
                founded[owner] = founded.get(owner, 0) + 1
        return founded

    @staticmethod
    def _new_unit(*, game, unit, turn):
        units = game.get_units()
        kind = UnitControl.kind_of(game=game, unit=unit)
        level = units.get_value(column=UnitColumn.LEVEL, unit=unit)
        return {
            Key.ID: unit, Key.KIND: shown_name(kind), Key.MILITARY: is_military(kind), Key.CIVILIZATION: units.get_value(column=UnitColumn.OWNER, unit=unit),
            Key.MADE: turn, Key.GONE: NOT_GONE, Key.ENDING: Ending.ALIVE, Key.FIRST_LEVEL: level, Key.LEVEL: level, Key.MOVED: 0, Key.LIVED: 0, Key.INSIDE: 0,
            Key.SETTLER: issubclass(kind, SettlerUnit), Key.PLACE: GameLog._place(game=game, unit=unit),
        }

    @staticmethod
    def _place(*, game, unit):
        units = game.get_units()
        return [units.get_value(column=column, unit=unit) for column in (UnitColumn.WORLD, UnitColumn.X, UnitColumn.Y)]

    def _follow(self, *, game, unit):
        """Add how far a unit is from where the unit was at the last look to the tiles the unit has moved, and keep the unit's level."""
        record = self._units[unit]
        world, x, y = self._place(game=game, unit=unit)
        _, was_x, was_y = record[Key.PLACE]
        record[Key.MOVED] += distance(world=game.get_world(world), from_x=was_x, from_y=was_y, to_x=x, to_y=y)
        record[Key.PLACE] = [world, x, y]
        record[Key.LEVEL] = game.get_units().get_value(column=UnitColumn.LEVEL, unit=unit)

    @staticmethod
    def _end(*, record, turn, founded):
        """Say what became of a unit that is gone: a settler of a civilization that just founded a city built the city, and any other unit was lost."""
        owner = record[Key.CIVILIZATION]
        record[Key.GONE] = turn
        if record[Key.SETTLER] and founded.get(owner, 0) > 0:
            founded[owner] -= 1
            record[Key.ENDING] = Ending.SETTLED
        else:
            record[Key.ENDING] = Ending.LOST

    def count(self, game):
        """Count, at the end of a turn, a turn of life for every unit, and every number the log keeps for each civilization still playing. The strength of a civilization is what the four parts of the score count on one turn, which rises and falls, and each part of the score is the total of its count over every turn so far."""
        units = game.get_units()
        for unit in units.get_ids():
            record = self._units[unit]
            record[Key.LIVED] += 1
            if units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING:
                record[Key.INSIDE] += 1
        for civilization in game.get_still_playing():
            self._count_civilization(game=game, civilization=civilization)

    def _count_civilization(self, *, game, civilization):
        units = game.get_units()
        own = UnitControl.units_of(game=game, civilization=civilization)
        fighters = [unit for unit in own if self._units[unit][Key.MILITARY]]
        cities = [game.get_city(city) for city in game.get_cities_of(civilization)]
        now = {
            HIT_POINTS: sum(units.get_value(column=UnitColumn.HIT_POINTS, unit=unit) for unit in fighters),
            TECHNOLOGIES: len(game.get_civilization(civilization).get_technologies()),
            CITIZENS: sum(city.get_citizens() for city in cities),
            BUILDINGS: sum(len(city.get_buildings()) for city in cities),
        }
        series = self._series[civilization]
        scores = self._scores[civilization]
        for name, counted in SCORES.items():
            scores[name] += now[counted]
            series[name].append(scores[name])
        series[Series.SCORE].append(sum(scores.values()))
        series[Series.HIT_POINTS].append(now[HIT_POINTS])
        series[Series.STRENGTH].append(sum(now.values()))
        series[Series.BUILDINGS].append(now[BUILDINGS])
        series[Series.POLICY].append(TurnControl.control_points(game=game, civilization=civilization, points=Policy))
        series[Series.POLICY_TAKEN].append(OrderControl.taken(game=game, civilization=civilization, points=Policy))
        series[Series.COMMAND].append(TurnControl.control_points(game=game, civilization=civilization, points=Command))
        series[Series.COMMAND_TAKEN].append(OrderControl.taken(game=game, civilization=civilization, points=Command))
        series[Series.INSIDE].append(len([unit for unit in fighters if units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING]))
        levels = [units.get_value(column=UnitColumn.LEVEL, unit=unit) for unit in fighters]
        series[Series.LEVEL].append(round(sum(levels) / len(levels), ONE_PLACE) if levels else 0)

    def as_data(self, *, game, chronicle, seed):
        """Return everything the log and the chronicle hold of a game, as the data a log file is written from."""
        theme = game.get_theme()
        world = game.get_worlds()[0]
        civilizations = chronicle.get_civilizations()
        return {
            Key.THEME: shown_name(theme), Key.SEED: seed, Key.WIDTH: world.get_width(), Key.HEIGHT: world.get_height(), Key.TURNS: game.get_turn(),
            Key.CITY_WORD: theme.CITY.NAME, Key.RESOURCE_WORD: shown_name(theme.PRIMARY_RESOURCE),
            Key.CIVILIZATIONS: [self._civilization_data(game=game, civilization=civilization) for civilization in civilizations],
            Key.EVENTS: [self._event_data(event) for event in chronicle.get_events()],
            Key.SERIES: self._series_data(chronicle=chronicle, civilizations=civilizations),
            Key.UNITS: [self._unit_data(record) for record in self._units.values()],
            Key.CITIES: [self._city_data(game=game, city_id=city_id) for city_id in game.get_city_ids()],
        }

    @staticmethod
    def _civilization_data(*, game, civilization):
        holder = game.get_civilization(civilization)
        traits = {trait: holder.get_traits().get(trait) for trait in TRAITS} if holder.is_computer_played() else {}
        return {Key.ID: civilization, Key.NAME: holder.get_name(), Key.LOST: holder.has_lost(), Key.TRAITS: traits}

    @staticmethod
    def _event_data(event):
        return {Key.TURN: event.turn, Key.WHAT: name_of_what(event.what), Key.CIVILIZATION: event.civilization, Key.SUBJECT: event.subject, Key.OTHER: event.other}

    def _series_data(self, *, chronicle, civilizations):
        series = {name: {str(civilization): chronicle.get_counts(civilization=civilization, measure=measure) for civilization in civilizations} for name, measure in MEASURES.items()}
        for name in Series.OWN:
            series[name] = {str(civilization): list(self._series[civilization][name]) for civilization in civilizations}
        return series

    @staticmethod
    def _unit_data(record):
        """Return what a log file says of one unit: everything but where the unit was last seen."""
        return {key: value for key, value in record.items() if key not in (Key.PLACE, Key.SETTLER)}

    def _city_data(self, *, game, city_id):
        city = game.get_city(city_id)
        catalog = game.get_catalog()
        buildings = [catalog.get_kind(category=Category.BUILDINGS, kind_id=building) for building in city.get_buildings()]
        return {
            Key.ID: city_id, Key.NAME: city.get_name(), Key.FOUNDER: self._cities[city_id][Key.FOUNDER], Key.FOUNDED: self._cities[city_id][Key.FOUNDED],
            Key.OWNER: city.get_owner(), Key.CITIZENS: city.get_citizens(), Key.BUILDINGS: [shown_name(building) for building in buildings],
        }


def write_log(*, data, path):
    """Write the data of a game's log to a file as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, WRITE_MODE, encoding=FILE_ENCODING) as file:
        json.dump(data, file)


def read_log(path):
    """Return the data of a game's log from the file the log was written to."""
    with open(path, READ_MODE, encoding=FILE_ENCODING) as file:
        return json.load(file)
