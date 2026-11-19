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

"""The report of a game's log: tables that answer questions about the game, and a timeline of the high points of each civilization.

Everything here is worked out from the data of a log file (`game_log.py`), with no game in
memory, so that a log written once can be asked again and again. New questions about a game
are answered by adding a table here. `game_log_page.py` puts the same tables on a page beside
the charts.
"""

from dataclasses import dataclass

from microsponge.engine.kinds.catalog import NOTHING
from microsponge.engine.units.combat import Tally
from microsponge.support.chronicle import What
from microsponge.support.game_log import NEVER, WHATS, Ending, Group, Key, Series
from microsponge.support.game_story import SENTENCES
from microsponge.support.tables import BLANK_LINE, shown_flag, shown_number, table_lines
from microsponge.ui_strings import (
    MSG_LOG_BUILDINGS_HEADING, MSG_LOG_BUILDINGS_TITLE, MSG_LOG_BUILT_HEADING, MSG_LOG_BUILT_TITLE, MSG_LOG_MADE_HEADING, MSG_LOG_MADE_TITLE, MSG_LOG_ORDERS_HEADING, MSG_LOG_ORDERS_TITLE, MSG_NONE_MARK, MSG_LOG_CITIES_HEADING, MSG_LOG_CITIES_TITLE, MSG_LOG_FIGHTING_HEADING, MSG_LOG_FIGHTING_TITLE, MSG_LOG_FORCES_HEADING, MSG_LOG_FORCES_TITLE, MSG_LOG_POINTS_HEADING, MSG_LOG_POINTS_TITLE, MSG_LOG_SCORES_HEADING,
    MSG_LOG_SCORES_TITLE, MSG_LOG_TIMELINE_ENDED, MSG_LOG_TIMELINE_LOST_CITY, MSG_LOG_TIMELINE_STRONGEST, MSG_LOG_TIMELINE_TITLE, MSG_LOG_TIMELINE_WAR_DECLARED_ON, MSG_LOG_NO_WINNER, MSG_LOG_TITLE, MSG_LOG_WON_BY_CONQUEST, MSG_LOG_WON_ON_SCORE,
    MSG_LOG_UNITS_HEADING, MSG_LOG_UNITS_TITLE, MSG_STORY_NOBODY,
)

WHOLE = 100
ONE_PLACE = 1
FIRST_PLACE = 1
ONE_WINNER = 1
# The events a timeline leaves out, because each civilization has many and they are in the charts.
LEFT_OUT_OF_TIMELINES = (What.LEARNT,)
SCORE_PARTS = (Series.MILITARY_SCORE, Series.SCIENCE_SCORE, Series.POPULATION_SCORE, Series.DEVELOPMENT_SCORE)
POINTS_AVERAGED = (Series.POLICY, Series.POLICY_TAKEN, Series.COMMAND, Series.COMMAND_TAKEN, Series.UNITS, Series.INSIDE)


@dataclass(slots=True, kw_only=True)
class Table:

    title: str
    heading: list
    rows: list


@dataclass(slots=True, kw_only=True)
class Timeline:

    title: str
    lines: list


def average(numbers):
    """Return the average of some numbers to one decimal place, or 0 of none."""
    return round(sum(numbers) / len(numbers), ONE_PLACE) if numbers else 0


def percent(*, part, whole):
    return round(WHOLE * part / whole) if whole else 0


def civilization_ids(data):
    return [civilization[Key.ID] for civilization in data[Key.CIVILIZATIONS]]


def name_of(*, data, civilization):
    """Return the name of a civilization of a log, or the words for none when there is none."""
    names = {entry[Key.ID]: entry[Key.NAME] for entry in data[Key.CIVILIZATIONS]}
    return names.get(civilization, MSG_STORY_NOBODY)


def series_of(*, data, civilization, series):
    """Return what a log counted of one thing for a civilization, at the end of each turn the civilization was still playing."""
    return data[Key.SERIES][series][str(civilization)]


def last_of(*, data, civilization, series):
    counted = series_of(data=data, civilization=civilization, series=series)
    return counted[-1] if counted else 0


def strongest_turn(*, data, civilization):
    """Return (the turn, the strength) of the last turn on which a civilization was at its strongest."""
    strength = series_of(data=data, civilization=civilization, series=Series.STRENGTH)
    if not strength:
        return (0, 0)
    most = max(strength)
    return (max(turn for turn, counted in enumerate(strength) if counted == most), most)


def ranked(data):
    """Return the ids of the civilizations of a log, the highest score first."""
    return sorted(civilization_ids(data), key=lambda civilization: -last_of(data=data, civilization=civilization, series=Series.SCORE))


