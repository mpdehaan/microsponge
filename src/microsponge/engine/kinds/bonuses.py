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

"""What the technologies a civilization has add up to. Bonuses are percentages, and they are additive."""

WHOLE = 100
FREE = 0


def harvest_percent(*, technologies, resource):
    """Return how fast a resource is harvested with some technologies, as a percent of the plain rate: 100 with no bonus."""
    return WHOLE + sum(technology.HARVEST_BONUS.get(resource, 0) for technology in technologies)


def unit_support_percent(technologies):
    """Return what a unit costs to support with some technologies, as a percent of the plain cost, never less than nothing."""
    return max(WHOLE - sum(technology.UNIT_SUPPORT_BONUS for technology in technologies), FREE)
