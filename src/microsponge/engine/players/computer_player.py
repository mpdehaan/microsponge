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
`Orders`. Each trait tips one decision through `Traits.favors()`. The player never knows a theme: it
reads every kind it raises, builds and researches from the theme's properties, through the
appraisal (`appraisal.py`), so that it plays any theme. A theme may subclass it to change its
weights.
"""

from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.control_points import CONTROL_POINTS, Command
from microsponge.engine.orders.given_order import Reason
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.requirements import known_technologies
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.orders.order import BuildOrder, ExpandOrder, GarrisonOrder, ImproveOrder, MarchOrder, RaiseOrder, ResearchOrder, ResourcesPolicyOrder, RetireOrder, SettlerOrder
from microsponge.engine.orders.order_control import OrderControl
from microsponge.engine.orders.thing import city_thing, civilization_thing, division_thing, unit_thing
from microsponge.engine.orders.what import BuildTarget, Buildings, CityTarget, Garrison, March, NoDetails, PointTarget, Priority, Technologies, Units
from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.unit_kinds import SettlerUnit, can_hit
from microsponge.engine.players.appraisal import Appraisal
from microsponge.engine.players.hand import Hand
from microsponge.engine.players.knowledge import Knowledge, distance
from microsponge.engine.players.traits import AGGRESSIVE_HYPERFOCUS, BOLDNESS, CONQUEST, ECONOMICS, EXPANSION, MOST, PEACE, SCIENCE
from microsponge.engine.turns.orders import Orders
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.unit_control import UnitControl

# Each city keeps this many units of the division inside.
GARRISON = 1
# A division asks for this many units of each kind of use, beyond its fighters.
ONE_EACH = 1
# A civilization of the most expansive traits keeps out one more settler for this many cities.
CITIES_PER_SETTLER = 2
# The best fighters, which most of a division is, by which a division judges what it can hit.
MAIN_BODY = 1
NONE_WANTED = 0


class Weights:
    """What a computer player counts each effect of a kind as worth, when it ranks kinds against each other. A theme's player may subclass these."""

    RESEARCH_WEIGHT = 4
    CONTROL_WEIGHT = 2
    INCOME_WEIGHT = 1
    GROWTH_WEIGHT = 3
    TILE_WEIGHT = 3
    ARMOR_WEIGHT = 3
    LEVEL_WEIGHT = 3
    PRODUCE_WEIGHT = 2
    UPKEEP_WEIGHT = 4
    # What a building that allows a unit counts of the best unit's worth, and what a technology counts of the units it allows.
    ALLOWS_WEIGHT = 10
    UNIT_WEIGHT = 10
    # What a technology counts of the bonuses it gives itself, and of what the technologies it opens allow.
    BONUS_WEIGHT = 1
    OPENS_WEIGHT = 0.5


class ScienceWeights(Weights):
    """The weights of a player whose science trait wins: research and the economy count more than units."""

    RESEARCH_WEIGHT = 8
    UNIT_WEIGHT = 4


class MilitaryWeights(Weights):
    """The weights of a player whose science trait loses: units count more than research."""

    RESEARCH_WEIGHT = 2
    UNIT_WEIGHT = 20
    ALLOWS_WEIGHT = 20


