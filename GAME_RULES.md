# The model: the rules of microsponge

This document is the model. It defines the game the way the rule book of a strategy board game
would: what is in the game, what a player can do on a turn, and what happens as a result. It's for
people who want to know how the game works and for Claude alike. The user decides everything in
it, and each decision is written here when it's made, before anything is built on it. The model
objects in the code are derived from this document, so the code and this document are kept saying
the same thing: a change to the model changes this document in the same commit.

Everything here is about the theme called classic, described under "Themes", unless a line says
otherwise. What classic itself chooses, like its list of resources, is kept in
`.claude/THEMES_CLASSIC.md`.

## Themes

- microsponge is a flexible engine, and a theme is the kind of game played on it. The person
  playing chooses what kind of game to play.
- A theme of historic earth civilizations from the ancient world is a different theme from a game
  in a futuristic world, or in a fantasy world filled with magic and spells and other technology.
  There could be a theme about robots.
- A theme may have no combat at all.
- Each theme may have its own resources, its own tech tree and its own units.
- A theme can have terrain of its own. Caveman has the tarpit: a terrain that land units cannot
  cross, that nothing can be built on, that provides no resources and that cannot be removed.
- What a city is called belongs to the theme: in caveman a city is a village. The model says
  city throughout, and the game shows the theme's word.
- Each theme has a small set of constants that say what a city means in the theme, called the
  city spec. The city spec can say which resources a city produces by default, and what a city
  requires.
- Each theme says the default costs and properties of its units. A default can be given once
  for all the units of the theme, and a kind of unit can then differ.
- The first theme, the one being developed now, models historic earth in the style of a
  civilization game. It's called classic.
- microsponge is not FreeCiv and is not a clone of FreeCiv. What features FreeCiv has may be
  looked at occasionally, and nothing more.

## Starting, saving and loading a game

- Starting a new game means picking a theme, and then answering what the game asks about some
  parameters, like the size of the map and the difficulty.
- There may be only one difficulty to start with, and what difficulty means is not defined yet.
- A game can be saved and loaded.
- A saved game can still be loaded after its theme has changed in a later version of the game.
- A saved game records the version it requires. A later version of the game may decide that
  saved games from before some version can no longer be loaded. There is no code that upgrades
  an old saved game, for now.
- Time in the game is counted in turns only. There are no years: nothing the game shows is a
  year, and a length of time is a number of turns.
- Starting a new game may later mean choosing how far along in time the game starts, further on
  than turn 0. The technologies line up with a timeline, and a game that starts after a
  technology's time on the timeline starts with that technology already known.

## Civilizations

- The game supports an arbitrary number of civilizations. For now the most a game has is 7.
- Each player chooses a civilization from a list when the game starts.
- Each civilization has a color of its own.
- A civilization is mostly just a name. The game does not tell a player up front what a
  civilization is like: a player has to learn what each civilization is like by playing.
- Civilizations can have different bonuses. A bonus is small, like 10% off the price of certain
  buildings, or research that is 10% faster, and the amounts can be tuned later.
- World leaders are never named, and no leader is modelled as a person.
- No civilization has units that only that civilization can build, because unique units are
  extra trouble to balance.
- Each civilization has resources, and a number of action points.
- There are types of government, each with different advantages and disadvantages.

## Traits

- A civilization played by the computer has traits, which work like a personality. Some
  civilizations care less about loyalty, some are more predictable, and some care about loyalty
  and ethics a lot more.
- Traits belong to one game. Each game that is started gives its civilizations their traits
  afresh, as if each civilization were a new person, so what a player learnt about a
  civilization in one game does not hold in the next.
- The traits of a civilization can change as the civilization itself changes over time, on the
  same slow timescale as its memory.
- A person playing a civilization sets up no traits: the person plays as themselves.
- The traits of a civilization may be shown in a window on the diplomacy screens, which may
  always be available to a civilization that has a spy network.

## Diplomacy

- There is to be a diplomacy system, defined later. It is to be more developed, with more
  subtlety and complexity, than the diplomacy of a game that is mostly about making war.
