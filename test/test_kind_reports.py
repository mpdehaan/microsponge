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

"""The reports on a theme's units, buildings, world wonders and tech tree, and the tools that print them."""

import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path

from later_caveman import later_caveman
from microsponge.engine.kinds.building import Wonder
from microsponge.engine.kinds.category import Category
from microsponge.engine.kinds.domain import Domain
from microsponge.engine.kinds.kind import shown_name
from microsponge.support.kind_reports import allowed_by, building_row, buildings_report, tech_report, technology_row, unit_row, units_report, unused_columns, without_columns, wonder_row, wonders_report
from microsponge.support.tables import shown_amounts, shown_flag, shown_kinds, shown_number
from microsponge.support.theme_tools import FAILED, MARKDOWN_FLAG, SUCCEEDED, parse, run_theme_tool, theme_called
from microsponge.themes.caveman import buildings as caveman_buildings
from microsponge.themes.caveman.theme import Caveman
from microsponge.themes.caveman.technologies import Agriculture, Clubs
from microsponge.themes.caveman.units import SlingshotCaveman, Warrior, Worker
from microsponge.themes.classic.theme import Classic
from microsponge.themes.planetwars.theme import PlanetWars
from microsponge.ui_strings import (
    MSG_BUILDINGS_HEADING, MSG_BUILDINGS_TITLE, MSG_EXTRA_DICE, MSG_KIND_BUILDING, MSG_LIST_SEPARATOR, MSG_MARKDOWN_ROW, MSG_NAME_ONE_THEME, MSG_NO_BUILDINGS,
    MSG_NO_TECHNOLOGIES, MSG_NO_UNITS, MSG_NO_WONDERS, MSG_NONE_MARK, MSG_TECH_HEADING, MSG_UNITS_HEADING, MSG_UNITS_TITLE, MSG_UNUSED_COLUMNS, MSG_WONDERS_HEADING, MSG_WONDERS_TITLE,
)

ROOT = Path(__file__).resolve().parents[1]
TOOLS = {units_report: 'unit_report.py', buildings_report: 'building_report.py', wonders_report: 'wonder_report.py', tech_report: 'tech_report.py'}
NO_SUCH_THEME = 'atlantis'
BARE_CAVEMAN = later_caveman({Category.BUILDINGS: (), Category.TECHNOLOGIES: (), Category.UNITS: ()})
A_HEADING = ('name', 'empty', 'full')
ROWS = [['one', MSG_NONE_MARK, '1'], ['two', MSG_NONE_MARK, MSG_NONE_MARK]]


def names(line):
    return line.split(MSG_LIST_SEPARATOR)


