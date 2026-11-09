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

"""The reports on a theme's kinds that the tools print: its units, its buildings, its world wonders and its tech tree, each as a table.

A column that no kind of the theme sets is left out of the table, and a line below the table
names the columns left out, so that a table stays as narrow as the theme.
"""

from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.kind import shown_name
from microsponge.support.tables import shown_amounts, shown_amounts_by_kind, shown_flag, shown_kinds, shown_number, table_lines
from microsponge.ui_strings import (
    MSG_BUILDINGS_HEADING, MSG_BUILDINGS_TITLE, MSG_KIND_BUILDING, MSG_KIND_TECHNOLOGY, MSG_KIND_WONDER, MSG_LIST_SEPARATOR, MSG_NO_BUILDINGS, MSG_NO_TECHNOLOGIES,
    MSG_NO_WONDERS, MSG_TECH_HEADING, MSG_TECH_TITLE, MSG_UNUSED_COLUMNS, MSG_WONDERS_HEADING, MSG_WONDERS_TITLE, MSG_EXTRA_DICE, MSG_KIND_UNIT, MSG_NO_CLASS,
    MSG_NO_UNITS, MSG_UNITS_HEADING, MSG_UNITS_TITLE,
)

# Each class of unit with the property of a kind that says whether the kind can hit it.
CAN_HIT = {Domain.LAND: 'CAN_HIT_LAND', Domain.SEA: 'CAN_HIT_SEA', Domain.AIR: 'CAN_HIT_AIR', Domain.SPACE: 'CAN_HIT_SPACE'}


BLANK_LINE = ''


def unused_columns(*, heading, rows):
    """Return the headings of the columns that hold nothing in every row."""
    return [name for column, name in enumerate(heading) if all(is_empty(row[column]) for row in rows)]


def without_columns(*, heading, rows, names):
    """Return the heading and the rows without the columns named."""
    kept = [column for column, name in enumerate(heading) if name not in names]
    return [heading[column] for column in kept], [[row[column] for column in kept] for row in rows]


def is_empty(cell):
    return cell == shown_number(0)


def narrow_table(*, title, heading, rows, kind, theme, markdown):
    """Return a titled table without the columns no row uses, and a line naming those columns when there are any."""
    unused = unused_columns(heading=heading, rows=rows)
    kept_heading, kept_rows = without_columns(heading=heading, rows=rows, names=unused)
    lines = table_lines(title=title, heading=kept_heading, rows=kept_rows, markdown=markdown)
    if unused:
        lines += [BLANK_LINE] * markdown + [MSG_UNUSED_COLUMNS.format(kind=kind, theme=shown_name(theme), columns=MSG_LIST_SEPARATOR.join(unused))]
    return lines


def building_properties(building):
    """Return a building's properties as cells, in the order of MSG_WONDERS_HEADING after the name: what it requires, costs and gives."""
    return [
        shown_kinds(building.REQUIRES), shown_amounts(building.COST), str(building.BUILD_TURNS), shown_amounts(building.SUPPORT),
        shown_amounts(building.PRODUCES), shown_number(building.INCOME_BONUS), shown_number(building.RESEARCH_POINTS),
        shown_number(building.ACTION_POINTS), shown_number(building.GROWS_SOONER), shown_amounts_by_kind(building.WORKED_TILE_BONUS),
        shown_number(building.ARMOR_BONUS), shown_number(building.LEVEL_BONUS), shown_flag(building.WALLS), shown_flag(building.BESIDE_WATER),
    ]


def building_row(building):
    """Return a building's row: one cell for each heading in MSG_BUILDINGS_HEADING, in that order."""
    return [shown_name(building), shown_flag(issubclass(building, Wonder))] + building_properties(building)


def wonder_row(wonder):
    """Return a world wonder's row: one cell for each heading in MSG_WONDERS_HEADING, in that order."""
    return [shown_name(wonder)] + building_properties(wonder)


def wonders_of(theme):
    return [building for building in theme.BUILDINGS if issubclass(building, Wonder)]


