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

"""The Hand: the helper AI that carries out a civilization's standing orders.

The Hand is the sergeant and not the general (`GAME_RULES.md`, "Priorities and the helper
AI"): it follows the orders in a civilization's table, for a person and for a computer player
alike, and does nothing no order asks for, except that a civilization with a technology left
to pick and no research order researches one at random. It touches the units and the cities
only through the single actions of `helper_ai.py`, each one led by a standing order, and reads
the map only through the civilization's view and memory. Where the Hand has to decide
something an order leaves open, it makes orders of its own in the table, its realized orders,
which cost nothing and which no player reads.
"""

from collections import deque

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.research import Research
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.orders.order import BuildOrder, BuildTargetOrder, ExpandOrder, GarrisonOrder, MarchOrder, RaiseOrder, ResearchOrder, SettlerOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.referee import Referee
from microsponge.engine.orders.thing import city_thing, unit_thing
from microsponge.engine.orders.what import NoDetails
from microsponge.engine.players.helper_ai import HelperAI
from microsponge.engine.players.knowledge import Knowledge, distance
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.land import NEIGHBORS, Land
from microsponge.engine.world.layer import Layer
from microsponge.ui_strings import MSG_CITY_NUMBERED

# The next city a civilization founds is numbered from 1.
FIRST_CITY_NUMBER = 1
# The first turn of a build, whose part of the cost is the largest.
FIRST_PART = 0
# The most tiles the search for a route looks at before it gives up.
ROUTE_TILES = 4000


def try_order(order):
    """Give an order, and return whether the game took it: a refused order changes nothing, and the Hand tries something else."""
    try:
        order()
    except ValueError:
        return False
    return True


