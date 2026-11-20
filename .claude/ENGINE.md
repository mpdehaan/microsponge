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
  terrain bonus. `memory.py` is a civilization's memory of one world, a `World` with every
  layer but the units. `terrain_bonus_control.py` is the static class for terrain bonuses.
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
  resource, the technologies it knows, its Policy (`get_policy_points()`), its bankrupt turns, its wars,
  what it researches, whether it has lost and its memory of each world. `requirements.py` says
  what a civilization or a city lacks of what a kind requires, `research.py` is the static
  class for research, `strategic.py` the static class for strategic resources, `sight.py` the
  static class for the fog of war, and `view.py` the view of the map a player reads.
- `orders`: standing orders. `order.py` has the kinds of order, definitions a theme lists in
  `ORDERS` and may subclass (`PolicyOrder`, `CommandOrder`, `BuildTargetOrder`, `BuildOrder`,
  `RaiseOrder`, `ImproveOrder`, `CivilOrder`, `SettlerOrder`, `ExpandOrder` (a settler and a
  `PointTarget`), `WorkOrder`, `ResourcesPolicyOrder`, `RetireOrder`, `ResearchOrder`, `GarrisonOrder`,
  `MarchOrder`). `thing.py` names what gives and receives orders, `what.py` is what each kind
  of order says and the targets an order mentions, `given_order.py` is `GivenOrder`, one order
  in a game with its giver, receiver, what and reason for being inactive, `order_table.py` is a
  civilization's `OrderTable`, `forces.py` its armies and divisions, `order_control.py` the
  static class for giving an order, what orders cost, the limits on armies and divisions and
  whether a turn may end, and `referee.py` the referee AI.
- `players`: `helper_ai.py` is `HelperAI`, the single actions for a unit or a city, a pass
  through to `Orders`. `hand.py` is `Hand`, the helper AI that carries out standing orders
  through those actions. `knowledge.py` is `Knowledge`, what a civilization knows through its
  view. `traits.py` is the eight traits of a computer-played civilization, how they are dealt
  and the named tendencies, `appraisal.py` is `Appraisal`, which reads a theme's kinds by
  their properties and ranks them by worth, and `computer_player.py` is `ComputerPlayer`, the
  main AI, which only gives standing orders and knows no theme. Caveman's `PLAYER` is
  `ComputerPlayer` itself; a theme may subclass it only to change its weights.
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
- `TurnControl.start()` gives each civilization the theme's `STARTS_WITH` and its Policy
  (`TurnControl.policy_points()`: the theme's `POLICY_POINTS`, the city spec's for each
  city and each building's, like caveman's chieftain's hut).
  The civilizations play in the order they joined, and the turn number goes up after the last.
- `TurnControl.pay_support(before=)` lifts a civilization with a city to at least the theme's
  `LEAST_INCOME` more currency than it held before collecting, or does nothing when the theme
  sets None, so a civilization with a city is never bankrupt.
- A technology's `GROWS_SOONER`, a terrain bonus's `PROVIDES` (strategic resources within the
  borders of a civilization that knows a technology, through `Strategic.provided_at()`), and a
  building's `UNIT_SUPPORT_DISCOUNT` (off each unit's upkeep) are effects caveman uses for
  sewing, elephants and the arrangement of rocks.
- Food. A city keeps its own food store (`City.get_food()`), and the civilization never holds
  food: `TurnControl.collect()` puts a city's food in its store, `feed()` takes what its
  citizens eat and takes a citizen away when the store cannot feed them, and `grow()` adds a
  citizen and empties the store when the store reaches `store_size()`, the city spec's
  `STORE_FOOD` times the citizens, less the `GROWS_SOONER` of the city's buildings and the
  civilization's technologies for each citizen.
