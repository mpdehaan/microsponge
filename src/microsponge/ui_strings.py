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

"""Every piece of text the program shows people that isn't an error or part of a data format.

Each constant starts with MSG_. Labels, key legends, prompts, titles, notes and the command line's
help all live here and nowhere else, so that wording can be kept consistent. The groups are by the
module that uses them, in the order of the modules' names.
"""


# cli.py
MSG_CLI_DESCRIPTION = 'A turn based strategy game played in a text UI.'
MSG_HELP_VERSION = 'show the version and stop'
MSG_NOTHING_TO_PLAY = '{title}: there is nothing to play yet'
MSG_TITLE = 'microsponge {version}'
