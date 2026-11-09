# The model objects

Reference notes for Claude on the model objects: the code in `src/microsponge/engine` and
`src/microsponge/themes`, derived from the model, `GAME_RULES.md`. `CLAUDE.md` imports this file,
so it's in force in every session. The rules the code keeps are in `.claude/STYLE.md`; this file
says where things are and how the parts fit, and is kept true with every change to them.

## The engine, by subpackage

- `kinds`: the base classes a theme builds on. `kind.py` has `Kind`, and beside it are
  `dice.py` (the dice an attack is written as), `terrain.py`, `resource.py`, `technology.py`, `unit_kinds.py` (land, sea, air and space units,
  the settler, and which class of unit can hit which), `domain.py` (the classes of unit), `building.py` (buildings and world wonders), `city_spec.py` (what a city means
  in a theme), `bonuses.py` (what a civilization's technologies add up to) and `theme.py` (the lists of a theme's kinds, and its limits). `improvement.py` (what a worker unit builds on a tile), `terrain_bonus.py` (a special tile that gives more). `category.py` names
  the seven categories of kind, and `catalog.py` gives every kind of a theme its id.
- `world`: `world.py` is one map of tiles, and `layer.py` numbers its layers: terrain, unit,
  city (whose city radius a tile belongs to), city center, improvement, strategic resource and
  terrain bonus. `terrain_bonus_control.py` is the static class for terrain bonuses.
- `cities`: `city.py` is one city, with its citizens, its count toward growing, its
  priorities, its buildings and its production queue. `city_control.py` is the static class with the rules for building a city, the
  tiles a city covers, and units going inside and coming out. `harvest.py` is the static class
  for which tile each citizen takes and what a city collects in a turn. `production.py` is the
  static class for what a city builds.
- `units`: `units.py` holds every unit as columns of integers, `unit_column.py` numbers the
  columns, `unit_control.py` is the static class with the rules for units, and
  `work_control.py` is the static class for a unit building an improvement, `combat.py`
  is the static class for attacks, experience and who has lost, and `levels.py` is the static
  class for what a level takes and adds.
- `civilizations`: `civilization.py` is one civilization: its name, what it holds of each
  resource, the technologies it knows, its action points, its bankrupt turns, its wars,
  what it researches and whether it has lost. `requirements.py` says what a civilization or a
  city lacks of what a kind requires, `research.py` is the static class for research, and
  `strategic.py` the static class for strategic resources.
- `game`: `game.py`, the turn, whose turn it is, the civilizations, the worlds, the cities and
  the units of one game, whether the game is over, and the one source of random draws.
- `turns`: `turn_control.py` is the static class that starts a game and does the work of ending
  a turn, and `orders.py` is the static class with every order a civilization gives on its
  turn. A screen and a computer player both go through `Orders`.
- `saving`: `saved_game.py` writes and reads the JSON file, and `keys.py` has the helper for
  numbers used as JSON keys.

## How the parts fit

- A kind is a class that only holds constants and is never made into an object. A theme's kind
  subclasses an engine base and sets what differs. `REQUIRES` lists technologies or resources,
  and `COST` and `GIVES` are dictionaries keyed by the theme's resource classes.
- The `Catalog` of a game numbers each category's kinds from 1 in the theme's order. 0 is
  `NOTHING`: no kind, no unit, no civilization. The world and the units hold ids, never classes.
- A `World` is one list of rows of integers for each layer, and is the only code that touches
  them: `get_value(layer=, x=, y=)` and `set_value(...)`. Columns wrap from east to west, and a
  row off the top or the bottom is refused.
- `Units` is one list for each column, indexed by the unit's id, and is the only code that
  touches them. A removed unit keeps its id with kind `NOTHING`.
- `UnitControl` keeps the world's unit layer and the units' columns in step, and `CityControl`
  does the same for a unit that goes inside a city or comes out. Nothing else writes where a
  unit is.
- A unit inside a city is on no tile: the unit's city column holds the city's id, the unit's x
  and y are the middle of the city, and the city lists the unit. No unit stands on a tile of a
  city center.
- A city's id is its place among the game's cities, from 1. `CityControl.problem_founding()`
  returns the reason a settler cannot build a city where the settler stands, or `None`, so that
  a screen can ask before the player tries.
- What a city is called comes from the theme's city spec (`NAME`, `NAMES`): caveman says
  village. Messages a player can meet take the word as `{city}`.