- Civilizations remember what another civilization has done to them, and can also change their
  mind over time when that civilization acts well towards them.
- The memory is read from the record of what happens, the same record the history story is told
  from ("History").
- Each thing a civilization does changes the opinion other civilizations have of it. Small
  things have a small impact on opinion, and bigger things have a bigger impact.
- The impact of a past deed declines over time, but slowly. World leaders live for about as long
  as people do, so the memory of a generation changes about every 960 turns, and a memory can
  clear after that time.
- How much a deed matters to a civilization depends on that civilization's traits.
- The game can help a player see the history between civilizations.
- A civilization that another civilization has discovered can be contacted, if the appropriate
  technology has been researched.
- It may be possible to make another civilization an ally, at least temporarily.
- A civilization can have at most 3 allies, in a game of 7 civilizations.

## How a game ends

- A game ends when one civilization is the only one remaining.
- A civilization has lost when it has lost all the cities it has created. A civilization that
  has not yet created any city has lost when it has lost all of its units. So once all the
  cities of a civilization are gone, nobody has to search the map for its hiding settlers.
  The units of a civilization that has lost are taken off the map.
- A game that was given an ending turn, at setup or by a test, also ends at that turn.
- Allies could win together.
- A theme with no combat needs another way to win. It would probably involve a building goal, so
  that a computer player would typically want to acquire lots of land, and there may be other
  ways for a city to change hands.

## Visibility

- Explored land and the fog of war are two different things. Explored land is about the map, and
  the fog of war is about units.
- A theme decides whether land starts out unexplored. Land that a civilization has explored
  stays known to that civilization, and the fog of war never hides explored land.
- A theme may have technology that reveals land, or the whole map, without exploring.
- The fog of war hides units. Each civilization can see units only so far, which can be thought
  of as a visibility radius.
- What a civilization can see decides which units of other civilizations are drawn for that
  civilization.
- A computer player makes its decisions from what its civilization can see.
- A theme may have stealth units.

## Resources

- Each theme may have different resources, and there are different ways to add to a resource.
- A civilization holds its resources in one place: every city of the civilization adds to what
  the civilization holds and spends from what the civilization holds. No city holds resources
  of its own, so that the game stays playable.
- One resource of a theme is its primary resource, and the primary resource is called currency,
  for now.
- Every kind of unit costs at least 10 currency to build, and every kind of building costs at
  least 10 currency to build.
- A civilization is bankrupt on every turn that ends with its currency at 0 after its support
  costs are paid, even when nothing was owed. A bankrupt civilization cannot build anything,
  and there may be other penalties: each theme sets a bankruptcy penalty, which could be 50
  percent off the resources the civilization collects.
- When a civilization has been bankrupt for 50 turns in a row, the civilization loses, which
  ends a game of two civilizations. This also keeps a test from getting stuck, and the
  guardrail may be removed later.
- Each citizen eats food every turn, taken from what the civilization holds. How much a citizen
  eats is set in the theme.
- The rules about resources that follow are generic: they hold in every theme, and are not
  a theme's to change.
- No resource is ever used up from a tile: a mountain goes on giving metal, a farm goes on
  giving food and a forest goes on giving wood. Tiles that ran out would be confusing and could
  break the game.
- Food, metal, wood and stone are collected, for now. A collected resource is farmed or mined, goes
  into what the civilization holds, which the user also calls the bank of the civilization, and
  is consumed there when the resource is used to build things.
- Every other resource is a strategic resource, for now, like iron, in the way of Civilization
  II. A strategic resource is not collected and is not consumed. Only 1 of a strategic resource
  is needed to unlock whatever depends on the resource: when a tile that has the resource is
  within the borders of a civilization, the civilization is able to build every unit that
  requires the resource.
- The borders of a civilization are the city limits of all its cities. A strategic resource
  must be within the city limits of one of those cities, and the tile does not have to be a
  tile a citizen works.