- Obsolete units. A kind's `OBSOLETED_BY` names the kind that makes it obsolete;
  `units/upgrades.py` is `Upgrades`: `newer_of()` (None when the newer kind requires a
  strategic resource), `is_obsolete_in()`, which `Production.problem_building()` asks,
  `price()` (the theme's `UPGRADE_PERCENT`), `is_within_borders()`, `problem_upgrading()` and
  `upgrade()`, which keeps the level, the experience and the share of hit points.
  `Orders.upgrade()`, `HelperAI.upgrade()`, the free `UpgradeOrder`, `Hand.upgrade()` and the
  main AI's `plan_upgrades()` carry it out. `Tally.CITY_ATTACKS` and
  `Tally.ATTACKS_ON_ITS_CITIES` count attacks on cities for both sides.
- Ranged attacks and bonuses versus. `kinds/weight.py` has `Weight` (light, medium, heavy)
  and `Versus.IN_CITY`. A kind's `EXTRA_DICE` and `RANGED_EXTRA_DICE` and its
  `ARMOR_BONUS_AGAINST` are keyed by a class of unit, a weight class or `Versus.IN_CITY`
  (`attack_dice()`, `armor_against()`, `versus_keys()`); `RANGED_ATTACK`, `RANGE` and
  `RANGED_HITS` make the ranged attack, and `ATTACKS_CITIES` false keeps a kind from
  attacking the units inside a city. `Combat.attack()` (melee) and `Combat.ranged_attack()`
  share `Combat.resolve()`; `Orders.ranged_attack()` ends the unit's turn. The Hand's
  `shoot()` has a marching ranged unit fire at its target city or an enemy in range, and a
  division asks for a siege unit (`Appraisal.siege()`) while at war. `Tally.LOSSES` counts
  each loss four ways.
- `TurnControl.end_turn()` does, for the civilization playing and in this order: building units
  go on building, the cities collect, the citizens eat, the units and buildings are paid for,
  the cities go on with what they build, the cities grow, the units heal, research goes on, and
  all action points and the Policy refill. Then the turn passes to the next civilization that has not
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
  civilization, then the action points of the unit and the Policy of the civilization, then the model
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
- The fog of war. A kind of unit has `VISION`, 5 by default: the unit sees the square of
  tiles that many each way, and a city sees its city radius. `Sight.start()`, from
  `TurnControl.start()`, gives every civilization a `Memory` of every world, blank unless the
  theme's `LAND_STARTS_EXPLORED`, and `Sight.refresh()` records what a civilization sees
  when its turn starts (`TurnControl.pass_on()`). The orders that move a unit or found or
  take a city call `Sight.look_around_unit()` or `Sight.look_around_city()`, so the memory
  holds each tile as last seen, in every layer but the units, and who owned each city when
  last seen. `Sight.view()` makes a `View`, which a screen or a computer player reads the map
  through, never the world: `can_see()` is vision now, `has_seen()` says whether a tile is
  drawn at all, `remembered()` gives a layer's value as it is in vision and as last seen
  elsewhere, `owner_of()` a city's owner the same way, and `units_seen()` and `unit_on()`
  the other civilizations' units in vision. A technology with `ENDS_FOG_OF_WAR` makes
  `units_seen()` every unit on a tile, and reveals no land. Units inside a city are on no
  tile and are never seen. Classic has `SpySatellites` and fantasy `RemoteViewing`, with no
  numbers; caveman has none, and the tests add one to a later caveman.
- Control points. `kinds/control_points.py` has `ControlPoints` with its two subclasses,
  `Policy` and `Command`. A theme, its city spec and its buildings give them in
  `CONTROL_POINTS`, a dictionary, and a city that builds nothing adds the city spec's
  `IDLE_CONTROL_POINTS`. `TurnControl.control_points(game=, civilization=, points=)` adds them
  up. A civilization still stores a pool of Policy, which a single action given directly
  takes from; an action the Hand takes for a standing order is `led=True` and takes only the
  unit's action points.
- Standing orders. `OrderControl.give()` adds a `GivenOrder` to the civilization's table,
  refused when the theme has no such kind or the receiver is the wrong type of thing.
  `OrderControl.cost()` is the kind's `BASE_COST`, its `UNIT_COST` for each unit led (the
  units of the division, or the count a garrison order keeps) and `LONE_UNIT_COST` for an
  order to one unit; an inactive order and a realized order cost nothing.
  `OrderControl.left()` is what a civilization has beyond what its active orders take, and
  `Orders.end_turn()` is refused while that is below 0 for Policy or Command. A
  `RetireOrder` is free, to a unit, a division or an army, and `Hand.retire()` takes the
  living units out of the game; the main AI gives one a turn while `is_starved()`, for a
  fighter beyond the garrisons. An order is
  active, or inactive with a `Reason`: completed, disabled, or invalid for good, which
  `Referee.review()` sets when the giver, the receiver or the city to garrison is no longer
  the civilization's. `OrderControl.add_army()` and `add_division()` keep the theme's
  `CITIES_PER_ARMY` and `CITIES_PER_DIVISION`, rounding up, always at least one. The order
  table and the forces are not in a saved game yet.