- Time is the turn, a whole number from 0. There are no years.
- `TurnControl.start()` gives each civilization the theme's `STARTS_WITH` and its action points.
  The civilizations play in the order they joined, and the turn number goes up after the last.
- `TurnControl.end_turn()` does, for the civilization playing and in this order: building units
  go on building, the cities collect, the citizens eat, the units and buildings are paid for,
  the cities go on with what they build, the cities grow, the units heal, research goes on, and
  all action points refill. Then the turn passes to the next civilization that has not
  lost.
- `Harvest` gives each working citizen one tile of the city's radius outside the center. A
  citizen with a priority takes the tile that gives the most of that resource, every other
  citizen the tile that gives the most food, the nearest first, and with no food tile left, the
  tile that gives the most of anything. A city collects what the tiles give (`GIVES` of the
  terrain plus `TILE_BONUS` of the improvement, plus `WORKED_TILE_BONUS` of the city's
  buildings for that terrain), the city spec's `PRODUCES` and each building's, and
  `CITIZEN_CURRENCY` for each working citizen, and then the buildings' `INCOME_BONUS` percent
  is added to the currency.
- A city's production queue holds `(category, id)` pairs, and the city builds the first.
  `Production.part()` splits a cost evenly over `BUILD_TURNS`, with what is left over paid in
  the first turns. `Production.advance()` pays a part each turn and counts the turns paid for
  in the city's progress. A build is blocked, which the city records, on a turn when the part
  cannot be paid, when the civilization is bankrupt, or when what is paid for has nowhere to go.
- A finished unit goes inside the city when the city has room, and otherwise on an empty tile
  next to the city center that the unit can stand on, chosen with the game's random source
  (`CityControl.muster()`). A finished building is added to the city.
- `missing_in_city()` says what a city lacks for building a kind: technologies the civilization
  knows, world wonders in any of the civilization's cities, and any other building in the city
  itself.
- `Game.get_terrain(world=, x=, y=)` is the one place that turns a tile's terrain id into the
  theme's class.
- A terrain with `CROSSED_BY_LAND_UNITS` false takes no land unit, and one with `BUILDABLE`
  false takes no city center, no improvement and no change of terrain: caveman's tarpit is
  both. A tile never runs out of what its terrain `GIVES`.
- An improvement with `BECOMES` is work that changes the tile's terrain and leaves nothing on
  the tile, like caveman's clearing, which turns forest into grassland. `WorkControl` handles
  it like any improvement until the work is done.
- A strategic resource is an id in the world's strategic resource layer, on a tile whose
  terrain lists the resource in `CAN_HAVE`. `Strategic.held()` gives the resources on the
  tiles of a civilization's cities' radii, each once, worked or not. Caveman has flint, and the
  watchtower requires fire and flint. A kind lists a strategic resource in `REQUIRES`
  beside technologies and buildings, and `strategic_for()` only looks for them when a kind
  requires one. `Strategic.terrain_changed()` takes a resource off a tile whose new terrain
  cannot have the resource.
- A building with `BESIDE_WATER` can be built only by a city with a water tile next to the city
  center (`CityControl.is_beside_water()`), like caveman's harbor, which the raft requires.
- `Game.get_random()` is the one source of random draws, and `set_seed()` seeds it. The source
  is not in a saved game yet.
- `Research.points_a_turn()` is the city spec's `RESEARCH_POINTS` for each city plus each
  building's. `Research.advance()` puts a turn's points toward the technology being
  researched, and when they reach its `RESEARCH`, the civilization knows the technology and
  researches nothing until it picks again. There is no pool: the points past what a
  technology takes are lost, and with nothing left to research, each turn's points become
  currency at the theme's `RESEARCH_TO_CURRENCY`. `Research.problem_choosing()` refuses
  switching away from the technology being researched, for now.
- `Orders.end_turn()` is refused while `Research.must_choose()`, through
  `Research.problem_ending_turn()`, which a screen asks before ending a turn: a pick is forced.
  `TurnControl.end_turn()` still ends any turn, and the tests' `end_rounds()` goes through it;
  `end_turn_by_order()` in `test/caveman_game.py` picks the first technology left and then
  ends the turn by order.
