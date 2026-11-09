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

"""The orders a civilization gives during its turn. Each is refused when it breaks the model, and nothing changes then."""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.cities.production import Production
from microsponge.engine.civilizations.research import Research
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.engine.units.combat import Combat
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.unit_control import UnitControl
from microsponge.engine.units.work_control import WorkControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_NO_ACTION_POINTS, ERR_NO_CIVILIZATION_ACTION_POINTS, ERR_NOT_AT_WAR, ERR_NOT_NEXT_TO_UNIT, ERR_NOT_YOUR_TURN, ERR_PRIORITY_FOOD, ERR_UNIT_IN_A_CITY,
    ERR_WAR_ON_YOURSELF,
)

# How far a tile next to another is from it, across or down.
NEXT_TO = (-1, 0, 1)
SAME_TILE = (0, 0)


class Orders:
    """What a civilization may do on its turn, as static methods over a game. It is never made into an object.

    A person's screen and a computer player give the same orders. An order by a unit costs
    action points from the unit's pool and from the pool of the unit's civilization alike.
    """

    __slots__ = ()

    @staticmethod
    def check_turn(*, game, civilization):
        """Check that it is a civilization's turn in a game that is being played."""
        TurnControl.check_playing(game)
        if game.get_playing() != civilization:
            raise ValueError(ERR_NOT_YOUR_TURN.format(name=game.get_civilization(civilization).get_name()))

    @staticmethod
    def owner_of(*, game, unit):
        return game.get_units().get_value(column=UnitColumn.OWNER, unit=unit)

    @staticmethod
    def check_points(*, game, unit, cost):
        """Check that it is the turn of a unit's civilization, and that the unit and its civilization both have the action points an order costs."""
        owner = Orders.owner_of(game=game, unit=unit)
        Orders.check_turn(game=game, civilization=owner)
        left = game.get_units().get_value(column=UnitColumn.ACTION_POINTS, unit=unit)
        if left < cost:
            raise ValueError(ERR_NO_ACTION_POINTS.format(unit=unit, left=left, cost=cost))
        pool = game.get_civilization(owner).get_action_points()
        if pool < cost:
            raise ValueError(ERR_NO_CIVILIZATION_ACTION_POINTS.format(name=game.get_civilization(owner).get_name(), left=pool, cost=cost))

    @staticmethod
    def charge(*, game, unit, cost):
        """Take the action points an order costs from a unit and from its civilization."""
        units = game.get_units()
        owner = game.get_civilization(Orders.owner_of(game=game, unit=unit))
        units.set_value(column=UnitColumn.ACTION_POINTS, unit=unit, value=units.get_value(column=UnitColumn.ACTION_POINTS, unit=unit) - cost)
        owner.set_action_points(owner.get_action_points() - cost)

    @staticmethod
    def step(*, game, unit, x, y):
        """Return how far a tile is from a unit as (across, down), each -1, 0 or 1, going around the world. The tile has to be next to the unit."""
        world_id, from_x, from_y = UnitControl.tile_of(game=game, unit=unit)
        world = game.get_world(world_id)
        steps = [(across, down) for across in NEXT_TO for down in NEXT_TO if (world.column(from_x + across), from_y + down) == (world.column(x), y)]
        if not steps or steps[0] == SAME_TILE:
            raise ValueError(ERR_NOT_NEXT_TO_UNIT.format(x=x, y=y, unit=unit))
        return steps[0]

    @staticmethod
    def move_cost(*, game, unit, x, y):
        """Return the action points it costs a unit to move onto a tile next to it: the theme's base cost, straight or diagonal, times the terrain's."""
        theme = game.get_theme()
        across, down = Orders.step(game=game, unit=unit, x=x, y=y)
        world_id, _, _ = UnitControl.tile_of(game=game, unit=unit)
        terrain = game.get_terrain(world=world_id, x=x, y=y)
        base = theme.DIAGONAL_MOVE_COST_BASE if across and down else theme.STRAIGHT_MOVE_COST_BASE
        return base * terrain.MOVE_COST

    @staticmethod
    def check_may_enter(*, game, unit, x, y):
        """Check that a unit may be on a tile as far as territory goes: a tile of another civilization's city radius needs a war with that civilization."""
        owner = Orders.owner_of(game=game, unit=unit)
        world_id, _, _ = UnitControl.tile_of(game=game, unit=unit)
        city = game.get_world(world_id).get_value(layer=Layer.CITY, x=x, y=y)
        if city == NOTHING:
            return
        other = game.get_city(city).get_owner()
        if other != owner and not game.get_civilization(owner).is_at_war_with(other):
            raise ValueError(ERR_NOT_AT_WAR.format(name=game.get_civilization(other).get_name()))

    @staticmethod
    def move(*, game, unit, x, y):
        """Move a unit onto a tile next to it."""
        if game.get_units().get_value(column=UnitColumn.CITY, unit=unit) != NOTHING:
            raise ValueError(ERR_UNIT_IN_A_CITY.format(unit=unit, city=game.get_theme().CITY.NAME))
        WorkControl.check_idle(game=game, unit=unit)
        cost = Orders.move_cost(game=game, unit=unit, x=x, y=y)
        Orders.check_points(game=game, unit=unit, cost=cost)
        Orders.check_may_enter(game=game, unit=unit, x=x, y=y)
        UnitControl.move_to(game=game, unit=unit, x=x, y=y)
        Orders.charge(game=game, unit=unit, cost=cost)

    @staticmethod
    def attack_cost(*, game, unit, x, y):
        """Return the action points it costs a unit to attack a tile next to it: the theme's base cost, straight or diagonal."""
        theme = game.get_theme()
        across, down = Orders.step(game=game, unit=unit, x=x, y=y)
        return theme.DIAGONAL_ATTACK_COST_BASE if across and down else theme.STRAIGHT_ATTACK_COST_BASE

    @staticmethod
    def attack(*, game, unit, x, y):
        """Have a unit attack the unit on a tile next to it, or the units inside the city whose center covers the tile, and return what the attack did."""
        if game.get_units().get_value(column=UnitColumn.CITY, unit=unit) != NOTHING:
            raise ValueError(ERR_UNIT_IN_A_CITY.format(unit=unit, city=game.get_theme().CITY.NAME))
        WorkControl.check_idle(game=game, unit=unit)
        cost = Orders.attack_cost(game=game, unit=unit, x=x, y=y)
        Orders.check_points(game=game, unit=unit, cost=cost)
        problem = Combat.problem_attacking(game=game, unit=unit, x=x, y=y)
        if problem is not None:
            raise ValueError(problem)
        Orders.charge(game=game, unit=unit, cost=cost)
        return Combat.attack(game=game, unit=unit, x=x, y=y)

    @staticmethod
    def found_city(*, game, settler, name):
        """Build a city where a settler stands, and return the city's id."""
        cost = game.get_theme().ACTION_COST_BASE
        Orders.check_points(game=game, unit=settler, cost=cost)
        owner = game.get_civilization(Orders.owner_of(game=game, unit=settler))
        city = CityControl.found(game=game, settler=settler, name=name)
        owner.set_action_points(owner.get_action_points() - cost)
        return city

    @staticmethod
    def enter_city(*, game, unit, city):
        """Move a unit from a tile next to the center of a city into the city, taking the city when the city is another civilization's and has no unit inside."""
        cost = game.get_theme().STRAIGHT_MOVE_COST_BASE
        Orders.check_points(game=game, unit=unit, cost=cost)
        WorkControl.check_idle(game=game, unit=unit)
        CityControl.enter(game=game, unit=unit, city=city)
        Orders.charge(game=game, unit=unit, cost=cost)

    @staticmethod
    def leave_city(*, game, unit, x, y):
        """Move a unit out of the city it is inside, onto a tile next to the city center."""
        cost = game.get_theme().STRAIGHT_MOVE_COST_BASE
        Orders.check_points(game=game, unit=unit, cost=cost)
        CityControl.leave(game=game, unit=unit, x=x, y=y)
        Orders.charge(game=game, unit=unit, cost=cost)

    @staticmethod
    def build_improvement(*, game, unit, improvement):
        """Set a unit to building an improvement on the tile it stands on, which takes the turns the improvement says."""
        cost = game.get_theme().ACTION_COST_BASE
        Orders.check_points(game=game, unit=unit, cost=cost)
        WorkControl.start(game=game, unit=unit, improvement=improvement)
        Orders.charge(game=game, unit=unit, cost=cost)

    @staticmethod
    def abandon_improvement(*, game, unit):
        """Stop a unit building its improvement, so that the unit can move again. It costs no action points."""
        Orders.check_turn(game=game, civilization=Orders.owner_of(game=game, unit=unit))
        WorkControl.abandon(game=game, unit=unit)

    @staticmethod
    def prioritize(*, game, city, resource, citizens):
        """Set how many citizens of a city look for a resource other than food first. None takes the priority away. It costs no action points."""
        target = game.get_city(city)
        Orders.check_turn(game=game, civilization=target.get_owner())
        if resource is game.get_theme().FOOD:
            raise ValueError(ERR_PRIORITY_FOOD.format(resource=shown_name(resource)))
        target.set_priority(resource=game.get_catalog().get_id(category=Category.RESOURCES, kind=resource), citizens=citizens)

    @staticmethod
    def build(*, game, city, kind):
        """Put a unit or a building at the end of what a city builds. Deciding what to build costs no action points."""
        Orders.check_turn(game=game, civilization=game.get_city(city).get_owner())
        Production.queue(game=game, city=city, kind=kind)

    @staticmethod
    def build_instead(*, game, city, kind):
        """Make a city build a unit or a building instead of everything it was going to build. What was paid for the build under way is lost."""
        Orders.check_turn(game=game, civilization=game.get_city(city).get_owner())
        Production.switch(game=game, city=city, kind=kind)

    @staticmethod
    def build_nothing(*, game, city):
        """Set a city to build nothing. What was paid for the build under way is lost."""
        Orders.check_turn(game=game, civilization=game.get_city(city).get_owner())
        Production.stop(game=game, city=city)

    @staticmethod
    def research(*, game, civilization, technology):
        """Set the technology a civilization researches. Deciding what to research costs no action points."""
        Orders.check_turn(game=game, civilization=civilization)
        Research.choose(game=game, civilization=civilization, technology=technology)

    @staticmethod
    def declare_war(*, game, civilization, on):
        """Declare war on another civilization, which puts both at war with each other."""
        Orders.check_turn(game=game, civilization=civilization)
        other = game.get_civilization(on)
        if civilization == on:
            raise ValueError(ERR_WAR_ON_YOURSELF)
        other.declare_war(civilization)
        game.get_civilization(civilization).declare_war(on)

    @staticmethod
    def end_turn(*, game, civilization):
        """End a civilization's turn, which is refused while a technology is left to pick and none is picked."""
        Orders.check_turn(game=game, civilization=civilization)
        problem = Research.problem_ending_turn(game=game, civilization=civilization)
        if problem is not None:
            raise ValueError(problem)
        TurnControl.end_turn(game)
