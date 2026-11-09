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

"""What a city builds: units and buildings, one at a time, paid for a part each turn."""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.harvest import added
from microsponge.engine.civilizations.requirements import missing_in_city
from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import UnitKind
from microsponge.err_messages import ERR_ALREADY_BUILT, ERR_ALREADY_QUEUED, ERR_BUILD_NEEDS_WATER, ERR_BUILD_REQUIRES, ERR_NO_CITIZEN_TO_SPARE, ERR_WONDER_BUILT

WHOLE = 100


class Production:
    """The rules for what cities build, as static methods over a game. It is never made into an object.

    A city builds one thing at a time, the first of its production queue. The cost is split
    evenly over the turns the build takes, and a part is paid each turn from what the
    civilization holds. On a turn when the part cannot be paid, or the civilization is
    bankrupt, the build is blocked: it waits, and takes a turn longer.
    """

    __slots__ = ()

    @staticmethod
    def category_of(kind):
        """Return the category of something a city can build: a unit or a building."""
        return Category.UNITS if issubclass(kind, UnitKind) else Category.BUILDINGS

    @staticmethod
    def item_of(*, game, kind):
        """Return a kind as a production queue holds it: (category, id)."""
        category = Production.category_of(kind)
        return (category, game.get_catalog().get_id(category=category, kind=kind))

    @staticmethod
    def queue_of(*, game, city):
        """Return what a city builds, in order, as the theme's classes."""
        catalog = game.get_catalog()
        return [catalog.get_kind(category=category, kind_id=kind) for category, kind in game.get_city(city).get_queue()]

    @staticmethod
    def building(*, game, city):
        """Return what a city is building, as the theme's class, or None when its production queue is empty."""
        queue = Production.queue_of(game=game, city=city)
        return queue[0] if queue else None

    @staticmethod
    def turns_left(*, game, city):
        """Return how many more turns the build under way takes when none of them is blocked."""
        return Production.building(game=game, city=city).BUILD_TURNS - game.get_city(city).get_progress()

    @staticmethod
    def wonder_is_built(*, game, wonder):
        """Return whether a world wonder stands in any city of the game: only one civilization can build one."""
        _, wonder_id = Production.item_of(game=game, kind=wonder)
        return any(city.has_building(wonder_id) for city in game.get_cities())

    @staticmethod
    def wonder_builders(*, game, wonder):
        """Return the ids of every city of the game that has a world wonder in its production queue, so that a player can be warned that another civilization is building it."""
        item = Production.item_of(game=game, kind=wonder)
        return [city for city in game.get_city_ids() if item in game.get_city(city).get_queue()]

    @staticmethod
    def problem_building(*, game, city, kind):
        """Return why a city cannot build a unit or a building at all, as an error message, or None when it can.

        The civilization has to have what the kind requires, and a building that is required
        has to stand in the city itself. A unit that uses up citizens cannot be built by a city
        it would leave with no citizen. A building like a harbor needs a water tile next to
        the city center. A city has one of each building, so a building the city has is
        refused, and so is a world wonder that already stands somewhere.
        """
        target = game.get_city(city)
        _, kind_id = Production.item_of(game=game, kind=kind)
        missing = missing_in_city(game=game, city=city, kind=kind)
        if missing:
            return ERR_BUILD_REQUIRES.format(kind=shown_name(kind), required=shown_name(missing[0]))
        if issubclass(kind, UnitKind):
            if kind.CITIZENS and target.get_citizens() <= kind.CITIZENS:
                return ERR_NO_CITIZEN_TO_SPARE.format(unit=shown_name(kind), name=target.get_name(), citizens=target.get_citizens(), uses=kind.CITIZENS)
            return None
        if target.has_building(kind_id):
            return ERR_ALREADY_BUILT.format(name=target.get_name(), building=shown_name(kind))
        if issubclass(kind, Wonder) and Production.wonder_is_built(game=game, wonder=kind):
            return ERR_WONDER_BUILT.format(wonder=shown_name(kind))
        if kind.BESIDE_WATER and not CityControl.is_beside_water(game=game, city=city):
            return ERR_BUILD_NEEDS_WATER.format(building=shown_name(kind), city=game.get_theme().CITY.NAME)
        return None

    @staticmethod
    def problem_queueing(*, game, city, kind):
        """Return why a unit or a building cannot go at the end of what a city builds, as an error message, or None when it can: a building goes in the queue once."""
        problem = Production.problem_building(game=game, city=city, kind=kind)
        if problem is None and not issubclass(kind, UnitKind) and Production.item_of(game=game, kind=kind) in game.get_city(city).get_queue():
            return ERR_ALREADY_QUEUED.format(name=game.get_city(city).get_name(), building=shown_name(kind))
        return problem

    @staticmethod
    def queue(*, game, city, kind):
        """Put a unit or a building at the end of what a city builds."""
        problem = Production.problem_queueing(game=game, city=city, kind=kind)
        if problem is not None:
            raise ValueError(problem)
        category, kind_id = Production.item_of(game=game, kind=kind)
        game.get_city(city).add_to_queue(category=category, kind=kind_id)

    @staticmethod
    def switch(*, game, city, kind):
        """Make a city build a unit or a building instead of everything in its production queue, refunding part of what was paid for the build under way."""
        problem = Production.problem_building(game=game, city=city, kind=kind)
        if problem is not None:
            raise ValueError(problem)
        category, kind_id = Production.item_of(game=game, kind=kind)
        Production._drop_with_refund(game=game, city=city)
        game.get_city(city).add_to_queue(category=category, kind=kind_id)

    @staticmethod
    def stop(*, game, city):
        """Set a city to build nothing, refunding part of what was paid for the build under way."""
        Production._drop_with_refund(game=game, city=city)
        game.get_city(city).set_builds_nothing(True)

    @staticmethod
    def refund(*, game, city):
        """Return what comes back to the civilization if the city gives up the build under way: the theme's percent of what was paid so far, rounded down, each resource with its amount."""
        kind = Production.building(game=game, city=city)
        if kind is None:
            return {}
        percent = game.get_theme().SWITCH_REFUND_PERCENT
        paid = Production.paid(kind=kind, turns=game.get_city(city).get_progress())
        return {resource: amount * percent // WHOLE for resource, amount in paid.items()}

    @staticmethod
    def _drop_with_refund(*, game, city):
        """Empty a city's production queue, and give the civilization the refund for the build under way."""
        target = game.get_city(city)
        holder = game.get_civilization(target.get_owner())
        catalog = game.get_catalog()
        for resource, amount in Production.refund(game=game, city=city).items():
            holder.add(resource=catalog.get_id(category=Category.RESOURCES, kind=resource), amount=amount)
        target.clear_queue()

    @staticmethod
    def part(*, kind, turn):
        """Return the part of a kind's cost paid in one turn of its build, counted from 0: each resource with its amount.

        The cost is split evenly over the turns the build takes. What does not divide evenly is
        paid one more each in the first turns.
        """
        turns = kind.BUILD_TURNS
        return {resource: amount // turns + (turn < amount % turns) for resource, amount in kind.COST.items()}

    @staticmethod
    def paid(*, kind, turns):
        """Return what the first turns of a kind's build have paid, all together: each resource with its amount."""
        totals = {}
        for turn in range(turns):
            added(totals=totals, amounts=Production.part(kind=kind, turn=turn))
        return totals

    @staticmethod
    def blocked_cities(*, game, civilization):
        """Return the ids of a civilization's cities whose build waited last turn."""
        return [city for city in game.get_cities_of(civilization) if game.get_city(city).is_blocked()]

    @staticmethod
    def waiting_cities(*, game, civilization):
        """Return the ids of a civilization's cities that need to be told what to build: nothing queued, and not set to build nothing."""
        cities = [(city, game.get_city(city)) for city in game.get_cities_of(civilization)]
        return [city for city, target in cities if not target.get_queue() and not target.builds_nothing()]

    @staticmethod
    def advance(*, game, civilization):
        """Take each city of a civilization a turn further with what the city is building."""
        for city in game.get_cities_of(civilization):
            Production._advance_city(game=game, city=city)

    @staticmethod
    def _advance_city(*, game, city):
        target = game.get_city(city)
        kind = Production.building(game=game, city=city)
        if kind is None:
            return
        if issubclass(kind, Wonder) and Production.wonder_is_built(game=game, wonder=kind):
            target.remove_first()
            return
        if target.get_progress() < kind.BUILD_TURNS:
            if not Production._pay_part(game=game, city=city, kind=kind):
                target.set_blocked(True)
                return
            target.set_progress(target.get_progress() + 1)
        finished = target.get_progress() >= kind.BUILD_TURNS
        target.set_blocked(finished and not Production._finish(game=game, city=city, kind=kind))

    @staticmethod
    def _pay_part(*, game, city, kind):
        """Pay this turn's part of what a city is building, and return whether it was paid. A bankrupt civilization pays for nothing."""
        target = game.get_city(city)
        holder = game.get_civilization(target.get_owner())
        catalog = game.get_catalog()
        part = Production.part(kind=kind, turn=target.get_progress())
        owed = {catalog.get_id(category=Category.RESOURCES, kind=resource): amount for resource, amount in part.items()}
        if holder.is_bankrupt() or any(holder.get_amount(resource) < amount for resource, amount in owed.items()):
            return False
        for resource, amount in owed.items():
            holder.pay(resource=resource, amount=amount)
        return True

    @staticmethod
    def _finish(*, game, city, kind):
        """Put what a city has paid for in the game, and return whether there was a way to: a building in the city, a unit in or beside it.

        A unit that uses up citizens waits until the city has more citizens than the unit
        uses, which can happen when a city builds two such units, and a unit with nowhere to
        go waits for room.
        """
        target = game.get_city(city)
        if issubclass(kind, UnitKind):
            if kind.CITIZENS and target.get_citizens() <= kind.CITIZENS:
                return False
            if CityControl.muster(game=game, city=city, kind=kind) is None:
                return False
            target.set_citizens(target.get_citizens() - kind.CITIZENS)
        else:
            target.add_building(game.get_catalog().get_id(category=Category.BUILDINGS, kind=kind))
        target.remove_first()
        return True