- The Hand. `Hand.carry_out(game=, civilization=)` runs on the civilization's turn: the
  referee reviews, `muster()` drops finished realized orders, takes dead units out of
  divisions, puts each new fighter in the division of the raise order that wants its kind;
  `direct_settlers()` moves each settler with all its action points, to its expand order's
  place or to a site of its own; `research()` picks from the research order, or at random with none;
  `direct_cities()` has each waiting or blocked city start what the order that has waited
  longest wants (`GivenOrder.get_served()`); `direct_settlers()` settles; and
  `direct_divisions()` fills garrisons and then marches, never moving a unit a garrison
  order keeps. Units walk by `first_step()`, a breadth first search over what the
  civilization remembers, at most `ROUTE_TILES` tiles, so a unit goes around a lake. A
  march order's `bold` and `ignore_units` decide the fights on the way. An `ImproveOrder` has a
  city build an engineer while the civilization has fewer than cities ordered to improve, and
  `muster()` gives each new engineer a realized `WorkOrder`; `direct_engineers()` walks it to
  the nearest tile of the city it can improve and builds the lasting improvement that adds
  most. A `ResourcesPolicyOrder` says what a city's citizens look for first (`Priority`), and
  `direct_priorities()` sets each city's priorities to its active orders. The main AI gives
  one when the first building a city's build order wants costs a resource the bank lacks,
  and asks its division for units by what they can do (`division_wanted()`): counters to
  enemy kinds its best fighter cannot hit, harassers no enemy kind seen can hit, invaders
  that move on water and take cities when an enemy city is beside water, units that fight on
  water when a city of its own is, and fighters for the rest. A raise order's city builds
  from the first unmet target it can build. Nothing happens for a city or a unit with no
  order.
- The computer players. A civilization with `Traits` is computer-played (`is_computer_played()`),
  and one without is a person's; the traits are in the saved game. `Traits.dealt(random)` deals
  40 to 60 percent of the 800 points there could be, `Traits.tending_to(tendency=, random=)`
  nudges a named tendency (`LOGICAL`, `CAMPAIGNER`, `PEACEFUL_BUILDER`), and
  `Traits.favors(trait=, random=)` is the one draw every decision goes through. A theme names
  its player in `Theme.PLAYER`, and `PLAYER.play_turn(game=, civilization=)` is `plan()`, then
  `Hand.carry_out()`, `keep_within_points()` again, then `Orders.end_turn()`. `plan()` tidies
  the table, gives the research order once (the technologies ranked by `Appraisal` with the
  `ScienceWeights` or the `MilitaryWeights`, as the science trait says), a settler order to
  each settler of a civilization with no city, a build order to each city (the buildings
  ranked by worth, leaving out a world wonder another civilization started unless the
  boldness trait gambles), an improve order to the first city and every city of
  `IMPROVING_CITIZENS`, a settler first in the build order of `settling_city()` while fewer
  settlers are out than `settlers_wanted()` reads from the expansion trait, and an expand
  order to each settler with none, to `Knowledge.nearest_site()`, keeps as many armies and
  divisions as the theme's limits allow, shares the cities out among the divisions as their
  bases (`plan_bases()`), a raise order from each base's division to the base (`division_wanted()`: a unit that hits air for each enemy air unit seen, an
  air unit when the enemy units seen cannot hit air, and fighters that take cities for the
  rest; active up to the garrisons, and beyond them while the bank holds `RESERVE` and the
  economics trait allows), retires a fighter beyond the garrisons while starved, and a
  garrison order for each city, declares
  war on the first civilization met when the division is full (peace trait), gives each ready division a march
  order on the nearest known enemy city no other division marches on (conquest trait, with boldness and aggressive
  hyperfocus written into the order), and disables the orders given last until the active
  orders fit the Policy and the Command. The main AI never names `HelperAI`, which
  `test/test_helper_ai.py` checks.