- A strategic resource is on a tile, and may appear on more than one type of terrain. When the
  terrain of the tile is changed to a terrain the resource cannot be on, the resource is gone
  for good.
- A terrain bonus is something else: a special tile, like cows on grassland, that provides
  more food when the tile is worked. A terrain bonus is not a strategic resource, and is not
  required by anything.
- A terrain bonus has a list of compatible terrain types, which is usually just one type, like
  grassland for cows. A terrain bonus goes away when the terrain of the tile changes
  incompatibly, to a terrain not on the list, and most changes are incompatible changes:
  removing the grass removes the cows.
- A resource may come only from the tiles of a terrain that have the resource: metal comes
  from the mountains that have metal, which is not all mountains. In classic, metal is a
  terrain bonus on mountains that cannot be removed for now, because a worker cannot blow away
  a mountain.
- A resource may stop being needed as a game goes on: in classic, almost nothing uses stone
  once the stone age is gone. A civilization may have ages, which make some earlier steps not
  required. That is kept limited for now.
- Wood needs trees. A worker can cut the trees of a tile to make farmland.
- No improvement blocks a strategic resource from being accessed.
- An area of the map that can be mined gives several resources at once, and the game can tell
  how much of each resource the area gives.
- A civilization collects resources from the resource tiles in its area with the citizens of
  its cities. Citizens get resources. A worker is something else: the unit that builds
  improvements, like roads ("Improvements").
- Citizens are never managed by hand. A city assigns its citizens to the city's tiles by itself,
  following the preferences in the city's settings. These preferences are what "city AI" means.
- How a city harvests is configurable in the city's settings. Which settings there should be is
  not known yet. The easiest is a setting for how many citizens look for a certain resource
  first.
- Citizens can be prioritized to claim resources: a city's settings can say that a number of
  the city's citizens must look for a certain resource other than food first.
- Every priority falls back to food: a citizen whose priority cannot be met collects food, and
  with no priorities set, every citizen collects food.
- A citizen who collects food takes the tile that gives the most food, the nearest to the city
  center first when tiles give the same. When no tile gives food, the citizen takes whatever
  tile delivers the most of any resource. No two citizens share a tile. The choice of tile is
  never random, so that a game can be replayed.
- Whoever works a tile gets everything the tile produces at once, every resource of the tile.
- Every working citizen generates currency automatically, for now.
- Some improved tiles can produce currency.
- A building can produce a constant amount of currency each turn. Some buildings may later
  produce currency by some kind of math, to be worked out.
- A building can increase the income in currency of its city by a percentage.
- Not every tile can produce food. A theme can have a terrain that produces no food, and a
  technology that lets such a tile be converted to another terrain when the tile is next to
  fresh water.
- An improvement built on certain tiles that hold resources may make it possible to harvest the
  resources there faster.
- Various resources may be revealed around the map based on the tech tree.
- Buildings take resources.

## The tech tree

- Each theme can have a different tech tree. The tech tree of classic is to be discussed soon.
- A civilization researches only one technology at a time. There is no research queue: when a
  technology is finished, the civilization must pick the next technology to research.
- When no technology is available to research, the civilization picks one when one becomes
  available. That should only happen once the whole tech tree is researched.
- A civilization that is slow at researching the tech tree automatically gets a technology it
  has not discovered 6000 turns later.
- A civilization can also acquire a technology through trade. Trading technology is not allowed
  very often: each civilization can give away a technology only about once every 100 turns, so
  that allies cannot farm technology together.
- A technology can give bonuses to harvesting rates. Each bonus is a percentage, and the
  bonuses of all the technologies a civilization has are additive: two bonuses of 10 percent
  make 20 percent.
- A technology can give bonuses to the support costs of units, which make units cheaper to
  support.
- Research points do not gather in a pool. A civilization has a research capacity each turn,
  which is applied to the current research target, the one technology the civilization
  researches. A civilization researches one technology at a time, with no queue, and picks the
  next when a technology is known.
- The research capacity of a civilization is based on the number of cities the civilization has,
  and on certain buildings in those cities. The theme decides which buildings.