- `Production.waiting_cities()`, `Production.blocked_cities()` and `Research.must_choose()` are
  what a screen or a computer player asks before ending a turn. Only a technology left to
  pick stops a turn from ending.
- A kind's `ATTACK` is a `Dice` (count, sides, plus), `NO_DICE` for a kind that cannot attack,
  and `EXTRA_DICE` maps a `Domain` to the extra dice rolled against that class of unit:
  `attack_dice()` in `unit_kinds.py` puts them together. `ARMOR_CLASS` is 10 (`NO_ARMOR`) for
  no armor and 0 for the best; `UnitControl.mitigated()` takes 10 percent off a roll for each
  point below 10, rounding up, with `CHIP_DAMAGE` as the floor. A building's `ARMOR_BONUS` and
  a unit's level make the armor class better. `UnitControl.damage()` and `attacks_to_kill()`
  work on the average roll, for `tools/balance.py` and for screens; `Combat.attack()` rolls
  from `Game.get_random()`. A strike back is `STRIKE_BACK_PERCENT` of the striker's own roll
  through the attacker's armor.
- Units have a `LEVEL` and an `EXPERIENCE` column (`COLUMN_DEFAULTS` fills a missing level
  with `FIRST_LEVEL`). `Levels` says what a level takes (`experience_for()`, 10 times the
  triangular number) and adds: a damage point at levels 10 and 20, an armor point at 5 and
  15, and `Theme.LEVEL_HIT_POINTS_PERCENT` of the kind's hit points a level. `Combat.reward()`
  gives `ATTACK_EXPERIENCE` (2) for an attack, `SURVIVAL_EXPERIENCE` for surviving one, which
  is `DEFENSE_EXPERIENCE_PERCENT` (50) of the attack experience, and the victim's
  `EXPERIENCE_WORTH` plus level for a kill, to the attacker or to the striker that killed the
  attacker alike, and `Combat.gain()` raises the level and
  adds the new hit points on top of the wounds. A building's `LEVEL_BONUS` raises the level a
  unit built in its city starts at (`CityControl.starting_level()`), like caveman's barracks.
- Every `Orders` method checks that the game is being played and that the turn belongs to the
  civilization, then the action points of the unit and of the civilization, then the model
  object's own rule, and charges the points last, so a refused order changes nothing.
- A unit that is building has the improvement's id and the turns left in two unit columns.
  `WorkControl.problem_starting()` returns the reason a unit cannot start, or `None`.
- Building a city and starting an improvement cost `ACTION_COST_BASE`, and going into a city
  and coming out each cost the straight move cost. `Orders.build()`, `build_instead()`,
  `build_nothing()` and `research()` are free.
- Chosen by Claude and not yet confirmed by the user: percentages round down. In production: a unit with nowhere to go
  waits, and a second settler queued while the city had citizens to spare waits when the
  city has shrunk.
- Confirmed by the user: abandoning an improvement is free and keeps nothing, and a tile
  takes one improvement; a city has one of each building; a build of a world wonder that
  another city finishes first is dropped with what was paid; switching a build, or building
  nothing, refunds the theme's `SWITCH_REFUND_PERCENT` of what `Production.paid()` says was
  paid, through `Production.refund()`; a city cannot queue a unit that uses up citizens
  unless the city has more citizens than the unit uses; `Production.wonder_builders()` lists
  the cities building a world wonder, for a screen to warn with, since who has met whom is
  not built.
- A terrain bonus is an id in the world's terrain bonus layer, on a tile whose terrain is in
  the bonus's `ON`, and `Harvest.tile_gives()` adds the bonus's `GIVES`.
  `TerrainBonusControl.terrain_changed()` takes a bonus off a tile whose new terrain is not in
  `ON`. Caveman's bison and elephants are on grassland, and classic's metal deposit marks the
  mountains that have metal.
- City radii never overlap: `CityControl.problem_founding()` refuses a site whose radius
  reaches a tile of another city's radius, so a tile belongs to one city at most.
- `Combat.attack()` resolves one attack on a tile next to the attacker: the unit on the tile,
  or the units inside the city whose center covers the tile, where the best armor class is
  hit with `CityControl.armor_bonus()` making the armor better, leaving out the `WALLS`
  buildings against a kind with `BYPASSES_WALLS`, and the strongest dice able to hit strike
  back. It returns an `AttackOutcome` for a screen or a log, and then `settle_losses()` marks
  as lost each civilization with nothing left (`Civilization.get_cities_founded()` says
  whether cities or units count) and takes its units off the map. `CityControl.enter()` takes
  a city of a civilization at war with no unit inside, through `problem_taking()` and
  `capture()`, which changes the owner and ends the city's production with no refund. Razing,
  and the turns that taking or razing will take, are not built.
