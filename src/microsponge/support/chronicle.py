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

"""The chronicle of a game: what happened on each turn and how each civilization stood, kept by watching the game from outside as it is played.

The chronicle reads a game only through its getters, after each civilization's turn, and
notes what changed since it last looked. It is for the report of a scripted game
(`game_story.py`), and is not the history record of the model, which the game itself will keep.
"""

from dataclasses import dataclass

from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl

FIRST_CIVILIZATION = 1
NO_SUBJECT = ''


class What:
    """The kinds of event a chronicle notes."""

    FOUNDED = 1
    TOOK = 2
    LEARNT = 3
    KNEW_EVERYTHING = 4
    DECLARED_WAR = 5
    FINISHED_WONDER = 6
    DEFEATED = 7
    # Defeated by staying bankrupt too long, with no enemy needed.
    WENT_BANKRUPT = 8


class Measure:
    """What a chronicle counts for each civilization at the end of each turn."""

    CITIES = 1
    CITIZENS = 2
    WEALTH = 3
    UNITS = 4
    TECHNOLOGIES = 5

    ALL = (CITIES, CITIZENS, WEALTH, UNITS, TECHNOLOGIES)


@dataclass(slots=True, kw_only=True)
class Event:
    """One thing that happened: the turn, what (a What), the civilization that did it or that it happened to, the name of the city, technology or world wonder, and the other civilization, or NOTHING."""

    turn: int
    what: int
    civilization: int
    subject: str = NO_SUBJECT
    other: int = NOTHING


def counted(*, counts, civilization, kind, change=1):
    """Add to how many of a kind a civilization has in a nested count."""
    of_civilization = counts.setdefault(civilization, {})
    of_civilization[kind] = of_civilization.get(kind, 0) + change


