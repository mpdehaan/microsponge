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

"""Fighting: a unit attacking a unit on the next tile, or the units inside a city, and the losses that follow."""

from dataclasses import dataclass

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import can_hit
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.levels import NO_EXPERIENCE, Levels
from microsponge.engine.units.unit_control import NO_BONUS, NO_DAMAGE, WHOLE, UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import ERR_ATTACK_OWN, ERR_CANNOT_HIT, ERR_CITY_UNDEFENDED, ERR_NOT_AT_WAR, ERR_NOTHING_TO_ATTACK

# The hit points of a unit that is gone.
DEAD = 0
# The experience a unit gains for an attack it makes, beside what a kill gives, and the percent of that a unit gains for being attacked and surviving.
# The attack experience is 2 so that half of it is a whole point, since percentages round down.
ATTACK_EXPERIENCE = 2
DEFENSE_EXPERIENCE_PERCENT = 50
SURVIVAL_EXPERIENCE = ATTACK_EXPERIENCE * DEFENSE_EXPERIENCE_PERCENT // WHOLE


@dataclass(slots=True, kw_only=True)
class AttackOutcome:
    """What one attack did, for a screen or a log of the game."""

    # The id of the unit that was hit, and the hit points taken off it.
    defender: int
    damage: int
    # The hit points the defender took off the attacker by striking back, 0 when it did not.
    strike_back: int
    defender_killed: bool
    attacker_killed: bool
    # The id of the unit that struck back, or None.
    striker: int | None = None


