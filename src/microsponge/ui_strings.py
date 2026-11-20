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


# charts.py
MSG_CHART_AXIS_CORNER = ' +'
MSG_CHART_AXIS_LINE = '-'
MSG_CHART_BLANK = ' '
MSG_CHART_LEGEND_ITEM = '{mark} {name}'
MSG_CHART_LEGEND_SEPARATOR = '   '
MSG_CHART_ROW = '{label} |{cells}'
MSG_CHART_SHARED = '*'
MSG_CHART_SHARED_LEGEND = '{mark} more than one'
MSG_CHART_TURNS = '{indent}  0{last}'

# game_log_page.py
MSG_PAGE_CHART_BANK_OF = 'Bank of {kind}'
MSG_PAGE_CHART_BUILDINGS = 'Buildings'
MSG_PAGE_CHART_CITIES = 'Cities'
MSG_PAGE_CHART_CITIZENS = 'Citizens'
MSG_PAGE_CHART_COMMAND = 'Command each civilization has'
MSG_PAGE_CHART_COMMAND_TAKEN = 'Command the active orders take'
MSG_PAGE_CHART_DEVELOPMENT_SCORE = 'Development score: buildings, added up every turn'
MSG_PAGE_CHART_FOOD_STORED = 'Food stored in all the cities'
MSG_PAGE_CHART_HIT_POINTS = 'Hit points of military units'
MSG_PAGE_CHART_IMPROVEMENTS_OF_KIND = 'Improvements of the kind {kind} on the tiles of the {city} radii'
MSG_PAGE_CHART_INSIDE = 'Military units inside a city'
MSG_PAGE_CHART_LEVEL = 'Average level of military units'
MSG_PAGE_CHART_LOST_ATTACKING_CITY = 'Units lost attacking a city, added up over the turns'
MSG_PAGE_CHART_LOST_ATTACKING_FIELD = 'Units lost attacking in the field, added up over the turns'
MSG_PAGE_CHART_LOST_DEFENDING_CITY = 'Units lost defending a city, added up over the turns'
MSG_PAGE_CHART_LOST_DEFENDING_FIELD = 'Units lost defending in the field, added up over the turns'
MSG_PAGE_CHART_MILITARY_SCORE = 'Military score: hit points of military units, added up every turn'
MSG_PAGE_CHART_ORDERS_OF_KIND = 'Orders of the kind {kind} given in each {turns} turns'
MSG_PAGE_CHART_POLICY = 'Policy each civilization has'
MSG_PAGE_CHART_POLICY_TAKEN = 'Policy the active orders take'
MSG_PAGE_CHART_POPULATION_SCORE = 'Population score: citizens, added up every turn'
MSG_PAGE_CHART_SCIENCE_SCORE = 'Science score: technologies known, added up every turn'
MSG_PAGE_CHART_SCORE = 'Score: what may decide a winner'
MSG_PAGE_CHART_STRENGTH = 'Strength each turn: the rise and fall of each civilization'
MSG_PAGE_CHART_TECHNOLOGIES = 'Technologies known'
MSG_PAGE_CHART_UNITS = 'Units in all'
MSG_PAGE_CHART_UNITS_OF_KIND = 'Units of the kind {kind}'
MSG_PAGE_CHART_WARS = 'How many other civilizations each civilization is at war with'
MSG_PAGE_NO_CHARTS = 'The charts could not be drawn, because the chart library could not be loaded from the internet. The tabs Timelines and Tables hold the same game.'
MSG_PAGE_NO_IMPROVEMENTS = 'No improvement was built on a tile of any {city} radius in this game.'
MSG_PAGE_TAB_BUILDINGS = 'Buildings'
MSG_PAGE_TAB_CITIES = 'Cities'
MSG_PAGE_TAB_CONTROL_POINTS = 'Control points'
MSG_PAGE_TAB_IMPROVEMENTS = 'Improvements'
MSG_PAGE_TAB_ORDERS = 'Orders'
MSG_PAGE_TAB_SCORE = 'Score'
MSG_PAGE_TAB_TABLES = 'Tables'
MSG_PAGE_TAB_TIMELINES = 'Timelines'
MSG_PAGE_TAB_UNITS = 'Units'
MSG_PAGE_TURN = 'turn {turn}'
MSG_PAGE_TURNS_FROM_TO = 'turns {first} to {last}'