def scores_table(data):
    rows = []
    for civilization in ranked(data):
        turn, most = strongest_turn(data=data, civilization=civilization)
        lost = next(entry[Key.LOST] for entry in data[Key.CIVILIZATIONS] if entry[Key.ID] == civilization)
        parts = [last_of(data=data, civilization=civilization, series=part) for part in SCORE_PARTS]
        rows.append([
            name_of(data=data, civilization=civilization), str(last_of(data=data, civilization=civilization, series=Series.SCORE)), *[str(part) for part in parts],
            str(last_of(data=data, civilization=civilization, series=Series.STRENGTH)), str(most), str(turn), shown_flag(lost),
        ])
    return Table(title=MSG_LOG_SCORES_TITLE, heading=MSG_LOG_SCORES_HEADING, rows=rows)


def events_of(*, data, what):
    name = next(name for name, known in WHATS.items() if known == what)
    return [event for event in data[Key.EVENTS] if event[Key.WHAT] == name]


def cities_table(data):
    rows = []
    took = events_of(data=data, what=What.TOOK)
    for civilization in civilization_ids(data):
        held = [city for city in data[Key.CITIES] if city[Key.OWNER] == civilization]
        rows.append([
            name_of(data=data, civilization=civilization),
            shown_number(len([city for city in data[Key.CITIES] if city[Key.FOUNDER] == civilization])),
            shown_number(len([event for event in took if event[Key.CIVILIZATION] == civilization])),
            shown_number(len([event for event in took if event[Key.OTHER] == civilization])),
            shown_number(len(held)), shown_number(sum(city[Key.CITIZENS] for city in held)), shown_number(sum(len(city[Key.BUILDINGS]) for city in held)),
        ])
    return Table(title=MSG_LOG_CITIES_TITLE, heading=MSG_LOG_CITIES_HEADING, rows=rows)


def kinds_in_order(units):
    """Return the kinds of some units of a log, each once, in the order they first appear."""
    return list(dict.fromkeys(unit[Key.KIND] for unit in units))


def units_row(*, name, kind, units):
    """Return the row of the units table for the units of one kind of one civilization."""
    ended = {ending: len([unit for unit in units if unit[Key.ENDING] == ending]) for ending in (Ending.LOST, Ending.RETIRED, Ending.SETTLED, Ending.ALIVE)}
    lived = sum(unit[Key.LIVED] for unit in units)
    gained = [unit for unit in units if unit[Key.LEVEL] > unit[Key.FIRST_LEVEL]]
    return [
        name, kind, str(len(units)), shown_number(ended[Ending.LOST]), shown_number(ended[Ending.RETIRED]), shown_number(ended[Ending.SETTLED]), shown_number(ended[Ending.ALIVE]),
        str(average([unit[Key.LIVED] for unit in units])), str(average([unit[Key.MOVED] for unit in units])),
        str(percent(part=sum(unit[Key.INSIDE] for unit in units), whole=lived)),
        str(average([unit[Key.LEVEL] for unit in units])), str(max(unit[Key.LEVEL] for unit in units)), str(percent(part=len(gained), whole=len(units))),
    ]


def units_table(data):
    rows = []
    for civilization in civilization_ids(data):
        own = [unit for unit in data[Key.UNITS] if unit[Key.CIVILIZATION] == civilization]
        for kind in kinds_in_order(own):
            rows.append(units_row(name=name_of(data=data, civilization=civilization), kind=kind, units=[unit for unit in own if unit[Key.KIND] == kind]))
    return Table(title=MSG_LOG_UNITS_TITLE, heading=MSG_LOG_UNITS_HEADING, rows=rows)


def points_table(data):
    rows = []
    for civilization in civilization_ids(data):
        averages = [str(average(series_of(data=data, civilization=civilization, series=series))) for series in POINTS_AVERAGED]
        rows.append([name_of(data=data, civilization=civilization), *averages])
    return Table(title=MSG_LOG_POINTS_TITLE, heading=MSG_LOG_POINTS_HEADING, rows=rows)


def buildings_table(data):
    civilizations = civilization_ids(data)
    held = {civilization: [building for city in data[Key.CITIES] if city[Key.OWNER] == civilization for building in city[Key.BUILDINGS]] for civilization in civilizations}
    kinds = list(dict.fromkeys(building for civilization in civilizations for building in held[civilization]))
    rows = [[kind, *[shown_number(held[civilization].count(kind)) for civilization in civilizations]] for kind in kinds]
    heading = [MSG_LOG_BUILDINGS_HEADING, *[name_of(data=data, civilization=civilization) for civilization in civilizations]]
    return Table(title=MSG_LOG_BUILDINGS_TITLE, heading=heading, rows=rows)