class Combat:
    """The rules for fighting, as static methods over a game. It is never made into an object.

    An attack rolls the attacker's dice, and the defender's armor class mitigates the roll, down
    to chip damage at the least; the defender strikes back with a percent of its own roll,
    through the attacker's armor, when its kind does and can hit the attacker. Inside a city,
    the city's buildings make the armor class of every unit inside better, the unit with the
    best armor class is the one hit, and the unit with the strongest dice among those that can
    hit the attacker is the one that strikes back. Fighting gives experience, and experience
    gives levels (`Levels`).
    """

    __slots__ = ()

    @staticmethod
    def target_at(*, game, world, x, y):
        """Return what stands on a tile as (unit, city): the unit on it, or the city whose center covers it, each NOTHING when there is none."""
        tiles = game.get_world(world)
        return tiles.get_value(layer=Layer.UNIT, x=x, y=y), tiles.get_value(layer=Layer.CITY_CENTER, x=x, y=y)

    @staticmethod
    def problem_attacking(*, game, unit, x, y):
        """Return why a unit cannot attack a tile next to it, as an error message, or None when it can.

        There has to be a unit on the tile, or a city center with units inside, of a
        civilization the attacker's is at war with, and the attacker's kind has to be able to
        hit the unit that would be hit.
        """
        units = game.get_units()
        world, _, _ = UnitControl.tile_of(game=game, unit=unit)
        target, city = Combat.target_at(game=game, world=world, x=x, y=y)
        if target == NOTHING and city == NOTHING:
            return ERR_NOTHING_TO_ATTACK.format(x=game.get_world(world).column(x), y=y)
        owner = units.get_value(column=UnitColumn.OWNER, unit=unit)
        other = game.get_city(city).get_owner() if target == NOTHING else units.get_value(column=UnitColumn.OWNER, unit=target)
        if other == owner:
            return ERR_ATTACK_OWN.format(unit=unit)
        if not game.get_civilization(owner).is_at_war_with(other):
            return ERR_NOT_AT_WAR.format(name=game.get_civilization(other).get_name())
        if target == NOTHING:
            target = Combat.defender_of_city(game=game, city=city)
            if target is None:
                return ERR_CITY_UNDEFENDED.format(name=game.get_city(city).get_name(), city=game.get_theme().CITY.NAME)
        kind = UnitControl.kind_of(game=game, unit=unit)
        hit = UnitControl.kind_of(game=game, unit=target)
        if not can_hit(kind=kind, target=hit):
            return ERR_CANNOT_HIT.format(unit=shown_name(kind), target=shown_name(hit))
        return None

    @staticmethod
    def defender_of_city(*, game, city):
        """Return the id of the unit inside a city that an attack hits, the one with the best armor class, or None when no unit is inside."""
        inside = game.get_city(city).get_units()
        return min(inside, key=lambda unit: UnitControl.armor_class_of(game=game, unit=unit), default=None)

    @staticmethod
    def striker_of_city(*, game, city, attacker):
        """Return the id of the unit inside a city that strikes back at an attacker, the one with the strongest dice on average among those that can hit the attacker, or None."""
        kind = UnitControl.kind_of(game=game, unit=attacker)
        able = [unit for unit in game.get_city(city).get_units() if can_hit(kind=UnitControl.kind_of(game=game, unit=unit), target=kind)]
        return max(able, key=lambda unit: UnitControl.average_roll(attacker=UnitControl.kind_of(game=game, unit=unit), defender=kind), default=None)

    @staticmethod
    def attack(*, game, unit, x, y):
        """Have a unit attack the tile next to it, and return what the attack did. The order checks and the action points are Orders' business."""
        problem = Combat.problem_attacking(game=game, unit=unit, x=x, y=y)
        if problem is not None:
            raise ValueError(problem)
        world, _, _ = UnitControl.tile_of(game=game, unit=unit)
        target, city = Combat.target_at(game=game, world=world, x=x, y=y)
        if target != NOTHING:
            defender = target
            striker = target
            bonus = NO_BONUS
        else:
            defender = Combat.defender_of_city(game=game, city=city)
            striker = Combat.striker_of_city(game=game, city=city, attacker=unit)
            bonus = CityControl.armor_bonus(game=game, city=city, against=UnitControl.kind_of(game=game, unit=unit))
        roll = UnitControl.roll_against(game=game, unit=unit, target=defender)
        damage = UnitControl.mitigated(roll=roll, armor_class=UnitControl.armor_class_of(game=game, unit=defender, bonus=bonus))
        prizes = {defender: Combat.kill_experience(game=game, unit=defender), unit: Combat.kill_experience(game=game, unit=unit)}
        defender_killed = Combat.hurt(game=game, unit=defender, damage=damage)
        strike_back = NO_DAMAGE
        attacker_killed = False
        if striker is not None and not (defender_killed and striker == defender):
            strike_back = Combat.strike_back(game=game, attacker=unit, striker=striker)
            attacker_killed = Combat.hurt(game=game, unit=unit, damage=strike_back)
        Combat.reward(game=game, attacker=unit, defender=defender, striker=striker, prizes=prizes, defender_killed=defender_killed, attacker_killed=attacker_killed)
        Combat.settle_losses(game)
        return AttackOutcome(defender=defender, damage=damage, strike_back=strike_back, defender_killed=defender_killed, attacker_killed=attacker_killed, striker=striker if strike_back else None)

    @staticmethod
    def strike_back(*, game, attacker, striker):
        """Return the damage a unit that was attacked deals its attacker by striking back: its kind's percent of its own roll, through the attacker's armor, or nothing when its kind does not strike back at the attacker."""
        roll = UnitControl.strike_back_roll(
            attacker=UnitControl.kind_of(game=game, unit=attacker), defender=UnitControl.kind_of(game=game, unit=striker),
            roll=UnitControl.roll_against(game=game, unit=striker, target=attacker),
        )
        if roll is None:
            return NO_DAMAGE
        return UnitControl.mitigated(roll=roll, armor_class=UnitControl.armor_class_of(game=game, unit=attacker))

    @staticmethod
    def kill_experience(*, game, unit):
        """Return the experience killing a unit gives, worked out while the unit is still there."""
        return Levels.kill_experience(killed=UnitControl.kind_of(game=game, unit=unit), level=UnitControl.level_of(game=game, unit=unit))

    @staticmethod
    def reward(*, game, attacker, defender, striker, prizes, defender_killed, attacker_killed):
        """Give the units of an attack their experience: the attacker a little for attacking and the defender's prize for a kill, the defender half of that little for surviving, and the striker the attacker's whole prize for killing the attacker on defense.

        The prizes are what killing each unit gives, worked out before anyone was removed.
        """
        if attacker_killed:
            Combat.gain(game=game, unit=striker, experience=prizes[attacker])
        else:
            Combat.gain(game=game, unit=attacker, experience=ATTACK_EXPERIENCE + (prizes[defender] if defender_killed else NO_EXPERIENCE))
        if not defender_killed:
            Combat.gain(game=game, unit=defender, experience=SURVIVAL_EXPERIENCE)

    @staticmethod
    def gain(*, game, unit, experience):
        """Give a unit experience, and when the experience reaches a level, the level and the hit points the level adds, on top of the unit's wounds."""
        units = game.get_units()
        total = units.get_value(column=UnitColumn.EXPERIENCE, unit=unit) + experience
        units.set_value(column=UnitColumn.EXPERIENCE, unit=unit, value=total)
        before = UnitControl.level_of(game=game, unit=unit)
        after = Levels.level_for(experience=total)
        if after > before:
            whole_before = UnitControl.max_hit_points(game=game, unit=unit)
            units.set_value(column=UnitColumn.LEVEL, unit=unit, value=after)
            gained = UnitControl.max_hit_points(game=game, unit=unit) - whole_before
            units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=units.get_value(column=UnitColumn.HIT_POINTS, unit=unit) + gained)

    @staticmethod
    def hurt(*, game, unit, damage):
        """Take hit points off a unit, remove the unit when none are left, and return whether it was removed."""
        units = game.get_units()
        left = units.get_value(column=UnitColumn.HIT_POINTS, unit=unit) - damage
        if left > DEAD:
            units.set_value(column=UnitColumn.HIT_POINTS, unit=unit, value=left)
            return False
        UnitControl.remove(game=game, unit=unit)
        return True

    @staticmethod
    def has_nothing_left(*, game, civilization):
        """Return whether a civilization is beaten: it has founded cities and holds none now, or has founded none and has no unit left."""
        holder = game.get_civilization(civilization)
        if holder.get_cities_founded() > NOTHING:
            return not game.get_cities_of(civilization)
        return not UnitControl.units_of(game=game, civilization=civilization)

    @staticmethod
    def settle_losses(game):
        """Mark as lost every civilization still playing that has nothing left, and take its units off the map."""
        for civilization in game.get_still_playing():
            if Combat.has_nothing_left(game=game, civilization=civilization):
                for unit in UnitControl.units_of(game=game, civilization=civilization):
                    UnitControl.remove(game=game, unit=unit)
                game.get_civilization(civilization).lose()