- The map generator. `world/generator.py` is the static class `MapGenerator`: `make(game=,
  width=, height=)` fills a world with the theme's `MAP.BASE_TERRAIN`, grows patches of each
  terrain in `MAP.TERRAIN_PERCENT` by a random walk of `PATCH_SIZE` steps, then scatters
  strategic resources (`STRATEGIC_PERCENT` of the tiles whose terrain `CAN_HAVE` one) and
  terrain bonuses (`TERRAIN_BONUS_PERCENT` of the tiles each is `ON`), all from
  `Game.get_random()`. `place_civilizations()` puts each civilization's settler on a site
  where `problem_with_site()` passes, searched on every `SITE_STEP` tile, the first at random
  and each next the farthest from those chosen, refusing when two would be closer than a city
  radius. `kinds/map_spec.py` is `MapSpec`, the theme's `MAP`, and caveman's is
  `themes/caveman/map.py`; a theme with no base terrain cannot have its maps made yet.
  `support/map_preview.py` and `tools/map_preview.py` (`make map THEME= SEED= CIVILIZATIONS=`)
  print a world as a grid of throwaway letters with a legend, for talking about the generator.
- Starting sites. `MapGenerator.starting_tiles()` tries three pools of sites in turn, the
  sites that are ready, the sites that only have room, and every site, and takes the first
  pool that `spread()` can place every civilization in, far apart. `world/start_survey.py` is
  `StartSurvey`, read once from a world: `has_room()` (the theme's `MAP.START_REACHABLE_PERCENT`
  of the square `START_REACH` steps each way can be walked to, tiles off the world counting
  against), `lacks()` (the resources in `START_NEEDS` that too few tiles of the first city
  radius give, outside the center), `misses()` (the resources in `START_STRATEGIC` not within
  `START_STRATEGIC_DISTANCE` of the radius) and `is_ready()`. `world/land.py` is `Land`, the
  pieces of a world a kind of unit can walk, by the eight `NEIGHBORS`, and
  `world/square_count.py` is `SquareCount`, a running count along each row that answers how
  many marked tiles a square holds. `world/start_improver.py` is the static class
  `StartImprover`, which `place_civilizations()` calls for each chosen site: it turns plain
  land tiles of the radius into the terrain that gives the most of a lacking resource, never
  taking a tile a needed resource cannot spare, and puts a missing strategic resource on a
  tile near that can have it, or on a tile outside the radius changed for it. Caveman's
  `MAP` asks for 3 tiles each of food, wood and stone, and flint, on a world of 80 by 80.
  `world/terrain_control.py` is `TerrainControl.change()`, the one place a tile's terrain
  changes after a world is made, which `WorkControl` uses too.
- Not built yet: satellites, the colony ship, styles of map, the technology given after
  6000 turns, trading technology, and a technology that reveals land without exploring.

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
- The scripted game. `support/scripted_game.py` has `started_game(theme=, seed=,
  civilizations=)`, a game on a generated world with traits dealt to every civilization, and
  `play(game=, turns=, stall_turns=)`, which has the theme's `PLAYER` play until the game is
  over, reaches a turn, or has had nothing built for `STALL_TURNS`, and returns the
  `Chronicle`. `support/chronicle.py` is `Chronicle`, which watches a game only through its
  getters: `note()` after each civilization's turn turns what changed into `Event`s (a
  `What`: founded, took, learnt, knew everything, declared war, finished a world wonder,
  defeated, went bankrupt) and counts units made and lost, and `count()` at the end of each
  turn records each `Measure` (cities, citizens, wealth, units, technologies) of each
  civilization still playing. It is not the history record of the model. `support/charts.py`
  draws `chart_lines()` in plain characters, and `support/game_story.py` writes
  `report_lines()`: the story, the curve of the game, and tables of traits, technologies and
  units. `tools/scripted_game.py` is `make game THEME= SEED= CIVILIZATIONS= TURNS=`.
  `number_at()` in `support/theme_tools.py` reads a number from a tool's command line.
