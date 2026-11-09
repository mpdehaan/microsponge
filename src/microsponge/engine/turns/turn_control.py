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

"""Starting a game, and what happens when a civilization ends its turn."""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.harvest import Harvest
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.requirements import buildings_held, known_technologies
from microsponge.engine.civilizations.research import Research
from microsponge.engine.kinds.bonuses import harvest_percent, unit_support_percent
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.units.work_control import WorkControl
from microsponge.err_messages import ERR_GAME_NOT_STARTED, ERR_GAME_OVER, ERR_GAME_STARTED, ERR_NO_CIVILIZATIONS

WHOLE = 100
NO_PENALTY = 0
FIRST_CIVILIZATION = 1
NOT_BANKRUPT = 0
NO_CURRENCY = 0
NOT_GROWING = 0
NOTHING_OWED = 0
# However much sooner its buildings make a city grow, growing takes at least this many turns.
LEAST_GROWTH_TURNS = 1


class TurnControl:
    """The turn order and the work of a turn, as static methods over a game. It is never made into an object.

    The civilizations play one after another, in the order they joined the game. When a
    civilization ends its turn, its units that are building go on building, its cities collect,
    its citizens eat, its units and buildings are paid for, its cities go on with what they
    build and grow, its units heal, its research goes on and its action points refill. The turn number goes up when the
    last civilization has played.
    """

    __slots__ = ()

    @staticmethod
    def start(game):
        """Start a game: every civilization gets what the theme starts it with and its action points, and the first civilization plays."""
        if game.get_playing() != NOTHING:
            raise ValueError(ERR_GAME_STARTED)
        if not game.get_civilizations():
            raise ValueError(ERR_NO_CIVILIZATIONS)
        for civilization in game.get_still_playing():
            for resource, amount in game.get_theme().STARTS_WITH.items():
                game.get_civilization(civilization).add(resource=game.get_catalog().get_id(category=Category.RESOURCES, kind=resource), amount=amount)
            TurnControl.refill(game=game, civilization=civilization)
        game.set_playing(FIRST_CIVILIZATION)

    @staticmethod
    def check_playing(game):
        """Check that a game has started and has not ended."""
        if game.get_playing() == NOTHING:
            raise ValueError(ERR_GAME_NOT_STARTED)
        if game.is_over():
            raise ValueError(ERR_GAME_OVER)

    @staticmethod
    def end_turn(game):
        """End the turn of the civilization that is playing, and pass the turn to the next civilization that has not lost."""
        TurnControl.check_playing(game)
        civilization = game.get_playing()
        WorkControl.advance(game=game, civilization=civilization)
        TurnControl.collect(game=game, civilization=civilization)
        TurnControl.feed(game=game, civilization=civilization)
        TurnControl.pay_support(game=game, civilization=civilization)
        Production.advance(game=game, civilization=civilization)
        TurnControl.grow(game=game, civilization=civilization)
        TurnControl.heal(game=game, civilization=civilization)
        Research.advance(game=game, civilization=civilization)
        TurnControl.refill(game=game, civilization=civilization)
        TurnControl.pass_on(game)

    @staticmethod
    def pass_on(game):
        """Give the turn to the next civilization still playing after the one playing. The turn number goes up when the order starts again."""
        still_playing = game.get_still_playing()
        if not still_playing:
            return
        later = [civilization for civilization in still_playing if civilization > game.get_playing()]
        if not later:
            game.next_turn()
        game.set_playing(later[0] if later else still_playing[0])

    @staticmethod
    def collect(*, game, civilization):
        """Add what every city of a civilization collects this turn to what the civilization holds.

        The civilization's technologies make the harvest of a resource faster, and a bankrupt
        civilization collects less of everything. Parts of a resource are rounded down.
        """
        holder = game.get_civilization(civilization)
        catalog = game.get_catalog()
        technologies = known_technologies(game=game, civilization=civilization)
        kept = WHOLE - (game.get_theme().BANKRUPTCY_HARVEST_PENALTY if holder.is_bankrupt() else NO_PENALTY)
        for city in game.get_cities_of(civilization):
            for resource, amount in Harvest.of_city(game=game, city=city).items():
                faster = amount * harvest_percent(technologies=technologies, resource=resource) // WHOLE
                holder.add(resource=catalog.get_id(category=Category.RESOURCES, kind=resource), amount=faster * kept // WHOLE)

    @staticmethod
    def feed(*, game, civilization):
        """Take the food the citizens of a civilization's cities eat this turn from what the civilization holds, as far as the food goes."""
        theme = game.get_theme()
        citizens = sum(game.get_city(city).get_citizens() for city in game.get_cities_of(civilization))
        food = game.get_catalog().get_id(category=Category.RESOURCES, kind=theme.FOOD)
        game.get_civilization(civilization).pay(resource=food, amount=citizens * theme.CITY.CITIZEN_FOOD)

    @staticmethod
    def support_cost(*, game, civilization):
        """Return what a civilization's units and buildings cost to support this turn: each resource's id with its amount.

        The civilization's technologies can take a percent off what all its units cost of each resource, rounded down.
        """
        percent = unit_support_percent(known_technologies(game=game, civilization=civilization))
        units = [UnitControl.kind_of(game=game, unit=unit) for unit in UnitControl.units_of(game=game, civilization=civilization)]
        cost = {resource: amount * percent // WHOLE for resource, amount in TurnControl.support_of(units).items()}
        for resource, amount in TurnControl.support_of(buildings_held(game=game, civilization=civilization)).items():
            cost[resource] = cost.get(resource, NOTHING_OWED) + amount
        catalog = game.get_catalog()
        return {catalog.get_id(category=Category.RESOURCES, kind=resource): amount for resource, amount in cost.items()}

    @staticmethod
    def support_of(kinds):
        """Return what some units or buildings cost to support each turn, added up: each resource with its amount."""
        cost = {}
        for kind in kinds:
            for resource, amount in kind.SUPPORT.items():
                cost[resource] = cost.get(resource, NOTHING_OWED) + amount
        return cost

    @staticmethod
    def pay_support(*, game, civilization):
        """Pay what a civilization's units and buildings cost this turn, as far as what it holds goes, and count the turn as bankrupt when its currency is at 0 afterwards.

        A civilization that has been bankrupt for as many turns in a row as the theme allows has lost.
        """
        theme = game.get_theme()
        holder = game.get_civilization(civilization)
        for resource, amount in TurnControl.support_cost(game=game, civilization=civilization).items():
            holder.pay(resource=resource, amount=amount)
        currency = game.get_catalog().get_id(category=Category.RESOURCES, kind=theme.PRIMARY_RESOURCE)
        bankrupt = holder.get_amount(currency) == NO_CURRENCY
        holder.set_bankrupt_turns(holder.get_bankrupt_turns() + 1 if bankrupt else NOT_BANKRUPT)
        if holder.get_bankrupt_turns() >= theme.BANKRUPTCY_TURNS:
            holder.lose()

    @staticmethod
    def growth_turns(*, game, city):
        """Return how many turns in a row with enough food a city needs to grow, at the size it is. Its buildings can make that sooner."""
        turns = game.get_theme().CITY.GROWTH_TURNS
        plain = turns[min(game.get_city(city).get_citizens(), len(turns)) - 1]
        sooner = sum(building.GROWS_SOONER for building in CityControl.buildings_of(game=game, city=city))
        return max(plain - sooner, LEAST_GROWTH_TURNS)

    @staticmethod
    def grow(*, game, civilization):
        """Count this turn toward the growth of each city of a civilization when there is enough food, and grow the cities whose count is reached."""
        spec = game.get_theme().CITY
        food = game.get_civilization(civilization).get_amount(game.get_catalog().get_id(category=Category.RESOURCES, kind=game.get_theme().FOOD))
        for city in game.get_cities_of(civilization):
            target = game.get_city(city)
            can_grow = target.get_citizens() < spec.MAX_CITIZENS and food >= spec.GROWTH_FOOD * target.get_citizens()
            target.set_growth(target.get_growth() + 1 if can_grow else NOT_GROWING)
            if can_grow and target.get_growth() >= TurnControl.growth_turns(game=game, city=city):
                target.set_citizens(target.get_citizens() + 1)
                target.set_growth(NOT_GROWING)

    @staticmethod
    def heal(*, game, civilization):
        """Give each unit of a civilization back the hit points its kind heals in a turn, more inside a city, up to the hit points of a whole unit at its level."""
        units = game.get_units()
        for unit in UnitControl.units_of(game=game, civilization=civilization):
            kind = UnitControl.kind_of(game=game, unit=unit)
            healed = kind.CITY_HEAL if units.get_value(column=UnitColumn.CITY, unit=unit) != NOTHING else kind.HEAL
            hit_points = min(units.get_value(column=UnitColumn.HIT_POINTS, unit=unit) + healed, UnitControl.max_hit_points(game=game, unit=unit))
            units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=hit_points)

    @staticmethod
    def action_points(*, game, civilization):
        """Return the action points a civilization has each turn: the theme's, and what each of its cities and buildings adds."""
        theme = game.get_theme()
        from_cities = theme.CITY.ACTION_POINTS * len(game.get_cities_of(civilization))
        return theme.ACTION_POINTS + from_cities + sum(building.ACTION_POINTS for building in buildings_held(game=game, civilization=civilization))

    @staticmethod
    def refill(*, game, civilization):
        """Give a civilization and each of its units all their action points again."""
        units = game.get_units()
        game.get_civilization(civilization).set_action_points(TurnControl.action_points(game=game, civilization=civilization))
        for unit in UnitControl.units_of(game=game, civilization=civilization):
            units.set_value(column=UnitColumn.ACTION_POINTS, unit=unit, value=UnitControl.kind_of(game=game, unit=unit).ACTION_POINTS)
