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

"""Every Python file and shell script starts with the GPLv3 header, below a script's #! line.

The header every file should carry is read from the top of this file, so that the text is written
out in no test, and a new file gets its header by copying any existing one.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The folders that hold Python: the program, its tests and the tools for working on it.
PYTHON_FOLDERS = [ROOT / 'src', ROOT / 'test', ROOT / 'tools']
ALL_PYTHON = '**/*.py'
# Shell scripts live at the top of the project and in tools/.
SHELL_FOLDERS = [ROOT, ROOT / 'tools']
SHELL_SCRIPTS = '*.sh'
SETUP = ROOT / 'setup.py'
# How many lines the header has, from its first line to the line that names the license's address.
HEADER_LENGTH = 15
# A script's first line, which names what runs it, comes before the header.
INTERPRETER_MARK = '#!'
FIRST_LINE = '# microsponge: a strategy game'
ENCODING = 'utf-8'


def header_of(path):
    """Return the lines where a file's header should be: its first lines, after a script's #! line."""
    lines = path.read_text(encoding=ENCODING).splitlines()
    if lines and lines[0].startswith(INTERPRETER_MARK):
        lines = lines[1:]
    return lines[:HEADER_LENGTH]


def python_files():
    return [path for folder in PYTHON_FOLDERS for path in sorted(folder.glob(ALL_PYTHON))]


def shell_scripts():
    return [path for folder in SHELL_FOLDERS for path in sorted(folder.glob(SHELL_SCRIPTS))]


def files_with_headers():
    """Return every file the rule covers: the Python files, the shell scripts and setup.py."""
    return python_files() + shell_scripts() + [SETUP]


class TestLicenseHeaders(unittest.TestCase):

    def test_this_file_starts_with_the_header(self):
        header = header_of(Path(__file__))
        self.assertEqual(header[0], FIRST_LINE)
        self.assertEqual(len(header), HEADER_LENGTH)

    def test_every_python_file_and_shell_script_starts_with_the_header(self):
        header = header_of(Path(__file__))
        for path in files_with_headers():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(header_of(path), header)

    def test_the_rule_finds_files_to_check(self):
        # If the folders moved, the test above would pass by checking nothing.
        self.assertIn(Path(__file__).resolve(), files_with_headers())
        self.assertTrue(shell_scripts())


if __name__ == '__main__':
    unittest.main()
