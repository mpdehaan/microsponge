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

"""What a civilization researches: one technology at a time, paid for with research points."""

from microsponge.engine.civilizations.requirements import buildings_held, known_technologies, missing_requirements
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.err_messages import ERR_ALREADY_KNOWN, ERR_ALREADY_RESEARCHING, ERR_MUST_PICK_RESEARCH, ERR_RESEARCH_REQUIRES

NO_POINTS = 0


class Research:
    """The rules for research, as static methods over a game. It is never made into an object.

    A civilization has a research capacity each turn, from its cities and from certain
    buildings, which goes toward the one technology it researches, with no queue: when the
    points put toward the technology reach what the technology takes, the civilization knows
    the technology and has to pick the next. Points never gather in a pool: a turn with no
    technology picked puts its points nowhere, and once there is nothing left to research,
    each turn's points become currency.
    """

    __slots__ = ()

    @staticmethod
    def available(*, game, civilization):
        """Return the technologies a civilization could research now, in the theme's order: not known yet, with what each requires."""
        known = known_technologies(game=game, civilization=civilization)
        unknown = [technology for technology in game.get_theme().TECHNOLOGIES if technology not in known]
        return [technology for technology in unknown if not missing_requirements(game=game, civilization=civilization, kind=technology)]

    @staticmethod
    def researching(*, game, civilization):
        """Return the technology a civilization is researching, as the theme's class, or None."""
        technology = game.get_civilization(civilization).get_researching()
        return None if technology == NOTHING else game.get_catalog().get_kind(category=Category.TECHNOLOGIES, kind_id=technology)

    @staticmethod
    def must_choose(*, game, civilization):
        """Return whether a civilization has to pick a technology: it is researching nothing, and there is one it could research."""
        return Research.researching(game=game, civilization=civilization) is None and bool(Research.available(game=game, civilization=civilization))

    @staticmethod
    def problem_choosing(*, game, civilization, technology):
        """Return why a civilization cannot research a technology, as an error message, or None when it can.

        The civilization cannot know the technology already, has to have what the technology
        requires, and cannot switch away from a technology it is researching, for now.
        """
        technology_id = game.get_catalog().get_id(category=Category.TECHNOLOGIES, kind=technology)
        holder = game.get_civilization(civilization)
        if holder.knows(technology_id):
            return ERR_ALREADY_KNOWN.format(name=holder.get_name(), technology=shown_name(technology))
        current = Research.researching(game=game, civilization=civilization)
        if current is not None and current is not technology:
            return ERR_ALREADY_RESEARCHING.format(name=holder.get_name(), technology=shown_name(current), wanted=shown_name(technology))
        missing = missing_requirements(game=game, civilization=civilization, kind=technology)
        if missing:
            return ERR_RESEARCH_REQUIRES.format(technology=shown_name(technology), required=shown_name(missing[0]))
        return None

    @staticmethod
    def choose(*, game, civilization, technology):
        """Set the technology a civilization researches. Picking the same technology again changes nothing."""
        problem = Research.problem_choosing(game=game, civilization=civilization, technology=technology)
        if problem is not None:
            raise ValueError(problem)
        game.get_civilization(civilization).set_researching(game.get_catalog().get_id(category=Category.TECHNOLOGIES, kind=technology))

    @staticmethod
    def problem_ending_turn(*, game, civilization):
        """Return why a civilization cannot end its turn yet, as an error message, or None when it can: a pick is forced while a technology is left to pick."""
        if Research.must_choose(game=game, civilization=civilization):
            return ERR_MUST_PICK_RESEARCH.format(name=game.get_civilization(civilization).get_name())
        return None

    @staticmethod
    def points_a_turn(*, game, civilization):
        """Return the research points a civilization gathers each turn: what the theme gives for each city, and what its buildings add."""
        from_cities = game.get_theme().CITY.RESEARCH_POINTS * len(game.get_cities_of(civilization))
        return from_cities + sum(building.RESEARCH_POINTS for building in buildings_held(game=game, civilization=civilization))

    @staticmethod
    def advance(*, game, civilization):
        """Put a turn's research points toward the technology a civilization researches, and let the civilization know the technology once the points reach what that takes.

        The points past what the technology takes are lost. With nothing left to research,
        the points become currency at the theme's rate. A turn cannot be ended by order with a
        technology left to pick, but the engine can end one, and then the points go nowhere.
        """
        holder = game.get_civilization(civilization)
        points = Research.points_a_turn(game=game, civilization=civilization)
        technology = Research.researching(game=game, civilization=civilization)
        if technology is None:
            if not Research.available(game=game, civilization=civilization):
                theme = game.get_theme()
                currency = game.get_catalog().get_id(category=Category.RESOURCES, kind=theme.PRIMARY_RESOURCE)
                holder.add(resource=currency, amount=points * theme.RESEARCH_TO_CURRENCY)
            return
        holder.set_research(holder.get_research() + points)
        if holder.get_research() >= technology.RESEARCH:
            holder.learn(holder.get_researching())
            holder.set_researching(NOTHING)
            holder.set_research(NO_POINTS)
