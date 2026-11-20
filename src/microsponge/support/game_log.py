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
civilization one number a turn of each thing worth a chart: the series, and the count of each
kind of unit the civilization has and of each kind of improvement on the tiles of its cities'
radii. `game_log_report.py` reads the
file back and answers questions about the game, and `game_log_page.py` draws the charts.
"""

import json

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.control_points import Command, Policy
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.resource import StrategicResource
from microsponge.engine.orders.given_order import Reason
from microsponge.engine.orders.order import RetireOrder
from microsponge.engine.orders.thing import ThingType, army_thing, division_thing, unit_thing
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.players.knowledge import distance
from microsponge.engine.players.traits import TRAITS
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.combat import Tally
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.support.chronicle import FIRST_CIVILIZATION, Measure, What

# A unit that is still alive when the log is written has no turn on which the unit was gone.
NOT_GONE = -1
# A kind of order that was never in use has no turn on which it was first or last in use.
NEVER = -1
FILE_ENCODING = 'utf-8'
# The tallies of fights each civilization keeps for each kind of its units.
TALLIES = (Tally.ATTACKS, Tally.KILLS, Tally.CITY_ATTACKS, Tally.ATTACKS_ON_ITS_CITIES, *Tally.LOSSES)
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
    UNIT_KINDS = 'unit_kinds'
    BANKS = 'banks'
    BUILT = 'built'
    ORDERS = 'orders'
    BUILDING = 'building'
    FORCES = 'forces'
    TALLIES = 'tallies'
    GROUP = 'group'
    MADE_TURNS = 'made_turns'
    RETIRED_TURNS = 'retired_turns'
    ARMY = 'army'
    DIVISION = 'division'
    CITY = 'city'
    GIVEN = 'given'
    FIRST_IN_USE = 'first_in_use'
    LAST_IN_USE = 'last_in_use'
    IMPROVEMENTS = 'improvements'
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
    RETIRED = 'retired'


class Group:
    """What a civilization makes and retires, which the log counts with the turns of each."""

    UNIT = 'unit'
    DIVISION = 'division'
    ARMY = 'army'

    ALL = (UNIT, DIVISION, ARMY)


# The group each type of thing an order to retire can name stands for.
RETIRED_GROUPS = {ThingType.UNIT: Group.UNIT, ThingType.DIVISION: Group.DIVISION, ThingType.ARMY: Group.ARMY}


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
    FOOD_STORED = 'food_stored'
    WARS = 'wars'
    LOST_ATTACKING_CITY = Tally.LOST_ATTACKING_CITY
    LOST_ATTACKING_FIELD = Tally.LOST_ATTACKING_FIELD
    LOST_DEFENDING_CITY = Tally.LOST_DEFENDING_CITY
    LOST_DEFENDING_FIELD = Tally.LOST_DEFENDING_FIELD

    OWN = (HIT_POINTS, STRENGTH, FOOD_STORED, WARS, LOST_ATTACKING_CITY, LOST_ATTACKING_FIELD, LOST_DEFENDING_CITY, LOST_DEFENDING_FIELD, POLICY, POLICY_TAKEN, COMMAND, COMMAND_TAKEN, INSIDE, LEVEL, BUILDINGS, MILITARY_SCORE, SCIENCE_SCORE, POPULATION_SCORE, DEVELOPMENT_SCORE, SCORE)


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


def counted_improvements(theme):
    """Return the kinds of improvement of a theme that stay on a tile once built, which are the ones the log counts: work that changes the terrain, like caveman's clearing, leaves nothing to count."""
    return [kind for kind in theme.IMPROVEMENTS if kind.BECOMES is None]


def collected_resources(theme):
    """Return the resources of a theme that a civilization collects and holds in its bank, which are every resource but the strategic ones and food, which each city stores for itself."""
    return [resource for resource in theme.RESOURCES if not issubclass(resource, StrategicResource) and resource is not theme.FOOD]


def empty_counts(*, civilizations, names):
    """Return, for each civilization, an empty list of counts for each name."""
    return {civilization: {name: [] for name in names} for civilization in civilizations}


def is_military(kind):
    """Return whether a kind of unit can attack, which is what makes a unit count toward the military score."""
    return kind.ATTACK is not NO_DICE


