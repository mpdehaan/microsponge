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
from microsponge.engine.civilizations.sight import Sight
from microsponge.engine.kinds.unit_kinds import armor_against, attack_dice, can_hit, can_hit_ranged, has_melee, has_ranged
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.units.levels import NO_EXPERIENCE, Levels
from microsponge.engine.units.unit_control import NO_BONUS, NO_DAMAGE, WHOLE, UnitControl
from microsponge.engine.world.layer import Layer
from microsponge.err_messages import (
    ERR_ATTACK_OWN, ERR_CANNOT_ATTACK_CITIES, ERR_CANNOT_HIT, ERR_CITY_UNDEFENDED, ERR_NO_MELEE, ERR_NO_RANGED, ERR_NOT_AT_WAR, ERR_NOT_IN_SIGHT, ERR_NOTHING_TO_ATTACK, ERR_OUT_OF_RANGE,
)

# The hit points of a unit that is gone.
DEAD = 0
# A ranged attack reaches at least the tiles next to the attacker.
NEXT_TO = 1
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



class Tally:
    """The names of what a civilization counts for each kind of its units in fights."""

    ATTACKS = 'attacks'
    KILLS = 'kills'
    # Attacks the civilization's units made on a city, and attacks on the civilization's cities, by the kind of the unit attacking.
    CITY_ATTACKS = 'city_attacks'
    ATTACKS_ON_ITS_CITIES = 'attacks_on_its_cities'
    # The civilization's units lost, by their kind: attacking a city, attacking a unit in the field, defending inside a city and defending in the field.
    LOST_ATTACKING_CITY = 'lost_attacking_city'
    LOST_ATTACKING_FIELD = 'lost_attacking_field'
    LOST_DEFENDING_CITY = 'lost_defending_city'
    LOST_DEFENDING_FIELD = 'lost_defending_field'

    LOSSES = (LOST_ATTACKING_CITY, LOST_ATTACKING_FIELD, LOST_DEFENDING_CITY, LOST_DEFENDING_FIELD)


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
        """Return why a unit cannot make a melee attack on a tile next to it, as an error message, or None when it can.

        The unit's kind has to have a melee attack. There has to be a unit on the tile, or a
        city center with units inside, of a civilization the attacker's is at war with; a kind
        that does not attack cities cannot attack the units inside one; and the attacker's kind
        has to be able to hit the unit that would be hit.
        """
        kind = UnitControl.kind_of(game=game, unit=unit)
        if not has_melee(kind):
            return ERR_NO_MELEE.format(unit=shown_name(kind))
        return Combat.problem_target(game=game, unit=unit, x=x, y=y, hits=can_hit)

    @staticmethod
    def problem_ranged(*, game, unit, x, y):
        """Return why a unit cannot make a ranged attack on a tile, as an error message, or None when it can: its kind has a ranged attack, the tile is within the range and in its civilization's sight, and the target is one the ranged attack can hit, as for a melee attack."""
        kind = UnitControl.kind_of(game=game, unit=unit)
        if not has_ranged(kind):
            return ERR_NO_RANGED.format(unit=shown_name(kind))
        world, from_x, from_y = UnitControl.tile_of(game=game, unit=unit)
        away = Combat.tiles_apart(game=game, world=world, from_x=from_x, from_y=from_y, to_x=x, to_y=y)
        if not NEXT_TO <= away <= kind.RANGE:
            return ERR_OUT_OF_RANGE.format(unit=shown_name(kind), range=kind.RANGE)
        owner = game.get_units().get_value(column=UnitColumn.OWNER, unit=unit)
        if not Sight.view(game=game, civilization=owner).can_see(world=world, x=x, y=y):
            return ERR_NOT_IN_SIGHT.format(unit=shown_name(kind))
        return Combat.problem_target(game=game, unit=unit, x=x, y=y, hits=lambda kind, target: can_hit_ranged(kind=kind, target=target))

    @staticmethod
    def tiles_apart(*, game, world, from_x, from_y, to_x, to_y):
        """Return how many moves apart two tiles of a world are, going around the world the shorter way."""
        return max(game.get_world(world).columns_apart(first=from_x, second=to_x), abs(from_y - to_y))

    @staticmethod
    def problem_target(*, game, unit, x, y, hits):
        """Return why a unit cannot attack what is on a tile, as an error message, or None when it can, with hits(kind, target) saying whether the attack can hit a kind of unit."""
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
        kind = UnitControl.kind_of(game=game, unit=unit)
        if target == NOTHING:
            if not kind.ATTACKS_CITIES:
                return ERR_CANNOT_ATTACK_CITIES.format(unit=shown_name(kind), city=game.get_theme().CITY.NAME)
            target = Combat.defender_of_city(game=game, city=city)
            if target is None:
                return ERR_CITY_UNDEFENDED.format(name=game.get_city(city).get_name(), city=game.get_theme().CITY.NAME)
        hit = UnitControl.kind_of(game=game, unit=target)
        if not hits(kind=kind, target=hit):
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
        able = [unit for unit in game.get_city(city).get_units() if has_melee(UnitControl.kind_of(game=game, unit=unit)) and can_hit(kind=UnitControl.kind_of(game=game, unit=unit), target=kind)]
        return max(able, key=lambda unit: UnitControl.average_roll(attacker=UnitControl.kind_of(game=game, unit=unit), defender=kind), default=None)

    @staticmethod
    def attack(*, game, unit, x, y):
        """Have a unit make a melee attack on the tile next to it, and return what the attack did. The order checks and the action points are Orders' business."""
        problem = Combat.problem_attacking(game=game, unit=unit, x=x, y=y)
        if problem is not None:
            raise ValueError(problem)
        return Combat.resolve(game=game, unit=unit, x=x, y=y, ranged=False)

    @staticmethod
    def ranged_attack(*, game, unit, x, y):
        """Have a unit make a ranged attack on a tile within its range, and return what the attack did. A ranged attack never takes a city, and the target strikes back only with a ranged attack of its own that reaches the attacker."""
        problem = Combat.problem_ranged(game=game, unit=unit, x=x, y=y)
        if problem is not None:
            raise ValueError(problem)
        return Combat.resolve(game=game, unit=unit, x=x, y=y, ranged=True)

    @staticmethod
    def ranged_striker(*, game, candidates, attacker):
        """Return the unit among some that strikes back at a ranged attacker, the one with the strongest ranged dice among those whose ranged attack reaches and can hit the attacker, or None."""
        world, x, y = UnitControl.tile_of(game=game, unit=attacker)
        kind = UnitControl.kind_of(game=game, unit=attacker)

        def reaches(unit):
            striker = UnitControl.kind_of(game=game, unit=unit)
            _, from_x, from_y = UnitControl.tile_of(game=game, unit=unit)
            return can_hit_ranged(kind=striker, target=kind) and Combat.tiles_apart(game=game, world=world, from_x=from_x, from_y=from_y, to_x=x, to_y=y) <= striker.RANGE

        able = [unit for unit in candidates if UnitControl.kind_of(game=game, unit=unit).STRIKES_BACK and reaches(unit)]
        return max(able, key=lambda unit: attack_dice(kind=UnitControl.kind_of(game=game, unit=unit), target=kind, ranged=True).average(), default=None)

    @staticmethod
    def resolve(*, game, unit, x, y, ranged):
        """Resolve an attack, melee or ranged, on a tile: the roll through the defender's armor, the strike back, the experience, the tallies, and who has lost. Return what the attack did."""
        world, _, _ = UnitControl.tile_of(game=game, unit=unit)
        target, city = Combat.target_at(game=game, world=world, x=x, y=y)
        in_city = target == NOTHING
        attacking = UnitControl.kind_of(game=game, unit=unit)
        if not in_city:
            defender = target
            candidates = [target]
            bonus = NO_BONUS
        else:
            defender = Combat.defender_of_city(game=game, city=city)
            candidates = game.get_city(city).get_units()
            bonus = CityControl.armor_bonus(game=game, city=city, against=attacking)
        if ranged:
            striker = Combat.ranged_striker(game=game, candidates=candidates, attacker=unit)
        else:
            striker = target if not in_city else Combat.striker_of_city(game=game, city=city, attacker=unit)
        bonus += armor_against(defender=UnitControl.kind_of(game=game, unit=defender), attacker=attacking)
        attacker_kind = Combat.owner_and_kind(game=game, unit=unit)
        defender_kind = Combat.owner_and_kind(game=game, unit=defender)
        striker_kind = None if striker is None else Combat.owner_and_kind(game=game, unit=striker)
        roll = UnitControl.roll_against(game=game, unit=unit, target=defender, in_city=in_city, ranged=ranged)
        damage = UnitControl.mitigated(roll=roll, armor_class=UnitControl.armor_class_of(game=game, unit=defender, bonus=bonus))
        prizes = {defender: Combat.kill_experience(game=game, unit=defender), unit: Combat.kill_experience(game=game, unit=unit)}
        defender_killed = Combat.hurt(game=game, unit=defender, damage=damage)
        strike_back = NO_DAMAGE
        attacker_killed = False
        if striker is not None and not (defender_killed and striker == defender):
            strike_back = Combat.strike_back(game=game, attacker=unit, striker=striker, ranged=ranged)
            attacker_killed = Combat.hurt(game=game, unit=unit, damage=strike_back)
        Combat.reward(game=game, attacker=unit, defender=defender, striker=striker, prizes=prizes, defender_killed=defender_killed, attacker_killed=attacker_killed)
        Combat.tally(game=game, attacker=attacker_kind, striker=striker_kind, defender_killed=defender_killed, attacker_killed=attacker_killed)
        Combat.tally_losses(game=game, attacker=attacker_kind, defender=defender_kind, in_city=in_city, defender_killed=defender_killed, attacker_killed=attacker_killed)
        if in_city:
            Combat.tally_city_attack(game=game, attacker=attacker_kind, city=city)
        Combat.settle_losses(game)
        return AttackOutcome(defender=defender, damage=damage, strike_back=strike_back, defender_killed=defender_killed, attacker_killed=attacker_killed, striker=striker if strike_back else None)

    @staticmethod
    def tally_losses(*, game, attacker, defender, in_city, defender_killed, attacker_killed):
        """Count a unit lost for its civilization and kind: the attacker lost attacking a city or in the field, and the defender lost defending a city or in the field."""
        if attacker_killed:
            owner, kind = attacker
            game.get_civilization(owner).add_to_tally(tally=Tally.LOST_ATTACKING_CITY if in_city else Tally.LOST_ATTACKING_FIELD, kind=kind)
        if defender_killed:
            owner, kind = defender
            game.get_civilization(owner).add_to_tally(tally=Tally.LOST_DEFENDING_CITY if in_city else Tally.LOST_DEFENDING_FIELD, kind=kind)

    @staticmethod
    def owner_and_kind(*, game, unit):
        """Return (the owner, the kind's id) of a unit, kept before a fight in which the unit may die."""
        units = game.get_units()
        return (units.get_value(column=UnitColumn.OWNER, unit=unit), units.get_value(column=UnitColumn.KIND, unit=unit))

    @staticmethod
    def tally(*, game, attacker, striker, defender_killed, attacker_killed):
        """Count an attack for the attacking civilization's kind of unit, and a kill for the kind that killed: the attacker that killed the defender, or the striker that killed the attacker."""
        owner, kind = attacker
        game.get_civilization(owner).add_to_tally(tally=Tally.ATTACKS, kind=kind)
        if defender_killed:
            game.get_civilization(owner).add_to_tally(tally=Tally.KILLS, kind=kind)
        if attacker_killed and striker is not None:
            striker_owner, striker_kind = striker
            game.get_civilization(striker_owner).add_to_tally(tally=Tally.KILLS, kind=striker_kind)

    @staticmethod
    def tally_city_attack(*, game, attacker, city):
        """Count an attack on a city, for the attacking civilization's kind of unit and for the civilization the city belongs to."""
        owner, kind = attacker
        game.get_civilization(owner).add_to_tally(tally=Tally.CITY_ATTACKS, kind=kind)
        game.get_civilization(game.get_city(city).get_owner()).add_to_tally(tally=Tally.ATTACKS_ON_ITS_CITIES, kind=kind)

    @staticmethod
    def strike_back(*, game, attacker, striker, ranged=False):
        """Return the damage a unit that was attacked deals its attacker by striking back: its kind's percent of its own roll, melee or ranged as the attack was, through the attacker's armor, or nothing when its kind does not strike back at the attacker."""
        attacking = UnitControl.kind_of(game=game, unit=attacker)
        striking = UnitControl.kind_of(game=game, unit=striker)
        if ranged:
            roll = UnitControl.roll_against(game=game, unit=striker, target=attacker, ranged=True) * striking.STRIKE_BACK_PERCENT // WHOLE
        else:
            roll = UnitControl.strike_back_roll(attacker=attacking, defender=striking, roll=UnitControl.roll_against(game=game, unit=striker, target=attacker))
        if roll is None:
            return NO_DAMAGE
        bonus = armor_against(defender=attacking, attacker=striking)
        return UnitControl.mitigated(roll=roll, armor_class=UnitControl.armor_class_of(game=game, unit=attacker, bonus=bonus))

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
