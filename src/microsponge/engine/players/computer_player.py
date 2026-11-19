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

"""The computer player: the algorithm that plays a civilization's turn by the civilization's traits.

The player is a list of rules tried in order each turn, with no search ahead
(`AI_STRATEGIES_CAVEMAN.md`, "How Claude would try to win"): pick research, settle, garrison the
cities and march on the enemy, tell the cities what to build, end the turn. The player reads the
map only through the civilization's `View`, so it never sees through the fog of war, and gives
every order through `Orders`, as a person would, trying each move and letting a refused order
change nothing. Each trait tips one decision in one place, through `Traits.favors()`. The
players of each theme are subclasses that say which kinds are the theme's: `CavemanPlayer` in
the caveman theme is the first.
"""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.research import Research
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.players.traits import AGGRESSIVE_HYPERFOCUS, BOLDNESS, CONQUEST, ECONOMICS, EXPANSION, PEACE, SCIENCE
from microsponge.engine.turns.orders import Orders
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.world.land import NEIGHBORS
from microsponge.engine.world.layer import Layer
from microsponge.ui_strings import MSG_CITY_NUMBERED

# A city holds at least this many units for the player to send one out.
ONE_DEFENDER = 1
# The next city a civilization founds is numbered from 1.
FIRST_CITY_NUMBER = 1
# The first turn of a build, whose part of the cost is the largest.
FIRST_PART = 0


def ring(*, x, y, reach):
    """Return the tiles exactly so many moves from a tile, as (x, y), which may be off the map: the tile itself at a reach of 0."""
    if reach == 0:
        return [(x, y)]
    tiles = [(x + dx, y - reach) for dx in range(-reach, reach + 1)] + [(x + dx, y + reach) for dx in range(-reach, reach + 1)]
    tiles += [(x - reach, y + dy) for dy in range(-reach + 1, reach)] + [(x + reach, y + dy) for dy in range(-reach + 1, reach)]
    return tiles


def distance(*, world, from_x, from_y, to_x, to_y):
    """Return how many moves apart two tiles are, going around the world the shorter way, since a unit moves diagonally as easily as straight."""
    return max(world.columns_apart(first=from_x, second=to_x), abs(from_y - to_y))


