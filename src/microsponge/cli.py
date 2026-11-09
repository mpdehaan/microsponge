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

"""The microsponge command, which will start the game.

    microsponge
    microsponge --version

There is no game to start yet, so for now the command says so and names its version.
"""

import argparse
import sys

from microsponge.support.version import VERSION
from microsponge.ui_strings import MSG_CLI_DESCRIPTION, MSG_HELP_VERSION, MSG_NOTHING_TO_PLAY, MSG_TITLE

PROGRAM = 'microsponge'
OPTION_VERSION = '--version'
# argparse's own action for an option that prints the version and stops.
VERSION_ACTION = 'version'
SUCCEEDED = 0


def title():
    """Return the program's name with its version, as the command and, later, every screen shows it."""
    return MSG_TITLE.format(version=VERSION)


def main(*, argv=None):
    """Return 0 after saying that there is nothing to play yet."""
    parser = argparse.ArgumentParser(prog=PROGRAM, description=MSG_CLI_DESCRIPTION)
    parser.add_argument(OPTION_VERSION, action=VERSION_ACTION, version=title(), help=MSG_HELP_VERSION)
    parser.parse_args(argv)
    print(MSG_NOTHING_TO_PLAY.format(title=title()))
    return SUCCEEDED


if __name__ == '__main__':
    sys.exit(main())
