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

"""The referee AI: the part of the engine, belonging to no player, that marks an order invalid when the order can no longer work."""

from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.orders.given_order import Reason
from microsponge.engine.orders.thing import ThingType
from microsponge.engine.orders.what import Garrison


class Referee:
    """Static: reviews a civilization's orders. An order whose giver or receiver is gone, or whose city to garrison is no longer the civilization's, is invalid for good."""

    __slots__ = ()

    @staticmethod
    def exists(*, game, civilization, thing):
        """Return whether a thing an order names is still the civilization's: its city, its army, its division or its living unit."""
        forces = game.get_civilization(civilization).get_forces()
        if thing.type is ThingType.CITY:
            return thing.id in game.get_cities_of(civilization)
        if thing.type is ThingType.ARMY:
            return thing.id in forces.get_armies()
        if thing.type is ThingType.DIVISION:
            return forces.has_division(thing.id)
        if thing.type is ThingType.UNIT:
            return thing.id in Sight.units_of(game=game, civilization=civilization)
        return True

    @staticmethod
    def can_work(*, game, civilization, order):
        what = order.get_what()
        if isinstance(what, Garrison) and what.place.city not in game.get_cities_of(civilization):
            return False
        return all(Referee.exists(game=game, civilization=civilization, thing=thing) for thing in (order.get_giver(), order.get_receiver()))

    @staticmethod
    def review(*, game, civilization):
        """Mark invalid every order of a civilization that can no longer work. An order already completed stays completed."""
        for order in game.get_civilization(civilization).get_orders().get_all():
            if order.get_reason() not in (Reason.INVALID, Reason.COMPLETED) and not Referee.can_work(game=game, civilization=civilization, order=order):
                order.invalidate()
