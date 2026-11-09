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

"""What a civilization has of what a kind requires."""

from microsponge.engine.cities.city_control import CityControl
from microsponge.engine.civilizations.strategic import Strategic
from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.resource import StrategicResource
from microsponge.engine.kinds.technology import Technology


def known_technologies(*, game, civilization):
    """Return the technologies a civilization knows, as the theme's classes."""
    catalog = game.get_catalog()
    return [catalog.get_kind(category=Category.TECHNOLOGIES, kind_id=technology) for technology in game.get_civilization(civilization).get_technologies()]


def buildings_held(*, game, civilization):
    """Return the buildings in every city of a civilization, as the theme's classes, a class once for each city that has one."""
    held = []
    for city in game.get_cities_of(civilization):
        held += CityControl.buildings_of(game=game, city=city)
    return held


def strategic_for(*, game, civilization, kind):
    """Return the strategic resources a civilization has, for checking what a kind requires.

    The resources are looked for only when the kind requires one, since looking goes over
    every tile of every city of the civilization.
    """
    if not any(issubclass(required, StrategicResource) for required in kind.REQUIRES):
        return []
    return Strategic.held(game=game, civilization=civilization)


def lacking(*, required, technologies, wonders, buildings, strategic):
    """Return the kinds among required that are not had: a technology among technologies, a strategic resource among strategic, a world wonder among wonders, any other building among buildings."""
    def had(kind):
        if issubclass(kind, Technology):
            return kind in technologies
        if issubclass(kind, StrategicResource):
            return kind in strategic
        return kind in (wonders if issubclass(kind, Wonder) else buildings)

    return [kind for kind in required if not had(kind)]


def missing_requirements(*, game, civilization, kind):
    """Return what a kind requires that a civilization does not have, in the kind's order.

    A kind requires technologies, which the civilization has to know, world wonders and other
    buildings, which one of the civilization's cities has to hold, or strategic resources,
    which have to be within the civilization's borders.
    """
    held = buildings_held(game=game, civilization=civilization)
    return lacking(
        required=kind.REQUIRES,
        technologies=known_technologies(game=game, civilization=civilization),
        wonders=held,
        buildings=held,
        strategic=strategic_for(game=game, civilization=civilization, kind=kind),
    )


def missing_in_city(*, game, city, kind):
    """Return what a kind requires that a city does not have for building it, in the kind's order.

    The city's civilization has to know the technologies, hold the world wonders in any of
    its cities, and have the strategic resources within its borders. Any other building that
    is required has to stand in the city itself.
    """
    civilization = game.get_city(city).get_owner()
    return lacking(
        required=kind.REQUIRES,
        technologies=known_technologies(game=game, civilization=civilization),
        wonders=buildings_held(game=game, civilization=civilization),
        buildings=CityControl.buildings_of(game=game, city=city),
        strategic=strategic_for(game=game, civilization=civilization, kind=kind),
    )
