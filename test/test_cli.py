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

"""The microsponge command: what it says while there is nothing to play, its version and the options it refuses."""

import contextlib
import io
import unittest

from microsponge.cli import OPTION_VERSION, SUCCEEDED, main, title
from microsponge.support.version import VERSION
from microsponge.ui_strings import MSG_NOTHING_TO_PLAY

# An option the command doesn't have.
UNKNOWN_OPTION = '--conquer'
# What argparse exits with when it refuses the command line.
REFUSED = 2


def printed_by(*, argv):
    """Run the command and return (what it returned, what it printed)."""
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        returned = main(argv=argv)
    return returned, output.getvalue()


class TestCommandLine(unittest.TestCase):

    def test_the_title_names_the_version(self):
        self.assertIn(VERSION, title())

    def test_with_no_options_it_says_there_is_nothing_to_play(self):
        returned, printed = printed_by(argv=[])
        self.assertEqual(returned, SUCCEEDED)
        self.assertEqual(printed.strip(), MSG_NOTHING_TO_PLAY.format(title=title()))

    def test_the_version_option_shows_the_title_and_stops(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as stopped:
            main(argv=[OPTION_VERSION])
        self.assertEqual(stopped.exception.code, SUCCEEDED)
        self.assertEqual(output.getvalue().strip(), title())

    def test_an_unknown_option_is_refused(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
            main(argv=[UNKNOWN_OPTION])
        self.assertEqual(stopped.exception.code, REFUSED)


if __name__ == '__main__':
    unittest.main()
