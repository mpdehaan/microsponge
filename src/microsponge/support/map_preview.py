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

"""A plain text preview of a world the map generator makes, for talking about the generator before any screen exists.

Each tile is one character: a lowercase letter for its terrain, an uppercase letter where the
tile has a strategic resource or a terrain bonus, and a digit where a civilization's settler
starts. The letters are throwaway, picked from each kind's name so that no two kinds share one,
and a legend below the grid says what each means. This is not what the screens will draw.
"""

from string import ascii_lowercase, ascii_uppercase, digits

from microsponge.engine.civilizations.civilization import Civilization
from microsponge.engine.game.game import Game
from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.units.unit_column import UnitColumn
from microsponge.engine.world.generator import MapGenerator
from microsponge.engine.world.layer import Layer
from microsponge.ui_strings import MSG_MAP_CIVILIZATION, MSG_MAP_LEGEND_ITEM, MSG_MAP_LEGEND_TITLE, MSG_MAP_STARTS, MSG_MAP_TITLE

# The civilizations a preview starts when asked for none in particular, and the most a digit can show.
CIVILIZATIONS = 3
FIRST_CIVILIZATION = 1


def marks_for(*, kinds, alphabet):
    """Return a mark for each kind: the first letter of its name not taken yet, else the first free letter of the alphabet."""
    marks = {}
    for kind in kinds:
        free = [letter for letter in shown_name(kind).lower() + alphabet.lower() if letter in alphabet.lower() and letter not in marks.values()]
        marks[kind] = free[0]
    return {kind: mark if alphabet == ascii_lowercase else mark.upper() for kind, mark in marks.items()}


def previewed_game(*, theme, seed, civilizations=CIVILIZATIONS, width=None, height=None):
    """Return a game of a theme on a world the generator made from a seed, with each civilization's settler on its starting tile, and the world's id."""
    game = Game(theme)
    game.set_seed(seed)
    for number in range(FIRST_CIVILIZATION, civilizations + FIRST_CIVILIZATION):
        game.add_civilization(Civilization(MSG_MAP_CIVILIZATION.format(number=number)))
    world = MapGenerator.make(game=game, width=width, height=height)
    MapGenerator.place_civilizations(game=game, world_id=world)
    return game, world


def preview_lines(*, game, world_id, seed):
    """Return the preview of a world as lines: a title, the grid, and the legend."""
    theme = game.get_theme()
    world = game.get_world(world_id)
    catalog = game.get_catalog()
    terrain_marks = marks_for(kinds=theme.TERRAINS, alphabet=ascii_lowercase)
    special = [kind for kind in theme.RESOURCES if kind in {resource for terrain in theme.TERRAINS for resource in terrain.CAN_HAVE}] + list(theme.TERRAIN_BONUSES)
    special_marks = marks_for(kinds=special, alphabet=ascii_uppercase)
    units = game.get_units()
    lines = [MSG_MAP_TITLE.format(theme=shown_name(theme), seed=seed, width=world.get_width(), height=world.get_height())]
    for y in range(world.get_height()):
        row = []
        for x in range(world.get_width()):
            unit = world.get_value(layer=Layer.UNIT, x=x, y=y)
            resource = world.get_value(layer=Layer.STRATEGIC_RESOURCE, x=x, y=y)
            bonus = world.get_value(layer=Layer.TERRAIN_BONUS, x=x, y=y)
            if unit != NOTHING:
                row.append(digits[units.get_value(column=UnitColumn.OWNER, unit=unit) % len(digits)])
            elif resource != NOTHING:
                row.append(special_marks[catalog.get_kind(category=Category.RESOURCES, kind_id=resource)])
            elif bonus != NOTHING:
                row.append(special_marks[catalog.get_kind(category=Category.TERRAIN_BONUSES, kind_id=bonus)])
            else:
                row.append(terrain_marks[game.get_terrain(world=world_id, x=x, y=y)])
        lines.append(''.join(row))
    lines.append(MSG_MAP_LEGEND_TITLE)
    lines += [MSG_MAP_LEGEND_ITEM.format(mark=mark, name=shown_name(kind)) for kind, mark in {**terrain_marks, **special_marks}.items()]
    lines.append(MSG_MAP_STARTS)
    return lines
