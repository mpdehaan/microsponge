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

"""The helper AI: the layer every player, a person or a computer player, moves units through.

The model says that a player sets behaviors and preferences and a helper AI carries them out
(`GAME_RULES.md`, "Priorities and the helper AI"). For now the helper AI is mostly a pass
through, with no intelligence of its own: it takes the bare minimum of orders, each for one unit
or one city, and gives each to the game as it is. Anyone may use this layer, which moves a unit
tile by tile. The orders that say what a unit or a city is for, which the helper AI then works
out, are added on top of it.

A player never gives the game an order for a unit or a city directly: the main AI of a computer
player asks the helper AI, as a person will. What a civilization decides as a whole, which is
what to research, whom to declare war on and when to end the turn, is not about a unit or a
city, and goes to the game (`turns/orders.py`).
"""

from microsponge.engine.turns.orders import Orders


class HelperAI:
    """Static: the orders for single units and single cities, which the helper AI gives to the game. It is never made into an object.

    A refused order raises what the game raises, and changes nothing. An action for a unit that carries
    out a standing order is led, and takes no Policy of its own, because the standing order takes its points.
    """

    __slots__ = ()

    @staticmethod
    def move(*, game, unit, x, y, led=False):
        """Move a unit to a tile next to the unit."""
        Orders.move(game=game, unit=unit, x=x, y=y, led=led)

    @staticmethod
    def attack(*, game, unit, x, y, led=False):
        """Have a unit attack what is on a tile next to the unit, and return the outcome of the attack."""
        return Orders.attack(game=game, unit=unit, x=x, y=y, led=led)

    @staticmethod
    def found_city(*, game, settler, name, led=False):
        """Have a settler build a city where the settler stands, and return the city's id."""
        return Orders.found_city(game=game, settler=settler, name=name, led=led)

    @staticmethod
    def enter_city(*, game, unit, city, led=False):
        """Send a unit next to a city center into the city, which takes the city when the city belongs to an enemy and has no unit inside."""
        Orders.enter_city(game=game, unit=unit, city=city, led=led)

    @staticmethod
    def leave_city(*, game, unit, x, y, led=False):
        """Bring a unit out of its city onto a tile next to the city center."""
        Orders.leave_city(game=game, unit=unit, x=x, y=y, led=led)

    @staticmethod
    def build_improvement(*, game, unit, improvement, led=False):
        """Set a unit to building an improvement on the tile the unit stands on."""
        Orders.build_improvement(game=game, unit=unit, improvement=improvement, led=led)

    @staticmethod
    def abandon_improvement(*, game, unit):
        """Stop a unit building its improvement."""
        Orders.abandon_improvement(game=game, unit=unit)

    @staticmethod
    def upgrade(*, game, unit, led=False):
        """Upgrade an obsolete unit to the kind that made it obsolete."""
        Orders.upgrade(game=game, unit=unit, led=led)

    @staticmethod
    def prioritize(*, game, city, resource, citizens):
        """Set how many citizens of a city look for a resource other than food first."""
        Orders.prioritize(game=game, city=city, resource=resource, citizens=citizens)

    @staticmethod
    def build(*, game, city, kind):
        """Put a unit or a building at the end of what a city builds."""
        Orders.build(game=game, city=city, kind=kind)

    @staticmethod
    def build_instead(*, game, city, kind):
        """Make a city build a unit or a building instead of everything the city was going to build."""
        Orders.build_instead(game=game, city=city, kind=kind)

    @staticmethod
    def build_nothing(*, game, city):
        """Set a city to build nothing."""
        Orders.build_nothing(game=game, city=city)