def first_and_last(turns):
    """Return the cells for the first and the last of some turns."""
    return [str(min(turns)), str(max(turns))]


def built_table(data):
    """Return the table of how many of each building each civilization built, with the turns of the first and the last."""
    rows = []
    for civilization in civilization_ids(data):
        own = [entry for entry in data[Key.BUILT] if entry[Key.CIVILIZATION] == civilization]
        for building in list(dict.fromkeys(entry[Key.BUILDING] for entry in own)):
            turns = [entry[Key.TURN] for entry in own if entry[Key.BUILDING] == building]
            rows.append([name_of(data=data, civilization=civilization), building, str(len(turns)), *first_and_last(turns)])
    return Table(title=MSG_LOG_BUILT_TITLE, heading=MSG_LOG_BUILT_HEADING, rows=rows)


def made_table(data):
    """Return the table of how many units of each kind each civilization made, with the turns of the first and the last."""
    rows = []
    for civilization in civilization_ids(data):
        own = [unit for unit in data[Key.UNITS] if unit[Key.CIVILIZATION] == civilization]
        for kind in kinds_in_order(own):
            turns = [unit[Key.MADE] for unit in own if unit[Key.KIND] == kind]
            rows.append([name_of(data=data, civilization=civilization), kind, str(len(turns)), *first_and_last(turns)])
    return Table(title=MSG_LOG_MADE_TITLE, heading=MSG_LOG_MADE_HEADING, rows=rows)


def fighting_table(data):
    """Return the table of what each kind of unit of each civilization did: how many were made, the attacks they made, the tiles they moved, the units they killed and how many were lost."""
    rows = []
    for entry in data[Key.CIVILIZATIONS]:
        civilization = entry[Key.ID]
        own = [unit for unit in data[Key.UNITS] if unit[Key.CIVILIZATION] == civilization]
        tallies = entry[Key.TALLIES]
        for kind in kinds_in_order(own):
            units = [unit for unit in own if unit[Key.KIND] == kind]
            rows.append([
                entry[Key.NAME], kind, str(len(units)), shown_number(tallies[Tally.ATTACKS].get(kind, 0)), shown_number(sum(unit[Key.MOVED] for unit in units)),
                shown_number(tallies[Tally.KILLS].get(kind, 0)), shown_number(len([unit for unit in units if unit[Key.ENDING] == Ending.LOST])),
            ])
    return Table(title=MSG_LOG_FIGHTING_TITLE, heading=MSG_LOG_FIGHTING_HEADING, rows=rows)


def shown_turn(turn):
    """Return the cell for a turn, or the mark for none when there was no such turn."""
    return MSG_NONE_MARK if turn == NEVER else str(turn)


def orders_table(data):
    """Return the table of how many orders of each kind each civilization gave, with the first and the last turn an order of the kind was in use."""
    rows = []
    for civilization in civilization_ids(data):
        for record in [record for record in data[Key.ORDERS] if record[Key.CIVILIZATION] == civilization]:
            rows.append([
                name_of(data=data, civilization=civilization), record[Key.KIND], str(len(record[Key.GIVEN])),
                shown_turn(record[Key.FIRST_IN_USE]), shown_turn(record[Key.LAST_IN_USE]),
            ])
    return Table(title=MSG_LOG_ORDERS_TITLE, heading=MSG_LOG_ORDERS_HEADING, rows=rows)


def counted_with_turns(turns):
    """Return the cells for how many of something there were, and the first and the last turn, with the mark for none when there were none."""
    return [shown_number(len(turns)), *(first_and_last(turns) if turns else [MSG_NONE_MARK, MSG_NONE_MARK])]


def forces_table(data):
    """Return the table of the divisions and armies each civilization made, and the units, divisions and armies it retired, each with the first and the last turn."""
    rows = []
    for civilization in civilization_ids(data):
        groups = {record[Key.GROUP]: record for record in data[Key.FORCES] if record[Key.CIVILIZATION] == civilization}
        rows.append([
            name_of(data=data, civilization=civilization),
            *counted_with_turns(groups[Group.DIVISION][Key.MADE_TURNS]), *counted_with_turns(groups[Group.ARMY][Key.MADE_TURNS]),
            *counted_with_turns(groups[Group.UNIT][Key.RETIRED_TURNS]), *counted_with_turns(groups[Group.DIVISION][Key.RETIRED_TURNS]),
            *counted_with_turns(groups[Group.ARMY][Key.RETIRED_TURNS]),
        ])
    return Table(title=MSG_LOG_FORCES_TITLE, heading=MSG_LOG_FORCES_HEADING, rows=rows)


