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

"""The report of a scripted game: a little story of the major events, tables of what each civilization did, charts over the turns, and how the game followed the curve a game is meant to follow."""

from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.players.traits import TRAITS
from microsponge.support.charts import chart_lines
from microsponge.support.chronicle import FIRST_CIVILIZATION, Measure, What
from microsponge.support.scripted_game import STALL_TURNS
from microsponge.support.tables import BLANK_LINE, table_lines
from microsponge.ui_strings import (
    MSG_CHART_CITIES, MSG_CHART_CITIZENS, MSG_CHART_TECHNOLOGIES, MSG_CHART_UNITS, MSG_CHART_WEALTH, MSG_CURVE_AFTER_OPEN, MSG_CURVE_AFTER_WON, MSG_CURVE_DEFEATS, MSG_CURVE_HEADING,
    MSG_CURVE_KNEW_EVERYTHING, MSG_CURVE_NEVER_KNEW_EVERYTHING, MSG_CURVE_NO_DEFEATS, MSG_LIST_SEPARATOR, MSG_NONE_MARK, MSG_STORY_DECLARED_WAR, MSG_STORY_DECLINE, MSG_STORY_DEFEATED, MSG_STORY_FINISHED_WONDER,
    MSG_STORY_FOUNDED, MSG_STORY_HEADING, MSG_STORY_KNEW_EVERYTHING, MSG_STORY_LEARNT, MSG_STORY_NOBODY, MSG_STORY_STALLED, MSG_STORY_TITLE, MSG_STORY_TOOK, MSG_STORY_UNFINISHED, MSG_STORY_WENT_BANKRUPT, MSG_STORY_WON, MSG_TALLY,
    MSG_TALLY_HEADING, MSG_TALLY_TITLE, MSG_TECHNOLOGIES_LEARNT_HEADING, MSG_TECHNOLOGIES_LEARNT_TITLE, MSG_TRAITS_HEADING, MSG_TRAITS_TITLE,
)

SENTENCES = {
    What.FOUNDED: MSG_STORY_FOUNDED,
    What.TOOK: MSG_STORY_TOOK,
    What.LEARNT: MSG_STORY_LEARNT,
    What.KNEW_EVERYTHING: MSG_STORY_KNEW_EVERYTHING,
    What.DECLARED_WAR: MSG_STORY_DECLARED_WAR,
    What.FINISHED_WONDER: MSG_STORY_FINISHED_WONDER,
    What.DEFEATED: MSG_STORY_DEFEATED,
    What.WENT_BANKRUPT: MSG_STORY_WENT_BANKRUPT,
}
# A civilization that ends a game with less than this percent of the most citizens and units it ever had is said to have started to lose.
DECLINE_PERCENT = 50
WHOLE = 100
ONE_WINNER = 1


def name_of(*, game, civilization):
    """Return the name of a civilization, or the words for none when there is none."""
    return MSG_STORY_NOBODY if civilization < FIRST_CIVILIZATION else game.get_civilization(civilization).get_name()


def names_of(*, game, civilizations):
    return MSG_LIST_SEPARATOR.join(name_of(game=game, civilization=civilization) for civilization in civilizations) or MSG_STORY_NOBODY


def all_names(*, game, chronicle):
    return [name_of(game=game, civilization=civilization) for civilization in chronicle.get_civilizations()]


def sentence_of(*, game, event):
    """Return the sentence of the story that tells an event."""
    return SENTENCES[event.what].format(
        turn=event.turn, name=name_of(game=game, civilization=event.civilization), subject=event.subject,
        other=name_of(game=game, civilization=event.other), city=game.get_theme().CITY.NAME,
    )


def decline_turn(strength):
    """Return the last turn on which a civilization was as strong as it ever was, when it ended with less than DECLINE_PERCENT of that, or None for a civilization that did not decline.

    strength is one number for each turn the civilization played.
    """
    if not strength or max(strength) == 0 or strength[-1] * WHOLE >= max(strength) * DECLINE_PERCENT:
        return None
    return len(strength) - 1 - strength[::-1].index(max(strength))


def declines(*, game, chronicle):
    """Return, for each civilization that started to lose, the turn and the sentence of the story that says so."""
    found = []
    for civilization in chronicle.get_civilizations():
        citizens = chronicle.get_counts(civilization=civilization, measure=Measure.CITIZENS)
        units = chronicle.get_counts(civilization=civilization, measure=Measure.UNITS)
        turn = decline_turn([people + army for people, army in zip(citizens, units)])
        if turn is not None:
            found.append((turn, MSG_STORY_DECLINE.format(turn=turn, name=name_of(game=game, civilization=civilization), citizens=citizens[turn], units=units[turn])))
    return found


def ending(*, game, chronicle):
    """Return the last sentence of the story: who won, or why the game stopped with no winner."""
    playing = game.get_still_playing()
    names = names_of(game=game, civilizations=playing)
    if game.is_over() and len(playing) == ONE_WINNER:
        return MSG_STORY_WON.format(turn=game.get_turn(), name=names)
    if chronicle.is_stalled():
        return MSG_STORY_STALLED.format(turn=game.get_turn(), turns=STALL_TURNS, names=names)
    return MSG_STORY_UNFINISHED.format(turn=game.get_turn(), names=names)