class Chronicle:
    """What happened in one game, noted turn by turn: the events, what each civilization counted of each Measure at the end of each turn, and the units each civilization made and lost."""

    __slots__ = ('_events', '_counts', '_made', '_lost', '_owners', '_buildings', '_technologies', '_wars', '_units', '_defeated', '_last_progress', '_stalled')

    def __init__(self, game):
        """Start a chronicle of a game, before its first turn is played."""
        civilizations = range(FIRST_CIVILIZATION, len(game.get_civilizations()) + FIRST_CIVILIZATION)
        self._events = []
        self._counts = {civilization: {measure: [] for measure in Measure.ALL} for civilization in civilizations}
        self._made = {}
        self._lost = {}
        self._owners = {}
        self._buildings = {}
        self._technologies = {civilization: set() for civilization in civilizations}
        self._wars = {civilization: set() for civilization in civilizations}
        self._units = self._units_now(game)
        self._defeated = set()
        self._last_progress = game.get_turn()
        self._stalled = False

    @staticmethod
    def _units_now(game):
        """Return every unit that exists, each with its owner and its kind."""
        units = game.get_units()
        return {unit: (units.get_value(column=UnitColumn.OWNER, unit=unit), UnitControl.kind_of(game=game, unit=unit)) for unit in units.get_ids()}

    def note(self, *, game, turn):
        """Note what has changed in a game since the chronicle last looked, as events of a turn."""
        founded = self._note_cities(game=game, turn=turn)
        self._note_buildings(game=game, turn=turn)
        self._note_civilizations(game=game, turn=turn)
        self._note_units(game=game, turn=turn, founded=founded)

    def _note_cities(self, *, game, turn):
        """Note the cities founded and taken, and return how many cities each civilization founded."""
        founded = {}
        for city_id in game.get_city_ids():
            city = game.get_city(city_id)
            before = self._owners.get(city_id, NOTHING)
            if before == NOTHING:
                self._events.append(Event(turn=turn, what=What.FOUNDED, civilization=city.get_owner(), subject=city.get_name()))
                founded[city.get_owner()] = founded.get(city.get_owner(), 0) + 1
                self._last_progress = turn
            elif before != city.get_owner():
                self._events.append(Event(turn=turn, what=What.TOOK, civilization=city.get_owner(), subject=city.get_name(), other=before))
            self._owners[city_id] = city.get_owner()
        return founded

    def _note_buildings(self, *, game, turn):
        for city_id in game.get_city_ids():
            city = game.get_city(city_id)
            known = self._buildings.setdefault(city_id, set())
            for building in city.get_buildings():
                if building not in known:
                    known.add(building)
                    self._last_progress = turn
                    kind = game.get_catalog().get_kind(category=Category.BUILDINGS, kind_id=building)
                    if issubclass(kind, Wonder):
                        self._events.append(Event(turn=turn, what=What.FINISHED_WONDER, civilization=city.get_owner(), subject=shown_name(kind)))

    def _note_civilizations(self, *, game, turn):
        """Note the technologies learnt, the wars declared and the civilizations defeated."""
        catalog = game.get_catalog()
        every_technology = len(game.get_theme().TECHNOLOGIES)
        for civilization, holder in enumerate(game.get_civilizations(), start=FIRST_CIVILIZATION):
            for technology in holder.get_technologies():
                if technology not in self._technologies[civilization]:
                    self._technologies[civilization].add(technology)
                    self._events.append(Event(turn=turn, what=What.LEARNT, civilization=civilization, subject=shown_name(catalog.get_kind(category=Category.TECHNOLOGIES, kind_id=technology))))
                    if len(self._technologies[civilization]) == every_technology:
                        self._events.append(Event(turn=turn, what=What.KNEW_EVERYTHING, civilization=civilization))
            for enemy in holder.get_wars():
                if enemy not in self._wars[civilization]:
                    self._wars[civilization].add(enemy)
                    self._events.append(Event(turn=turn, what=What.DECLARED_WAR, civilization=civilization, other=enemy))
            if holder.has_lost() and civilization not in self._defeated:
                self._defeated.add(civilization)
                self._events.append(Event(turn=turn, what=What.WENT_BANKRUPT if holder.is_bankrupt() else What.DEFEATED, civilization=civilization))

    def _note_units(self, *, game, turn, founded):
        """Count the units made and the units lost. A settler that is gone when its civilization founded a city built the city, and is not lost."""
        now = self._units_now(game)
        for unit, (owner, kind) in now.items():
            if unit not in self._units:
                counted(counts=self._made, civilization=owner, kind=kind)
                self._last_progress = turn
        for unit, (owner, kind) in self._units.items():
            if unit not in now:
                if issubclass(kind, SettlerUnit) and founded.get(owner, 0) > 0:
                    founded[owner] -= 1
                else:
                    counted(counts=self._lost, civilization=owner, kind=kind)
        self._units = now

    def count(self, game):
        """Count every Measure of every civilization still playing, at the end of a turn."""
        catalog = game.get_catalog()
        currency = catalog.get_id(category=Category.RESOURCES, kind=game.get_theme().PRIMARY_RESOURCE)
        for civilization in game.get_still_playing():
            holder = game.get_civilization(civilization)
            cities = game.get_cities_of(civilization)
            counts = self._counts[civilization]
            counts[Measure.CITIES].append(len(cities))
            counts[Measure.CITIZENS].append(sum(game.get_city(city).get_citizens() for city in cities))
            counts[Measure.WEALTH].append(holder.get_amount(currency))
            counts[Measure.UNITS].append(len(UnitControl.units_of(game=game, civilization=civilization)))
            counts[Measure.TECHNOLOGIES].append(len(holder.get_technologies()))

    def get_events(self):
        """Return the events, in the order they happened."""
        return list(self._events)

    def events_of(self, *whats):
        """Return the events of any of some kinds, in the order they happened."""
        return [event for event in self._events if event.what in whats]

    def get_counts(self, *, civilization, measure):
        """Return what a civilization counted of a Measure at the end of each turn the civilization was still playing."""
        return list(self._counts[civilization][measure])

    def get_civilizations(self):
        return list(self._counts)

    def get_made(self, *, civilization, kind):
        return self._made.get(civilization, {}).get(kind, 0)

    def get_lost(self, *, civilization, kind):
        return self._lost.get(civilization, {}).get(kind, 0)

    def turns_without_progress(self, turn):
        """Return how many turns it has been since anything was built: a unit, a building or a city."""
        return turn - self._last_progress

    def is_stalled(self):
        return self._stalled

    def set_stalled(self, stalled):
        self._stalled = bool(stalled)