- Not built yet: satellites, the colony ship,
  putting strategic resources on the map when a world is made, the technology given after
  6000 turns, and trading technology.

## The reports and the guides

- `support/tables.py` lines up a table's columns, numbers at the right and words at the left,
  as plain text or as Markdown (`table_lines(*, title, heading, rows, markdown)`), and shows
  cells as people read them: `shown_number()` writes 0 as a dash, `shown_flag()` writes yes or a
  dash, `shown_kinds()` and `shown_amounts()` list kinds and resource amounts.
- `support/theme_tools.py` is the command line the theme tools share: one theme's name and
  `--markdown`, through `run_theme_tool(*, arguments, report)`, which calls
  `report(theme, markdown=)`.
- `support/kind_reports.py` reports on a theme's units, buildings, world wonders and tech tree,
  one row for each kind and one column for each property, leaving out and naming the columns
  no kind of the theme sets. A technology's "allows" column is every kind whose `REQUIRES` lists
  the technology. `support/balance_report.py` is the balance report, moved out of
  `tools/balance.py`, which is now a few lines like the other tools.
- `support/guides.py` knows where each theme's guide is (`GUIDE_<THEME>.md`, from the saved
  name) and generates its appendix, the five reports as Markdown between `START_MARKER` and
  `END_MARKER`. `tools/theme_guides.py` refreshes every guide, or with `--check` says which
  are stale and fails, and `test/test_theme_guides.py` fails when any is stale.

## The saved game

- JSON: `required_version`, `saved_by`, `theme`, `turn`, `playing`, `names`, `civilizations`,
  `worlds`, `cities` and `units`. A city holds its buildings, its production queue and its
  progress, and a civilization what it researches, the research points put toward it and
  how many cities it has founded. Layers and columns are keyed by their numbers, and `names` records the name of every
  id in every category.
- Loading matches the saved names to the current theme's catalog and renumbers the layers and
  columns that hold kind ids (`LAYER_CATEGORIES`, `COLUMN_CATEGORIES`), only where an id differs,
  and the resources, technologies, buildings and queued kinds that civilizations and cities
  hold, through each one's `renumber(category=, numbers=)`.
  A saved name the theme no longer has is refused, until the user says what becomes of a removed
  kind.
- A layer or column the file lacks is filled with `NOTHING`, and one this version doesn't have
  is left behind. So adding a feature adds a number, and removing one moves its number to
  `RETIRED_LAYERS` or `RETIRED_UNIT_COLUMNS`, never to be used again.
- `REQUIRED_VERSION` in `saved_game.py` moves to the current version only when the format
  changes in a way old files can't follow. Files that require an older version are then refused.

## The themes

- `src/microsponge/themes/__init__.py` lists them in `THEMES`: caveman, classic, SciFi, fantasy and PlanetWars.
- Each theme is a package with a module for each category it has, a `city.py` for its city spec
  and a `theme.py`.
- Caveman is the tests' theme, and its numbers are Claude's to choose
  (`.claude/THEMES_CAVEMAN.md`). A caveman unit lists `CavemanUnit`, which has the defaults,
  before its class of unit, like `LandUnit`. Classic, SciFi, fantasy and PlanetWars hold only the names and the few
  properties the user has given, with no numbers but the siege units' and the city walls'. Space as a layer, and the astral plane, are
  not built: `SpaceUnit` is only a class of unit.

## The tests

- `test/caveman_game.py` builds the small game of caveman the tests share, and `game_facts()`
  there reads everything a game holds through its getters, with kinds by name, to compare two
  games.
- `test/later_caveman.py` has caveman as later versions might change it, for loading old saved
  games.
- The test world is 48 by 24, so that the two civilizations' first city radii do not meet
  around the edge, since city radii cannot overlap.
- `test/caveman_game.py` also has `started_caveman_game()`, `found_village()`, `end_rounds()`,
  `learn()`, `give_building()` and `held()`, for tests that play turns. The test world has a
  strip of forest inside the first civilization's first city radius and mountains inside the
  second's.
