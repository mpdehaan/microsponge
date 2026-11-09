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

"""Writing a game to a file as JSON, and reading one back.

A saved game is mostly integers. It records the version it requires, REQUIRED_VERSION: the
version of microsponge in which the format last changed in a way older files can't follow.
When the format changes that way again, REQUIRED_VERSION moves to the version that changes it,
and every file saved before then is refused. There is no code that upgrades an old file.
"""

import json

from microsponge.engine.game.game import GAME_KEYS, Game
from microsponge.err_messages import ERR_NOT_A_SAVED_GAME, ERR_SAVED_GAME_TOO_NEW, ERR_SAVED_GAME_TOO_OLD
from microsponge.support.version import VERSION, is_version, version_numbers

REQUIRED_VERSION = '0.0.2'
# What a saved game calls its parts, beside the game's own.
REQUIRED_VERSION_KEY = 'required_version'
SAVED_BY_KEY = 'saved_by'
WRITE = 'w'
# No spaces between the numbers, since the file is nearly all numbers.
ITEM_SEPARATOR = ','
KEY_SEPARATOR = ':'


def save_game(*, game, path):
    """Write a game to a file."""
    data = {REQUIRED_VERSION_KEY: REQUIRED_VERSION, SAVED_BY_KEY: VERSION, **game.to_data()}
    with open(path, WRITE) as file:
        json.dump(data, file, separators=(ITEM_SEPARATOR, KEY_SEPARATOR))


def load_game(*, path, themes):
    """Return the game a file holds, played in whichever of themes the file names."""
    with open(path) as file:
        try:
            data = json.load(file)
        except ValueError:
            raise ValueError(ERR_NOT_A_SAVED_GAME.format(path=path)) from None
    check_is_a_saved_game(data=data, path=path)
    check_required_version(data[REQUIRED_VERSION_KEY])
    return Game.from_data(data=data, themes=themes)


def check_is_a_saved_game(*, data, path):
    """Check that what a file holds has every part of a saved game."""
    if not isinstance(data, dict) or not is_version(data.get(REQUIRED_VERSION_KEY)) or any(key not in data for key in GAME_KEYS):
        raise ValueError(ERR_NOT_A_SAVED_GAME.format(path=path))


def check_required_version(required):
    """Refuse a saved game from before the format last changed, or one that needs a later microsponge than this."""
    if version_numbers(required) > version_numbers(VERSION):
        raise ValueError(ERR_SAVED_GAME_TOO_NEW.format(required=required, version=VERSION))
    if version_numbers(required) < version_numbers(REQUIRED_VERSION):
        raise ValueError(ERR_SAVED_GAME_TOO_OLD.format(oldest=REQUIRED_VERSION))