def story_lines(*, game, chronicle):
    """Return the story of a game: every major event in the order it happened, when each civilization started to lose, and how the game ended."""
    told = [(event.turn, sentence_of(game=game, event=event)) for event in chronicle.get_events()] + declines(game=game, chronicle=chronicle)
    told.sort(key=lambda turn_and_sentence: turn_and_sentence[0])
    return [MSG_STORY_HEADING, *[sentence for _, sentence in told], ending(game=game, chronicle=chronicle)]


def technologies_lines(*, game, chronicle):
    """Return the table of the turn each civilization learnt each technology."""
    learnt = {(event.civilization, event.subject): event.turn for event in chronicle.events_of(What.LEARNT)}
    rows = []
    for technology in game.get_theme().TECHNOLOGIES:
        turns = [learnt.get((civilization, shown_name(technology))) for civilization in chronicle.get_civilizations()]
        rows.append([shown_name(technology), *[MSG_NONE_MARK if turn is None else str(turn) for turn in turns]])
    return table_lines(title=MSG_TECHNOLOGIES_LEARNT_TITLE, heading=[MSG_TECHNOLOGIES_LEARNT_HEADING, *all_names(game=game, chronicle=chronicle)], rows=rows)


def tally_lines(*, game, chronicle):
    """Return the table of how many units of each kind each civilization made and lost."""
    rows = []
    for kind in game.get_theme().UNITS:
        cells = [MSG_TALLY.format(made=chronicle.get_made(civilization=civilization, kind=kind), lost=chronicle.get_lost(civilization=civilization, kind=kind)) for civilization in chronicle.get_civilizations()]
        rows.append([shown_name(kind), *cells])
    return table_lines(title=MSG_TALLY_TITLE, heading=[MSG_TALLY_HEADING, *all_names(game=game, chronicle=chronicle)], rows=rows)


def traits_lines(*, game, chronicle):
    """Return the table of the traits each computer-played civilization was dealt."""
    holders = [game.get_civilization(civilization) for civilization in chronicle.get_civilizations()]
    rows = [[trait, *[str(holder.get_traits().get(trait)) if holder.is_computer_played() else MSG_NONE_MARK for holder in holders]] for trait in TRAITS]
    return table_lines(title=MSG_TRAITS_TITLE, heading=[MSG_TRAITS_HEADING, *all_names(game=game, chronicle=chronicle)], rows=rows)


def chart_titles(game):
    """Return the title of the chart of each Measure."""
    return {
        Measure.CITIES: MSG_CHART_CITIES.format(cities=game.get_theme().CITY.NAMES),
        Measure.CITIZENS: MSG_CHART_CITIZENS,
        Measure.WEALTH: MSG_CHART_WEALTH.format(resource=shown_name(game.get_theme().PRIMARY_RESOURCE)),
        Measure.UNITS: MSG_CHART_UNITS,
        Measure.TECHNOLOGIES: MSG_CHART_TECHNOLOGIES,
    }


def charts_lines(*, game, chronicle):
    """Return a chart of each Measure over the turns, with a blank line before each."""
    lines = []
    names = all_names(game=game, chronicle=chronicle)
    for measure, title in chart_titles(game).items():
        series = [chronicle.get_counts(civilization=civilization, measure=measure) for civilization in chronicle.get_civilizations()]
        lines += [BLANK_LINE, *chart_lines(title=title, series=series, names=names)]
    return lines


def curve_lines(*, game, chronicle):
    """Return how the game followed the curve a game is meant to follow: when the tech tree was exhausted, how long the game went on after, and when civilizations were defeated."""
    lines = [MSG_CURVE_HEADING]
    exhausted = chronicle.events_of(What.KNEW_EVERYTHING)
    if exhausted:
        first = exhausted[0]
        after = game.get_turn() - first.turn
        won = game.is_over() and len(game.get_still_playing()) == ONE_WINNER
        lines.append(MSG_CURVE_KNEW_EVERYTHING.format(name=name_of(game=game, civilization=first.civilization), turn=first.turn))
        lines.append((MSG_CURVE_AFTER_WON if won else MSG_CURVE_AFTER_OPEN).format(turns=after))
    else:
        lines.append(MSG_CURVE_NEVER_KNEW_EVERYTHING)
    defeats = [str(event.turn) for event in chronicle.events_of(What.DEFEATED, What.WENT_BANKRUPT)]
    lines.append(MSG_CURVE_DEFEATS.format(turns=MSG_LIST_SEPARATOR.join(defeats)) if defeats else MSG_CURVE_NO_DEFEATS)
    return lines


def report_lines(*, game, chronicle, seed):
    """Return the whole report of a scripted game as lines."""
    world = game.get_worlds()[0]
    title = MSG_STORY_TITLE.format(theme=shown_name(game.get_theme()), seed=seed, civilizations=len(game.get_civilizations()), width=world.get_width(), height=world.get_height())
    return [
        title, BLANK_LINE, *story_lines(game=game, chronicle=chronicle), BLANK_LINE, *curve_lines(game=game, chronicle=chronicle),
        BLANK_LINE, *traits_lines(game=game, chronicle=chronicle), BLANK_LINE, *technologies_lines(game=game, chronicle=chronicle),
        BLANK_LINE, *tally_lines(game=game, chronicle=chronicle), *charts_lines(game=game, chronicle=chronicle),
    ]
