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

"""The catalog of one theme's kinds: the number each kind goes by while a game runs."""

from microsponge.engine.kinds.category import CATEGORIES, Category, shown_category
from microsponge.engine.kinds.kind import saved_name
from microsponge.engine.kinds.unit_kinds import SettlerUnit
from microsponge.engine.saving.keys import text_keys
from microsponge.err_messages import ERR_KIND_GONE, ERR_KIND_TWICE, ERR_NO_SUCH_KIND_ID, ERR_NOT_IN_THEME, ERR_SETTLER_REQUIRES, ERR_UNKNOWN_ID

# The id that means no kind at all, like no unit on a tile. Real ids count up from 1.
NOTHING = 0


def numbered(kinds):
    """Return kinds in a tuple where each one's place is its id, with nothing at NOTHING."""
    return (None, *kinds)


def ids_by_kind(kinds):
    """Return the id of each kind in a numbered tuple."""
    return {kind: kind_id for kind_id, kind in enumerate(kinds) if kind_id != NOTHING}


def names_by_id(ids):
    """Return the saved name of each id, from the id of each kind."""
    return {kind_id: saved_name(kind) for kind, kind_id in ids.items()}


def renumbered(*, values, numbers):
    """Return a list of ids with each id replaced by its number in numbers."""
    try:
        return [numbers[value] for value in values]
    except (KeyError, TypeError):
        raise ValueError(ERR_UNKNOWN_ID.format(known=sorted(numbers))) from None


def renumbered_keys(*, numbered, numbers):
    """Return a dictionary keyed by ids with each id replaced by its number in numbers."""
    return dict(zip(renumbered(values=list(numbered), numbers=numbers), numbered.values()))


class Catalog:
    """Gives every kind of a theme an id within its category, counted from 1 in the theme's order.

    The world and the units hold these ids, never the kinds. Ids belong to a running game: a
    saved game records each id's name, and renumbering() matches those names to this catalog,
    so a theme can reorder its kinds or add to them and old saved games still load.
    """

    __slots__ = ('_theme', '_kinds', '_ids')

    def __init__(self, theme):
        self._theme = theme
        self._kinds = {category: numbered(getattr(theme, category)) for category in CATEGORIES}
        self._ids = {category: ids_by_kind(kinds) for category, kinds in self._kinds.items()}
        for category in CATEGORIES:
            self._check_names_differ(category)
        self._check_settlers_require_nothing()

    def _check_names_differ(self, category):
        """A saved game tells kinds apart by name, so a category can't hold a name twice."""
        names = [saved_name(kind) for kind in getattr(self._theme, category)]
        for name in names:
            if names.count(name) > 1:
                raise ValueError(ERR_KIND_TWICE.format(category=shown_category(category), theme=saved_name(self._theme), name=name))

    def _check_settlers_require_nothing(self):
        """A settler can be built without any technology, in every theme."""
        for kind in self._ids[Category.UNITS]:
            if issubclass(kind, SettlerUnit) and kind.REQUIRES:
                raise ValueError(ERR_SETTLER_REQUIRES.format(name=saved_name(kind), theme=saved_name(self._theme)))

    def get_theme(self):
        return self._theme

    def get_kinds(self, category):
        """Return a category's kinds in a tuple where each one's place is its id, with None at NOTHING."""
        return self._kinds[category]

    def get_kind(self, *, category, kind_id):
        kinds = self._kinds[category]
        if type(kind_id) is not int or not NOTHING < kind_id < len(kinds):
            raise ValueError(ERR_NO_SUCH_KIND_ID.format(category=shown_category(category), kind_id=kind_id, theme=saved_name(self._theme)))
        return kinds[kind_id]

    def get_id(self, *, category, kind):
        try:
            return self._ids[category][kind]
        except (KeyError, TypeError):
            raise ValueError(ERR_NOT_IN_THEME.format(kind=kind, category=shown_category(category), theme=saved_name(self._theme))) from None

    def get_names(self):
        """Return what a saved game records: for each category, the name of each id."""
        return {category: text_keys(names_by_id(ids)) for category, ids in self._ids.items()}

    def renumbering(self, *, category, saved_names):
        """Return the id here of each id in a saved game's names for a category, or None when every id is the same.

        A saved game's ids are its own. A name this theme no longer has is refused, since
        nothing says yet what becomes of a kind that a later version removed.
        """
        here = {saved_name(kind): kind_id for kind, kind_id in self._ids[category].items()}
        numbers = {NOTHING: NOTHING}
        for saved_id, name in saved_names.items():
            if name not in here:
                raise ValueError(ERR_KIND_GONE.format(name=name, category=shown_category(category), theme=saved_name(self._theme)))
            numbers[int(saved_id)] = here[name]
        if all(saved_id == kind_id for saved_id, kind_id in numbers.items()):
            return None
        return numbers

    def renumberings(self, saved_names):
        """Return renumbering() for every category of a saved game's names. A category the saved game lacks changes nothing."""
        return {category: self.renumbering(category=category, saved_names=saved_names.get(category, {})) for category in CATEGORIES}