def buildings_report(theme, *, markdown=False):
    """Return the report on a theme's buildings, world wonders included, as lines of text or of Markdown."""
    if not theme.BUILDINGS:
        return [MSG_NO_BUILDINGS.format(theme=shown_name(theme))]
    rows = [building_row(building) for building in theme.BUILDINGS]
    return narrow_table(title=MSG_BUILDINGS_TITLE.format(theme=shown_name(theme)), heading=MSG_BUILDINGS_HEADING, rows=rows, kind=MSG_KIND_BUILDING, theme=theme, markdown=markdown)


def wonders_report(theme, *, markdown=False):
    """Return the report on a theme's world wonders as lines of text or of Markdown."""
    wonders = wonders_of(theme)
    if not wonders:
        return [MSG_NO_WONDERS.format(theme=shown_name(theme))]
    rows = [wonder_row(wonder) for wonder in wonders]
    return narrow_table(title=MSG_WONDERS_TITLE.format(theme=shown_name(theme)), heading=MSG_WONDERS_HEADING, rows=rows, kind=MSG_KIND_WONDER, theme=theme, markdown=markdown)


def shown_extra_dice(extra):
    """Return a kind's extra dice as a cell: 1 against air, or the mark for none."""
    return MSG_LIST_SEPARATOR.join(MSG_EXTRA_DICE.format(dice=dice, domain=domain) for domain, dice in extra.items()) or shown_number(0)


def cannot_hit(unit):
    """Return the classes of unit a kind cannot hit, as a cell."""
    return MSG_LIST_SEPARATOR.join(domain for domain, property_name in CAN_HIT.items() if not getattr(unit, property_name)) or shown_number(0)


def unit_row(unit):
    """Return a unit's row: one cell for each heading in MSG_UNITS_HEADING, in that order."""
    return [
        shown_name(unit), unit.DOMAIN or MSG_NO_CLASS, shown_kinds(unit.REQUIRES), shown_amounts(unit.COST), str(unit.BUILD_TURNS), shown_amounts(unit.SUPPORT),
        shown_number(unit.CITIZENS), unit.ATTACK.shown() if unit.ATTACK.most() else shown_number(0), shown_extra_dice(unit.EXTRA_DICE), str(unit.ARMOR_CLASS), str(unit.HIT_POINTS), str(unit.EXPERIENCE_WORTH),
        str(unit.ACTION_POINTS), shown_number(unit.HEAL), shown_number(unit.CITY_HEAL), shown_number(unit.STRIKE_BACK_PERCENT if unit.STRIKES_BACK else 0),
        cannot_hit(unit), shown_flag(unit.TAKES_CITIES), shown_flag(unit.BYPASSES_WALLS), shown_kinds(unit.BUILDS),
    ]


def units_report(theme, *, markdown=False):
    """Return the report on a theme's units as lines of text or of Markdown."""
    if not theme.UNITS:
        return [MSG_NO_UNITS.format(theme=shown_name(theme))]
    rows = [unit_row(unit) for unit in theme.UNITS]
    return narrow_table(title=MSG_UNITS_TITLE.format(theme=shown_name(theme)), heading=MSG_UNITS_HEADING, rows=rows, kind=MSG_KIND_UNIT, theme=theme, markdown=markdown)


def allowed_by(*, theme, technology):
    """Return the units, buildings and improvements of a theme that require a technology, in the theme's order."""
    return [kind for kind in (*theme.UNITS, *theme.BUILDINGS, *theme.IMPROVEMENTS) if technology in kind.REQUIRES]


def technology_row(*, theme, technology):
    """Return a technology's row: one cell for each heading in MSG_TECH_HEADING, in that order."""
    return [
        shown_name(technology), shown_number(technology.RESEARCH), shown_kinds(technology.REQUIRES),
        shown_kinds(allowed_by(theme=theme, technology=technology)), shown_amounts(technology.HARVEST_BONUS), shown_number(technology.UNIT_SUPPORT_BONUS),
    ]


def tech_report(theme, *, markdown=False):
    """Return the report on a theme's tech tree as lines of text or of Markdown."""
    if not theme.TECHNOLOGIES:
        return [MSG_NO_TECHNOLOGIES.format(theme=shown_name(theme))]
    rows = [technology_row(theme=theme, technology=technology) for technology in theme.TECHNOLOGIES]
    return narrow_table(title=MSG_TECH_TITLE.format(theme=shown_name(theme)), heading=MSG_TECH_HEADING, rows=rows, kind=MSG_KIND_TECHNOLOGY, theme=theme, markdown=markdown)