- The only way a civilization can be researching nothing is to have completed the tech tree.
  Then the research points turn into currency, 1 research point for 1 currency for now, which
  may change and may become a choice of the theme.
- The points past what a technology takes are lost when the technology is known.
- Switching to another technology while one is being researched is not supported for now,
  neither on the screens nor for the computer players, so the game refuses it. If it comes,
  the points put toward the technology before are lost.
- A pick is forced: while a technology is left to pick and none is picked, the turn cannot
  end.

## Points

- The game scores points in different categories.

## The map

- The map is a grid of tiles, and every city is on the map.
- A tile is land or water. Mountains are land that costs more to move across.
- Only one unit may occupy a tile at any time.
- Maps can be very large.
- A random map generator makes the map, and makes good choices.

## Worlds

- A game has one world or more. Each world is a map of its own, a grid of tiles. Classic has one
  world.
- A world wraps around horizontally, from east to west, as the world of a civilization game
  does.
- A polar world in classic does not wrap vertically: a unit cannot cross the poles at the north
  and south edges.
- In SciFi, crossing the poles of a world may require a certain level of technology, and only
  when the world has ice caps. A civilization may be futuristic enough to start with that level,
  depending on where in time the game starts.
- A theme may have several worlds, such as planets, and the grid of a planet can be small.
- Every theme says the fewest and the most worlds a game of the theme can have. A theme with
  planets allows more than one, and the person setting up the game chooses how many, within the
  theme's limits. Classic, caveman and fantasy have exactly 1 world. SciFi has at least 1 and at
  most 50, for now. PlanetWars has a planet for each civilization, and may have more.
- Classic starts with every civilization on one planet, called Earth, which is the only
  planet, and so the only map, in the game. SciFi can start with multiple planets.
- A theme may have portals, which let a unit jump from one world to another.
- What a theme with planets chooses is kept in the theme's file, `.claude/THEMES_SCIFI.md` for
  SciFi, the theme inspired by Stargate.

## Space

- Space is a layer above the planets, which even classic has in a limited way, and which SciFi
  uses fully. Units that are not space units are stuck on their planet, and cities are on the
  maps of the planets.
- Space units are classified as those that can de-orbit, which requires a city with a
  spaceport, and those that are space-only and can only orbit a planet.
- A space unit that can only orbit must be built at a starport. A starport orbits a planet, and
  is created by a city as a very large project.
- Space units can attack each other. Some space units can be flagged as capable of aerial
  bombardment.
- Every space unit orbiting a planet can attack every other space unit orbiting the planet, and
  can also destroy the starports orbiting the planet.
- A city with the special facilities called anti space missiles or anti space lasers can target
  large space units, but not small ones.
- A city, if the theme enables it, can launch up to three satellites into the space around its
  planet, which provide bonuses. Classic enables it. Space fighter type units around the planet,
  or land to space missiles from the planet, can destroy satellites, from space or from the
  planet as appropriate.
- A theme may have a layer that is like space but works only for the current planet: in
  fantasy, the astral plane, whose properties are undefined for now, and which some units can
  move between the real world and. Fantasy's file, `.claude/THEMES_FANTASY.md`, holds what the
  user decides about the astral plane.
- A theme may have a colony ship: a space unit that, when the colony ship hits a world, can
  spawn a settler there, with rules to be figured out: spawning may cost extra population, may
  spawn multiple settlers, and may give the player some choice about where to land.
- A space transport may behave in a similar way about where to land, but land defenses, the
  anti space defenses, may be able to shoot a space transport down.
- A theme may start every civilization alone on a planet of its own, only big enough for one
  city, with empty planets besides, like PlanetWars. What such a theme chooses is kept in its
  file, `.claude/THEMES_PLANETWARS.md` for PlanetWars.
- A theme with space allows stargates to be built. A stargate supports the transport of
  giant ships between planets; without a stargate, a giant ship must take a long voyage, which
  is slow.
