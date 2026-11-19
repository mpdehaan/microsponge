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

"""What a computer player makes of a theme: which kinds fight, fly, hit air units or improve tiles, and what each kind of unit, building and technology is worth for what it costs.

Everything here is read from the properties of a theme's kinds, so that a computer player
plays any theme without knowing one (`GAME_RULES.md`, "Computer players"). The worth of a kind
is a rough number for ranking kinds against each other, never shown to a player. The weights
are constants on `ComputerPlayer`, which a theme's player may change.
"""

from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.dice import NO_DICE
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.unit_kinds import SettlerUnit, attack_dice

NOTHING_WORTH = 0
# A kind that costs nothing is counted as costing this much, so that its worth can be divided by its cost.
LEAST_COST = 1


def total_cost(kind):
    """Return everything a kind costs to build, every resource added together."""
    return max(sum(kind.COST.values()), LEAST_COST)


def can_fight(kind):
    return kind.ATTACK is not NO_DICE


def hits_air(kind):
    """Return whether a kind of unit can hit air units, or rolls extra dice against them."""
    return can_fight(kind) and (kind.CAN_HIT_AIR or Domain.AIR in kind.EXTRA_DICE)


class Appraisal:
    """Static: reads a theme's kinds by their properties, for a computer player."""

    __slots__ = ()

    @staticmethod
    def strength(kind):
        """Return how strong a kind of unit is in a fight: the average of its attack dice times its hit points."""
        return attack_dice(kind=kind, target=kind).average() * kind.HIT_POINTS if can_fight(kind) else NOTHING_WORTH

    @staticmethod
    def unit_worth(kind):
        """Return a kind of unit's strength for what it costs."""
        return Appraisal.strength(kind) / total_cost(kind)

    @staticmethod
    def ranked_units(kinds):
        """Return some kinds of unit, the most worth for its cost first."""
        return sorted(kinds, key=Appraisal.unit_worth, reverse=True)

    @staticmethod
    def fighters(theme):
        """Return the kinds of unit that fight on land and can take a city, the most worth first: what a division is raised from."""
        return Appraisal.ranked_units([kind for kind in theme.UNITS if can_fight(kind) and kind.TAKES_CITIES and kind.DOMAIN == Domain.LAND])

    @staticmethod
    def flyers(theme):
        """Return the kinds of air unit that fight, the most worth first."""
        return Appraisal.ranked_units([kind for kind in theme.UNITS if can_fight(kind) and kind.DOMAIN == Domain.AIR])

    @staticmethod
    def anti_air(theme):
        """Return the kinds of unit that can hit air units, those that roll most against them first."""
        kinds = [kind for kind in theme.UNITS if hits_air(kind) and kind.DOMAIN != Domain.AIR]
        return sorted(kinds, key=lambda kind: attack_dice(kind=kind, target=Appraisal.an_air_unit(theme) or kind).average() / total_cost(kind), reverse=True)

    @staticmethod
    def an_air_unit(theme):
        flyers = [kind for kind in theme.UNITS if kind.DOMAIN == Domain.AIR]
        return flyers[0] if flyers else None

    @staticmethod
    def engineers(theme):
        """Return the kinds of unit that build improvements on tiles."""
        return [kind for kind in theme.UNITS if kind.BUILDS and not issubclass(kind, SettlerUnit)]

    @staticmethod
    def lasting_improvements(kind):
        """Return the improvements a kind of unit builds that stay on the tile, the most a tile gains first: work that changes the terrain is left out."""
        lasting = [improvement for improvement in kind.BUILDS if improvement.BECOMES is None]
        return sorted(lasting, key=lambda improvement: sum(improvement.TILE_BONUS.values()), reverse=True)

    @staticmethod
    def building_worth(*, building, theme, weights):
        """Return what a building gives for what it costs, each effect counted by its weight, and what the best unit it allows is worth."""
        effects = {
            weights.RESEARCH_WEIGHT: building.RESEARCH_POINTS,
            weights.CONTROL_WEIGHT: sum(building.CONTROL_POINTS.values()),
            weights.INCOME_WEIGHT: building.INCOME_BONUS,
            weights.GROWTH_WEIGHT: building.GROWS_SOONER,
            weights.TILE_WEIGHT: sum(sum(amounts.values()) for amounts in building.WORKED_TILE_BONUS.values()),
            weights.ARMOR_WEIGHT: building.ARMOR_BONUS,
            weights.LEVEL_WEIGHT: building.LEVEL_BONUS,
            weights.PRODUCE_WEIGHT: sum(building.PRODUCES.values()),
            weights.UPKEEP_WEIGHT: sum(building.UNIT_SUPPORT_DISCOUNT.values()),
        }
        worth = sum(weight * amount for weight, amount in effects.items())
        allowed = [kind for kind in theme.UNITS if building in kind.REQUIRES]
        worth += max((Appraisal.unit_worth(kind) for kind in allowed), default=NOTHING_WORTH) * weights.ALLOWS_WEIGHT
        return worth / total_cost(building)

    @staticmethod
    def ranked_buildings(*, theme, weights):
        """Return a theme's buildings and world wonders, the most worth for their cost first."""
        return sorted(theme.BUILDINGS, key=lambda building: Appraisal.building_worth(building=building, theme=theme, weights=weights), reverse=True)

    @staticmethod
    def is_wonder(building):
        return issubclass(building, Wonder)

    @staticmethod
    def technology_worth(*, technology, theme, weights):
        """Return what a technology is worth for its research points: what the kinds it allows are worth, and a share of what the technologies it opens are worth."""
        worth = Appraisal.allows_worth(technology=technology, theme=theme, weights=weights)
        opened = [later for later in theme.TECHNOLOGIES if technology in later.REQUIRES]
        worth += sum(Appraisal.allows_worth(technology=later, theme=theme, weights=weights) for later in opened) * weights.OPENS_WEIGHT
        return worth / max(technology.RESEARCH, LEAST_COST)

    @staticmethod
    def allows_worth(*, technology, theme, weights):
        """Return what the kinds a technology allows are worth, with the technology's own bonuses."""
        units = sum(Appraisal.unit_worth(kind) for kind in theme.UNITS if technology in kind.REQUIRES) * weights.UNIT_WEIGHT
        buildings = sum(Appraisal.building_worth(building=building, theme=theme, weights=weights) for building in theme.BUILDINGS if technology in building.REQUIRES)
        improvements = sum(sum(improvement.TILE_BONUS.values()) for improvement in theme.IMPROVEMENTS if technology in improvement.REQUIRES) * weights.TILE_WEIGHT
        own = (sum(technology.HARVEST_BONUS.values()) + technology.UNIT_SUPPORT_BONUS + technology.GROWS_SOONER) * weights.BONUS_WEIGHT
        return units + buildings + improvements + own

    @staticmethod
    def ranked_technologies(*, theme, weights):
        """Return a theme's technologies, the most worth for their research points first."""
        return sorted(theme.TECHNOLOGIES, key=lambda technology: Appraisal.technology_worth(technology=technology, theme=theme, weights=weights), reverse=True)
