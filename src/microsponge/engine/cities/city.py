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

"""One city."""

from microsponge.engine.kinds.catalog import renumbered, renumbered_keys
from microsponge.engine.kinds.category import Category
from microsponge.engine.saving.keys import number_keys, text_keys
from microsponge.err_messages import (
    ERR_BUILDING_ALREADY_HELD, ERR_CITIZENS, ERR_CITY_NAME, ERR_GROWTH, ERR_NOTHING_QUEUED, ERR_PRIORITY, ERR_PROGRESS, ERR_UNIT_ALREADY_HELD, ERR_UNIT_NOT_HELD,
)
from microsponge.support.numbers import is_a_count
from microsponge.support.text import is_a_name

# What a saved game calls the parts of a city.
NAME_KEY = 'name'
OWNER_KEY = 'owner'
WORLD_KEY = 'world'
X_KEY = 'x'
Y_KEY = 'y'
FOUNDED_KEY = 'founded'
CITIZENS_KEY = 'citizens'
UNITS_KEY = 'units'
GROWTH_KEY = 'growth'
PRIORITIES_KEY = 'priorities'
BUILDINGS_KEY = 'buildings'
QUEUE_KEY = 'queue'
PROGRESS_KEY = 'progress'
BLOCKED_KEY = 'blocked'
BUILDS_NOTHING_KEY = 'builds_nothing'
NO_PROGRESS = 0
NO_CITIZENS = 0


def check_name(name):
    if not is_a_name(name):
        raise ValueError(ERR_CITY_NAME.format(value=name))
    return name


def check_citizens(citizens):
    if not is_a_count(citizens):
        raise ValueError(ERR_CITIZENS.format(value=citizens))
    return citizens


def check_growth(turns):
    if not is_a_count(turns):
        raise ValueError(ERR_GROWTH.format(value=turns))
    return turns


def check_progress(turns):
    if not is_a_count(turns):
        raise ValueError(ERR_PROGRESS.format(value=turns))
    return turns


def renumbered_queue(*, queue, category, numbers):
    """Return a production queue with the ids of one category of kinds replaced by their numbers in numbers."""
    return [(kind_category, renumbered(values=[kind], numbers=numbers)[0] if kind_category == category else kind) for kind_category, kind in queue]