- The smaller space ships basically only do space defense around a planet, for example to
  fight a large ship that gets close. A space carrier transports the smaller ships between
  planets.
- How the planets are distributed over space is not decided.

## Cities

- A city is made of two parts, and these are the words for them. The city center is the 5 by 5
  tiles in the middle, unlike the cities of most civilization games. The city radius is the 15 by
  15 tiles that belong to the city, with the city center in the middle.
- Cities do not have to be lined up with each other. A city can be placed with its center
  anywhere on the map, as long as the city doesn't cover anything up.
- The center tile of a city must be land.
- At least half of the tiles of the city center must be land, which is 13 of the 25.
- The rest of the city radius has no restrictions, except that the city radius must hold at least
  one land tile.
- Water tiles in a city reduce how much the city can build, and may provide extra fish and
  happiness. How happiness works is not decided yet.
- City limits cannot overlap at all: the city radius of a city never overlaps the city radius
  of another city, whether of the same civilization or of another. A settler cannot build a
  city where the city radius would overlap another, and so a tile belongs to one city at most.
- The size of a city allows many units to surround it.
- Generally a unit may not enter the city radius of another civilization's city at all, unless
  the two are friendly or in a state of war.
- A civilization can declare war on another civilization. For now, declaring war is required
  before a unit enters the territory of the other civilization.
- A city has citizens. A city grows more citizens over time, when there has been enough food for
  enough turns in a row.
- A turn counts toward growth when the civilization holds at least a set amount of food for
  each citizen of the city. When the count of such turns in a row reaches the number the city's
  size requires, the city grows one citizen and the count starts again. Growing spends no food.
- How many turns in a row each size requires is set in the theme: something like 5 turns for
  the first growth and 10 turns for each growth after that, and 20 turns for a city above 10
  citizens if cities are ever allowed that large. The numbers will be tuned.
- A city has at most 10 citizens.
- A city can build only one thing at a time, one thing in a turn.
- The cost of what a city builds is paid a part each turn, not all at once, so that switching a
  city to build something else has a natural cost. The cost is split evenly over the turns the
  build takes.
- On a turn when the civilization does not hold enough to pay that turn's part, the build is blocked:
  the build waits and takes a turn longer. The game can tell which builds are blocked, so that
  a screen can show them.
- A unit can be inside a city. A unit inside a city does not occupy a tile: the city holds the
  unit. A unit inside a city may contribute to the city's attack and defense, and may be injured
  when the city is attacked.
- A friendly unit enters a city by moving from a tile next to the city center into the city
  center.
- A city can hold 3 units, for now.
- When a city that is full of units finishes building a unit, the new unit is placed on an empty
  tile next to the city center, if there is one, chosen at random.
- When a unit is finished, a free action lets the player choose the tile the unit is placed on,
  and the cursor can then only reach the tiles that surround the city center.
- The rules for getting units into and out of a city may all change.
- A city has no pool of action points of its own. In certain situations a city adds action
  points to the pool of its civilization, or uses some of them up.
- A city may have a production queue. When the production queue is empty, the game asks what to
  build.
- A city may be set to build nothing, and a city set to build nothing is easy to see somewhere.
- When a city switches what it builds, or is set to build nothing, a partial refund of what was
  paid for the build under way comes back to the civilization: 20 percent, rounded down.
- A city has one of each building, and that is not a choice the player makes: most buildings
  come one to a city, with some exceptions being possible in the future.
- A city cannot build a settler, or any unit that uses up citizens, if the unit would reduce
  the population of the city to 0.
- There are important events, like a city that cannot build what it was told to, which a
  player is told of and can hop through, jumping to each thing that needs attention. The
  screens will say how.
- Settler units build cities, in every theme. A settler unit expends itself to build a city: the
  settler unit is gone and the city stands where the settler unit was. A settler unit can build
  a city only where the settler unit is not within the city radius of another city.
- A city can be disbanded. Disbanding a city redeems a value in currency, which by default is
  10 percent of the value of all the buildings in the city.
