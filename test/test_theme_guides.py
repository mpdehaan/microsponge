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

"""Every theme has a guide, and the appendix of tables in each guide is what the code generates now."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from microsponge.engine.kinds.kind import saved_name, shown_name
from microsponge.support.guides import END_MARKER, START_MARKER, appendix_lines, guide_path, is_current, refresh, with_appendix
from microsponge.support.theme_tools import FAILED, SUCCEEDED
from microsponge.themes import THEMES
from microsponge.themes.caveman.theme import Caveman
from microsponge.ui_strings import MSG_GUIDE_APPENDIX, MSG_GUIDE_CURRENT, MSG_GUIDE_MISSING, MSG_GUIDE_STALE

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'theme_guides.py'
CHECK_FLAG = '--check'
SOME_WORDS = '# A guide\n\nWords written by hand.\n'
OLD_APPENDIX = START_MARKER + '\nold tables\n' + END_MARKER
WORDS_AFTER = '\n\nMore words after the appendix.\n'
COMMON_GUIDE = ROOT / 'GUIDE.md'


class TestThemeGuides(unittest.TestCase):

    def test_every_theme_has_a_guide_named_after_it_and_the_common_guide_links_to_each(self):
        common = COMMON_GUIDE.read_text()
        for theme in THEMES:
            with self.subTest(theme=theme):
                path = guide_path(root=ROOT, theme=theme)
                self.assertEqual(path.name, 'GUIDE_' + saved_name(theme).upper() + '.md')
                self.assertTrue(path.exists(), MSG_GUIDE_MISSING.format(path=path.name))
                self.assertIn(path.name, common)

    def test_the_appendix_of_every_guide_is_current(self):
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertTrue(is_current(path=guide_path(root=ROOT, theme=theme), theme=theme), MSG_GUIDE_STALE.format(path=guide_path(root=ROOT, theme=theme).name))

    def test_the_appendix_holds_the_markers_the_heading_and_a_table_of_the_units(self):
        lines = appendix_lines(Caveman)
        self.assertEqual((lines[0], lines[-1]), (START_MARKER, END_MARKER))
        self.assertEqual(lines[1], MSG_GUIDE_APPENDIX.format(theme=shown_name(Caveman)))
        self.assertTrue(any(shown_name(unit) in line for unit in Caveman.UNITS for line in lines))

    def test_the_appendix_replaces_an_old_one_between_the_markers_and_is_added_to_a_guide_without_one(self):
        refreshed = with_appendix(text=SOME_WORDS + OLD_APPENDIX + WORDS_AFTER, theme=Caveman)
        self.assertTrue(refreshed.startswith(SOME_WORDS))
        self.assertTrue(refreshed.endswith(WORDS_AFTER))
        self.assertNotIn('old tables', refreshed)
        self.assertEqual(refreshed.count(START_MARKER), 1)
        added = with_appendix(text=SOME_WORDS, theme=Caveman)
        self.assertTrue(added.startswith(SOME_WORDS))
        self.assertTrue(added.rstrip().endswith(END_MARKER))
        self.assertEqual(with_appendix(text=added, theme=Caveman), added)

    def test_refreshing_a_guide_rewrites_a_stale_appendix_once_and_then_finds_it_current(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / guide_path(root=folder, theme=Caveman).name
            path.write_text(SOME_WORDS + OLD_APPENDIX)
            self.assertFalse(is_current(path=path, theme=Caveman))
            self.assertTrue(refresh(path=path, theme=Caveman))
            self.assertTrue(is_current(path=path, theme=Caveman))
            self.assertFalse(refresh(path=path, theme=Caveman))

    def test_the_tool_checks_every_guide_and_succeeds_when_all_are_current(self):
        run = subprocess.run([sys.executable, str(TOOL), CHECK_FLAG], capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
        self.assertEqual(run.stdout.splitlines(), [MSG_GUIDE_CURRENT.format(path=guide_path(root=ROOT, theme=theme).name) for theme in THEMES])
        self.assertNotEqual(FAILED, SUCCEEDED)