# game_log_report.py
MSG_LOG_BUILDINGS_HEADING = 'building'
MSG_LOG_BUILDINGS_TITLE = 'The buildings each civilization held at the end:'
MSG_LOG_BUILT_HEADING = ['civilization', 'building', 'built', 'first on turn', 'last on turn']
MSG_LOG_BUILT_TITLE = 'The buildings each civilization built, with the turns it finished the first and the last of each:'
MSG_LOG_CITIES_HEADING = ['civilization', 'attacks made on cities', 'attacks on its cities', 'founded', 'took', 'lost', 'held at the end', 'citizens at the end', 'buildings at the end']
MSG_LOG_CITIES_TITLE = 'The cities of each civilization:'
MSG_LOG_FIGHTING_HEADING = ['civilization', 'unit', 'made', 'attacks made', 'attacks on cities', 'tiles moved', 'units killed', 'units lost']
MSG_LOG_FIGHTING_TITLE = 'What the units of each kind of each civilization did, added up over every unit of the kind:'
MSG_LOG_FORCES_HEADING = [
    'civilization', 'divisions made', 'first', 'last', 'armies made', 'first', 'last', 'units retired', 'first', 'last', 'divisions retired', 'first', 'last', 'armies retired', 'first', 'last',
]
MSG_LOG_FORCES_TITLE = 'The divisions and armies each civilization made, and the units, divisions and armies it retired, each with the first and the last turn:'
MSG_LOG_LOSSES_HEADING = ['civilization', 'unit', 'lost attacking a city', 'lost attacking in the field', 'lost defending a city', 'lost defending in the field']
MSG_LOG_LOSSES_TITLE = 'The units each kind of each civilization lost, and where:'
MSG_LOG_MADE_HEADING = ['civilization', 'unit', 'made', 'first on turn', 'last on turn']
MSG_LOG_MADE_TITLE = 'The units each civilization made, with the turns it made the first and the last of each kind:'
MSG_LOG_ORDERS_HEADING = ['civilization', 'order', 'given', 'first turn in use', 'last turn in use']
MSG_LOG_ORDERS_TITLE = 'The orders each civilization gave, by kind, with the first and the last turn an order of the kind was in use:'
MSG_LOG_POINTS_HEADING = ['civilization', 'Policy had', 'Policy taken', 'Command had', 'Command taken', 'units', 'military units inside a city']
MSG_LOG_POINTS_TITLE = 'Control points and units, as the average over the turns each civilization played:'
MSG_LOG_REPORT_USAGE = 'name the log file of a game, written by tools/game_log.py, and add --markdown for Markdown tables, --html to write the page with the charts, or --open to write the page and open it in the browser, like: logs/caveman_seed1.json --open'
MSG_LOG_SCORES_HEADING = ['civilization', 'score', 'military', 'science', 'population', 'development', 'strength at the end', 'most strength', 'on turn', 'defeated']
MSG_LOG_SCORES_TITLE = 'The scores at the end, the highest first. Each part of the score is what the part counts, added up over every turn:'
MSG_LOG_TIMELINE_ENDED = '  Turn {turn}: {name} ended the game in place {place} of {of}, with a score of {score}.'
MSG_LOG_TIMELINE_LOST_CITY = '  Turn {turn}: {name} lost the {city} {subject} to {other}.'
MSG_LOG_TIMELINE_STRONGEST = '  Turn {turn}: {name} was at its strongest, with a strength of {strength}.'
MSG_LOG_TIMELINE_TITLE = 'The timeline of {name}:'
MSG_LOG_TIMELINE_WAR_DECLARED_ON = '  Turn {turn}: {other} declared war on {name}.'
MSG_LOG_NO_WINNER = 'No civilization won.'
MSG_LOG_WON_BY_CONQUEST = 'Turn {turn}: {name} was the only civilization remaining, and won.'
MSG_LOG_WON_ON_SCORE = 'Turn {turn}: the game reached its last turn with {count} civilizations still playing, and {name} won with the highest score among them, {score}.'
MSG_LOG_TITLE = 'A game of {theme} from seed {seed}: {civilizations} civilizations on a world of {width} by {height} tiles, played for {turns} turns.'
MSG_LOG_UNITS_HEADING = ['civilization', 'unit', 'made', 'lost', 'retired', 'built a city', 'alive at the end', 'turns lived', 'tiles moved', 'percent of turns inside a city', 'level at the end', 'highest level', 'percent that gained a level']
MSG_LOG_UNITS_TITLE = 'The units of each civilization. Turns lived, tiles moved and the level are averages over the units of the kind:'
MSG_LOG_WRITTEN = 'wrote {path}'