- When a city is disbanded, the units that were inside the city stay in the game, each placed
  at random on a tile inside where the city center was.

## Improvements

- An improvement is something a worker builds on a tile, like a farm or a road. A worker is a
  unit on the map. A settler unit does not build improvements, and neither do the citizens of
  a city, who harvest the city's tiles ("Resources").
- A theme says which improvements a worker can build, which terrain each improvement can be
  built on, and which technology each improvement requires.
- A civilization can build a worker as soon as the civilization has discovered any
  technology that enables an improvement. A civilization may start with no ability to build
  improvements at all, as in caveman.
- An improvement increases the resources that come from the tile the improvement is built on.
- Building an improvement takes a certain number of turns, set for each kind of improvement.
  The unit that builds the improvement cannot move until the improvement is done. The unit can
  abandon the effort, and then nothing comes of the turns already spent. Abandoning costs
  nothing, and starting the improvement again starts from the beginning.
- A tile can only have one improvement, for now.
- Building an improvement costs nothing, for now.
- Enemy units can destroy improvements.
- A worker can also change the terrain of a tile, like cutting the trees of a forest tile,
  which takes turns the way building an improvement does.

## World wonders

- Every building defines its support cost, paid every turn like the support cost of a unit.
- A world wonder is something only one civilization can build. When two cities build the same
  world wonder, the first to finish has the world wonder, and the other city's build is dropped
  with everything paid for the world wonder: there is a great cost to not finishing one.
- A player is warned when any other civilization starts a world wonder, at any time, and the
  warning does not say which civilization when the player has not met that civilization. A
  player who starts a world wonder that another civilization is already building is warned too.
- A world wonder is captured with the city that holds the world wonder.
- A world wonder can be what unlocks something else, the way a technology does.
- A building can require a technology.
- A building can require a water tile next to the city center, like a harbor.
- A building can add to what a worked tile of a certain terrain gives, like 1 more food from
  each worked tile of grassland, and can make its city grow a citizen a number of turns sooner.

## Units

- A unit may perform various actions. Settler units can build cities, and combat units can
  fight.
- Every theme has a settler unit. A settler unit can be built without researching any
  technology.
- A settler unit costs currency like every other unit, time to build, and also one citizen of
  the city that builds the settler unit.
- A civilization starts the game with only one settler unit, and by default, for now, with no
  cities and no other units. This may change when a game can start further on than turn 0.
- A unit can be disbanded. Disbanding a unit returns no currency, unless the unit is inside a
  city, in which case 20 percent of the value of the unit is returned in currency.
- Every kind of unit is defined by the theme. A player does not design custom units.
- A kind of unit can require a building in a city, like a barracks, the way a kind of unit can
  require a technology. Only a city that has the building can build the unit.
- Certain kinds of unit may be marked as not being able to take over a city.
- Every unit has upkeep, also called its support cost, paid every turn from what the
  unit's civilization holds: a cost in
  currency and a cost in food. Each cost is a fixed amount for each unit, and the amount depends on
  the civilization's type of government.
- A unit may be given a destination order, which the computer then carries out, and this is so
  for a person's own units too. There can be other types of orders.
- A land unit is not amphibious unless its kind of unit says so. A unit may or may not be
  amphibious.
- Air units may get fuel: an air unit with fuel left would not have to return to base every
  turn.
- Aerial units may only travel so far from home or from a city, where they are at the end of
  their turn.
- Naval units can only move in water.

## Action points

- There are two pools of action points: each unit has a pool, and each civilization has a pool.
  A city has none.
- All action points refill every turn.
- A unit has a very small number of action points.
- Whatever a unit does costs the same number of action points from both pools: from the unit's
  pool and from the pool of the unit's civilization.
- Moving a unit one tile always costs 1 action point, except onto mountains, which cost 2 action
  points.
- Attacking costs 1 action point.
- Building a city costs 1 action point. Going into a city costs 1 action point, and coming out
  of a city costs 1 action point.