class TestKindReports(unittest.TestCase):

    def test_a_unit_row_has_a_cell_for_every_heading_in_order(self):
        row = unit_row(SlingshotCaveman)
        self.assertEqual(len(row), len(MSG_UNITS_HEADING))
        self.assertEqual(row[:3], [shown_name(SlingshotCaveman), Domain.LAND, shown_kinds((Clubs,))])
        self.assertEqual(row[MSG_UNITS_HEADING.index('attack dice')], SlingshotCaveman.ATTACK.shown())
        self.assertEqual(row[MSG_UNITS_HEADING.index('extra dice')], MSG_EXTRA_DICE.format(dice=1, domain=Domain.AIR))
        self.assertEqual(row[MSG_UNITS_HEADING.index('cannot hit')], MSG_NONE_MARK)
        self.assertEqual(unit_row(Warrior)[MSG_UNITS_HEADING.index('cannot hit')], Domain.AIR)
        self.assertEqual(unit_row(Worker)[MSG_UNITS_HEADING.index('attack dice')], MSG_NONE_MARK)
        self.assertEqual(unit_row(Worker)[MSG_UNITS_HEADING.index('builds')], shown_kinds(Worker.BUILDS))

    def test_a_building_row_and_a_wonder_row_share_the_properties_and_the_building_row_says_whether_it_is_a_wonder(self):
        granary = caveman_buildings.Granary
        painting = caveman_buildings.GreatCavePainting
        self.assertEqual(len(building_row(granary)), len(MSG_BUILDINGS_HEADING))
        self.assertEqual(len(wonder_row(painting)), len(MSG_WONDERS_HEADING))
        self.assertEqual(building_row(granary)[:2], [shown_name(granary), shown_flag(False)])
        self.assertEqual(building_row(painting)[:2], [shown_name(painting), shown_flag(True)])
        self.assertEqual(building_row(painting)[2:], wonder_row(painting)[1:])
        self.assertEqual(building_row(granary)[MSG_BUILDINGS_HEADING.index('cost')], shown_amounts(granary.COST))
        self.assertEqual(building_row(caveman_buildings.Barracks)[MSG_BUILDINGS_HEADING.index('level bonus')], shown_number(caveman_buildings.Barracks.LEVEL_BONUS))
        self.assertEqual(building_row(caveman_buildings.Harbor)[MSG_BUILDINGS_HEADING.index('beside water')], shown_flag(True))

    def test_a_technology_row_says_what_the_technology_allows_which_is_every_kind_that_requires_it(self):
        self.assertEqual(allowed_by(theme=Caveman, technology=Agriculture), [kind for kind in (*Caveman.UNITS, *Caveman.BUILDINGS, *Caveman.IMPROVEMENTS) if Agriculture in kind.REQUIRES])
        self.assertIn(Worker, allowed_by(theme=Caveman, technology=Agriculture))
        row = technology_row(theme=Caveman, technology=Agriculture)
        self.assertEqual(len(row), len(MSG_TECH_HEADING))
        self.assertEqual(row[MSG_TECH_HEADING.index('research points')], str(Agriculture.RESEARCH))
        self.assertEqual(row[MSG_TECH_HEADING.index('allows')], shown_kinds(allowed_by(theme=Caveman, technology=Agriculture)))

    def test_columns_that_no_row_uses_are_left_out_and_named_below_the_table(self):
        self.assertEqual(unused_columns(heading=A_HEADING, rows=ROWS), ['empty'])
        heading, rows = without_columns(heading=A_HEADING, rows=ROWS, names=['empty'])
        self.assertEqual((heading, rows), (['name', 'full'], [['one', '1'], ['two', MSG_NONE_MARK]]))
        lines = buildings_report(Caveman)
        self.assertEqual(lines[0], MSG_BUILDINGS_TITLE.format(theme=shown_name(Caveman)))
        unused = unused_columns(heading=MSG_BUILDINGS_HEADING, rows=[building_row(building) for building in Caveman.BUILDINGS])
        self.assertIn('walls', unused)
        self.assertEqual(lines[-1], MSG_UNUSED_COLUMNS.format(kind=MSG_KIND_BUILDING, theme=shown_name(Caveman), columns=MSG_LIST_SEPARATOR.join(unused)))
        self.assertNotIn('walls', lines[1])

    def test_each_report_has_a_row_for_each_kind_and_says_so_when_a_theme_has_none(self):
        self.assertEqual(len([line for line in units_report(Caveman) if any(line.startswith(shown_name(unit)) for unit in Caveman.UNITS)]), len(Caveman.UNITS))
        self.assertEqual(units_report(Caveman)[0], MSG_UNITS_TITLE.format(theme=shown_name(Caveman)))
        self.assertEqual(wonders_report(Caveman)[0], MSG_WONDERS_TITLE.format(theme=shown_name(Caveman)))
        wonders = [building for building in Caveman.BUILDINGS if issubclass(building, Wonder)]
        self.assertEqual(len([line for line in wonders_report(Caveman) if any(line.startswith(shown_name(wonder)) for wonder in wonders)]), len(wonders))
        self.assertEqual(units_report(BARE_CAVEMAN), [MSG_NO_UNITS.format(theme=shown_name(BARE_CAVEMAN))])
        self.assertEqual(buildings_report(BARE_CAVEMAN), [MSG_NO_BUILDINGS.format(theme=shown_name(BARE_CAVEMAN))])
        self.assertEqual(wonders_report(BARE_CAVEMAN), [MSG_NO_WONDERS.format(theme=shown_name(BARE_CAVEMAN))])
        self.assertEqual(tech_report(BARE_CAVEMAN), [MSG_NO_TECHNOLOGIES.format(theme=shown_name(BARE_CAVEMAN))])
        self.assertEqual(wonders_report(PlanetWars), [MSG_NO_WONDERS.format(theme=shown_name(PlanetWars))])

    def test_a_report_comes_as_markdown_when_asked(self):
        for report in TOOLS:
            with self.subTest(report=report):
                plain = report(Caveman)
                marked = report(Caveman, markdown=True)
                self.assertFalse(any(line.startswith(MSG_MARKDOWN_ROW[0]) for line in plain))
                self.assertEqual(len([line for line in marked if line.startswith(MSG_MARKDOWN_ROW[0])]), len(plain) - 2 + 1)

    def test_the_command_line_names_a_theme_and_may_ask_for_markdown(self):
        self.assertEqual(parse([shown_name(Caveman)]), (Caveman, False))
        self.assertEqual(parse([shown_name(Classic), MARKDOWN_FLAG]), (Classic, True))
        self.assertEqual(parse([MARKDOWN_FLAG, shown_name(Classic)]), (Classic, True))
        self.assertEqual(parse([]), (None, False))
        self.assertEqual(parse([NO_SUCH_THEME]), (None, False))
        self.assertEqual(parse([shown_name(Caveman), shown_name(Classic)]), (None, False))
        self.assertIs(theme_called(shown_name(Caveman)), Caveman)
        self.assertIsNone(theme_called(NO_SUCH_THEME))

    def test_running_a_report_prints_it_and_a_bad_command_line_prints_the_themes_and_fails(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            returned = run_theme_tool(arguments=[shown_name(Caveman), MARKDOWN_FLAG], report=units_report)
        self.assertEqual((returned, output.getvalue().splitlines()), (SUCCEEDED, units_report(Caveman, markdown=True)))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            returned = run_theme_tool(arguments=[NO_SUCH_THEME], report=units_report)
        self.assertEqual(returned, FAILED)
        self.assertTrue(output.getvalue().startswith(MSG_NAME_ONE_THEME.split(':')[0]))

    def test_each_script_prints_its_report_of_the_theme_named(self):
        for report, script in TOOLS.items():
            with self.subTest(script=script):
                run = subprocess.run([sys.executable, str(ROOT / 'tools' / script), shown_name(Caveman)], capture_output=True, text=True, cwd=ROOT, check=False)
                self.assertEqual(run.returncode, SUCCEEDED, run.stderr)
                self.assertEqual(run.stdout.splitlines(), report(Caveman))