- The game log. `support/game_log.py` is `GameLog`, which `play(log=)` has watch a game
  beside the chronicle: `note()` after each civilization's turn follows every unit (tiles
  moved, level, lost or built a city) and each new city, and `count()` at the end of each
  turn adds a turn of life to each unit and records each `Series` of each civilization:
  Policy and Command had and taken, military units inside a city, average level, buildings,
  hit points, strength (hit points of military units plus technologies plus citizens plus
  buildings, that turn) and the four scores that add those up over the turns, with their
  sum, and beside the series how many units of each kind of the theme's `UNITS` each
  civilization has and how many improvements of each kind that stays on a tile (no
  `BECOMES`) are on the tiles of its cities' radii, the radius of each city worked out once.
  `as_data()` is what `write_log()` writes as JSON, with names from `Key`: the per-kind
  counts are `Key.UNIT_KINDS` and `Key.IMPROVEMENTS`, by the kind's shown name and then the
  civilization, every kind present even with all zeros.
  `support/game_log_report.py` works only from that data: `tables()`, `timelines()` and
  `report_lines()`. `support/game_log_page.py` puts `page_data()` into the template
  `game_log_page.html` beside it, which draws the charts with Chart.js loaded by the
  browser: `tabs_of()` gives the tabs in `Tab.ORDER` (score, cities, units, improvements,
  control points, timelines, tables), each with its charts, leaving out a kind no
  civilization ever had (`kinds_ever_had()`), and the page draws a tab the first time it is
  shown and keeps the tab in the address's hash. `tools/game_log.py` writes `logs/<theme>_seed<seed>.json`, and
  `tools/game_report.py` prints the report, or with `--html` or `--open` writes the page.
  `DEV_TOOLS.md` is the guide to them.
- The optimizer, `support/optimizer/`: `depth.py` is `TreeDepth`, `parameters.py` has
  `PARAMETERS` and `Tuning` (`changes()`, `applied()`, which sets the theme's constants and
  puts them back, and `start()`, the numbers fitted to the theme as it is), `criteria.py` the
  criteria with `badness()` and `score()`, `search.py` `Anneal.search()`, `judge.py` `Judge`,
  which plays games in spawned worker processes with the numbers applied, `run.py`
  `optimize()`, and `report.py` the report. `tools/optimize.py` is `make optimize`, and
  `DEV_TOOLS.md` says how to read it.
- `support/guides.py` knows where each theme's guide is (`GUIDE_<THEME>.md`, from the saved
  name) and generates its appendix, the five reports as Markdown between `START_MARKER` and
  `END_MARKER`. `tools/theme_guides.py` refreshes every guide, or with `--check` says which
  are stale and fails, and `test/test_theme_guides.py` fails when any is stale.

## The saved game

- JSON: `required_version`, `saved_by`, `theme`, `turn`, `playing`, `names`, `civilizations`,
  `worlds`, `cities` and `units`. A city holds its buildings, its production queue and its
  progress, and a civilization what it researches, the research points put toward it, how
  many cities it has founded and its memories, one per world, each with its remembered layers
  and the owners of the cities it has seen. Layers and columns are keyed by their numbers, and `names` records the name of every
  id in every category. Memories arrived with version 0.0.5, and a civilization's `oversight_points` took the place of
  its `action_points` in version 0.0.9, and `policy_points` took the place of those in version 0.0.12, which `REQUIRED_VERSION` moved to.
- Loading matches the saved names to the current theme's catalog and renumbers the layers and
  columns that hold kind ids (`LAYER_CATEGORIES`, `COLUMN_CATEGORIES`), in the memories too, only where an id differs,
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