class GameLog:

    __slots__ = ('_units', '_cities', '_series', '_scores', '_unit_kinds', '_improvements', '_kind_counts', '_improvement_counts', '_radii', '_banks', '_bank_counts', '_buildings', '_built', '_orders', '_order_records', '_groups', '_seen_divisions', '_seen_armies', '_retired_orders', '_retiring')

    def __init__(self, game):
        civilizations = range(FIRST_CIVILIZATION, len(game.get_civilizations()) + FIRST_CIVILIZATION)
        theme = game.get_theme()
        catalog = game.get_catalog()
        self._units = {}
        self._cities = {}
        self._series = empty_counts(civilizations=civilizations, names=Series.OWN)
        self._scores = {civilization: {name: 0 for name in SCORES} for civilization in civilizations}
        self._unit_kinds = [shown_name(kind) for kind in theme.UNITS]
        # The shown name of each kind of improvement counted, by its id in the world's improvement layer.
        self._improvements = {catalog.get_id(category=Category.IMPROVEMENTS, kind=kind): shown_name(kind) for kind in counted_improvements(theme)}
        self._kind_counts = empty_counts(civilizations=civilizations, names=self._unit_kinds)
        self._improvement_counts = empty_counts(civilizations=civilizations, names=self._improvements.values())
        # The tiles of each city's radius, which never change, worked out once for each city.
        self._radii = {}
        # The shown name of each collected resource, by its id in the catalog.
        self._banks = {catalog.get_id(category=Category.RESOURCES, kind=resource): shown_name(resource) for resource in collected_resources(theme)}
        self._bank_counts = empty_counts(civilizations=civilizations, names=self._banks.values())
        # The ids of the buildings each city held at the last look, and each building finished since the game began.
        self._buildings = {}
        self._built = []
        # Every order a civilization has given, kept so that an order is counted once, and what the log says of each kind of order each civilization gave.
        self._orders = set()
        self._order_records = {}
        # For each civilization and each group, the turns one was made and the turns one was retired; the divisions and armies already seen; the orders to retire already counted; and the things being retired at this look.
        self._groups = {(civilization, group): {Key.MADE_TURNS: [], Key.RETIRED_TURNS: []} for civilization in civilizations for group in Group.ALL}
        self._seen_divisions = set()
        self._seen_armies = set()
        self._retired_orders = set()
        self._retiring = set()
        self.note(game=game, turn=game.get_turn())

    def note(self, *, game, turn):
        """Look at the game after a civilization's turn: the cities that are new, the units that are new, how far each unit moved, and the units that are gone."""
        founded = self._note_cities(game=game, turn=turn)
        self._note_buildings(game=game, turn=turn)
        self._note_orders(game=game, turn=turn)
        self._note_forces(game=game, turn=turn)
        units = game.get_units()
        alive = set(units.get_ids())
        for unit in alive:
            if unit not in self._units:
                self._units[unit] = self._new_unit(game=game, unit=unit, turn=turn)
            self._follow(game=game, unit=unit)
        for unit, record in self._units.items():
            if unit not in alive and record[Key.ENDING] == Ending.ALIVE:
                self._end(record=record, turn=turn, founded=founded)
        self._retiring = set()

    def _note_cities(self, *, game, turn):
        """Record each new city, and return how many cities each civilization founded since the last look."""
        founded = {}
        for city_id in game.get_city_ids():
            if city_id not in self._cities:
                owner = game.get_city(city_id).get_owner()
                self._cities[city_id] = {Key.FOUNDER: owner, Key.FOUNDED: turn}
                founded[owner] = founded.get(owner, 0) + 1
        return founded

    def _note_buildings(self, *, game, turn):
        """Record each building that a city holds and did not hold at the last look, as finished by the city's owner on this turn. A city that changes hands keeps its buildings, which are not counted again."""
        catalog = game.get_catalog()
        for city_id in game.get_city_ids():
            city = game.get_city(city_id)
            known = self._buildings.setdefault(city_id, set())
            for building in city.get_buildings():
                if building not in known:
                    known.add(building)
                    name = shown_name(catalog.get_kind(category=Category.BUILDINGS, kind_id=building))
                    self._built.append({Key.TURN: turn, Key.CIVILIZATION: city.get_owner(), Key.BUILDING: name, Key.CITY: city.get_name()})

    def _note_orders(self, *, game, turn):
        """Count each order a civilization gave since the last look, and the turns an order of each kind was in use, which is active. The orders the helper AI realizes for itself are not counted."""
        for civilization, holder in enumerate(game.get_civilizations(), start=FIRST_CIVILIZATION):
            for order in holder.get_orders().get_orders():
                if order.is_a(RetireOrder) and order.get_reason() is Reason.COMPLETED and order not in self._retired_orders:
                    self._retired_orders.add(order)
                    self._retiring.add((civilization, order.get_receiver()))
                    group = RETIRED_GROUPS[order.get_receiver().type]
                    if group != Group.UNIT:
                        self._groups[(civilization, group)][Key.RETIRED_TURNS].append(turn)
                record = self._order_records.setdefault((civilization, shown_name(order.get_kind())), {Key.GIVEN: [], Key.FIRST_IN_USE: NEVER, Key.LAST_IN_USE: NEVER})
                if order not in self._orders:
                    self._orders.add(order)
                    record[Key.GIVEN].append(turn)
                if order.is_active():
                    if record[Key.FIRST_IN_USE] == NEVER:
                        record[Key.FIRST_IN_USE] = turn
                    record[Key.LAST_IN_USE] = turn

    def _note_forces(self, *, game, turn):
        """Record each division and each army a civilization has that was not there at the last look, as made on this turn."""
        for civilization, holder in enumerate(game.get_civilizations(), start=FIRST_CIVILIZATION):
            forces = holder.get_forces()
            for division in forces.get_divisions():
                if (civilization, division.get_id()) not in self._seen_divisions:
                    self._seen_divisions.add((civilization, division.get_id()))
                    self._groups[(civilization, Group.DIVISION)][Key.MADE_TURNS].append(turn)
            for army in forces.get_armies():
                if (civilization, army) not in self._seen_armies:
                    self._seen_armies.add((civilization, army))
                    self._groups[(civilization, Group.ARMY)][Key.MADE_TURNS].append(turn)

    @staticmethod
    def _new_unit(*, game, unit, turn):
        units = game.get_units()
        kind = UnitControl.kind_of(game=game, unit=unit)
        level = units.get_value(column=UnitColumn.LEVEL, unit=unit)
        return {
            Key.ID: unit, Key.KIND: shown_name(kind), Key.MILITARY: is_military(kind), Key.CIVILIZATION: units.get_value(column=UnitColumn.OWNER, unit=unit),
            Key.MADE: turn, Key.GONE: NOT_GONE, Key.ENDING: Ending.ALIVE, Key.FIRST_LEVEL: level, Key.LEVEL: level, Key.MOVED: 0, Key.LIVED: 0, Key.INSIDE: 0,
            Key.SETTLER: issubclass(kind, SettlerUnit), Key.PLACE: GameLog._place(game=game, unit=unit), Key.DIVISION: NOTHING, Key.ARMY: NOTHING,
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
        division = game.get_civilization(record[Key.CIVILIZATION]).get_forces().division_of(unit)
        record[Key.DIVISION] = NOTHING if division is None else division.get_id()
        record[Key.ARMY] = NOTHING if division is None else division.get_army()

    def _is_retiring(self, record):
        """Return whether a unit that is gone was named by an order to retire completed since the last look, itself or through its division or its army."""
        owner = record[Key.CIVILIZATION]
        things = (unit_thing(record[Key.ID]), division_thing(record[Key.DIVISION]), army_thing(record[Key.ARMY]))
        return any((owner, thing) in self._retiring for thing in things)

    def _end(self, *, record, turn, founded):
        """Say what became of a unit that is gone: a unit an order retired was retired, a settler of a civilization that just founded a city built the city, and any other unit was lost."""
        owner = record[Key.CIVILIZATION]
        record[Key.GONE] = turn
        if self._is_retiring(record):
            record[Key.ENDING] = Ending.RETIRED
            self._groups[(owner, Group.UNIT)][Key.RETIRED_TURNS].append(turn)
        elif record[Key.SETTLER] and founded.get(owner, 0) > 0:
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
        series[Series.FOOD_STORED].append(sum(city.get_food() for city in cities))
        series[Series.WARS].append(len(game.get_civilization(civilization).get_wars()))
        for loss in Tally.LOSSES:
            series[loss].append(sum(game.get_civilization(civilization).get_tally(loss).values()))
        series[Series.POLICY].append(TurnControl.control_points(game=game, civilization=civilization, points=Policy))
        series[Series.POLICY_TAKEN].append(OrderControl.taken(game=game, civilization=civilization, points=Policy))
        series[Series.COMMAND].append(TurnControl.control_points(game=game, civilization=civilization, points=Command))
        series[Series.COMMAND_TAKEN].append(OrderControl.taken(game=game, civilization=civilization, points=Command))
        series[Series.INSIDE].append(len([unit for unit in fighters if units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING]))
        levels = [units.get_value(column=UnitColumn.LEVEL, unit=unit) for unit in fighters]
        series[Series.LEVEL].append(round(sum(levels) / len(levels), ONE_PLACE) if levels else 0)
        holder = game.get_civilization(civilization)
        for resource, name in self._banks.items():
            self._bank_counts[civilization][name].append(holder.get_amount(resource))
        self._count_kinds(civilization=civilization, own=own)
        self._count_improvements(game=game, civilization=civilization)

    def _count_kinds(self, *, civilization, own):
        """Record how many units of each kind of the theme a civilization has."""
        counts = dict.fromkeys(self._unit_kinds, 0)
        for unit in own:
            counts[self._units[unit][Key.KIND]] += 1
        for name, count in counts.items():
            self._kind_counts[civilization][name].append(count)

    def _count_improvements(self, *, game, civilization):
        """Record how many improvements of each kind counted are on the tiles of a civilization's cities' radii."""
        counts = dict.fromkeys(self._improvements.values(), 0)
        for city_id in game.get_cities_of(civilization):
            world = game.get_world(game.get_city(city_id).get_world())
            for x, y in self._radius_of(game=game, city_id=city_id):
                improvement = world.get_value(layer=Layer.IMPROVEMENT, x=x, y=y)
                if improvement in self._improvements:
                    counts[self._improvements[improvement]] += 1
        for name, count in counts.items():
            self._improvement_counts[civilization][name].append(count)

    def _radius_of(self, *, game, city_id):
        if city_id not in self._radii:
            self._radii[city_id] = CityControl.radius_tiles(game=game, city=city_id)
        return self._radii[city_id]

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
            Key.UNIT_KINDS: self._counts_data(counts=self._kind_counts, names=self._unit_kinds, civilizations=civilizations),
            Key.IMPROVEMENTS: self._counts_data(counts=self._improvement_counts, names=self._improvements.values(), civilizations=civilizations),
            Key.BANKS: self._counts_data(counts=self._bank_counts, names=self._banks.values(), civilizations=civilizations),
            Key.BUILT: list(self._built),
            Key.ORDERS: [{Key.CIVILIZATION: civilization, Key.KIND: kind, **record} for (civilization, kind), record in self._order_records.items()],
            Key.FORCES: [{Key.CIVILIZATION: civilization, Key.GROUP: group, **record} for (civilization, group), record in self._groups.items()],
            Key.UNITS: [self._unit_data(record) for record in self._units.values()],
            Key.CITIES: [self._city_data(game=game, city_id=city_id) for city_id in game.get_city_ids()],
        }

    @staticmethod
    def _civilization_data(*, game, civilization):
        holder = game.get_civilization(civilization)
        traits = {trait: holder.get_traits().get(trait) for trait in TRAITS} if holder.is_computer_played() else {}
        catalog = game.get_catalog()
        tallies = {tally: {shown_name(catalog.get_kind(category=Category.UNITS, kind_id=kind)): count for kind, count in holder.get_tally(tally).items()} for tally in TALLIES}
        return {Key.ID: civilization, Key.NAME: holder.get_name(), Key.LOST: holder.has_lost(), Key.TRAITS: traits, Key.TALLIES: tallies}

    @staticmethod
    def _event_data(event):
        return {Key.TURN: event.turn, Key.WHAT: name_of_what(event.what), Key.CIVILIZATION: event.civilization, Key.SUBJECT: event.subject, Key.OTHER: event.other}

    def _series_data(self, *, chronicle, civilizations):
        series = {name: {str(civilization): chronicle.get_counts(civilization=civilization, measure=measure) for civilization in civilizations} for name, measure in MEASURES.items()}
        for name in Series.OWN:
            series[name] = {str(civilization): list(self._series[civilization][name]) for civilization in civilizations}
        return series

    @staticmethod
    def _counts_data(*, counts, names, civilizations):
        """Return the counts of each kind for each civilization, by the kind's name and then the civilization's id as text, the shape of the series."""
        return {name: {str(civilization): list(counts[civilization][name]) for civilization in civilizations} for name in names}

    @staticmethod
    def _unit_data(record):
        """Return what a log file says of one unit: everything but where the unit was last seen."""
        return {key: value for key, value in record.items() if key not in (Key.PLACE, Key.SETTLER, Key.DIVISION, Key.ARMY)}

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
