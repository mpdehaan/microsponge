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

"""The computer player: the main AI, which plays a civilization's turn by giving standing orders, as the civilization's traits tip it.

The main AI adjusts the strategy the way a person would, and cannot touch a unit or a city
(`GAME_RULES.md`, "Priorities and the helper AI"): it keeps the civilization's table of orders,
its army and its division, within the Policy and the Command the civilization has, and the
Hand (`hand.py`) carries the orders out. The main AI reads only the orders it gave, never the
orders the Hand realized, and reads the map only through the civilization's view. What a
civilization decides as a whole, whom to declare war on and when to end the turn, goes to
`Orders`. Each trait tips one decision through `Traits.favors()`. The players of each theme
are subclasses that say which kinds are the theme's: `CavemanPlayer` is the first.
"""

from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.control_points import CONTROL_POINTS, Command
from microsponge.engine.orders.given_order import Reason
from microsponge.engine.orders.order import BuildOrder, ExpandOrder, GarrisonOrder, MarchOrder, RaiseOrder, ResearchOrder, RetireOrder, SettlerOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.thing import city_thing, civilization_thing, division_thing, unit_thing
from microsponge.engine.orders.what import BuildTarget, Buildings, CityTarget, Garrison, March, NoDetails, Technologies, Units
from microsponge.engine.players.hand import Hand
from microsponge.engine.players.knowledge import Knowledge, distance
from microsponge.engine.players.traits import AGGRESSIVE_HYPERFOCUS, BOLDNESS, CONQUEST, ECONOMICS, EXPANSION, PEACE, SCIENCE
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import TurnControl

# Each city keeps this many units of the division inside.
GARRISON = 1