class ComputerPlayer:
    """Static: plays a turn for a computer-played civilization. A theme's player subclasses it and sets what is the theme's."""

    __slots__ = ()
    # The technologies worth researching, in order, for a player that favors science and for one that favors the army.
    SCIENCE_RESEARCH = ()
    MILITARY_RESEARCH = ()
    # The kinds that defend a city and that attack, best first, and the buildings for the economy, in order.
    DEFENDERS = ()
    ATTACKERS = ()
    ECONOMY = ()
    # How many fighters gather before the army marches.
    GROUP_SIZE = 3
    # The currency a civilization keeps before it builds another fighter, so that it does not go bankrupt.
    RESERVE = 10

    @classmethod
    def play_turn(cls, *, game, civilization):
        """Play a civilization's whole turn and end it."""
        cls.pick_research(game=game, civilization=civilization)
        cls.settle(game=game, civilization=civilization)
        cls.consider_war(game=game, civilization=civilization)
        cls.command_fighters(game=game, civilization=civilization)
        cls.decide_builds(game=game, civilization=civilization)
        Orders.end_turn(game=game, civilization=civilization)

    # What the player knows

    @classmethod
    def traits_of(cls, *, game, civilization):
        return game.get_civilization(civilization).get_traits()

    @classmethod
    def favors(cls, *, game, civilization, trait):
        return cls.traits_of(game=game, civilization=civilization).favors(trait=trait, random=game.get_random())

    @classmethod
    def units_of(cls, *, game, civilization):
        return Sight.units_of(game=game, civilization=civilization)

    @classmethod
    def is_settler(cls, *, game, unit):
        return issubclass(UnitControl.kind_of(game=game, unit=unit), SettlerUnit)

    @classmethod
    def is_fighter(cls, *, game, unit):
        return UnitControl.kind_of(game=game, unit=unit).ATTACK is not NO_DICE

    @classmethod
    def fighters_of(cls, *, game, civilization):
        return [unit for unit in cls.units_of(game=game, civilization=civilization) if cls.is_fighter(game=game, unit=unit)]

    @classmethod
    def city_of(cls, *, game, unit):
        """Return the id of the city a unit is inside, or NOTHING."""
        return game.get_units().get_value(column=UnitColumn.CITY, unit=unit)

    @classmethod
    def nearest_city(cls, *, game, unit, cities):
        """Return the id of the nearest of some cities to a unit on the same world, or NOTHING."""
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        land = game.get_world(world)
        same_world = [city for city in cities if game.get_city(city).get_world() == world]
        if not same_world:
            return NOTHING
        return min(same_world, key=lambda city: distance(world=land, from_x=x, from_y=y, to_x=game.get_city(city).get_x(), to_y=game.get_city(city).get_y()))

    @classmethod
    def enemies_of(cls, *, game, civilization):
        """Return the ids of the civilizations this one is at war with and that are still playing."""
        holder = game.get_civilization(civilization)
        return [other for other in game.get_still_playing() if holder.is_at_war_with(other)]

    @classmethod
    def known_cities_of(cls, *, game, civilization, others):
        """Return the cities the civilization knows to belong to any of some other civilizations, as last seen."""
        view = Sight.view(game=game, civilization=civilization)
        return [city for city in game.get_city_ids() if view.owner_of(city) in others]

    @classmethod
    def known_civilizations(cls, *, game, civilization):
        """Return the other civilizations this one has met: whose unit it sees or whose city it has seen."""
        view = Sight.view(game=game, civilization=civilization)
        units = game.get_units()
        met = {units.get_value(column=UnitColumn.OWNER, unit=unit) for unit in view.units_seen()}
        met.update(view.owner_of(city) for city in game.get_city_ids())
        return sorted(other for other in met - {NOTHING, civilization} if not game.get_civilization(other).has_lost())

    # Moving

    @classmethod
    def try_order(cls, order):
        """Give an order, and return whether the game took it: a refused order changes nothing, and the player tries something else."""
        try:
            order()
        except ValueError:
            return False
        return True

    @classmethod
    def step_toward(cls, *, game, unit, to_x, to_y):
        """Move a unit one tile toward a tile, by the first neighboring tile that brings it closer and that the game lets it onto, and return whether it moved."""
        return cls.step(game=game, unit=unit, to_x=to_x, to_y=to_y, closer=True)

    @classmethod
    def step_away(cls, *, game, unit, from_x, from_y):
        """Move a unit one tile away from a tile the same way, and return whether it moved."""
        return cls.step(game=game, unit=unit, to_x=from_x, to_y=from_y, closer=False)

    @classmethod
    def step(cls, *, game, unit, to_x, to_y, closer):
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        land = game.get_world(world)
        here = distance(world=land, from_x=x, from_y=y, to_x=to_x, to_y=to_y)
        options = [(x + dx, y + dy) for dx, dy in NEIGHBORS if 0 <= y + dy < land.get_height()]
        options.sort(key=lambda tile: distance(world=land, from_x=tile[0], from_y=tile[1], to_x=to_x, to_y=to_y), reverse=not closer)
        for next_x, next_y in options:
            there = distance(world=land, from_x=next_x, from_y=next_y, to_x=to_x, to_y=to_y)
            if (there < here) != closer and there != here:
                break
            if cls.try_order(lambda: Orders.move(game=game, unit=unit, x=next_x, y=next_y)):
                return True
        return False

    @classmethod
    def leave_city(cls, *, game, unit):
        """Send a unit out of its city onto the first free tile around the center, and return whether it left."""
        city = cls.city_of(game=game, unit=unit)
        kind = UnitControl.kind_of(game=game, unit=unit)
        for x, y in CityControl.free_ring_tiles(game=game, city=city, kind=kind):
            if cls.try_order(lambda: Orders.leave_city(game=game, unit=unit, x=x, y=y)):
                return True
        return False

    # Research

    @classmethod
    def pick_research(cls, *, game, civilization):
        """Pick the next technology when the game asks for one: the first in the science order or the military order that can be researched, as the science trait decides."""
        if not Research.must_choose(game=game, civilization=civilization):
            return
        available = Research.available(game=game, civilization=civilization)
        science_first = cls.favors(game=game, civilization=civilization, trait=SCIENCE)
        order = (*cls.SCIENCE_RESEARCH, *cls.MILITARY_RESEARCH) if science_first else (*cls.MILITARY_RESEARCH, *cls.SCIENCE_RESEARCH)
        wanted = [technology for technology in order if technology in available]
        Orders.research(game=game, civilization=civilization, technology=(wanted or available)[0])

    # Settling

    @classmethod
    def settle(cls, *, game, civilization):
        """Have each settler found a city where it stands, else walk toward the nearest site it remembers, else explore toward the nearest tile never seen."""
        for unit in cls.units_of(game=game, civilization=civilization):
            if not cls.is_settler(game=game, unit=unit):
                continue
            if cls.city_of(game=game, unit=unit) != NOTHING:
                cls.leave_city(game=game, unit=unit)
                continue
            if CityControl.problem_founding(game=game, settler=unit) is None:
                cls.try_order(lambda: Orders.found_city(game=game, settler=unit, name=cls.next_city_name(game=game, civilization=civilization)))
                continue
            site = cls.nearest_site(game=game, unit=unit, civilization=civilization)
            if site is None:
                site = cls.nearest_unseen(game=game, unit=unit, civilization=civilization)
            if site is not None and not cls.step_toward(game=game, unit=unit, to_x=site[0], to_y=site[1]):
                cls.step_out_of_a_corner(game=game, unit=unit, civilization=civilization)

    @classmethod
    def step_out_of_a_corner(cls, *, game, unit, civilization):
        """Move a unit that could not step toward its goal away from the nearest known foreign city, so that it is not stuck against a border for ever."""
        world, _, _ = UnitControl.tile_of(game=game, unit=unit)
        foreign = [city for city in game.get_city_ids() if game.get_city(city) in cls.foreign_cities(game=game, civilization=civilization, world=world)]
        nearest = cls.nearest_city(game=game, unit=unit, cities=foreign)
        if nearest != NOTHING:
            cls.step_away(game=game, unit=unit, from_x=game.get_city(nearest).get_x(), from_y=game.get_city(nearest).get_y())

    @classmethod
    def foreign_cities(cls, *, game, civilization, world):
        """Return the cities of other civilizations on a world that the civilization knows of."""
        memory = game.get_civilization(civilization).get_memory(world)
        return [game.get_city(city) for city in game.get_city_ids() if memory.get_owner(city) not in (NOTHING, civilization) and game.get_city(city).get_world() == world]

    @classmethod
    def is_in_foreign_land(cls, *, game, civilization, world, x, y):
        """Return whether a tile lies within the city radius of a known city of another civilization, where a unit may not go without a war."""
        half = game.get_theme().CITY.RADIUS_SIZE // 2
        land = game.get_world(world)
        return any(distance(world=land, from_x=x, from_y=y, to_x=city.get_x(), to_y=city.get_y()) <= half for city in cls.foreign_cities(game=game, civilization=civilization, world=world))

    @classmethod
    def nearest_unseen(cls, *, game, unit, civilization):
        """Return the nearest tile the civilization has never seen and that is not in known foreign land, as (x, y), or None: where a settler explores toward."""
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        memory = game.get_civilization(civilization).get_memory(world)
        land = game.get_world(world)
        for reach in range(1, max(land.get_width() // 2, land.get_height()) + 1):
            for tile_x, tile_y in ring(x=x, y=y, reach=reach):
                if 0 <= tile_y < land.get_height() and not memory.has_seen(x=tile_x, y=tile_y) \
                        and not cls.is_in_foreign_land(game=game, civilization=civilization, world=world, x=tile_x, y=tile_y):
                    return (land.column(tile_x), tile_y)
        return None

    @classmethod
    def nearest_site(cls, *, game, unit, civilization):
        """Return the nearest tile the civilization remembers where a city could be built, as (x, y), or None.

        The tiles are tried ring by ring out from the settler. A tile too close to a city the
        civilization knows of, or never seen, is passed over before the full check of the site,
        which reads the whole city radius, so that the search stays cheap.
        """
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        memory = game.get_civilization(civilization).get_memory(world)
        land = game.get_world(world)
        too_close = game.get_theme().CITY.RADIUS_SIZE
        known = [game.get_city(city) for city in game.get_city_ids() if memory.get_owner(city) != NOTHING and game.get_city(city).get_world() == world]
        for reach in range(max(land.get_width() // 2, land.get_height()) + 1):
            for tile_x, tile_y in ring(x=x, y=y, reach=reach):
                if not 0 <= tile_y < land.get_height() or not memory.has_seen(x=tile_x, y=tile_y):
                    continue
                if any(distance(world=land, from_x=tile_x, from_y=tile_y, to_x=city.get_x(), to_y=city.get_y()) < too_close for city in known):
                    continue
                if CityControl.problem_with_site(game=game, tiles=memory, x=tile_x, y=tile_y) is None:
                    return (land.column(tile_x), tile_y)
        return None

    @classmethod
    def next_city_name(cls, *, game, civilization):
        holder = game.get_civilization(civilization)
        return MSG_CITY_NUMBERED.format(civilization=holder.get_name(), number=holder.get_cities_founded() + FIRST_CITY_NUMBER)

    # War

    @classmethod
    def army_is_ready(cls, *, game, civilization):
        """Return whether enough fighters stand outside the cities to march."""
        outside = [unit for unit in cls.fighters_of(game=game, civilization=civilization) if cls.city_of(game=game, unit=unit) == NOTHING]
        return len(outside) >= cls.GROUP_SIZE

    @classmethod
    def consider_war(cls, *, game, civilization):
        """Declare war on the first civilization met when the army is ready, unless the peace trait holds the player back."""
        if cls.enemies_of(game=game, civilization=civilization) or not cls.army_is_ready(game=game, civilization=civilization):
            return
        if cls.favors(game=game, civilization=civilization, trait=PEACE):
            return
        met = cls.known_civilizations(game=game, civilization=civilization)
        if met:
            cls.try_order(lambda: Orders.declare_war(game=game, civilization=civilization, on=met[0]))

    @classmethod
    def command_fighters(cls, *, game, civilization):
        """Keep one fighter inside each city, and send the rest to march on the enemy, or home when there is no enemy or the conquest trait keeps them there."""
        marching = bool(cls.enemies_of(game=game, civilization=civilization)) and cls.army_is_ready(game=game, civilization=civilization) \
            and cls.favors(game=game, civilization=civilization, trait=CONQUEST)
        for unit in cls.fighters_of(game=game, civilization=civilization):
            city = cls.city_of(game=game, unit=unit)
            if city != NOTHING:
                if len(game.get_city(city).get_units()) > ONE_DEFENDER:
                    cls.leave_city(game=game, unit=unit)
                continue
            if cls.garrison(game=game, unit=unit, civilization=civilization):
                continue
            if cls.fight_next_to(game=game, unit=unit, civilization=civilization, marching=marching):
                continue
            if marching:
                cls.march(game=game, unit=unit, civilization=civilization)
            else:
                cls.go_home(game=game, unit=unit, civilization=civilization)

    @classmethod
    def garrison(cls, *, game, unit, civilization):
        """Put a fighter into an own city next to it that has no unit inside, and return whether it went in."""
        for city in game.get_cities_of(civilization):
            if not game.get_city(city).get_units() and cls.is_next_to_center(game=game, unit=unit, city=city):
                return cls.try_order(lambda: Orders.enter_city(game=game, unit=unit, city=city))
        return False

    @classmethod
    def is_next_to_center(cls, *, game, unit, city):
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        return game.get_city(city).get_world() == world and (x, y) in CityControl.ring_tiles(game=game, city=city)

    @classmethod
    def fight_next_to(cls, *, game, unit, civilization, marching):
        """Attack an enemy on a tile next to the unit, or walk into an empty enemy city, and return whether the unit did either.

        A marching unit with aggressive hyperfocus leaves enemy units alone and attacks only cities; any unit attacks a city next to it. Below a sure win, the boldness trait decides.
        """
        world, x, y = UnitControl.tile_of(game=game, unit=unit)
        land = game.get_world(world)
        view = Sight.view(game=game, civilization=civilization)
        enemies = cls.enemies_of(game=game, civilization=civilization)
        hyperfocused = marching and cls.favors(game=game, civilization=civilization, trait=AGGRESSIVE_HYPERFOCUS)
        for dx, dy in NEIGHBORS:
            next_x, next_y = x + dx, y + dy
            if not 0 <= next_y < land.get_height():
                continue
            city = land.get_value(layer=Layer.CITY_CENTER, x=next_x, y=next_y)
            if city != NOTHING and game.get_city(city).get_owner() in enemies:
                if game.get_city(city).get_units():
                    return cls.try_order(lambda: Orders.attack(game=game, unit=unit, x=next_x, y=next_y))
                return cls.try_order(lambda: Orders.enter_city(game=game, unit=unit, city=city))
            other = view.unit_on(world=world, x=next_x, y=next_y)
            if other != NOTHING and game.get_units().get_value(column=UnitColumn.OWNER, unit=other) in enemies and not hyperfocused:
                if cls.worth_attacking(game=game, unit=unit, other=other, civilization=civilization):
                    return cls.try_order(lambda: Orders.attack(game=game, unit=unit, x=next_x, y=next_y))
        return False

    @classmethod
    def worth_attacking(cls, *, game, unit, other, civilization):
        """Return whether a unit should attack another: when it would kill the other in no more attacks than the other needs to kill it, or when boldness says so anyway."""
        theme = game.get_theme()
        mine = UnitControl.attacks_to_kill(theme=theme, attacker=UnitControl.kind_of(game=game, unit=unit), defender=UnitControl.kind_of(game=game, unit=other))
        theirs = UnitControl.attacks_to_kill(theme=theme, attacker=UnitControl.kind_of(game=game, unit=other), defender=UnitControl.kind_of(game=game, unit=unit))
        if mine is not None and (theirs is None or mine <= theirs):
            return True
        return mine is not None and cls.favors(game=game, civilization=civilization, trait=BOLDNESS)

    @classmethod
    def march(cls, *, game, unit, civilization):
        """Move a fighter toward the nearest enemy city it knows of, or toward the nearest enemy unit it sees, or away from home to find one."""
        enemies = cls.enemies_of(game=game, civilization=civilization)
        target = cls.nearest_city(game=game, unit=unit, cities=cls.known_cities_of(game=game, civilization=civilization, others=enemies))
        if target != NOTHING:
            city = game.get_city(target)
            cls.step_toward(game=game, unit=unit, to_x=city.get_x(), to_y=city.get_y())
            return
        view = Sight.view(game=game, civilization=civilization)
        units = game.get_units()
        seen = [other for other in view.units_seen() if units.get_value(column=UnitColumn.OWNER, unit=other) in enemies]
        if seen:
            _, to_x, to_y = UnitControl.tile_of(game=game, unit=seen[0])
            cls.step_toward(game=game, unit=unit, to_x=to_x, to_y=to_y)
            return
        home = cls.nearest_city(game=game, unit=unit, cities=game.get_cities_of(civilization))
        if home != NOTHING:
            cls.step_away(game=game, unit=unit, from_x=game.get_city(home).get_x(), from_y=game.get_city(home).get_y())

    @classmethod
    def go_home(cls, *, game, unit, civilization):
        """Move a fighter that is not marching toward the nearest own city, where it waits next to the center."""
        home = cls.nearest_city(game=game, unit=unit, cities=game.get_cities_of(civilization))
        if home != NOTHING and not cls.is_next_to_center(game=game, unit=unit, city=home):
            cls.step_toward(game=game, unit=unit, to_x=game.get_city(home).get_x(), to_y=game.get_city(home).get_y())

    # Building

    @classmethod
    def can_pay_a_part(cls, *, game, civilization, kind):
        """Return whether the civilization holds the first part of each resource a kind costs, so that the build is not blocked at once: a city with no stone does not start on a wonder of stone."""
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
    def decide_builds(cls, *, game, civilization):
        """Tell each city with nothing queued what to build, and each city whose build is blocked to build something else instead: a defender when the city has none, else a settler, an economy building or a fighter as the traits say."""
        for city in Production.waiting_cities(game=game, civilization=civilization):
            kind = cls.choose_build(game=game, city=city, civilization=civilization)
            if kind is not None:
                cls.try_order(lambda: Orders.build(game=game, city=city, kind=kind))
        for city in Production.blocked_cities(game=game, civilization=civilization):
            blocked = Production.kind_of(game=game, item=game.get_city(city).get_queue()[0])
            kind = cls.choose_build(game=game, city=city, civilization=civilization, except_for=blocked)
            if kind is not None:
                cls.try_order(lambda: Orders.build_instead(game=game, city=city, kind=kind))

    @classmethod
    def choose_build(cls, *, game, city, civilization, except_for=None):
        """Return what a city should build next, leaving one kind out, or None for nothing it can build."""
        theme = game.get_theme()
        settlers = [kind for kind in theme.UNITS if issubclass(kind, SettlerUnit)]
        holder = game.get_civilization(civilization)
        can_afford_fighter = holder.get_amount(game.get_catalog().get_id(category=Category.RESOURCES, kind=theme.PRIMARY_RESOURCE)) >= cls.RESERVE
        if not game.get_city(city).get_units():
            defender = cls.buildable(game=game, city=city, kinds=cls.DEFENDERS, except_for=except_for)
            if defender is not None:
                return defender
        has_a_settler = any(cls.is_settler(game=game, unit=unit) for unit in cls.units_of(game=game, civilization=civilization))
        if not has_a_settler and cls.favors(game=game, civilization=civilization, trait=EXPANSION):
            settler = cls.buildable(game=game, city=city, kinds=settlers, except_for=except_for)
            if settler is not None:
                return settler
        if cls.favors(game=game, civilization=civilization, trait=ECONOMICS):
            building = cls.buildable(game=game, city=city, kinds=cls.ECONOMY, except_for=except_for)
            if building is not None:
                return building
        if can_afford_fighter:
            fighter = cls.buildable(game=game, city=city, kinds=cls.ATTACKERS, except_for=except_for)
            if fighter is not None:
                return fighter
        return cls.buildable(game=game, city=city, kinds=(*cls.ECONOMY, *cls.DEFENDERS), except_for=except_for)
