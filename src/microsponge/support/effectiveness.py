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

"""The effectiveness report: what in a theme does nothing or too little, read from the theme's properties and from the logs of games the computer players played.

For each unit, how often the games made it, and how much it attacked, killed and lost; for each
building and world wonder, what it does and how often it was built; for each technology, what
it allows and gives and how often it was learnt; for each resource, what gives it and what uses
it. A note says what looks wrong, and the report starts with every note.
"""

from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.kinds.unit_kinds import has_melee, has_ranged
from microsponge.engine.units.combat import Tally
from microsponge.support.game_log import Key
from microsponge.support.kind_reports import allowed_by
from microsponge.support.tables import shown_kinds, shown_number, table_lines
from microsponge.ui_strings import (
    MSG_EFFECT_NAMES, MSG_EFFECTIVENESS_BUILDINGS_HEADING, MSG_EFFECTIVENESS_BUILDINGS_TITLE, MSG_EFFECTIVENESS_NOTE,
    MSG_EFFECTIVENESS_NOTES_TITLE, MSG_EFFECTIVENESS_NOTHING, MSG_EFFECTIVENESS_RESOURCES_HEADING, MSG_EFFECTIVENESS_RESOURCES_TITLE,
    MSG_EFFECTIVENESS_SUMMARY, MSG_EFFECTIVENESS_TECHNOLOGIES_HEADING, MSG_EFFECTIVENESS_TECHNOLOGIES_TITLE, MSG_EFFECTIVENESS_UNITS_HEADING,
    MSG_EFFECTIVENESS_UNITS_TITLE, MSG_LIST_SEPARATOR, MSG_NOTE_DOES_NOTHING, MSG_NOTE_LOSES_MORE, MSG_NOTE_NEVER_ATTACKED, MSG_NOTE_NEVER_BUILT,
    MSG_NOTE_NEVER_LEARNT, MSG_NOTE_NEVER_MADE, MSG_NOTE_NOTHING_GIVES, MSG_NOTE_NOTHING_USES, MSG_NOTE_RARELY_MADE, MSG_NONE_MARK,
)

# The properties of a building that do something, in the order the report names them.
BUILDING_EFFECTS = ('CONTROL_POINTS', 'RESEARCH_POINTS', 'PRODUCES', 'INCOME_BONUS', 'WORKED_TILE_BONUS', 'GROWS_SOONER', 'UNIT_SUPPORT_DISCOUNT', 'LEVEL_BONUS', 'ARMOR_BONUS', 'WALLS')
# The properties of a technology that do something.
TECHNOLOGY_EFFECTS = ('HARVEST_BONUS', 'UNIT_SUPPORT_BONUS', 'GROWS_SOONER', 'ENDS_FOG_OF_WAR')
# A unit that loses more than this many times as many units as it kills is noted.
LOSSES_PER_KILL = 2
# A unit made in fewer than this share of the games is noted as rarely made.
RARELY_SHARE = 0.5
LEARNT = 'learnt'
DECIMALS = '{:.1f}'
# Kills are counted for each this much of the primary resource spent on making the unit.
SPENT = 100


def shown_decimal(number):
    return DECIMALS.format(number) if number else MSG_NONE_MARK


def effects_of(*, kind, names):
    """Return the names, as people read them, of the properties of a kind that do something."""
    return [MSG_EFFECT_NAMES[name] for name in names if getattr(kind, name)]


def requirers_of(*, theme, kind):
    """Return the kinds of a theme that require a kind."""
    return [other for other in (*theme.UNITS, *theme.BUILDINGS, *theme.IMPROVEMENTS, *theme.TECHNOLOGIES) if kind in other.REQUIRES]


def provided_by(*, theme, technology):
    """Return the strategic resources a technology makes terrain bonuses provide."""
    return [resource for bonus in theme.TERRAIN_BONUSES for resource in bonus.PROVIDES.get(technology, ())]


def is_fighter(kind):
    return has_melee(kind) or has_ranged(kind)


def games_with(*, logs, used):
    """Return how many of the logs a test of one log is true of."""
    return len([data for data in logs if used(data)])


def unit_tally(*, logs, tally, name):
    return sum(entry[Key.TALLIES].get(tally, {}).get(name, 0) for data in logs for entry in data[Key.CIVILIZATIONS])


def unit_losses(*, logs, name):
    return sum(unit_tally(logs=logs, tally=loss, name=name) for loss in Tally.LOSSES)