class ComputerPlayer:
    """Static: plays a turn for a computer-played civilization. A theme's player subclasses it and sets what is the theme's."""

    __slots__ = ()
    # The technologies worth researching, in order, for a player that favors science and for one that favors the army.
    SCIENCE_RESEARCH = ()
    MILITARY_RESEARCH = ()
    # The kinds of unit the division is raised from, best first, and the buildings a city builds, in order.
    FIGHTERS = ()
    ECONOMY = ()
    # How many fighters beyond the garrisons gather before the army marches, when the Command allows that many.
    GROUP_SIZE = 3
    # The currency a civilization keeps before it raises another fighter, so that it does not go bankrupt.
    RESERVE = 10

    @classmethod
    def play_turn(cls, *, game, civilization):
        """Play a civilization's whole turn: set the orders, have the Hand carry them out, and end the turn, unless carrying them out won the game."""
        cls.plan(game=game, civilization=civilization)
        Hand.carry_out(game=game, civilization=civilization)
        if not game.is_over():
            Orders.end_turn(game=game, civilization=civilization)

    @classmethod
    def plan(cls, *, game, civilization):
        """Bring the civilization's table of orders up to date, and keep it within the civilization's Policy and Command."""
        cls.tidy(game=game, civilization=civilization)
        cls.plan_research(game=game, civilization=civilization)
        cls.plan_first_settlers(game=game, civilization=civilization)
        cls.plan_cities(game=game, civilization=civilization)
        cls.plan_division(game=game, civilization=civilization)
        cls.plan_retirement(game=game, civilization=civilization)
        cls.consider_war(game=game, civilization=civilization)
        cls.plan_march(game=game, civilization=civilization)
        cls.keep_within_points(game=game, civilization=civilization)

    # What the player knows

    @classmethod
    def favors(cls, *, game, civilization, trait):
        return game.get_civilization(civilization).get_traits().favors(trait=trait, random=game.get_random())

    @classmethod
    def table_of(cls, *, game, civilization):
        return game.get_civilization(civilization).get_orders()

    @classmethod
    def given(cls, *, game, civilization, kind, receiver=None):
        """Return the orders of a kind the player gave, to one receiver or to any."""
        orders = cls.table_of(game=game, civilization=civilization).get_orders()
        return [order for order in orders if order.is_a(kind) and receiver in (None, order.get_receiver())]

    @classmethod
    def give(cls, *, game, civilization, kind, giver, receiver, what):
        return OrderControl.give(game=game, civilization=civilization, kind=kind, giver=giver, receiver=receiver, what=what)

    @classmethod
    def division_of(cls, *, game, civilization):
        """Return the civilization's one division, or None before it has one."""
        divisions = game.get_civilization(civilization).get_forces().get_divisions()
        return divisions[0] if divisions else None

    @classmethod
    def bank(cls, *, game, civilization):
        theme = game.get_theme()
        return game.get_civilization(civilization).get_amount(game.get_catalog().get_id(category=Category.RESOURCES, kind=theme.PRIMARY_RESOURCE))

    # The table

    @classmethod
    def tidy(cls, *, game, civilization):
        """Take out of the table the orders that are invalid and the orders to settle or to march that are completed, and switch every order the player disabled back on, to be weighed again this turn."""
        table = cls.table_of(game=game, civilization=civilization)
        for order in table.get_orders():
            finished = order.get_reason() is Reason.COMPLETED and (order.is_a(SettlerOrder) or order.is_a(MarchOrder) or order.is_a(RetireOrder))
            if order.get_reason() is Reason.INVALID or finished:
                table.remove(order)
            elif order.get_reason() is Reason.DISABLED:
                order.activate()

    @classmethod
    def keep_within_points(cls, *, game, civilization):
        """Disable the orders given last until the active orders take no more Policy and no more Command than the civilization has."""
        for points in CONTROL_POINTS:
            orders = [order for order in cls.table_of(game=game, civilization=civilization).get_orders() if order.get_kind().POINTS is points]
            while OrderControl.left(game=game, civilization=civilization, points=points) < 0:
                active = [order for order in orders if order.is_active()]
                active[-1].disable()

    # Research and settling

    @classmethod
    def plan_research(cls, *, game, civilization):
        """Give the research order once: the science order first or the military order first, as the science trait decides."""
        if cls.given(game=game, civilization=civilization, kind=ResearchOrder):
            return
        science_first = cls.favors(game=game, civilization=civilization, trait=SCIENCE)
        order = (*cls.SCIENCE_RESEARCH, *cls.MILITARY_RESEARCH) if science_first else (*cls.MILITARY_RESEARCH, *cls.SCIENCE_RESEARCH)
        me = civilization_thing(civilization)
        cls.give(game=game, civilization=civilization, kind=ResearchOrder, giver=me, receiver=me, what=Technologies(kinds=order))

    @classmethod
    def plan_first_settlers(cls, *, game, civilization):
        """Order each settler of a civilization with no city to settle. Later settlers are sent by the Hand, for a city ordered to expand."""
        if game.get_cities_of(civilization):
            return
        for unit in Knowledge.settlers_of(game=game, civilization=civilization):
            settler = unit_thing(unit)
            if not cls.given(game=game, civilization=civilization, kind=SettlerOrder, receiver=settler):
                cls.give(game=game, civilization=civilization, kind=SettlerOrder, giver=settler, receiver=settler, what=NoDetails())

    @classmethod
    def plan_cities(cls, *, game, civilization):
        """Give every city its build order, and the first city the order to expand, which is active on the turns the expansion trait says."""
        cities = game.get_cities_of(civilization)
        for city in cities:
            here = city_thing(city)
            if not cls.given(game=game, civilization=civilization, kind=BuildOrder, receiver=here):
                cls.give(game=game, civilization=civilization, kind=BuildOrder, giver=here, receiver=here, what=Buildings(kinds=cls.ECONOMY))
        if not cities:
            return
        expanding = cls.given(game=game, civilization=civilization, kind=ExpandOrder)
        if not expanding:
            first = city_thing(cities[0])
            expanding = [cls.give(game=game, civilization=civilization, kind=ExpandOrder, giver=first, receiver=first, what=NoDetails())]
        if not cls.favors(game=game, civilization=civilization, trait=EXPANSION):
            expanding[0].disable()

    # The division

    @classmethod
    def wanted_size(cls, *, game, civilization):
        """Return how many units the division should have: a garrison for each city, and as many more as the Command pays to march, up to the group size."""
        cities = len(game.get_cities_of(civilization))
        command = TurnControl.control_points(game=game, civilization=civilization, points=Command)
        garrisons = cities * GARRISON
        return garrisons + max(0, min(cls.GROUP_SIZE, (command - garrisons * GarrisonOrder.UNIT_COST) // MarchOrder.UNIT_COST - garrisons))

    @classmethod
    def wants_fighters(cls, *, game, civilization, division):
        """Return whether the cities should raise fighters now: always up to the garrisons, and beyond them while the bank holds the reserve and the economics trait does not hold the player back."""
        size = len(division.get_units())
        if size < len(game.get_cities_of(civilization)) * GARRISON:
            return True
        if cls.is_starved(game=game, civilization=civilization):
            return False
        if size >= cls.wanted_size(game=game, civilization=civilization) or cls.bank(game=game, civilization=civilization) < cls.RESERVE:
            return False
        return not cls.favors(game=game, civilization=civilization, trait=ECONOMICS)

    @classmethod
    def plan_division(cls, *, game, civilization):
        """Keep one army with one division whose bases are all the cities, a raise order from the division to each city, and a garrison order for each city."""
        cities = game.get_cities_of(civilization)
        if not cities:
            return
        forces = game.get_civilization(civilization).get_forces()
        if not forces.get_armies():
            OrderControl.add_army(game=game, civilization=civilization)
        if not forces.get_divisions():
            OrderControl.add_division(game=game, civilization=civilization, army=forces.get_armies()[0])
        division = cls.division_of(game=game, civilization=civilization)
        division.set_bases(cities)
        me = division_thing(division.get_id())
        wanted = Units(targets=(BuildTarget(kinds=cls.FIGHTERS, count=cls.wanted_size(game=game, civilization=civilization)),))
        raising = cls.wants_fighters(game=game, civilization=civilization, division=division)
        for city in cities:
            here = city_thing(city)
            orders = cls.given(game=game, civilization=civilization, kind=RaiseOrder, receiver=here)
            order = orders[0] if orders else cls.give(game=game, civilization=civilization, kind=RaiseOrder, giver=me, receiver=here, what=wanted)
            order.set_what(wanted)
            if raising:
                order.activate()
            else:
                order.disable()
            if not cls.given_garrison(game=game, civilization=civilization, city=city):
                cls.give(game=game, civilization=civilization, kind=GarrisonOrder, giver=here, receiver=me, what=Garrison(place=CityTarget(city=city), count=GARRISON))

    @classmethod
    def income(cls, *, game, civilization):
        """Return the primary resource the civilization's cities collect in a turn, before upkeep."""
        primary = game.get_theme().PRIMARY_RESOURCE
        return sum(Harvest.of_city(game=game, city=city).get(primary, 0) for city in game.get_cities_of(civilization))

    @classmethod
    def upkeep(cls, *, game, civilization):
        """Return the primary resource the civilization's units and buildings cost each turn."""
        currency = game.get_catalog().get_id(category=Category.RESOURCES, kind=game.get_theme().PRIMARY_RESOURCE)
        return TurnControl.support_cost(game=game, civilization=civilization).get(currency, 0)

    @classmethod
    def is_starved(cls, *, game, civilization):
        """Return whether the upkeep takes more than the cities collect while the bank is below the reserve, which leaves nothing to build with."""
        return cls.bank(game=game, civilization=civilization) < cls.RESERVE and cls.upkeep(game=game, civilization=civilization) > cls.income(game=game, civilization=civilization)

    @classmethod
    def plan_retirement(cls, *, game, civilization):
        """Retire one fighter a turn beyond the garrisons while the civilization is starved, one outside a city first, so that the upkeep stops taking everything."""
        division = cls.division_of(game=game, civilization=civilization)
        if division is None or not cls.is_starved(game=game, civilization=civilization):
            return
        alive = Knowledge.units_of(game=game, civilization=civilization)
        fighters = [unit for unit in division.get_units() if unit in alive]
        if len(fighters) <= len(game.get_cities_of(civilization)) * GARRISON:
            return
        outside = [unit for unit in fighters if Knowledge.city_of(game=game, unit=unit) == NOTHING]
        unit = (outside or fighters)[-1]
        cls.give(game=game, civilization=civilization, kind=RetireOrder, giver=division_thing(division.get_id()), receiver=unit_thing(unit), what=NoDetails())

    @classmethod
    def given_garrison(cls, *, game, civilization, city):
        return [order for order in cls.given(game=game, civilization=civilization, kind=GarrisonOrder) if order.get_what().place.city == city]

    # War

    @classmethod
    def army_is_ready(cls, *, game, civilization):
        """Return whether the division has every unit it should have, and some beyond the garrisons to march with."""
        division = cls.division_of(game=game, civilization=civilization)
        garrisons = len(game.get_cities_of(civilization)) * GARRISON
        wanted = cls.wanted_size(game=game, civilization=civilization)
        return division is not None and wanted > garrisons and len(division.get_units()) >= wanted

    @classmethod
    def consider_war(cls, *, game, civilization):
        """Declare war on the first civilization met when the army is ready, unless the peace trait holds the player back."""
        if Knowledge.enemies_of(game=game, civilization=civilization) or not cls.army_is_ready(game=game, civilization=civilization):
            return
        if cls.favors(game=game, civilization=civilization, trait=PEACE):
            return
        met = Knowledge.known_civilizations(game=game, civilization=civilization)
        if met:
            Orders.declare_war(game=game, civilization=civilization, on=met[0])

    @classmethod
    def nearest_enemy_city(cls, *, game, civilization):
        """Return the known city of an enemy that is nearest to the civilization's first city, or NOTHING."""
        enemies = Knowledge.enemies_of(game=game, civilization=civilization)
        home = game.get_city(game.get_cities_of(civilization)[0])
        land = game.get_world(home.get_world())
        known = [city for city in Knowledge.known_cities_of(game=game, civilization=civilization, others=enemies) if game.get_city(city).get_world() == home.get_world()]
        if not known:
            return NOTHING
        return min(known, key=lambda city: distance(world=land, from_x=home.get_x(), from_y=home.get_y(), to_x=game.get_city(city).get_x(), to_y=game.get_city(city).get_y()))

    @classmethod
    def march_on(cls, *, game, civilization, city):
        """Return what an order to march on a city says: bold when the boldness trait says so, and ignoring enemy units on the way when aggressive hyperfocus does."""
        bold = cls.favors(game=game, civilization=civilization, trait=BOLDNESS)
        ignore_units = cls.favors(game=game, civilization=civilization, trait=AGGRESSIVE_HYPERFOCUS)
        return March(target=CityTarget(city=city), bold=bold, ignore_units=ignore_units)

    @classmethod
    def plan_march(cls, *, game, civilization):
        """Order the division to march on the nearest known city of an enemy when the army is ready and the conquest trait says so, and take back an order to march on a city that is no longer an enemy's."""
        enemies = Knowledge.enemies_of(game=game, civilization=civilization)
        marching = cls.given(game=game, civilization=civilization, kind=MarchOrder)
        for order in marching:
            if game.get_city(order.get_what().target.city).get_owner() not in enemies:
                cls.table_of(game=game, civilization=civilization).remove(order)
                return
        if marching or not enemies or not game.get_cities_of(civilization) or not cls.army_is_ready(game=game, civilization=civilization):
            return
        target = cls.nearest_enemy_city(game=game, civilization=civilization)
        if target != NOTHING and cls.favors(game=game, civilization=civilization, trait=CONQUEST):
            me = division_thing(cls.division_of(game=game, civilization=civilization).get_id())
            cls.give(game=game, civilization=civilization, kind=MarchOrder, giver=me, receiver=me, what=cls.march_on(game=game, civilization=civilization, city=target))
