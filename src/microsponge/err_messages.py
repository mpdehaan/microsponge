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

"""Every error message the program raises or reports, as templates filled in with .format().

Each constant starts with ERR_, and a message lives here and nowhere else, so that wording can be
kept consistent and a string in test code is never mistaken for a data key. The groups are by
the module that raises them, in the order of the modules' names.
"""


# catalog.py
ERR_KIND_GONE = 'the saved game holds {name}, which is no longer one of the {category} of the theme {theme}'
ERR_KIND_TWICE = 'the theme {theme} lists {name} more than once in its {category}'
ERR_NO_SUCH_KIND_ID = 'the theme {theme} has no {category} with the id {kind_id!r}'
ERR_NOT_IN_THEME = '{kind!r} is not one of the {category} of the theme {theme}'
ERR_SETTLER_REQUIRES = 'the settler {name} of the theme {theme} must require nothing'
ERR_UNKNOWN_ID = 'the saved game holds an id that is not one of {known}'

# city.py
ERR_BUILDING_ALREADY_HELD = '{name} already has the building {building}'
ERR_CITIZENS = 'the citizens of a city must be a whole number that is not negative, got {value!r}'
ERR_CITY_NAME = 'the name of a city must be text that is not blank, got {value!r}'
ERR_NOTHING_QUEUED = '{name} is building nothing'
ERR_GROWTH = 'the turns a city has counted toward growing must be a whole number that is not negative, got {value!r}'
ERR_PROGRESS = 'the turns of a build that are paid for must be a whole number that is not negative, got {value!r}'
ERR_PRIORITY = 'the citizens of a priority must be a whole number that is not negative, got {value!r}'
ERR_UNIT_ALREADY_HELD = 'the unit {unit} is already inside {name}'
ERR_UNIT_NOT_HELD = 'the unit {unit} is not inside {name}'

# city_control.py
ERR_CANNOT_TAKE_CITIES = 'a {unit} cannot take a {city}'
ERR_CITY_DEFENDED = '{name} has units inside: attack them first'
ERR_CITY_COVERS_A_UNIT = 'a {city} cannot be built here: the {city} center would cover the unit at {x}, {y}'
ERR_CITY_COVERS_TERRAIN = 'a {city} cannot be built here: the {city} center would cover the {terrain} at {x}, {y}'
ERR_CITY_FULL = 'the {city} {name} already holds {most} units'
ERR_CITY_NEEDS_LAND = 'a {city} cannot be built here: at least {least} tiles of the {city} center must be land, and {land} are'
ERR_CITY_OFF_THE_MAP = 'a {city} cannot be built here: the {city} center would reach past the top or the bottom of the map'
ERR_CITY_TOO_CLOSE = 'a {city} cannot be built here: the {city} radius would overlap the {city} radius of {name}'
ERR_NOT_A_SETTLER = 'a {unit} cannot build a {city}'
ERR_NOT_NEXT_TO_CENTER = 'the tile at {x!r}, {y!r} is not next to the {city} center of {name}'
ERR_NOT_NEXT_TO_CITY = 'the unit {unit} is not on a tile next to the {city} center of {name}'
ERR_UNIT_IN_A_CITY = 'the unit {unit} is already inside a {city}'
ERR_UNIT_NOT_IN_A_CITY = 'the unit {unit} is not inside a {city}'

# civilization.py
ERR_AMOUNT = 'an amount must be a whole number that is not negative, got {value!r}'
ERR_CIVILIZATION_NAME = 'the name of a civilization must be text that is not blank, got {value!r}'

# combat.py
ERR_ATTACK_OWN = 'the unit {unit} cannot attack its own civilization'
ERR_CANNOT_HIT = 'a {unit} cannot hit a {target}'
ERR_CITY_UNDEFENDED = 'no unit is inside {name}: move a unit in to take the {city}'
ERR_NOTHING_TO_ATTACK = 'there is nothing to attack at {x}, {y}'

# game.py
ERR_NO_SUCH_CITY = 'there is no city with the id {city!r}'
ERR_NO_SUCH_CIVILIZATION = 'there is no civilization with the id {civilization!r}'
ERR_NO_SUCH_THEME = 'there is no theme called {name}'
ERR_NO_SUCH_WORLD = 'there is no world with the id {world!r}'
ERR_TOO_MANY_CIVILIZATIONS = 'a game has at most {most} civilizations'
ERR_TOO_MANY_WORLDS = 'a game of the theme {theme} has at most {most} worlds'
ERR_TURN = 'a turn must be a whole number that is not negative, got {value!r}'

