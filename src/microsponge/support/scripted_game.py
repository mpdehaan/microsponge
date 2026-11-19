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

"""A scripted game: the computer players of a theme play each other on a generated world with no person and no screen, while a chronicle is kept.

It shows whether games end by themselves or stall, and what tuning would make them better
(`.claude/TESTING.md`, "The first scripted game"). `game_story.py` writes the report.
"""

from microsponge.engine.kinds.kind import shown_name
from microsponge.engine.players.traits import Traits
from microsponge.engine.turns.turn_control import TurnControl
from microsponge.err_messages import ERR_NO_PLAYER
from microsponge.support.chronicle import Chronicle
from microsponge.support.map_preview import previewed_game

# A scripted game runs this many turns when asked for no number in particular.
TURNS = 100
# A scripted game in which nothing has been built for this many turns is stopped, which never happens to a game a person plays.
STALL_TURNS = 200


def started_game(*, theme, seed, civilizations):
    """Return a started game of a theme on a world made from a seed, every civilization played by the computer with traits dealt from the seed."""
    if theme.PLAYER is None:
        raise ValueError(ERR_NO_PLAYER.format(theme=shown_name(theme)))
    game, _ = previewed_game(theme=theme, seed=seed, civilizations=civilizations)
    for holder in game.get_civilizations():
        holder.set_traits(Traits.dealt(game.get_random()))
    TurnControl.start(game)
    return game


def play(*, game, turns=TURNS, stall_turns=STALL_TURNS, log=None):
    """Have the theme's computer player play every civilization until the game is over, reaches a turn or stalls, and return the chronicle of the game. A log that is passed in watches the game beside the chronicle."""
    chronicle = Chronicle(game)
    player = game.get_theme().PLAYER
    while game.get_turn() < turns and not game.is_over():
        turn = game.get_turn()
        player.play_turn(game=game, civilization=game.get_playing())
        watchers = [chronicle] if log is None else [chronicle, log]
        for watcher in watchers:
            watcher.note(game=game, turn=turn)
        if game.get_turn() != turn:
            for watcher in watchers:
                watcher.count(game)
            if chronicle.turns_without_progress(game.get_turn()) >= stall_turns:
                chronicle.set_stalled(True)
                break
    return chronicle