class ComputerPlayer:
    """Static: plays a turn for a computer-played civilization. A theme's player subclasses it and sets what is the theme's."""

    __slots__ = ()
    # The weights for ranking kinds: for buildings, and for research by a player that favors science and by one that does not.
    BUILDING_WEIGHTS = Weights
    SCIENCE_WEIGHTS = ScienceWeights
    MILITARY_WEIGHTS = MilitaryWeights
    # A city with at least this many citizens is ordered to improve its tiles, as the first city always is.
    IMPROVING_CITIZENS = 3
    # How many citizens of a city a resources policy order sets looking for a resource first.
    PRIORITY_CITIZENS = 1
    # How many fighters beyond the garrisons gather before the army marches, when the Command allows that many.
    GROUP_SIZE = 3
    # The currency a civilization keeps before it raises another fighter, so that it does not go bankrupt.
    RESERVE = 10

    @classmethod
    def play_turn(cls, *, game, civilization):
        """Play a civilization's whole turn: set the orders, have the Hand carry them out, and end the turn, unless carrying them out won the game. The orders are kept within the points again before the turn ends, because a city that starts to build stops adding what an idle city adds."""
        cls.plan(game=game, civilization=civilization)
        Hand.carry_out(game=game, civilization=civilization)
        if not game.is_over():
            cls.keep_within_points(game=game, civilization=civilization)
            Orders.end_turn(game=game, civilization=civilization)

    @classmethod
    def plan(cls, *, game, civilization):
        """Bring the civilization's table of orders up to date, and keep it within the civilization's Policy and Command."""
        cls.tidy(game=game, civilization=civilization)
        cls.plan_research(game=game, civilization=civilization)
        cls.plan_first_settlers(game=game, civilization=civilization)
        cls.plan_settlers(game=game, civilization=civilization)
        cls.plan_cities(game=game, civilization=civilization)
        cls.plan_division(game=game, civilization=civilization)
        cls.plan_priorities(game=game, civilization=civilization)
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
            finished = order.get_reason() is Reason.COMPLETED and (order.is_a(SettlerOrder) or order.is_a(ExpandOrder) or order.is_a(MarchOrder) or order.is_a(RetireOrder))
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
        """Give a new research order whenever the technologies the civilization could research next have changed: only those, ranked by what they are worth, with the science weights or the military weights as the science trait decides. The planner sees no further into the tech tree than that, but for the share of what each leads to."""
        known = set(known_technologies(game=game, civilization=civilization))
        researchable = Appraisal.researchable(theme=game.get_theme(), known=known)
        orders = cls.given(game=game, civilization=civilization, kind=ResearchOrder)
        if orders and set(orders[0].get_what().kinds) == set(researchable):
            return
        for order in orders:
            cls.table_of(game=game, civilization=civilization).remove(order)
        if not researchable:
            return
        science_first = cls.favors(game=game, civilization=civilization, trait=SCIENCE)
        weights = cls.SCIENCE_WEIGHTS if science_first else cls.MILITARY_WEIGHTS
        order = tuple(Appraisal.ranked_technologies(theme=game.get_theme(), weights=weights, among=researchable))
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
        """Give every city its build order, with the buildings worth most first and a settler first in the city chosen to build one, and the first city and every large city the order to improve its tiles."""
        cities = game.get_cities_of(civilization)
        buildings = cls.buildings_wanted(game=game, civilization=civilization)
        settling = cls.settling_city(game=game, civilization=civilization)
        settlers = tuple(kind for kind in game.get_theme().UNITS if issubclass(kind, SettlerUnit))
        for city in cities:
            here = city_thing(city)
            wanted = Buildings(kinds=(*settlers, *buildings) if city == settling else buildings)
            orders = cls.given(game=game, civilization=civilization, kind=BuildOrder, receiver=here)
            order = orders[0] if orders else cls.give(game=game, civilization=civilization, kind=BuildOrder, giver=here, receiver=here, what=wanted)
            order.set_what(wanted)
            improving = city == cities[0] or game.get_city(city).get_citizens() >= cls.IMPROVING_CITIZENS
            if improving and Appraisal.engineers(game.get_theme()) and not cls.given(game=game, civilization=civilization, kind=ImproveOrder, receiver=here):
                cls.give(game=game, civilization=civilization, kind=ImproveOrder, giver=here, receiver=here, what=NoDetails())

    @classmethod
    def settlers_wanted(cls, *, game, civilization):
        """Return how many settlers the civilization keeps out at once, read from its expansion trait: none for no expansion at all, and up to one for every two cities, rounded up, for the most expansive."""
        expansion = game.get_civilization(civilization).get_traits().get(EXPANSION)
        return -(-len(game.get_cities_of(civilization)) * expansion // (MOST * CITIES_PER_SETTLER))

    @classmethod
    def settling_city(cls, *, game, civilization):
        """Return the city that should build a settler now, the one with the most citizens that can spare one, or NOTHING when the civilization has as many settlers out or being built as it wants."""
        settlers = tuple(kind for kind in game.get_theme().UNITS if issubclass(kind, SettlerUnit))
        out = len(Knowledge.settlers_of(game=game, civilization=civilization)) + Hand.being_built(game=game, civilization=civilization, kinds=settlers)
        if not settlers or out >= cls.settlers_wanted(game=game, civilization=civilization):
            return NOTHING
        able = [city for city in game.get_cities_of(civilization) if game.get_city(city).get_citizens() > settlers[0].CITIZENS]
        return max(able, key=lambda city: game.get_city(city).get_citizens(), default=NOTHING)

    @classmethod
    def plan_settlers(cls, *, game, civilization):
        """Give each settler with no order an order to expand to the nearest site the civilization remembers, away from the places other settlers are going, or an order to settle on a site of its own when it knows of none."""
        table = cls.table_of(game=game, civilization=civilization)
        led = {order.get_receiver().id for order in table.get_orders() if (order.is_a(SettlerOrder) or order.is_a(ExpandOrder)) and order.is_active()}
        taken = [order.get_what() for order in table.active(ExpandOrder)]
        for unit in Knowledge.settlers_of(game=game, civilization=civilization):
            if unit in led:
                continue
            settler = unit_thing(unit)
            site = Knowledge.nearest_site(game=game, civilization=civilization, unit=unit, taken=taken)
            if site is None:
                cls.give(game=game, civilization=civilization, kind=SettlerOrder, giver=settler, receiver=settler, what=NoDetails())
                continue
            world, x, y = site
            place = PointTarget(world=world, x=x, y=y)
            taken.append(place)
            cls.give(game=game, civilization=civilization, kind=ExpandOrder, giver=settler, receiver=settler, what=place)

    @classmethod
    def buildings_wanted(cls, *, game, civilization):
        """Return the theme's buildings worth most first, leaving out each world wonder another civilization started building first, unless the boldness trait gambles that the earlier builder fails."""
        ranked = Appraisal.ranked_buildings(theme=game.get_theme(), weights=cls.BUILDING_WEIGHTS)
        return tuple(building for building in ranked if not cls.is_raced(game=game, civilization=civilization, building=building))

    @classmethod
    def is_raced(cls, *, game, civilization, building):
        """Return whether a building is a world wonder another civilization is building, which the warning about world wonders tells every player, and the player does not gamble on it."""
        if not Appraisal.is_wonder(building):
            return False
        others = [city for city in Production.wonder_builders(game=game, wonder=building) if game.get_city(city).get_owner() != civilization]
        return bool(others) and not cls.favors(game=game, civilization=civilization, trait=BOLDNESS)

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
        wanted = cls.division_wanted(game=game, civilization=civilization)
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
    def division_wanted(cls, *, game, civilization):
        """Return what the division is raised to, every kind chosen by what it can do and never by its class.

        From the top: for each enemy kind seen that the division's best fighter cannot hit, units
        that can hit it; units the enemy kinds seen cannot hit, to harass them; units that move
        on water and take cities, when an enemy city known is beside water; units that fight on
        water, when a city of the civilization is beside water; and fighters that move on land
        and take cities for the rest.
        """
        theme = game.get_theme()
        size = cls.wanted_size(game=game, civilization=civilization)
        fighters = Appraisal.fighters(theme)
        enemies = cls.enemy_kinds_seen(game=game, civilization=civilization)
        targets = []
        unanswered = [enemy for enemy in enemies if not any(can_hit(kind=kind, target=enemy) for kind in fighters[:MAIN_BODY])]
        for enemy in unanswered[:size // 2]:
            targets.append(BuildTarget(kinds=tuple(Appraisal.counters_to(theme=theme, enemy=enemy)), count=ONE_EACH))
        harassers = Appraisal.unhittable_by(theme=theme, enemies=enemies)
        if harassers:
            targets.append(BuildTarget(kinds=tuple(harassers), count=ONE_EACH))
        water = Appraisal.water_fighters(theme)
        invaders = [kind for kind in water if kind.TAKES_CITIES]
        if invaders and cls.enemy_city_beside_water(game=game, civilization=civilization):
            targets.append(BuildTarget(kinds=tuple(invaders), count=ONE_EACH))
        if water and any(CityControl.is_beside_water(game=game, city=city) for city in game.get_cities_of(civilization)):
            targets.append(BuildTarget(kinds=tuple(water), count=ONE_EACH))
        targets = [target for target in targets if target.kinds][:max(size - GARRISON, NONE_WANTED)]
        targets.append(BuildTarget(kinds=tuple(fighters), count=max(size - len(targets), GARRISON)))
        return Units(targets=tuple(targets))

    @classmethod
    def enemy_kinds_seen(cls, *, game, civilization):
        """Return the kinds of the other civilizations' units the civilization sees, each once."""
        seen = [UnitControl.kind_of(game=game, unit=unit) for unit in Sight.view(game=game, civilization=civilization).units_seen()]
        return list(dict.fromkeys(seen))

    @classmethod
    def enemy_city_beside_water(cls, *, game, civilization):
        """Return whether the civilization knows a city of an enemy beside water."""
        enemies = Knowledge.enemies_of(game=game, civilization=civilization)
        known = Knowledge.known_cities_of(game=game, civilization=civilization, others=enemies)
        return any(CityControl.is_beside_water(game=game, city=city) for city in known)

    # What citizens look for

    @classmethod
    def plan_priorities(cls, *, game, civilization):
        """Order a city's citizens to look first for a resource the city's next building costs and the bank lacks, and take back the orders no longer needed."""
        for city in game.get_cities_of(civilization):
            here = city_thing(city)
            lacking = cls.lacking_resource(game=game, civilization=civilization, city=city)
            for order in cls.given(game=game, civilization=civilization, kind=ResourcesPolicyOrder, receiver=here):
                if lacking is None or order.get_what().resource is not lacking:
                    cls.table_of(game=game, civilization=civilization).remove(order)
            if lacking is not None and not cls.given(game=game, civilization=civilization, kind=ResourcesPolicyOrder, receiver=here):
                cls.give(game=game, civilization=civilization, kind=ResourcesPolicyOrder, giver=here, receiver=here, what=Priority(resource=lacking, citizens=cls.PRIORITY_CITIZENS))

    @classmethod
    def lacking_resource(cls, *, game, civilization, city):
        """Return a resource other than the primary one and food that the first building the city's build order wants costs more of than the bank holds, or None."""
        theme = game.get_theme()
        orders = cls.given(game=game, civilization=civilization, kind=BuildOrder, receiver=city_thing(city))
        if not orders:
            return None
        holder = game.get_civilization(civilization)
        for building in orders[0].get_what().kinds:
            if Production.problem_queueing(game=game, city=city, kind=building) is not None:
                continue
            for resource, amount in building.COST.items():
                if resource not in (theme.PRIMARY_RESOURCE, theme.FOOD) and holder.get_amount(game.get_catalog().get_id(category=Category.RESOURCES, kind=resource)) < amount:
                    return resource
            return None
        return None

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
