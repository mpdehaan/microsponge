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

"""One civilization in a game."""

from microsponge.engine.kinds.catalog import NOTHING, renumbered, renumbered_keys
from microsponge.engine.kinds.category import Category
from microsponge.engine.saving.keys import number_keys, text_keys
from microsponge.err_messages import ERR_AMOUNT, ERR_CIVILIZATION_NAME
from microsponge.support.numbers import is_a_count
from microsponge.support.text import is_a_name

# What a saved game calls the parts of a civilization.
NAME_KEY = 'name'
HOLDINGS_KEY = 'holdings'
ACTION_POINTS_KEY = 'action_points'
BANKRUPT_TURNS_KEY = 'bankrupt_turns'
WARS_KEY = 'wars'
TECHNOLOGIES_KEY = 'technologies'
RESEARCHING_KEY = 'researching'
RESEARCH_KEY = 'research'
LOST_KEY = 'lost'
CITIES_FOUNDED_KEY = 'cities_founded'
NOTHING_HELD = 0


def check_name(name):
    if not is_a_name(name):
        raise ValueError(ERR_CIVILIZATION_NAME.format(value=name))
    return name


def check_amount(amount):
    if not is_a_count(amount):
        raise ValueError(ERR_AMOUNT.format(value=amount))
    return amount


class Civilization:
    """A civilization: its name, what it holds of each resource, the technologies it knows, its action points, and who it is at war with.

    There are few civilizations, so each is an ordinary object. Every city of a civilization
    adds to what the civilization holds and spends from it: no city holds resources of its
    own. Resources, technologies and other civilizations go by their ids.
    """

    __slots__ = ('_name', '_holdings', '_technologies', '_researching', '_research', '_action_points', '_bankrupt_turns', '_wars', '_lost', '_cities_founded')

    def __init__(self, name):
        self._name = check_name(name)
        self._holdings = {}
        self._technologies = set()
        self._researching = NOTHING
        self._research = 0
        self._action_points = 0
        self._bankrupt_turns = 0
        self._wars = set()
        self._lost = False
        self._cities_founded = 0

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = check_name(name)

    def get_amount(self, resource):
        """Return how much of a resource the civilization holds."""
        return self._holdings.get(resource, NOTHING_HELD)

    def get_holdings(self):
        """Return what the civilization holds: each resource's id with its amount."""
        return dict(self._holdings)

    def add(self, *, resource, amount):
        self._holdings[resource] = self.get_amount(resource) + check_amount(amount)

    def pay(self, *, resource, amount):
        """Take an amount of a resource from what the civilization holds, or all there is when there is less, and return what was taken."""
        paid = min(check_amount(amount), self.get_amount(resource))
        self._holdings[resource] = self.get_amount(resource) - paid
        return paid

    def knows(self, technology):
        return technology in self._technologies

    def learn(self, technology):
        self._technologies.add(technology)

    def get_technologies(self):
        """Return the ids of the technologies the civilization knows, in order."""
        return sorted(self._technologies)

    def get_researching(self):
        """Return the id of the technology the civilization is researching, or NOTHING."""
        return self._researching

    def set_researching(self, technology):
        self._researching = technology

    def get_research(self):
        """Return the research points the civilization has gathered and not yet spent on a technology."""
        return self._research

    def set_research(self, points):
        self._research = check_amount(points)

    def get_action_points(self):
        return self._action_points

    def set_action_points(self, points):
        self._action_points = check_amount(points)

    def get_bankrupt_turns(self):
        """Return how many turns in a row the civilization has been bankrupt."""
        return self._bankrupt_turns

    def set_bankrupt_turns(self, turns):
        self._bankrupt_turns = check_amount(turns)

    def is_bankrupt(self):
        return self._bankrupt_turns > 0

    def is_at_war_with(self, civilization):
        return civilization in self._wars

    def declare_war(self, civilization):
        self._wars.add(civilization)

    def get_wars(self):
        """Return the ids of the civilizations this one is at war with, in order."""
        return sorted(self._wars)

    def has_lost(self):
        return self._lost

    def get_cities_founded(self):
        """Return how many cities the civilization has founded in the game, whoever holds them now."""
        return self._cities_founded

    def count_founded_city(self):
        self._cities_founded += 1

    def lose(self):
        self._lost = True

    def renumber(self, *, category, numbers):
        """Replace the ids of a category of kinds that the civilization holds, after loading a game saved with other ids."""
        if category == Category.RESOURCES:
            self._holdings = renumbered_keys(numbered=self._holdings, numbers=numbers)
        if category == Category.TECHNOLOGIES:
            self._technologies = set(renumbered(values=self.get_technologies(), numbers=numbers))
            self._researching = renumbered(values=[self._researching], numbers=numbers)[0]

    def to_data(self):
        return {
            NAME_KEY: self._name,
            HOLDINGS_KEY: text_keys(self._holdings),
            TECHNOLOGIES_KEY: self.get_technologies(),
            RESEARCHING_KEY: self._researching,
            RESEARCH_KEY: self._research,
            ACTION_POINTS_KEY: self._action_points,
            BANKRUPT_TURNS_KEY: self._bankrupt_turns,
            WARS_KEY: self.get_wars(),
            LOST_KEY: self._lost,
            CITIES_FOUNDED_KEY: self._cities_founded,
        }

    @classmethod
    def from_data(cls, data):
        civilization = cls(data[NAME_KEY])
        civilization._holdings = number_keys(data[HOLDINGS_KEY])
        civilization._technologies = set(data[TECHNOLOGIES_KEY])
        civilization.set_researching(data[RESEARCHING_KEY])
        civilization.set_research(data[RESEARCH_KEY])
        civilization.set_action_points(data[ACTION_POINTS_KEY])
        civilization.set_bankrupt_turns(data[BANKRUPT_TURNS_KEY])
        civilization._wars = set(data[WARS_KEY])
        civilization._lost = data[LOST_KEY]
        civilization._cities_founded = check_amount(data[CITIES_FOUNDED_KEY])
        return civilization