class Hand:
    """Static: carries out the standing orders of a civilization on the civilization's turn. It is never made into an object."""

    __slots__ = ()

    @classmethod
    def carry_out(cls, *, game, civilization):
        """Do this turn's work for every active order of a civilization: the referee reviews the orders first, new units join what asked for them, and then research, the cities, the settlers and the divisions are seen to."""
        Referee.review(game=game, civilization=civilization)
        cls.muster(game=game, civilization=civilization)
        cls.research(game=game, civilization=civilization)
        cls.direct_cities(game=game, civilization=civilization)
        cls.direct_settlers(game=game, civilization=civilization)
        cls.direct_divisions(game=game, civilization=civilization)

    @classmethod
    def table_of(cls, *, game, civilization):
        return game.get_civilization(civilization).get_orders()

    @classmethod
    def forces_of(cls, *, game, civilization):
        return game.get_civilization(civilization).get_forces()

    @classmethod
    def theme_order(cls, *, game, kind):
        """Return the theme's own kind of an order, which may be a subclass with other costs, or None when the theme has no such order."""
        for order in game.get_theme().ORDERS:
            if issubclass(order, kind):
                return order
        return None

    # New units

    @classmethod
    def muster(cls, *, game, civilization):
        """Drop the realized orders that are finished, take dead units out of their divisions, put each new fighter in the division that asked for it, and send each new settler to settle for a city that was ordered to expand."""
        alive = Knowledge.units_of(game=game, civilization=civilization)
        forces = cls.forces_of(game=game, civilization=civilization)
        table = cls.table_of(game=game, civilization=civilization)
        for order in table.get_realized():
            if not order.is_active():
                table.remove(order)
        for division in forces.get_divisions():
            for unit in division.get_units():
                if unit not in alive:
                    division.remove_unit(unit)
        led = [order.get_receiver().id for order in cls.table_of(game=game, civilization=civilization).active(SettlerOrder)]
        for unit in alive:
            if Knowledge.is_settler(game=game, unit=unit):
                if unit not in led:
                    cls.send_settler(game=game, civilization=civilization, unit=unit)
            elif Knowledge.is_fighter(game=game, unit=unit) and forces.division_of(unit) is None:
                cls.enlist(game=game, civilization=civilization, unit=unit)

    @classmethod
    def send_settler(cls, *, game, civilization, unit):
        """Give a settler no order leads a realized order to settle, from the first city ordered to expand. With no such city the settler waits."""
        kind = cls.theme_order(game=game, kind=SettlerOrder)
        expanding = cls.table_of(game=game, civilization=civilization).active(ExpandOrder)
        if kind is not None and expanding:
            OrderControl.give(game=game, civilization=civilization, kind=kind, giver=expanding[0].get_receiver(), receiver=unit_thing(unit), what=NoDetails(), realized=True)

    @classmethod
    def count_of(cls, *, game, division, target):
        """Return how many units of a build target's kinds a division has."""
        return len([unit for unit in division.get_units() if UnitControl.kind_of(game=game, unit=unit) in target.kinds])

    @classmethod
    def unmet_target(cls, *, game, civilization, order):
        """Return the first build target of a raise order that the giving division has not reached, counting units still being built, or None."""
        division = cls.forces_of(game=game, civilization=civilization).get_division(order.get_giver().id)
        for target in order.get_what().targets:
            if cls.count_of(game=game, division=division, target=target) + cls.being_built(game=game, civilization=civilization, kinds=target.kinds) < target.count:
                return target
        return None

    @classmethod
    def enlist(cls, *, game, civilization, unit):
        """Put a fighter that is in no division into the division of the first raise order that wants its kind, or else into the first division. With no division the unit waits."""
        forces = cls.forces_of(game=game, civilization=civilization)
        kind = UnitControl.kind_of(game=game, unit=unit)
        for order in cls.table_of(game=game, civilization=civilization).active(RaiseOrder):
            division = forces.get_division(order.get_giver().id)
            for target in order.get_what().targets:
                if kind in target.kinds and cls.count_of(game=game, division=division, target=target) < target.count:
                    division.add_unit(unit)
                    return
        if forces.get_divisions():
            forces.get_divisions()[0].add_unit(unit)

    # Research

    @classmethod
    def research(cls, *, game, civilization):
        """Pick the next technology when the game asks for one: the first a research order lists that can be researched, or else one at random."""
        if not Research.must_choose(game=game, civilization=civilization):
            return
        available = Research.available(game=game, civilization=civilization)
        orders = cls.table_of(game=game, civilization=civilization).active(ResearchOrder)
        wanted = [technology for order in orders for technology in order.get_what().kinds if technology in available]
        choice = wanted[0] if wanted else game.get_random().choice(available)
        Orders.research(game=game, civilization=civilization, technology=choice)

    # Cities

    @classmethod
    def can_pay_a_part(cls, *, game, civilization, kind):
        """Return whether the civilization holds the first part of each resource a kind costs, so that the build is not blocked at once."""
        holder = game.get_civilization(civilization)
        catalog = game.get_catalog()
        first_part = Production.part(kind=kind, turn=FIRST_PART)
        return all(holder.get_amount(catalog.get_id(category=Category.RESOURCES, kind=resource)) >= amount for resource, amount in first_part.items())

    @classmethod
    def buildable(cls, *, game, city, kinds, except_for=None):
        """Return the first of some kinds the city can build now and pay the first part of, leaving one kind out, or None."""
        owner = game.get_city(city).get_owner()
        for kind in kinds:
            if kind is not except_for and Production.problem_queueing(game=game, city=city, kind=kind) is None and cls.can_pay_a_part(game=game, civilization=owner, kind=kind):
                return kind
        return None

    @classmethod
    def being_built(cls, *, game, civilization, kinds):
        """Return how many of the civilization's cities are building one of some kinds now."""
        queues = [game.get_city(city).get_queue() for city in game.get_cities_of(civilization)]
        return len([queue for queue in queues if queue and Production.kind_of(game=game, item=queue[0]) in kinds])

    @classmethod
    def settler_kinds(cls, *, game):
        return tuple(kind for kind in game.get_theme().UNITS if issubclass(kind, SettlerUnit))

    @classmethod
    def wanted_build(cls, *, game, civilization, city, order, except_for):
        """Return what a city should build for one order, leaving one kind out, or None when the order wants nothing the city can build now.

        A build order wants its first building the city lacks. A raise order wants the first
        kind of its first unmet build target, and is completed when every target is met. An
        expand order wants a settler while the civilization has none alive or being built.
        """
        what = order.get_what()
        if order.is_a(BuildOrder):
            return cls.buildable(game=game, city=city, kinds=what.kinds, except_for=except_for)
        if order.is_a(RaiseOrder):
            target = cls.unmet_target(game=game, civilization=civilization, order=order)
            if target is None:
                order.complete()
                return None
            return cls.buildable(game=game, city=city, kinds=target.kinds, except_for=except_for)
        settlers = cls.settler_kinds(game=game)
        if Knowledge.settlers_of(game=game, civilization=civilization) or cls.being_built(game=game, civilization=civilization, kinds=settlers):
            return None
        return cls.buildable(game=game, city=city, kinds=settlers, except_for=except_for)

    @classmethod
    def orders_for_city(cls, *, game, civilization, city):
        """Return the active orders that aim at things a city builds, the order that has waited longest first."""
        orders = [order for order in cls.table_of(game=game, civilization=civilization).active(BuildTargetOrder) if order.get_receiver() == city_thing(city)]
        return sorted(orders, key=lambda order: order.get_served())

    @classmethod
    def start_build(cls, *, game, civilization, city, blocked):
        """Have a city start on what the order that has waited longest wants, in place of a blocked build when there is one."""
        give = HelperAI.build if blocked is None else HelperAI.build_instead
        for order in cls.orders_for_city(game=game, civilization=civilization, city=city):
            kind = cls.wanted_build(game=game, civilization=civilization, city=city, order=order, except_for=blocked)
            if kind is not None and try_order(lambda: give(game=game, city=city, kind=kind)):
                order.set_served(game.get_turn())
                return

    @classmethod
    def direct_cities(cls, *, game, civilization):
        """Have each city with nothing to build, and each city whose build is blocked, start on what its orders want."""
        for city in Production.waiting_cities(game=game, civilization=civilization):
            cls.start_build(game=game, civilization=civilization, city=city, blocked=None)
        for city in Production.blocked_cities(game=game, civilization=civilization):
            blocked = Production.kind_of(game=game, item=game.get_city(city).get_queue()[0])
            cls.start_build(game=game, civilization=civilization, city=city, blocked=blocked)

    # Moving

    @classmethod
    def can_walk_through(cls, *, game, civilization, world, x, y, walkable, at_peace):
        """Return whether a route may pass over a tile: a tile never seen is taken to be passable, and a tile seen has to be of a terrain the unit can be on, outside every city center, and outside known foreign land for a unit that is not marching to war."""
        memory = game.get_civilization(civilization).get_memory(world)
        if not memory.has_seen(x=x, y=y):
            return True
        if memory.get_value(layer=Layer.TERRAIN, x=x, y=y) not in walkable or memory.get_value(layer=Layer.CITY_CENTER, x=x, y=y) != NOTHING:
            return False
        return not (at_peace and Knowledge.is_in_foreign_land(game=game, civilization=civilization, world=world, x=x, y=y))

    @classmethod
    def first_step(cls, *, game, unit, civilization, arrived, at_peace=True):
        """Return the first tile, as (x, y), of the shortest walk from a unit to the nearest tile where arrived(x, y) is true, or None when the search finds no such tile within ROUTE_TILES tiles.

        The search spreads out from the unit over the tiles a route may pass over, by what the
        civilization remembers, so that a unit walks around a lake rather than into it.
        """
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        land = game.get_world(world)
        walkable = Land.walkable_terrains(game=game, kind=UnitControl.kind_of(game=game, unit=unit))
        first = {(x, y): None}
        queue = deque([(x, y)])
        while queue and len(first) < ROUTE_TILES:
            here = queue.popleft()
            for dx, dy in NEIGHBORS:
                tile = (land.column(here[0] + dx), here[1] + dy)
                if not 0 <= tile[1] < land.get_height() or tile in first:
                    continue
                step = first[here] or tile
                if arrived(tile[0], tile[1]):
                    return step
                first[tile] = step
                if cls.can_walk_through(game=game, civilization=civilization, world=world, x=tile[0], y=tile[1], walkable=walkable, at_peace=at_peace):
                    queue.append(tile)
        return None

    @classmethod
    def walk(cls, *, game, unit, civilization, arrived, at_peace=True):
        """Move a unit one tile along the shortest walk to the nearest tile where arrived(x, y) is true, and return whether the unit moved."""
        step = cls.first_step(game=game, unit=unit, civilization=civilization, arrived=arrived, at_peace=at_peace)
        return step is not None and try_order(lambda: HelperAI.move(game=game, unit=unit, x=step[0], y=step[1], led=True))

    @classmethod
    def walk_to_city(cls, *, game, unit, civilization, city, at_peace=True):
        """Move a unit one tile toward the tiles around a city center, and return whether the unit moved."""
        around = CityControl.ring_tiles(game=game, city=city)
        return cls.walk(game=game, unit=unit, civilization=civilization, arrived=lambda x, y: (x, y) in around, at_peace=at_peace)

    @classmethod
    def leave_city(cls, *, game, unit):
        """Send a unit out of its city onto the first free tile around the center, and return whether it left."""
        city = Knowledge.city_of(game=game, unit=unit)
        kind = UnitControl.kind_of(game=game, unit=unit)
        for x, y in CityControl.free_ring_tiles(game=game, city=city, kind=kind):
            if try_order(lambda: HelperAI.leave_city(game=game, unit=unit, x=x, y=y, led=True)):
                return True
        return False

    @classmethod
    def is_next_to_center(cls, *, game, unit, city):
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        return game.get_city(city).get_world() == world and (x, y) in CityControl.ring_tiles(game=game, city=city)

    @classmethod
    def repeat(cls, *, game, unit, action):
        """Have a unit do one thing after another while it can, at most once for each of its kind's action points."""
        for _ in range(UnitControl.kind_of(game=game, unit=unit).ACTION_POINTS):
            if unit not in game.get_units().get_ids() or not action():
                return

    # Settlers

    @classmethod
    def direct_settlers(cls, *, game, civilization):
        """Carry out each order for a settler, and complete the order when the settler has built its city."""
        for order in cls.table_of(game=game, civilization=civilization).active(SettlerOrder):
            if cls.settle(game=game, unit=order.get_receiver().id, civilization=civilization):
                order.complete()

    @classmethod
    def settle(cls, *, game, unit, civilization):
        """Have a settler build a city where it stands and return True, or else leave its city, walk toward the nearest site it remembers or explore toward the nearest tile never seen, and return False."""
        if Knowledge.city_of(game=game, unit=unit) != NOTHING:
            cls.leave_city(game=game, unit=unit)
            return False
        if CityControl.problem_founding(game=game, settler=unit) is None:
            name = cls.next_city_name(game=game, civilization=civilization)
            return try_order(lambda: HelperAI.found_city(game=game, settler=unit, name=name, led=True))
        world, _, _ = UnitControl.tile_of(game=game, unit=unit)
        if not cls.walk(game=game, unit=unit, civilization=civilization, arrived=lambda x, y: cls.is_site(game=game, civilization=civilization, world=world, x=x, y=y)):
            cls.walk(game=game, unit=unit, civilization=civilization, arrived=lambda x, y: cls.is_unseen(game=game, civilization=civilization, world=world, x=x, y=y))
        return False

    @classmethod
    def is_unseen(cls, *, game, civilization, world, x, y):
        """Return whether a tile is one the civilization has never seen and that is not in known foreign land: where a settler explores toward."""
        memory = game.get_civilization(civilization).get_memory(world)
        return not memory.has_seen(x=x, y=y) and not Knowledge.is_in_foreign_land(game=game, civilization=civilization, world=world, x=x, y=y)

    @classmethod
    def is_site(cls, *, game, civilization, world, x, y):
        """Return whether the civilization remembers a tile as one where a city could be built.

        A tile never seen, or too close to a city the civilization knows of, is passed over
        before the full check of the site, which reads the whole city radius, so that the
        search stays cheap.
        """
        memory = game.get_civilization(civilization).get_memory(world)
        if not memory.has_seen(x=x, y=y):
            return False
        land = game.get_world(world)
        too_close = game.get_theme().CITY.RADIUS_SIZE
        known = [game.get_city(city) for city in game.get_city_ids() if memory.get_owner(city) != NOTHING and game.get_city(city).get_world() == world]
        if any(distance(world=land, from_x=x, from_y=y, to_x=city.get_x(), to_y=city.get_y()) < too_close for city in known):
            return False
        return CityControl.problem_with_site(game=game, tiles=memory, x=x, y=y) is None

    @classmethod
    def next_city_name(cls, *, game, civilization):
        holder = game.get_civilization(civilization)
        return MSG_CITY_NUMBERED.format(civilization=holder.get_name(), number=holder.get_cities_founded() + FIRST_CITY_NUMBER)

    # Divisions

    @classmethod
    def direct_divisions(cls, *, game, civilization):
        """Carry out the garrison orders and then the march orders. A unit a garrison order keeps is never moved by another order."""
        table = cls.table_of(game=game, civilization=civilization)
        kept = []
        garrisons = table.active(GarrisonOrder)
        for order in garrisons:
            kept += cls.already_inside(game=game, civilization=civilization, order=order, kept=kept)
        for order in garrisons:
            kept += cls.fill_garrison(game=game, civilization=civilization, order=order, kept=kept)
        for order in table.active(MarchOrder):
            cls.march(game=game, civilization=civilization, order=order, kept=kept)

    @classmethod
    def division_units(cls, *, game, civilization, order):
        return cls.forces_of(game=game, civilization=civilization).get_division(order.get_receiver().id).get_units()

    @classmethod
    def already_inside(cls, *, game, civilization, order, kept):
        """Return the units of a garrison order's division that are inside the order's city and that no order keeps yet, as many as the order wants at most."""
        what = order.get_what()
        units = cls.division_units(game=game, civilization=civilization, order=order)
        inside = [unit for unit in units if unit not in kept and Knowledge.city_of(game=game, unit=unit) == what.place.city]
        return inside[:what.count]

    @classmethod
    def fill_garrison(cls, *, game, civilization, order, kept):
        """Send the nearest free units of a garrison order's division toward the order's city until the order has the units it wants, and return the units sent."""
        what = order.get_what()
        city = what.place.city
        units = cls.division_units(game=game, civilization=civilization, order=order)
        inside = [unit for unit in units if unit in kept and Knowledge.city_of(game=game, unit=unit) == city]
        free = [unit for unit in units if unit not in kept and Knowledge.city_of(game=game, unit=unit) != city]
        free.sort(key=lambda unit: Knowledge.steps_to_city(game=game, unit=unit, city=city))
        sent = free[:max(0, what.count - len(inside))]
        for unit in sent:
            cls.repeat(game=game, unit=unit, action=lambda: cls.go_into(game=game, unit=unit, civilization=civilization, city=city))
        return sent

    @classmethod
    def go_into(cls, *, game, unit, civilization, city):
        """Bring a unit one action closer to being inside a city, and return whether the unit did anything."""
        if Knowledge.city_of(game=game, unit=unit) == city:
            return False
        if Knowledge.city_of(game=game, unit=unit) != NOTHING:
            return cls.leave_city(game=game, unit=unit)
        if cls.is_next_to_center(game=game, unit=unit, city=city):
            return try_order(lambda: HelperAI.enter_city(game=game, unit=unit, city=city, led=True))
        return cls.walk_to_city(game=game, unit=unit, civilization=civilization, city=city)

    @classmethod
    def march(cls, *, game, civilization, order, kept):
        """Send the free units of a march order's division against the order's target, and complete the order when the civilization is seen to own the target."""
        city = order.get_what().target.city
        if Sight.view(game=game, civilization=civilization).owner_of(city) == civilization:
            order.complete()
            return
        for unit in cls.division_units(game=game, civilization=civilization, order=order):
            if unit not in kept:
                cls.repeat(game=game, unit=unit, action=lambda: cls.advance(game=game, unit=unit, civilization=civilization, what=order.get_what()))

    @classmethod
    def advance(cls, *, game, unit, civilization, what):
        """Have a marching unit leave its city, or fight what is next to it, or step toward its target, and return whether the unit did anything. A unit inside the target has arrived."""
        inside = Knowledge.city_of(game=game, unit=unit)
        if inside == what.target.city:
            return False
        if inside != NOTHING:
            return cls.leave_city(game=game, unit=unit)
        if cls.fight_next_to(game=game, unit=unit, civilization=civilization, what=what):
            return True
        return cls.walk_to_city(game=game, unit=unit, civilization=civilization, city=what.target.city, at_peace=False)

    @classmethod
    def fight_next_to(cls, *, game, unit, civilization, what):
        """Attack an enemy on a tile next to the unit, or walk into an empty enemy city, and return whether the unit did either.

        Any unit attacks an enemy city next to it. An enemy unit is left alone when the march
        order says to ignore units, and is otherwise attacked when the numbers say the attack
        is worth it, or whatever the numbers say when the march order is bold.
        """
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        land = game.get_world(world)
        view = Sight.view(game=game, civilization=civilization)
        enemies = Knowledge.enemies_of(game=game, civilization=civilization)
        for dx, dy in NEIGHBORS:
            next_x, next_y = x + dx, y + dy
            if not 0 <= next_y < land.get_height():
                continue
            city = land.get_value(layer=Layer.CITY_CENTER, x=next_x, y=next_y)
            if city != NOTHING and game.get_city(city).get_owner() in enemies:
                if game.get_city(city).get_units():
                    return try_order(lambda: HelperAI.attack(game=game, unit=unit, x=next_x, y=next_y, led=True))
                return try_order(lambda: HelperAI.enter_city(game=game, unit=unit, city=city, led=True))
            other = view.unit_on(world=world, x=next_x, y=next_y)
            if other != NOTHING and game.get_units().get_value(column=UnitColumn.OWNER, unit=other) in enemies and not what.ignore_units and (what.bold or cls.worth_attacking(game=game, unit=unit, other=other)):
                return try_order(lambda: HelperAI.attack(game=game, unit=unit, x=next_x, y=next_y, led=True))
        return False

    @classmethod
    def worth_attacking(cls, *, game, unit, other):
        """Return whether a unit should attack another: when it would kill the other in no more attacks than the other needs to kill it."""
        theme = game.get_theme()
        mine = UnitControl.attacks_to_kill(theme=theme, attacker=UnitControl.kind_of(game=game, unit=unit), defender=UnitControl.kind_of(game=game, unit=other))
        theirs = UnitControl.attacks_to_kill(theme=theme, attacker=UnitControl.kind_of(game=game, unit=other), defender=UnitControl.kind_of(game=game, unit=unit))
        return mine is not None and (theirs is None or mine <= theirs)