def unit_notes(*, kind, logs):
    """Return the notes on a unit: never made, rarely made, made but never attacked, or losing more than it kills."""
    name = shown_name(kind)
    made = len([unit for data in logs for unit in data[Key.UNITS] if unit[Key.KIND] == name])
    if not made:
        return [MSG_NOTE_NEVER_MADE]
    notes = []
    if games_with(logs=logs, used=lambda data: any(unit[Key.KIND] == name for unit in data[Key.UNITS])) < RARELY_SHARE * len(logs):
        notes.append(MSG_NOTE_RARELY_MADE)
    if is_fighter(kind):
        attacks = unit_tally(logs=logs, tally=Tally.ATTACKS, name=name)
        if not attacks:
            notes.append(MSG_NOTE_NEVER_ATTACKED)
        elif unit_losses(logs=logs, name=name) > LOSSES_PER_KILL * unit_tally(logs=logs, tally=Tally.KILLS, name=name):
            notes.append(MSG_NOTE_LOSES_MORE)
    return notes


def unit_row(*, kind, logs, theme):
    name = shown_name(kind)
    made = len([unit for data in logs for unit in data[Key.UNITS] if unit[Key.KIND] == name])
    attacks = unit_tally(logs=logs, tally=Tally.ATTACKS, name=name)
    kills = unit_tally(logs=logs, tally=Tally.KILLS, name=name)
    cost = kind.COST.get(theme.PRIMARY_RESOURCE, 0)
    per_made = (lambda count: count / made if made else 0)
    return [
        name, shown_number(made), shown_number(games_with(logs=logs, used=lambda data: any(unit[Key.KIND] == name for unit in data[Key.UNITS]))),
        shown_number(attacks), shown_number(kills), shown_number(unit_losses(logs=logs, name=name)),
        shown_decimal(per_made(attacks)), shown_decimal(per_made(kills)), shown_decimal(kills * SPENT / (made * cost) if made and cost else 0),
        MSG_LIST_SEPARATOR.join(unit_notes(kind=kind, logs=logs)) or MSG_NONE_MARK,
    ]


def building_notes(*, theme, kind, logs):
    notes = []
    if not effects_of(kind=kind, names=BUILDING_EFFECTS) and not requirers_of(theme=theme, kind=kind):
        notes.append(MSG_NOTE_DOES_NOTHING)
    if not built_count(logs=logs, kind=kind):
        notes.append(MSG_NOTE_NEVER_BUILT)
    return notes


def built_count(*, logs, kind):
    return len([entry for data in logs for entry in data[Key.BUILT] if entry[Key.BUILDING] == shown_name(kind)])


def first_turns(*, logs, matches):
    """Return the first turn of each game something happened in, from a test of a log's entries, as a list."""
    turns = []
    for data in logs:
        found = [entry[Key.TURN] for entry in matches(data)]
        if found:
            turns.append(min(found))
    return turns


def average(numbers):
    return sum(numbers) / len(numbers) if numbers else 0


def building_row(*, theme, kind, logs):
    name = shown_name(kind)
    does = effects_of(kind=kind, names=BUILDING_EFFECTS)
    turns = first_turns(logs=logs, matches=lambda data: [entry for entry in data[Key.BUILT] if entry[Key.BUILDING] == name])
    return [
        name, MSG_LIST_SEPARATOR.join(does) or MSG_NONE_MARK, shown_kinds(requirers_of(theme=theme, kind=kind)),
        shown_number(built_count(logs=logs, kind=kind)), shown_number(len(turns)), shown_number(round(average(turns))),
        MSG_LIST_SEPARATOR.join(building_notes(theme=theme, kind=kind, logs=logs)) or MSG_NONE_MARK,
    ]


def learnt_turns(*, logs, kind):
    return first_turns(logs=logs, matches=lambda data: [event for event in data[Key.EVENTS] if event[Key.WHAT] == LEARNT and event[Key.SUBJECT] == shown_name(kind)])


def technology_notes(*, theme, kind, logs):
    notes = []
    if not effects_of(kind=kind, names=TECHNOLOGY_EFFECTS) and not requirers_of(theme=theme, kind=kind) and not provided_by(theme=theme, technology=kind):
        notes.append(MSG_NOTE_DOES_NOTHING)
    if not learnt_turns(logs=logs, kind=kind):
        notes.append(MSG_NOTE_NEVER_LEARNT)
    return notes


def technology_row(*, theme, kind, logs):
    turns = learnt_turns(logs=logs, kind=kind)
    gives = effects_of(kind=kind, names=TECHNOLOGY_EFFECTS) + [shown_name(resource) for resource in provided_by(theme=theme, technology=kind)]
    return [
        shown_name(kind), shown_kinds([*allowed_by(theme=theme, technology=kind), *(other for other in theme.TECHNOLOGIES if kind in other.REQUIRES)]),
        MSG_LIST_SEPARATOR.join(gives) or MSG_NONE_MARK, shown_number(len(turns)), shown_number(round(average(turns))),
        MSG_LIST_SEPARATOR.join(technology_notes(theme=theme, kind=kind, logs=logs)) or MSG_NONE_MARK,
    ]


