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


# city_spec.py
MSG_CITIES = 'cities'
MSG_CITY = 'city'

# guides.py
MSG_GUIDE_APPENDIX = '## Appendix: the numbers of {theme}'
MSG_GUIDE_APPENDIX_NOTE = 'The tables below are generated from the code by `tools/theme_guides.py`, and `make guides` refreshes them. Do not edit them by hand.'
MSG_GUIDE_REFRESHED = 'refreshed {path}'
MSG_GUIDE_CURRENT = '{path} is current'
MSG_GUIDE_STALE = '{path} is out of date: run make guides'
MSG_GUIDE_MISSING = '{path} is missing, and the appendix of a guide is only refreshed in a guide that exists'

# kind_reports.py
MSG_BUILDING_PROPERTIES = ('requires', 'cost', 'turns', 'support', 'produces', 'income bonus %', 'research points', 'action points', 'grows sooner', 'worked tile bonus', 'armor bonus', 'level bonus', 'walls', 'beside water')
MSG_BUILDINGS_HEADING = ('building', 'world wonder', *MSG_BUILDING_PROPERTIES)
MSG_BUILDINGS_TITLE = 'The buildings of {theme}:'
MSG_KIND_BUILDING = 'building'
MSG_KIND_TECHNOLOGY = 'technology'
MSG_KIND_WONDER = 'world wonder'
MSG_NO_BUILDINGS = '{theme} has no buildings yet'
MSG_NO_TECHNOLOGIES = '{theme} has no technologies yet'
MSG_NO_WONDERS = '{theme} has no world wonders yet'
MSG_TECH_HEADING = ('technology', 'research points', 'requires', 'allows', 'harvest bonus %', 'unit support bonus %')
MSG_TECH_TITLE = 'The tech tree of {theme}:'
MSG_UNUSED_COLUMNS = 'no {kind} of {theme} sets these, so their columns are left out: {columns}'
MSG_WONDERS_HEADING = ('world wonder', *MSG_BUILDING_PROPERTIES)
MSG_WONDERS_TITLE = 'The world wonders of {theme}:'
MSG_UNITS_HEADING = (
    'unit', 'class', 'requires', 'cost', 'turns', 'support', 'citizens used', 'attack dice', 'extra dice', 'armor class', 'hit points', 'experience worth',
    'action points', 'heals', 'heals in a city', 'strikes back %', 'cannot hit', 'takes cities', 'bypasses walls', 'builds',
)
MSG_UNITS_TITLE = 'The units of {theme}:'
MSG_KIND_UNIT = 'unit'
MSG_NO_UNITS = '{theme} has no units yet'
MSG_EXTRA_DICE = '{dice} against {domain}'
MSG_NO_CLASS = 'undecided'

# tables.py
MSG_AMOUNT = '{amount} {name}'
MSG_AMOUNTS_OF = '{name}: {amounts}'
MSG_COLUMN_GAP = '  '
MSG_LIST_SEPARATOR = ', '
MSG_MARKDOWN_CELL_GAP = ' | '
MSG_MARKDOWN_RIGHT_MARK = ':'
MSG_MARKDOWN_RULE = '-'
MSG_MARKDOWN_ROW = '| {cells} |'
MSG_NONE_MARK = '-'
MSG_YES_MARK = 'yes'

# theme_tools.py
MSG_NAME_ONE_THEME = 'name one theme: {themes}, and {flag} for Markdown'

# dice.py
MSG_DICE = '{count}d{sides}'
MSG_DICE_PLUS = '{count}d{sides}+{plus}'
MSG_FIXED_ROLL = '{plus}'

# balance_report.py
MSG_BALANCE_ATTACKS_CORNER = 'attacker \\ defender'
MSG_BALANCE_ATTACKS_TITLE = 'Attacks needed, on average rolls, by the attacker in each row to kill a whole level 1 unit of the defender in each column ({cannot} means the attacker cannot hit that defender):'
MSG_BALANCE_KINDS_HEADING = ('unit', 'attack dice', 'armor class', 'hit points', 'experience worth')
MSG_BALANCE_KINDS_TITLE = 'The units of {theme} that can attack:'
MSG_BALANCE_LEVELS_HEADING = ('unit', 'level {last} attacking level {first}', 'level {first} attacking level {last}')
MSG_BALANCE_LEVELS_TITLE = 'A level {last} unit against a level {first} unit of the same kind, in attacks needed:'
MSG_BALANCE_NO_CLASS = 'left out, with no class of unit yet: {units}'
MSG_BALANCE_NO_FIGHTERS = 'no unit of {theme} has attack dice yet'
MSG_BALANCE_NOTHING_OUTSIDE = 'none: every defender is gone after {least} to {most} attacks by every attacker that can hit it'
MSG_BALANCE_ONE_ATTACK_NOTE = 'gone after one attack'
MSG_BALANCE_OUTSIDE_HEADING = ('attacker', 'defender', 'attacks', 'note')
MSG_BALANCE_OUTSIDE_TITLE = 'Pairs outside what the user wants, a defender gone after one attack or still standing after {most}:'
MSG_BALANCE_SLOW_NOTE = 'more than {most} attacks'

# cli.py
MSG_CLI_DESCRIPTION = 'A turn based strategy game played in a text UI.'
MSG_HELP_VERSION = 'show the version and stop'
MSG_NOTHING_TO_PLAY = '{title}: there is nothing to play yet'
MSG_TITLE = 'microsponge {version}'