# game_story.py
MSG_CHART_CITIES = 'The {cities} of each civilization over the turns:'
MSG_CHART_CITIZENS = 'The citizens of each civilization over the turns:'
MSG_CHART_TECHNOLOGIES = 'The technologies each civilization knows over the turns:'
MSG_CHART_UNITS = 'The units of each civilization over the turns:'
MSG_CHART_WEALTH = 'The {resource} in the bank of each civilization over the turns:'
MSG_CURVE_AFTER_OPEN = '  The game went on for {turns} turns after that with no winner.'
MSG_CURVE_AFTER_WON = '  The game was won {turns} turns after that.'
MSG_CURVE_DEFEATS = '  Civilizations were defeated on these turns: {turns}.'
MSG_CURVE_HEADING = 'The curve of the game:'
MSG_CURVE_KNEW_EVERYTHING = '  The first civilization to know every technology was {name}, on turn {turn}.'
MSG_CURVE_NEVER_KNEW_EVERYTHING = '  No civilization came to know every technology.'
MSG_CURVE_NO_DEFEATS = '  No civilization was defeated.'
MSG_GAME_LOG_USAGE = 'name one theme, then a seed, how many civilizations play and how many turns at most if you like, like: caveman 7 3 300. The log is written to logs/. The themes: {themes}'
MSG_GAME_USAGE = 'name one theme, then a seed, how many civilizations play and how many turns at most if you like, like: caveman 7 3 300. The themes: {themes}'
MSG_STORY_DECLARED_WAR = '  Turn {turn}: {name} declared war on {other}.'
MSG_STORY_DECLINE = '  Turn {turn}: {name} started to lose, and was never again as strong as on this turn, with {citizens} citizens and {units} units.'
MSG_STORY_DEFEATED = '  Turn {turn}: {name} was defeated.'
MSG_STORY_FINISHED_WONDER = '  Turn {turn}: {name} finished the world wonder {subject}.'
MSG_STORY_FOUNDED = '  Turn {turn}: {name} founded the {city} {subject}.'
MSG_STORY_HEADING = 'The story:'
MSG_STORY_KNEW_EVERYTHING = '  Turn {turn}: {name} knew every technology.'
MSG_STORY_LEARNT = '  Turn {turn}: {name} learnt {subject}.'
MSG_STORY_NOBODY = 'no civilization'
MSG_STORY_STALLED = '  Turn {turn}: the game was stopped because nothing had been built for {turns} turns, with these still playing: {names}.'
MSG_STORY_TITLE = 'A game of {theme} from seed {seed}: {civilizations} civilizations on a world of {width} by {height} tiles.'
MSG_STORY_TOOK = '  Turn {turn}: {name} took the {city} {subject} from {other}.'
MSG_STORY_UNFINISHED = '  Turn {turn}: the game stopped at its turn limit, with these still playing: {names}.'
MSG_STORY_WENT_BANKRUPT = '  Turn {turn}: {name} had been bankrupt for too long, and was defeated with no enemy needed.'
MSG_STORY_WON = '  Turn {turn}: {name} was the only civilization remaining, and won.'
MSG_TALLY = '{made} / {lost}'
MSG_TALLY_HEADING = 'unit'
MSG_TALLY_TITLE = 'The units each civilization made and lost, as made / lost:'
MSG_TECHNOLOGIES_LEARNT_HEADING = 'technology'
MSG_TECHNOLOGIES_LEARNT_TITLE = 'The turn each civilization learnt each technology:'
MSG_TRAITS_HEADING = 'trait'
MSG_TRAITS_TITLE = 'The traits each civilization was dealt:'

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
MSG_BUILDING_PROPERTIES = ('requires', 'cost', 'turns', 'support', 'produces', 'income bonus %', 'research points', 'control points', 'grows sooner', 'worked tile bonus', 'armor bonus', 'level bonus', 'walls', 'beside water', 'off each unit upkeep')
MSG_BUILDINGS_HEADING = ('building', 'world wonder', *MSG_BUILDING_PROPERTIES)
MSG_BUILDINGS_TITLE = 'The buildings of {theme}:'
MSG_KIND_BUILDING = 'building'
MSG_KIND_TECHNOLOGY = 'technology'
MSG_KIND_WONDER = 'world wonder'
MSG_NO_BUILDINGS = '{theme} has no buildings yet'
MSG_NO_TECHNOLOGIES = '{theme} has no technologies yet'
MSG_NO_WONDERS = '{theme} has no world wonders yet'
MSG_TECH_HEADING = ('technology', 'research points', 'requires', 'allows', 'harvest bonus %', 'unit support bonus %', 'grows sooner')
MSG_TECH_TITLE = 'The tech tree of {theme}:'
MSG_UNUSED_COLUMNS = 'no {kind} of {theme} sets these, so their columns are left out: {columns}'
MSG_WONDERS_HEADING = ('world wonder', *MSG_BUILDING_PROPERTIES)
MSG_WONDERS_TITLE = 'The world wonders of {theme}:'
MSG_UNITS_HEADING = (
    'unit', 'class', 'requires', 'cost', 'turns', 'support', 'citizens used', 'attack dice', 'extra dice', 'armor class', 'hit points', 'experience worth',
    'action points', 'heals', 'heals in a city', 'strikes back %', 'cannot hit', 'takes cities', 'bypasses walls', 'builds', 'obsoleted by',
    'weight', 'ranged attack', 'range', 'ranged extra dice', 'attacks cities', 'armor better against',
)
MSG_UNITS_TITLE = 'The units of {theme}:'
MSG_KIND_UNIT = 'unit'
MSG_NO_UNITS = '{theme} has no units yet'
MSG_EXTRA_DICE = '{dice} against {domain}'
MSG_NO_CLASS = 'undecided'

# map_preview.py
MSG_MAP_CIVILIZATION = 'civilization {number}'
MSG_MAP_LEGEND_ITEM = '  {mark}  {name}'
MSG_MAP_LEGEND_TITLE = 'Legend:'
MSG_MAP_STARTS = '  1-9  where each civilization starts, by its number in turn order'
MSG_MAP_TITLE = 'A world of {theme} from seed {seed}, {width} by {height} tiles, columns wrapping from east to west:'
MSG_MAP_USAGE = 'name one theme, then a seed and how many civilizations start if you like, like: caveman 7 3. The themes: {themes}'

# players/computer_player.py
MSG_CITY_NUMBERED = '{civilization} {number}'

# players/traits.py
MSG_TRAIT_AGGRESSIVE_HYPERFOCUS = 'aggressive hyperfocus'
MSG_TRAIT_BOLDNESS = 'boldness'
MSG_TRAIT_CONQUEST = 'conquest'
MSG_TRAIT_ECONOMICS = 'economics'
MSG_TRAIT_EXPANSION = 'expansion'
MSG_TRAIT_GRUDGE = 'grudge'
MSG_TRAIT_PEACE = 'peace'
MSG_TRAIT_SCIENCE = 'science'

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