- Everything a worker does on a tile costs 1 action point. A farm itself costs nothing: only
  the action point of starting the farm.
- Setting a priority in a city is free. Deciding what to build next and deciding what to
  research next are always free. Declaring war costs no action points, and ending the turn
  costs nothing.
- Action points are also written AP.
- The tiles are squares, because a grid of hexagons is difficult to draw. A unit can move and
  attack diagonally.
- Moving straight and moving diagonally each have a base cost in action points, kept as two
  numbers that are easy to change, and so do attacking straight and attacking diagonally. All
  four are 1, for now. The terrain of the tile attacked does not change the cost of an attack,
  as it does the cost of a move.
- A unit attacks a unit on a tile next to its own, for now. That is true of every kind of unit,
  so a land unit can hit a sea unit only when the two are next to each other.
- The idea of the civilization's pool is that a civilization cannot move all of its units in a
  turn, only so many, so that a player has to make good choices.
- A theme configures where the action points of a civilization come from. Each city that is
  built could come with a number of action points, and buildings could give action points too.

## Combat

- Each unit has hit points.
- Each unit has attack points and defense points. Every kind of unit defines its attack points,
  its defense points and its hit points.
- When a unit attacks another unit, the attack points of the attacking unit are reduced by the
  defense points of the other unit, and what is left is the damage dealt to the hit points of
  the other unit.
- An attack always deals at least 1 damage, called chip damage, however strong the defense.
- Hit points are large numbers: about 10 for even the weakest unit, and up to 500 for the
  largest. A unit that takes only chip damage from one attacker mostly heals the chip damage
  back.
- A unit whose hit points reach 0 is removed from the game.
- A unit that is attacked strikes back, by default. Whether a unit strikes back is a property
  of the kind of unit.
- A unit strikes back at reduced power: by default with 20 percent of its attack points. The
  percentage can be set for each kind of unit.
- Units are classified as land units, sea units, air units and space units, and there may be
  more classes. Each kind of unit says whether it can hit air units, whether it can hit land
  units and whether it can hit sea units.
- By default a land unit cannot strike back against an air unit, and a sea unit cannot strike
  back against an air unit. Some kinds of land unit and of sea unit can.
- A city with no units inside cannot be attacked. Moving a unit into such a city, when the two
  civilizations are at war and the unit is of a kind that takes cities, offers the player two
  options: take over the city, or raze the city. Both will take some turns, and the behavior
  is to be defined later; for now taking over is immediate and razing is not built. The city
  changes hands with its buildings and its priorities as they are. Taking a city ends all of
  the city's current production, with no refund. City walls and other defenses may come later.
- Destroying a unit does not move the attacker into the tile where the unit was destroyed.
- A building can boost the defense of its city by a percentage, like the watchtower of caveman:
  the boost applies to every unit inside the city when the city is attacked. City walls, when
  they come, provide an additional boost, and will be talked about with the tests for classic.
  The boosted defense rounds up, so that a boost of 25 percent raises a defense of 2 to 3
  rather than leaving it at 2, which is fine for now until the user decides it isn't.
- A theme may have city walls, a building whose boost certain kinds of unit bypass, like the
  catapult, the cannon and the howitzer of classic: against such a unit, the walls add nothing,
  while every other defensive building still counts.
- A unit attacks only a unit of a civilization its own is at war with, and attacking a city
  means attacking any tile of the city center from a tile next to that tile. A city with no
  unit inside cannot be attacked, only taken.
- When a city with units inside is attacked, the units inside are attacked in turn, the unit
  with the strongest defense first. The unit inside that strikes back is the one with the
  strongest attack among those that can actually hit the attacker, and when none of them can,
  nobody strikes back and that is fine. To defend against a unit, a unit must be able to hit
  that unit.
- What a kind of unit can hit covers attacking as well as striking back.
- Certain kinds of unit that can attack air units get a bonus against air units: the bonus is a
  different attack value against air units.
- Units are balanced so that fights take several attacks. A theme in which every unit can kill
  every unit in one turn is bad. In general, most units can be killed by any unit that can hit
  them in about 5 to 10 attacks at worst.