def sources_of(*, theme, resource):
    """Return the kinds of a theme a resource comes from: terrains, terrain bonuses, improvements and buildings that give it, terrains that can have it as a strategic resource, and terrain bonuses that provide it."""
    sources = [kind for kind in theme.TERRAINS if resource in kind.GIVES or resource in kind.CAN_HAVE]
    sources += [kind for kind in theme.TERRAIN_BONUSES if resource in kind.GIVES or any(resource in provided for provided in kind.PROVIDES.values())]
    sources += [kind for kind in theme.IMPROVEMENTS if resource in kind.TILE_BONUS]
    sources += [kind for kind in theme.BUILDINGS if resource in kind.PRODUCES]
    return sources


def users_of(*, theme, resource):
    """Return the kinds of a theme that cost or require a resource."""
    return [kind for kind in (*theme.UNITS, *theme.BUILDINGS) if resource in kind.COST or resource in kind.REQUIRES]


def resource_notes(*, theme, resource):
    """Return the notes on a resource: nothing uses it, which the primary resource and food never get, since everything is paid for in the one and citizens eat the other, or nothing gives it."""
    notes = []
    if resource not in (theme.PRIMARY_RESOURCE, theme.FOOD) and not users_of(theme=theme, resource=resource):
        notes.append(MSG_NOTE_NOTHING_USES)
    if resource is not theme.PRIMARY_RESOURCE and not sources_of(theme=theme, resource=resource) and not resource_from_city(theme=theme, resource=resource):
        notes.append(MSG_NOTE_NOTHING_GIVES)
    return notes


def resource_from_city(*, theme, resource):
    return resource in theme.CITY.PRODUCES


def resource_row(*, theme, resource):
    return [
        shown_name(resource), shown_kinds(sources_of(theme=theme, resource=resource)), shown_kinds(users_of(theme=theme, resource=resource)),
        MSG_LIST_SEPARATOR.join(resource_notes(theme=theme, resource=resource)) or MSG_NONE_MARK,
    ]


def all_notes(*, theme, logs):
    """Return (the kind, its notes) for every kind of a theme with a note, units first, then buildings, technologies and resources."""
    notes = [(kind, unit_notes(kind=kind, logs=logs)) for kind in theme.UNITS]
    notes += [(kind, building_notes(theme=theme, kind=kind, logs=logs)) for kind in theme.BUILDINGS]
    notes += [(kind, technology_notes(theme=theme, kind=kind, logs=logs)) for kind in theme.TECHNOLOGIES]
    notes += [(kind, resource_notes(theme=theme, resource=kind)) for kind in theme.RESOURCES]
    return [(kind, found) for kind, found in notes if found]


def report_lines(*, theme, logs, markdown=False):
    """Return the effectiveness report of a theme from some logs, as lines."""
    lines = [MSG_EFFECTIVENESS_SUMMARY.format(theme=shown_name(theme), games=len(logs), wonders=len([kind for kind in theme.BUILDINGS if issubclass(kind, Wonder)])), '', MSG_EFFECTIVENESS_NOTES_TITLE]
    notes = all_notes(theme=theme, logs=logs)
    lines += [MSG_EFFECTIVENESS_NOTE.format(kind=shown_name(kind), notes=MSG_LIST_SEPARATOR.join(found)) for kind, found in notes] or [MSG_EFFECTIVENESS_NOTHING]
    tables = (
        (MSG_EFFECTIVENESS_UNITS_TITLE, MSG_EFFECTIVENESS_UNITS_HEADING, [unit_row(kind=kind, logs=logs, theme=theme) for kind in theme.UNITS]),
        (MSG_EFFECTIVENESS_BUILDINGS_TITLE, MSG_EFFECTIVENESS_BUILDINGS_HEADING, [building_row(theme=theme, kind=kind, logs=logs) for kind in theme.BUILDINGS]),
        (MSG_EFFECTIVENESS_TECHNOLOGIES_TITLE, MSG_EFFECTIVENESS_TECHNOLOGIES_HEADING, [technology_row(theme=theme, kind=kind, logs=logs) for kind in theme.TECHNOLOGIES]),
        (MSG_EFFECTIVENESS_RESOURCES_TITLE, MSG_EFFECTIVENESS_RESOURCES_HEADING, [resource_row(theme=theme, resource=resource) for resource in theme.RESOURCES]),
    )
    for title, heading, rows in tables:
        lines += [''] + table_lines(title=title, heading=heading, rows=rows, markdown=markdown)
    return lines