def tables(data):
    """Return every table of the report of a log, as the text report prints them."""
    return [scores_table(data), cities_table(data), units_table(data), made_table(data), fighting_table(data), forces_table(data), points_table(data), buildings_table(data), built_table(data), orders_table(data)]


def told(*, data, event, sentence):
    """Return a sentence about an event of a log, filled in."""
    return sentence.format(
        turn=event[Key.TURN], name=name_of(data=data, civilization=event[Key.CIVILIZATION]), subject=event[Key.SUBJECT],
        other=name_of(data=data, civilization=event[Key.OTHER]), city=data[Key.CITY_WORD],
    )


def high_points(*, data, civilization):
    """Return (turn, sentence) for each high point of a civilization: what the civilization did, what was done to the civilization, and when the civilization was strongest."""
    name = name_of(data=data, civilization=civilization)
    points = []
    for event in data[Key.EVENTS]:
        what = WHATS[event[Key.WHAT]]
        if what in LEFT_OUT_OF_TIMELINES:
            continue
        if event[Key.CIVILIZATION] == civilization:
            points.append((event[Key.TURN], told(data=data, event=event, sentence=SENTENCES[what])))
        elif event[Key.OTHER] == civilization and what == What.TOOK:
            points.append((event[Key.TURN], MSG_LOG_TIMELINE_LOST_CITY.format(turn=event[Key.TURN], name=name, city=data[Key.CITY_WORD], subject=event[Key.SUBJECT], other=name_of(data=data, civilization=event[Key.CIVILIZATION]))))
        elif event[Key.OTHER] == civilization and what == What.DECLARED_WAR:
            points.append((event[Key.TURN], MSG_LOG_TIMELINE_WAR_DECLARED_ON.format(turn=event[Key.TURN], name=name, other=name_of(data=data, civilization=event[Key.CIVILIZATION]))))
    turn, most = strongest_turn(data=data, civilization=civilization)
    points.append((turn, MSG_LOG_TIMELINE_STRONGEST.format(turn=turn, name=name, strength=most)))
    return points


def still_playing(data):
    """Return the ids of the civilizations of a log that had not lost when the game ended."""
    return [entry[Key.ID] for entry in data[Key.CIVILIZATIONS] if not entry[Key.LOST]]


def winner_line(data):
    """Return the sentence that says who won: the only civilization remaining, or, when more than one remains at the game's last turn, the one with the highest score among them."""
    remaining = still_playing(data)
    if not remaining:
        return MSG_LOG_NO_WINNER
    if len(remaining) == ONE_WINNER:
        return MSG_LOG_WON_BY_CONQUEST.format(turn=data[Key.TURNS], name=name_of(data=data, civilization=remaining[0]))
    best = max(remaining, key=lambda civilization: last_of(data=data, civilization=civilization, series=Series.SCORE))
    score = last_of(data=data, civilization=best, series=Series.SCORE)
    return MSG_LOG_WON_ON_SCORE.format(turn=data[Key.TURNS], count=len(remaining), name=name_of(data=data, civilization=best), score=score)


def timeline_of(*, data, civilization):
    """Return the timeline of a civilization: its high points in the order they happened, and how the civilization ended the game."""
    name = name_of(data=data, civilization=civilization)
    points = sorted(high_points(data=data, civilization=civilization), key=lambda point: point[0])
    place = ranked(data).index(civilization) + FIRST_PLACE
    ended = MSG_LOG_TIMELINE_ENDED.format(turn=data[Key.TURNS], name=name, place=place, of=len(data[Key.CIVILIZATIONS]), score=last_of(data=data, civilization=civilization, series=Series.SCORE))
    return Timeline(title=MSG_LOG_TIMELINE_TITLE.format(name=name), lines=[sentence for _, sentence in points] + [ended])


def timelines(data):
    return [timeline_of(data=data, civilization=civilization) for civilization in civilization_ids(data) if civilization != NOTHING]


def title_of(data):
    return MSG_LOG_TITLE.format(theme=data[Key.THEME], seed=data[Key.SEED], civilizations=len(data[Key.CIVILIZATIONS]), width=data[Key.WIDTH], height=data[Key.HEIGHT], turns=data[Key.TURNS])


def report_lines(*, data, markdown=False):
    """Return the whole report of a log as lines: the title, the timeline of each civilization and every table."""
    lines = [title_of(data), winner_line(data)]
    for timeline in timelines(data):
        lines += [BLANK_LINE, timeline.title, *timeline.lines]
    for table in tables(data):
        lines += [BLANK_LINE, *table_lines(title=table.title, heading=table.heading, rows=table.rows, markdown=markdown)]
    return lines