class City:
    """A city: its name, the civilization it belongs to, where it is, when it was built, its citizens, its settings, its buildings, what it is building and the units inside.

    There are few cities, so each is an ordinary object. The tiles a city covers are not here:
    they are in two layers of the city's world, which CityControl keeps. x and y are the tile in
    the middle of the city center. The city's settings are its priorities: how many of its
    citizens look for a certain resource first, by the resource's id.

    The production queue is what the city builds, in order, each as (category, id): a unit or a
    building. The city builds the first, and its progress is the turns of that build paid for.
    """

    __slots__ = (
        '_name', '_owner', '_world', '_x', '_y', '_founded', '_citizens', '_units', '_growth', '_priorities',
        '_buildings', '_queue', '_progress', '_blocked', '_builds_nothing',
    )

    def __init__(self, *, name, owner, world, x, y, founded, citizens):
        self._name = check_name(name)
        self._owner = owner
        self._world = world
        self._x = x
        self._y = y
        self._founded = founded
        self._citizens = check_citizens(citizens)
        self._units = []
        self._growth = 0
        self._priorities = {}
        self._buildings = []
        self._queue = []
        self._progress = NO_PROGRESS
        self._blocked = False
        self._builds_nothing = False

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = check_name(name)

    def get_owner(self):
        return self._owner

    def set_owner(self, owner):
        self._owner = owner

    def get_world(self):
        return self._world

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def get_founded(self):
        """Return the turn the city was built in. Where two city radii overlap, the older city keeps the tiles."""
        return self._founded

    def get_citizens(self):
        return self._citizens

    def set_citizens(self, citizens):
        self._citizens = check_citizens(citizens)

    def get_growth(self):
        """Return how many turns in a row there has been enough food for the city to grow."""
        return self._growth

    def set_growth(self, turns):
        self._growth = check_growth(turns)

    def get_priorities(self):
        """Return the city's settings for its citizens: each resource's id with how many citizens look for that resource first."""
        return dict(self._priorities)

    def set_priority(self, *, resource, citizens):
        """Set how many citizens look for a resource first. None takes the priority away."""
        if not is_a_count(citizens):
            raise ValueError(ERR_PRIORITY.format(value=citizens))
        if citizens == NO_CITIZENS:
            self._priorities.pop(resource, None)
        else:
            self._priorities[resource] = citizens

    def get_buildings(self):
        """Return the ids of the buildings the city has, in the order they were built."""
        return list(self._buildings)

    def has_building(self, building):
        return building in self._buildings

    def add_building(self, building):
        if building in self._buildings:
            raise ValueError(ERR_BUILDING_ALREADY_HELD.format(name=self._name, building=building))
        self._buildings.append(building)

    def get_queue(self):
        """Return what the city builds, in order, each as (category, id). The city is building the first."""
        return list(self._queue)

    def add_to_queue(self, *, category, kind):
        """Put a unit or a building at the end of what the city builds, which also means the city is no longer set to build nothing."""
        self._queue.append((category, kind))
        self._builds_nothing = False

    def remove_first(self):
        """Take what the city is building off its queue, done or given up, so that the city starts on the next."""
        if not self._queue:
            raise ValueError(ERR_NOTHING_QUEUED.format(name=self._name))
        del self._queue[0]
        self._progress = NO_PROGRESS
        self._blocked = False

    def clear_queue(self):
        """Empty what the city builds. What was paid for the build under way is lost."""
        self._queue = []
        self._progress = NO_PROGRESS
        self._blocked = False

    def get_progress(self):
        """Return how many turns of the build under way have been paid for."""
        return self._progress

    def set_progress(self, turns):
        self._progress = check_progress(turns)

    def is_blocked(self):
        """Return whether the build under way waited last turn instead of going on."""
        return self._blocked

    def set_blocked(self, blocked):
        self._blocked = bool(blocked)

    def builds_nothing(self):
        """Return whether the city was set to build nothing, as opposed to waiting to be told what to build."""
        return self._builds_nothing

    def set_builds_nothing(self, builds_nothing):
        self._builds_nothing = bool(builds_nothing)

    def renumber(self, *, category, numbers):
        """Replace the ids of a category of kinds that the city holds, after loading a game saved with other ids."""
        if category == Category.RESOURCES:
            self._priorities = renumbered_keys(numbered=self._priorities, numbers=numbers)
        if category == Category.BUILDINGS:
            self._buildings = renumbered(values=self._buildings, numbers=numbers)
        self._queue = renumbered_queue(queue=self._queue, category=category, numbers=numbers)

    def get_units(self):
        """Return the ids of the units inside the city, in the order they entered."""
        return list(self._units)

    def holds(self, unit):
        return unit in self._units

    def add_unit(self, unit):
        if unit in self._units:
            raise ValueError(ERR_UNIT_ALREADY_HELD.format(unit=unit, name=self._name))
        self._units.append(unit)

    def remove_unit(self, unit):
        if unit not in self._units:
            raise ValueError(ERR_UNIT_NOT_HELD.format(unit=unit, name=self._name))
        self._units.remove(unit)

    def to_data(self):
        return {
            NAME_KEY: self._name,
            OWNER_KEY: self._owner,
            WORLD_KEY: self._world,
            X_KEY: self._x,
            Y_KEY: self._y,
            FOUNDED_KEY: self._founded,
            CITIZENS_KEY: self._citizens,
            UNITS_KEY: list(self._units),
            GROWTH_KEY: self._growth,
            PRIORITIES_KEY: text_keys(self._priorities),
            BUILDINGS_KEY: list(self._buildings),
            QUEUE_KEY: [list(item) for item in self._queue],
            PROGRESS_KEY: self._progress,
            BLOCKED_KEY: self._blocked,
            BUILDS_NOTHING_KEY: self._builds_nothing,
        }

    @classmethod
    def from_data(cls, data):
        city = cls(
            name=data[NAME_KEY], owner=data[OWNER_KEY], world=data[WORLD_KEY], x=data[X_KEY], y=data[Y_KEY],
            founded=data[FOUNDED_KEY], citizens=data[CITIZENS_KEY],
        )
        for unit in data[UNITS_KEY]:
            city.add_unit(unit)
        city.set_growth(data[GROWTH_KEY])
        city._priorities = number_keys(data[PRIORITIES_KEY])
        city._buildings = list(data[BUILDINGS_KEY])
        city._queue = [tuple(item) for item in data[QUEUE_KEY]]
        city.set_progress(data[PROGRESS_KEY])
        city.set_blocked(data[BLOCKED_KEY])
        city._builds_nothing = data[BUILDS_NOTHING_KEY]
        return city