- Space units can hit everything, for now. There may be space units that can only hit space
  units. What space units can do is under "Space".
- A unit heals a small amount every turn, and heals more inside a city. Every kind of unit
  defines how many hit points a unit heals each turn outside a city, and how many inside a
  city, and a theme can give a default for all of its units.
- A land unit gets a defense bonus from the terrain the land unit is on.
- Air units have advantages.
- Units do not gain experience from fighting. There are no veteran units.
- Combat needs more discussion, and attacking a city needs planning in more detail.

## Turns

- A game is counted in turns, and turns are all the game shows of time ("Starting, saving and
  loading a game").
- A game has no ending turn, unless the person setting up the game asks for one, or a test wants
  one.
- The civilizations have a defined turn order, and play one after another in that order.
- Ending the turn is always a manual choice.
- Changing the type of government makes a civilization skip a certain number of its turns, while
  the other civilizations go on playing. There could be other requirements or penalties for
  changing the type of government.

## History

- A game can tell the story of what happened in the world between two points in time, at a very
  high level, either when the game is over or in the middle of the game.
- The story is a summary that reads as a good story of the history of the world, in the way the
  stories of Dwarf Fortress do, but nothing in the story is invented: the story tells only what
  happened in the game.
- The game keeps a history record from the start of the game. The history record serves two
  purposes: the story is told from it, and the opinions civilizations have of one another are
  informed by it.
- The history record does not hold the moves of past turns. The history record is about how many
  attacks and affronts there were, and which.
- The history record is summarized every 12 turns, then summarized again at a higher level
  every 240 turns, and again every 1200 turns, the way monitoring data keeps less detail the
  further back in time it goes.

## Computer players

- The computer players are algorithms written for this game. No machine learning is involved.
- A goal of the game is that a game can be played with no person in it at all: every
  civilization is played by a computer player. A person can then read the summaries of the
  game, and replay the game on the map, zoomed out or not.
- A computer player plays its civilization according to the civilization's traits ("Traits"),
  so different civilizations play differently.
- The details are to be discussed.

## Not decided yet

- What a city may not cover up, beyond terrain that nothing can be built on.
- Whether civilizations have ages, and what an age makes not required.
- What bonuses satellites provide, and what launches them.
- Where on the map the strategic resources are, and how they are placed.
- The situations in which a city adds action points to its civilization's pool or uses them up.
- How far a civilization sees units, and what gives it sight.
- How land becomes explored.
- How happiness works.
- The tech tree of classic.
- The categories that points are scored in.
- The types of government, and the upkeep in currency and in food that each sets for a unit.
- The list of traits, how a game gives a civilization its traits, and what makes traits change.
- The bonus of each civilization.
- Which kinds of attack and affront the history record counts.
- How big the impact of each kind of deed is, and how fast the impact declines over the 960 turns.
- Whether there are spy networks.
- How many research points a technology takes.
- The timeline of the technologies, and what the 6000 turns are counted from.
- Whether every world is a polar world, and what the other kinds of world are.
- The numbers for the growth of a city, which each theme sets and which will be tuned.
- Which settings a city has for how its citizens harvest, beyond how many look for a certain
  resource first.
- The other penalties for being bankrupt.
- What happens to a city when its civilization has no food left for the citizens of the city.
- How big the defense bonus of each terrain is, and what the advantages of air units are.
- The diplomacy system.
- How far an aerial unit may travel, and what counts as its home.
- How a unit leaves a city.
- The priorities in a city's settings, and the improvements that can be built on tiles.
- How allies are made and lost, and how allies win together.
- What happens to what was already paid when a city switches to build something else.
- How the turn order is defined, how many turns a change of government skips, and the other
  requirements or penalties.
- What difficulty means.
- How long a settler unit takes to build, and how the time anything takes to build is worked
  out.
- The rest of the rules for capturing a city, noted in `IDEAS.md`.
- Transport units, noted in `IDEAS.md`.