# orders.py
ERR_NO_ACTION_POINTS = 'the unit {unit} has {left} action points left, and this costs {cost}'
ERR_NO_CIVILIZATION_ACTION_POINTS = '{name} has {left} action points left, and this costs {cost}'
ERR_NOT_AT_WAR = 'that tile belongs to {name}: declare war on {name} first'
ERR_NOT_NEXT_TO_UNIT = 'the tile at {x!r}, {y!r} is not next to the unit {unit}'
ERR_NOT_YOUR_TURN = 'it is not the turn of {name}'
ERR_PRIORITY_FOOD = 'every citizen falls back to {resource}, so a priority is for another resource'
ERR_WAR_ON_YOURSELF = 'a civilization cannot declare war on itself'

# production.py
ERR_ALREADY_BUILT = '{name} already has a {building}'
ERR_ALREADY_QUEUED = '{name} is already going to build a {building}'
ERR_BUILD_NEEDS_WATER = 'a {building} requires a water tile next to the {city} center'
ERR_BUILD_REQUIRES = 'a {kind} requires {required}'
ERR_NO_CITIZEN_TO_SPARE = 'a {unit} would leave {name} with no citizens: {name} has {citizens} and a {unit} uses up {uses}'
ERR_WONDER_BUILT = 'the {wonder} has already been built'

# research.py
ERR_ALREADY_KNOWN = '{name} already knows {technology}'
ERR_ALREADY_RESEARCHING = '{name} is already researching {technology}, and cannot switch to {wanted}'
ERR_MUST_PICK_RESEARCH = '{name} must pick a technology to research before ending the turn'
ERR_RESEARCH_REQUIRES = '{technology} requires {required}'

# saved_game.py
ERR_NOT_A_SAVED_GAME = '{path} is not a saved game'
ERR_SAVED_GAME_TOO_NEW = 'this saved game requires microsponge {required} or later, and this is microsponge {version}'
ERR_SAVED_GAME_TOO_OLD = 'this saved game is from before microsponge {oldest}, and can no longer be loaded'

# strategic.py
ERR_NOT_STRATEGIC = '{resource} is not a strategic resource'
ERR_RESOURCE_NOT_ON = '{resource} cannot be on {terrain}'

# terrain_bonus_control.py
ERR_BONUS_NOT_ON = '{bonus} cannot be on {terrain}'

# turn_control.py
ERR_GAME_NOT_STARTED = 'the game has not started'
ERR_GAME_OVER = 'the game is over'
ERR_GAME_STARTED = 'the game has already started'
ERR_NO_CIVILIZATIONS = 'a game needs at least one civilization to start'

# unit_control.py
ERR_CANNOT_BE_ON = 'a {unit} cannot be on {terrain}'
ERR_TILE_HAS_A_UNIT = 'the tile at {x}, {y} already holds a unit'
ERR_TILE_IN_A_CITY_CENTER = 'the tile at {x}, {y} is inside a {city} center, where no unit stands'

# unit_kinds.py
ERR_NO_DOMAIN = 'the kind of unit {name} is not a land, sea, air or space unit'

# units.py
ERR_COLUMNS_DIFFER = 'the columns of the units in the saved game are not all the same length'
ERR_NO_SUCH_COLUMN = 'the units have no column {column!r}'
ERR_NO_SUCH_UNIT = 'there is no unit with the id {unit!r}'

# version.py
ERR_BAD_VERSION_TEXT = 'version must be three integers separated by dots, such as 1.0.2, got {value!r}'

# work_control.py
ERR_CANNOT_BUILD_IMPROVEMENT = 'a {unit} cannot build a {improvement}'
ERR_IMPROVEMENT_NOT_ON = 'a {improvement} cannot be built on {terrain}'
ERR_IMPROVEMENT_REQUIRES = 'a {improvement} requires {required}'
ERR_TILE_IMPROVED = 'the tile at {x}, {y} already has a {improvement}'
ERR_UNIT_NOT_WORKING = 'the unit {unit} is not building anything'
ERR_UNIT_WORKING = 'the unit {unit} is building a {improvement}, and cannot move until the {improvement} is done or abandoned'

# world.py
ERR_LAYER_SHAPE = 'layer {layer} of the saved world is not {height} rows of {width} tiles'
ERR_NO_SUCH_LAYER = 'a world has no layer {layer!r}'
ERR_ROW_OFF_THE_MAP = 'a world does not wrap from north to south: a row is from 0 to {last}, got {value!r}'
ERR_WORLD_SIZE = 'the {name} of a world must be a whole number of at least 1, got {value!r}'
