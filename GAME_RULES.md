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
  same slow timescale as its memory. This is left for later (`IDEAS.md`): for now the traits
  stay as they were dealt for the whole game.
- A computer player's traits are eight numbers, each from 0 to 100: expansion, how much it
  values expansion over the army; boldness, how far below a sure win it will attack; grudge,
  how long it remembers a wrong; aggressive hyperfocus, how strongly it prefers one enemy;
  science, how much it values science and research; peace, how much it tries to be nonviolent
  while it can dominate by investing; conquest, how much it wants to conquer land rather than
  stay small and defensible or keep a large military; and economics, how much it values its
  economy.
- The traits are dealt as points. All the traits together could hold 800 points, and a
  civilization gets between 40 and 60 percent of that, chosen at random when the game starts,
  spread at random over its traits, no trait above 100. There are also named general
  tendencies, settings of the eight numbers that are then slightly randomized, like logical and
  strategic, campaigner and peaceful builder, so that a person setting up a game can later be
  asked what kind of opponents they like, with some canned choices to keep that simple.
- Every civilization is slightly subject to grudges when diplomacy happens, some more than
  others, by the grudge trait. The memory of wrongs comes with diplomacy (`IDEAS.md`).
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
  When more than one civilization remains at a game's last turn, the civilization with the
  highest score wins. The user decided this.
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
  of as a visibility radius. A unit has a vision radius of maybe 5 tiles, which can be changed
  for each kind of unit later.
- What a civilization can see decides which units of other civilizations are drawn for that
  civilization.
- A computer player makes its decisions from what its civilization can see. A computer player
  never cheats by looking at global information: the computer players simulate human behavior,
  with incomplete information subject to the fog of war, and may not have seen all of the
  terrain yet.
- A civilization remembers every tile it has ever seen, with the terrain as it last saw it, and
  sees units only on the tiles within the vision radius of its units and cities right now. A
  city sees its own city radius and no more.
- A vision radius is a square, for now: a unit with a vision radius of 5 sees the 11 by 11
  tiles with the unit in the middle, the same shape as a city radius. This may change later.
- A city of another civilization that a civilization has seen stays on that civilization's
  map, with the owner the city had when last seen. Coming back, the civilization may find the
  city gone or in other hands. Strategic resources, terrain bonuses and improvements are
  remembered the same way, as last seen.
- The map is drawn as the civilization last saw each tile, until the civilization next sees
  the tile and finds out what is different.
- A theme may have a technology that ends the fog of war: a civilization that knows it sees
  every unit everywhere. A screen is to take care not to overwhelm the player with every unit
  move that can then be seen.
- A civilization always sees everything of its own: its units, and everything inside its own
  cities. What is inside another civilization's city is never seen, not the units inside, not
  the buildings and not the production queue, even once the fog of war has ended. A theme may
  later have a technology that shows what is inside every city.
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
- A civilization that has at least one city always ends its collecting and its upkeep with at
  least 1 more currency than it held before, a number each theme can set: what the
  civilization cannot pay is let off. So a civilization with a city is never bankrupt, but a
  civilization whose upkeep takes everything becomes a sitting duck, with almost nothing to
  build with. The user decided this. A civilization with no city can still go bankrupt.
- A civilization is bankrupt on every turn that ends with its currency at 0 after its support
  costs are paid, even when nothing was owed. A bankrupt civilization cannot build anything,
  and there may be other penalties: each theme sets a bankruptcy penalty, which could be 50
  percent off the resources the civilization collects.
- When a civilization has been bankrupt for 50 turns in a row, the civilization loses, which
  ends a game of two civilizations. This also keeps a test from getting stuck, and the
  guardrail may be removed later.
- Food is never held by the civilization. Each city stores its own food: each turn, the food its
  citizens collect goes into the city's store, and its citizens eat from the store, how much
  each citizen eats being set in the theme. When the store cannot feed the citizens, the
  city loses a citizen, though never its last, and the store is empty. Units eat no food; a
  unit's upkeep is paid in other resources, like currency. The user decided this.
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
- A terrain bonus can provide a strategic resource within the borders of a civilization that
  knows a technology, like caveman's elephants, which provide ivory once sewing is known.
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

- A technology can make every city of the civilization that knows it grow a citizen sooner, by
  taking food off each citizen's share of a full store, like caveman's sewing.

## Points

- The game scores points in different categories.
- Each civilization accrues a score, in four parts, which is rough for now and will be refined.
- Each turn, the military score grows by the sum of the hit points of the civilization's
  military units, the science score by the number of technologies the civilization has
  researched, the population score by the sum of the citizens of its cities, and the
  development score by the sum of the number of buildings in each of its cities.
- The number each part counts on one turn is recorded too, beside the total that adds up.
- The score is shown for each civilization in the report of a game. What the score decides,
  like a winner when a game ends with more than one civilization remaining, is not decided.
- For now the score is kept by the log of a scripted game, and not by the game itself.

## The map

- The map is a grid of tiles, and every city is on the map.
- A tile is land or water. Mountains are land that costs more to move across.
- Only one unit may occupy a tile at any time.
- Maps can be very large.
- A random map generator makes the map, and makes good choices. For now it makes a map one
  way, from the game's seeded random source, so that a seed always makes the same map: the
  theme's base terrain, patches of each other terrain covering the theme's percent of the
  tiles, and strategic resources and terrain bonuses scattered on the terrains that can have
  them. Each civilization starts with its settler on a tile where a city can be built at once,
  the civilizations as far apart as the map allows and at least a city radius apart. Styles
  of map come later, once the maps made have been looked at.
- A mostly good starting site matters for every civilization. The map generator looks for the
  best sites to start the civilizations on, not too close to each other, preferring sites that
  are already good, and may then revise the map around a chosen site to make the site better.
- A good starting site has room: at least 60 percent of the tiles within 25 steps of the
  settler in every direction can be reached by land from the settler, for now. Tiles that
  would be off the top or the bottom of the world count as tiles that cannot be reached, so
  a civilization does not start pinned against an edge. The generator scatters resources
  evenly enough to be trusted to be reasonably fair, so a starting site is not judged by
  counting every resource: a theme only lists the resources that the first city radius must
  give, each with the fewest tiles that give the resource. Caveman lists food, wood and
  stone. Water beside the first city is not required, and terrain bonuses near a start are
  a matter of luck.
- The generator tries the sites that are good already, then the sites that have room and can
  be improved, and then, on a world too small for a good site, any site where a city can be
  built. Around a chosen site that lacks something, the generator changes a few plain land
  tiles, never a tile of the city center, a tile with a strategic resource or a terrain
  bonus, or water.
- A strategic resource may be something a civilization has to expand toward, but not too far:
  about 15 tiles at most from the first city radius, for now.
- These numbers are tuning, and how the generator optimizes a map is worked out later: maps
  built in different ways are played, and the way that makes the best games is kept and then
  generalized to the other themes. The generator is never written for one theme. The
  generator knows which theme and which kind of world the generator is making a map for,
  and optimizes for that, from what the theme says about itself.
- Ordinarily the person setting up a game is asked what kind of world to create. The first
  tests play on mostly flat land with small lakes.

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
- A city has citizens. A city's food store holds at most what one more citizen takes, which
  is a number the theme sets for each citizen times the city's citizens. When the store is
  full, the city grows one citizen and the store goes back to nothing. A city of the most
  citizens grows no more and keeps a full store.
- Buildings and technologies that make a city grow sooner take food off each citizen's share
  of a full store, never below 1.
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

- A building or a world wonder can make the upkeep of every unit of its civilization less,
  by an amount the theme sets, never below nothing, like caveman's arrangement of rocks.

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

- Each unit has a pool of action points. A civilization has Policy, which is what was
  first called the civilization's pool of action points, then oversight points and then
  Oversight ("Priorities
  and the helper AI"). A city has neither.
- All action points and all Policy refill every turn.
- A unit has a very small number of action points.
- A unit still needs action points: a move consumes some, and an attack consumes some. For
  now, whatever a unit is ordered to do tile by tile costs the unit action points and costs
  the unit's civilization the same number of Policy.
- A kind of unit can also have a limit on how many times a unit attacks in a turn, set for
  each class of unit attacked: an anti-air unit might attack air units 3 times a turn and
  ground units 0 times. The limit is not built yet.
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
- The idea of Policy is that a civilization cannot direct all of its units in a turn, only
  so many, so that a player has to make good choices.
- A theme configures where the Policy of a civilization comes from. Each city that is
  built could come with some Policy, and buildings could give Policy too, like
  caveman's chieftain's hut.

## Combat

- Each unit has hit points.
- Each unit has attack dice, an armor class and hit points. Every kind of unit defines the
  three.
- When a unit attacks another unit, the attacking unit rolls its attack dice, the armor class
  of the other unit mitigates the roll as below, and what is left is the damage dealt to the hit
  points of the other unit.
- An attack always deals at least 1 damage, called chip damage, however good the armor.
- The damage of an attack includes a degree of randomness: a damage roll, made with dice, for
  the feel of a tabletop role-playing game. An attack always does some damage, and the more
  attack a unit has, the wider the range of its damage can be: a warrior has a small range,
  and a unit like a tank might have a different range. In general, a unit that is evenly
  matched should kill a similar unit in a few turns, and an unmatched unit should often fall in
  one turn, unless the unit is in some kind of fortification. The dice roll from the game's one
  random source, so that a seeded game plays the same every time. A unit's attack is written as
  dice, like 2d6 or 2d6+4, and stored as the count of dice, the kind of die and the number added,
  so that code can edit it.
- Defense is an armor class, somewhat like the armor class of early tabletop role-playing
  games, in the versions where an armor class of 0 was the best. The armor class is not about
  whether an attack hits: the armor class mitigates damage. Every point of armor class below
  10 takes 10 percent off the damage roll, rounded up, and an attack always does at least the
  chip damage of 1: an armor class of 10 is no armor and lets a roll land whole, an armor class
  of 5 halves the roll, and an armor class of 0 or below lets only the chip damage through.
  The user has no idea whether this is right, and it changes if the games played show units
  trading blows too long, or that it sucks.
- A defensive building, like caveman's watchtower or classic's city walls, adds armor class
  levels in the direction that makes the units inside stronger, instead of a percentage.
- A unit that is attacked strikes back for 50 percent of its damage roll, rounded down, for
  now, and the armor of the attacker still counts against the strike back.
- Siege units like classic's catapult, cannon and howitzer will have two attack choices: a
  strike, at melee range, which is the attack on the next tile described here, and a bombard,
  at range, which wounds every unit in a city in a way that will probably not kill them all at
  once. Range and bombard are not built ("A range for siege units" in `IDEAS.md`).
- Units have levels, from 1 up to 20. A level mostly adds hit points, a tiny number each level,
  and very small bonuses, not many at all: at levels 10 and 20 a unit gets an extra damage
  point on every roll, and, interlaced with that, at levels 5 and 15 the unit's armor class
  gets 1 better. The user first said every 5 levels for each, and chose every 10 so that a
  level 20 unit is only about 50 percent better than a level 1 unit of the same kind, which
  every 5 levels made about three times better. The hit points a level adds are a percentage
  of the kind's hit points, set by the theme. A unit that goes up a level keeps its wounds and
  gains the new hit points on top.
- Experience comes from killing more than from attacking, but from both: a kill gives the
  killer the experience worth of the kind killed, which each kind sets so that weaker units
  offer less, plus the level of the unit killed, and every attack a unit makes gives it a
  little. A unit that is attacked and survives gets 50 percent of what an attack gives, and a
  unit that kills an attacker on defense gets the whole experience of the kill, as the
  attacker would have. The experience a level needs grows with the
  level: level 2 at 10, level 3 at 30, level 4 at 60, 10 times the triangular number, so level
  20 at 1900. These numbers are agreed for now, and change if the games played show that
  units do not level up, so that leveling can happen more.
- A building may start the units built in its city at a higher level, like a barracks that
  starts units at level 2, whole at that level and with the experience of that level.
- A unit's level and experience are in the saved game, and the screens show them, probably in
  the sidebar.
- A kind of unit that is better against one class of unit, air, sea or land, like caveman's
  slingshot caveman against air units, gets its bonus as extra dice: the kind says how many
  extra dice it rolls against that class, rather than a separate attack value.
- Hit points are large numbers: about 5 to 10 for even the weakest unit, and up to 500 for the
  largest. A unit that takes only chip damage from one attacker mostly heals the chip damage
  back.
- A unit whose hit points reach 0 is removed from the game.
- A unit that is attacked strikes back, by default. Whether a unit strikes back is a property
  of the kind of unit.
- A unit strikes back at reduced power: by default with 50 percent of its damage roll, as
  above. The percentage can be set for each kind of unit.
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
- Every city can boost the defense of the units inside it, with no building, by a number the
  theme sets, like caveman's villages.
- A building can boost the defense of its city, like the watchtower of caveman: the boost
  applies to every unit inside the city when the city is attacked. City walls, when they come,
  provide an additional boost, and will be talked about with the tests for classic.
- A theme may have city walls, a building whose boost certain kinds of unit bypass, like the
  catapult, the cannon and the howitzer of classic: against such a unit, the walls add nothing,
  while every other defensive building still counts.
- A unit attacks only a unit of a civilization its own is at war with, and attacking a city
  means attacking any tile of the city center from a tile next to that tile. A city with no
  unit inside cannot be attacked, only taken.
- When a city with units inside is attacked, the units inside are attacked in turn, the unit
  with the best armor class first. The unit inside that strikes back is the one with the
  strongest attack among those that can actually hit the attacker, and when none of them can,
  nobody strikes back and that is fine. To defend against a unit, a unit must be able to hit
  that unit.
- What a kind of unit can hit covers attacking as well as striking back.
- Certain kinds of unit that can attack air units get a bonus against air units, as the extra
  dice described above.
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

## Priorities and the helper AI

This is the direction of the game, and the user decided to record it here before the details
are worked out. The sections on units, action points and turns still describe orders given to
single units, and are rewritten as the details are decided.

- microsponge is a meta strategy game. A player does not ordinarily move single units. A
  player sets behaviors and preferences, and jockeys priorities, like a president and a
  general all at once, without tremendous detail.
- The settings form a tree: the civilization, its cities, the kinds of unit, and under each
  kind the single units. Everything in the tree can be given behaviors and preferences, a
  setting may carry a condition, and a setting may be for a kind of unit or a kind of unit
  under a condition.
- A player can define groups of units, called armies, and smaller groups, called divisions
  for now. A group takes settings of its own. For instance, many fighter planes could be
  ordered to station themselves in different cities, and may change behavior when the
  civilization goes to war. Army and division are the engine's words: a theme has words of
  its own for both, the way a theme has a word of its own for a city, because army and
  division are not appropriate for caveman.
- A helper AI carries the settings out: the helper AI is what moves the units and does the
  rest of the detailed work of a turn.
- The game is turn based in the player's eyes. A player may change any setting each turn.
- A computer player works more or less the same way, in two layers. The main AI of a
  computer player adjusts the strategy, which is the settings of the tree, and controls the
  same helper AI beneath.
- A player is allowed to give a direct order to a single unit, though doing so may quickly
  make the game tricky for people. So the AI must know about units that are doing something
  other than what the settings would have them do. Orders could include things like "attack
  units I can reliably defeat within a range", which is explored in greater depth later.
- A player cannot touch the units and the cities. The helper AI can, and a player can ask the
  helper AI to do anything. The computer players use the helper AI to move units, in the
  tests too.
- For now the helper AI has basically no intelligence, and is mostly a pass through: the
  helper AI takes the bare minimum set of orders, in a layer that does allow moves tile by
  tile. That layer is annoying to play through, and anyone is allowed access to the layer.
- An army is always made of divisions, and there are no free units: every unit must be in an
  army, in exactly one of the army's divisions.
- Units cannot stack on the map, so an army is not a thing on a tile. An army is a control
  system for the helper AI. An army may show statistics and help to tell a story, even after
  the army is disbanded and its units are reassigned.
- An order costs Policy every turn while the order is in the table. The moves and attacks
  that the helper AI makes to carry an order out cost only the action points of the units. A
  direct order for one unit, tile by tile, counts as an order in the table for that turn.
  Sending a single unit across the map is likely a very small Policy tax, like 1.
- No cost of an order is hard coded: every cost is in the common settings of the engine or in
  the theme, which are Python, like everything else a theme defines.
- The orders are heavily object oriented. An order is a class, with subclasses for the thing
  the order is given to: a unit order, a city order, an army order, a division order and so
  forth. There are probably no orders for the civilization as a whole at this time, and the
  design allows for them. There is a planet order as well: a city has a planet, and orders
  for a planet are needed later.
- For orders to work across a whole game, the engine has to model planes: space is a plane,
  and the astral plane of fantasy is a plane too ("Space").
- An army order could be an order to raise the army, which directs certain cities to build
  units for that army.
- Every order has a priority from 0 to 100, because several orders can point at the same
  thing: several priorities may go into one city. When several orders point at one thing, the
  highest priority wins.
- A unit and a city are each a thing that takes orders. A thing that takes orders can look at
  every order that points at the thing, and can have orders of its own that help the thing to
  decide what to do. An order on a city could be to prioritize military builds, and such an
  order might even cost no Policy.
- A city can be given build priorities. Without them a city builds mostly random things, and
  stalls when the city has nothing to do. Build priorities rest on the types of things a city
  builds, which the user has sketched and which are still being discussed: types of building
  like science, command and military; types of unit like engineer, settler and military; the
  class of a unit, like air, combined with the type; and for military units defense, offense
  and mixed, with gauges like powerful offensive units against weak air offensive units. A
  city may have basic orders that mix units and buildings, like increasing defense or
  improving offensive potential.
- An order can set what the citizens of a city look for first, like 20 percent more toward
  food, on one city or, as a planet order, on every city of a planet. Such orders cost very
  little Policy, some orders for a city may be free, and orders for armies cost more.
- A division can take most of the orders an army can, and an army most of the orders a
  division can: divisions make control easier. The Policy an order for an army or a
  division costs may depend on the number of units, which is probably the easiest first rule.
- There is an order to expand, which may take an area, to be defined. The order can be given
  for a planet, and also to a city, because a city has to produce settlers to expand toward
  somewhere.
- There is an order to explore. A city could be ordered to explore, with scouts, and so could
  military units: a division, or a single unit.
- Units cannot overlap on tiles, which is why cities are big. Units can overlap inside a
  city, and only there: inside a city there is just the one city, with all its units.
- A city is not told to build mixed units. A city, or whatever takes the order, is told what
  mix of units to aim for: the order takes a table, so the order is really something like a
  garrison order. The same goes for buildings: a buildings order takes a list of buildings
  in order, and the list can be managed.
- A civilization can set research goals with a research order.
- What a kind is for is its purposes: a building or a unit can serve many purposes at once.
- Orders are not named for the thing they are given to, like a city order or a planet order.
  Rather, the list of possible orders varies by the type of thing. In general an order at a
  lower level overrides an order at a higher level. An order for a planet sets a default
  policy for everything on the planet, which for now is just the cities.
- Engineer is the role of a unit that improves terrain. Engineer is a role and not a kind of
  unit: caveman's worker is an engineer.
- Settlers, engineers and scouts are not in an army. They belong to a city. Every unit
  belongs to something: a division of an army, or a city. A unit that belongs to a city can
  be given a new home in another city, which moves any upkeep the unit has, like its food,
  to the new city.
- Policy is meant to have a lot of points, to make the costs easy to set. An order for an
  army might cost something like 10 points plus 1 for each unit in the army. A city offers
  some Policy for free, and a building like the chieftain's hut offers more; how much is
  not decided.
- What an order aims to have built is its build targets: each is a build target. The class
  names are used in discussion for now, and the names a screen shows come later.
- The whole game could technically be played without a text UI, through different interface
  layers, and that may be tried. Nothing in the model assumes a particular screen.
- A lower level order wins over a higher level order, for now. One problem is not solved and
  may change that: a division that wants to raise units has a list of cities, called bases,
  that can build for the division. The army then has demands on a city, and the city has
  goals of its own and wants to balance them. How a player controls that balance in a way
  that is possible and intuitive is being discussed.
- Each city can have a resolution order, which is free: a policy that sets how the city
  balances conflicting priorities. The city can decide that military goals are the more
  important builds, that the city's own rules win, or that the city tries to balance the
  two, the details of which are not worked out.
- The priority from 0 to 100 may be removed. In its place, a resolution order would be just a
  configurable list of the things whose orders compete, whose precedence can be totally
  customized. A resolution order has no precedence list by default. When a list is set and
  something is not on the list, that goes into a view of what is resolved and what is
  problematic with the orders of each civilization, which a player reads and which a
  computer player may want to understand too. What decides with no precedence list is being
  discussed. When a city balances, the city alternates strictly, for now.
- A resolution order is set in one of three ways. Two are ready made and need no objects to
  be set up: the divisions before the city itself, or the city itself before the divisions.
  The third is a custom order, which names the things whose orders may come in, and can name
  general things like any army as well as specific armies and specific divisions.
- A request from something that is not on a city's precedence list is served after everything
  on the list.
- With no precedence list, which of the competing orders wins is chosen at random, and the
  conflict is flagged in the view of problematic orders.
- The view of problematic orders is not a log of history. The view says, right now, which
  conflicts would benefit from a resolution order, which orders are invalid, and which orders
  may never be valid because their targets do not exist. That last kind is tricky because of
  the fog of war: when a target city has been destroyed where the civilization cannot see,
  the player is not told that the order is invalid, because the player does not know. Such an
  order stays active in the civilization's view and keeps costing Policy, until one of the
  civilization's units or cities sees that the target is gone. The referee AI knows the
  truth, and each civilization's view shows only what that civilization has seen.
- A build target may name an exact kind of unit, or a general category for now: a purpose,
  and also a type of unit, like offensive air units, defensive air units or anti-air units.
  The user had not planned for general categories and accepts them for now.
- An order that holds build targets could have a property for how the targets are met: round
  robin, where the city works toward every target in turn, or top first, where the city
  meets the target at the top of the list before the next.
- The definition of an order is kept separate from an order given in a game. The definitions
  can be subclassed, the way a theme has buildings of its own: a theme may leave a type of
  order out, and may change what an order costs.
- An order given in a game has a giver, which is the thing the order comes from; a receiver,
  which is the thing ordered to do something, like a city, a unit, a division or an army;
  and a what, which is the parameters of that type of order. An order is never from the
  player: the giver is always a thing in the game. An order to raise units has the division
  that wants the units as its giver and the city that will build the units as its receiver,
  and knows what to raise. An order for a division to march has the division as both its
  giver and its receiver, and the destination is inside the what: the destination is not the
  receiver, because the destination is not the thing being ordered to do something.
- The Hand has a realized tree of orders of its own, which is how the Hand interprets the
  orders a civilization has given. The realized tree costs no Policy. A person who plays
  does not see the realized tree, though a test may need to, and a main AI cannot see the
  realized tree either, as part of what the main AI knows when deciding.
- The Hand does nothing that Policy has not asked for. What no order leads does its
  default natural thing, for a computer player's civilization and a person's alike, which
  is mostly absolutely nothing: units defend themselves if attacked, and the civilization
  researches its current targets, or a random technology when no target is set.
- An order for a planet can be a high level objective, like increase settlements here,
  conquer the cities in this area, or eliminate the units in this area. Such objectives can
  be given at lower levels too. An order higher up the chain does not cost more Policy, which the
  user first proposed and then changed. A high level order is instead probably a poor
  choice, because the order leaves everything up to the helper AI, and the helper AI is
  made dumber than a computer player's main AI and than a person: the helper AI is like a
  sergeant beside a general, and can follow orders but cannot strategize well. Given an
  order for a whole planet to attack a city, the helper AI would for example build units all
  over the place and start moving each across the map whenever the unit could, rather than
  bring in a squadron of bombers from the closest point. So a player who makes good orders
  at the middle levels can beat a player who relies on high level orders, and the same is
  true of computer players against computer players.
- An order for a division costs the number of units in the division, and an order for an
  army the number of units in the army, counting every unit. Every order keeps a base cost
  beside the cost for each unit, and the base cost is 0 so far. In the first test of the
  game every order costs 1, an order for an army or a division costs 1 for each unit with
  no base cost, and a resolution order costs 0.
- A civilization whose active orders cost more than its Policy must disable orders
  before ending its turn, a person and a computer player alike. Policy that is not
  spent in a turn is lost.
- What an order says is made of targets. Taking a city is a form of military target, and
  food first is a resources target, beside the build targets.
- A resolution order can be set a fourth way, balanced, which alternates one build for the
  divisions and one build for the city.
- A city with no order builds nothing, and a unit with no order stands still and only
  strikes back. So every city needs a build order attached: the buildings to build, in
  order of priority. A long build order costs no more Policy than a short one.
- Which base builds which unit for a division can be specified in many ways, and all are
  possible: the helper AI figures the split out, the order gives a balance in percentages
  over a pool of cities, or the order is very specific about each city.
- The purposes of the engine are science, defense, offense, growth, expansion,
  engineering and exploration, and a theme can add purposes of its own later. Policy and
  Command are not purposes: both are kinds of control points.
- Every category a kind belongs to, like its purposes and being an anti-air unit, is stored
  on the kind in the theme, so that the game reads all of the categories from the theme, and
  a person can open the one class of a kind, like caveman's captain caveman, and change
  everything about the kind in one place.
- Orders are modelled as object oriented classes, and the name of every order class ends in
  the word Order, like BuildTargetOrder. A military target is not an order: a military
  target is a location to attack, and an order mentions a military target.
- When an order names a category and a city can build several kinds that fit, the helper AI
  chooses the kind, starting from the strongest kind the city can build. The helper AI
  needs to be tuned to be reasonably smart about the choice, and the right tuning is not
  known yet.
- A single unit can take every type of order that an army or a division can take as a
  military order, and beside those the orders for an engineer and for a settler, depending
  on the type of unit.
- A garrison order is a military order: the order makes sure that so many units of a kind
  are in a place, however that is best resolved, which is different from an order to build
  units in a city. A garrison order can influence what cities build too.
- The orders for a settler and for an engineer, SettlerOrder and WorkOrder, are civil orders,
  subclasses of CivilOrder. The research order and the resolution order are policy orders,
  subclasses of PolicyOrder.
- An order that aims at things being built holds a list, and costs Policy once whatever
  the length of the list.
- The order for what the citizens look for first, like food first, is a policy order called
  ResourcesPolicyOrder. The order is not called a target, because the order is not a target
  like a position on the map.
- A target can be a city, a point or a region. An order to expand takes a target sometimes,
  and not always.
- An order is not just a giver, a receiver and a what: an order has configuration of its
  own.
- A garrison order means that a certain number of units, maybe of a certain type or with a
  certain property and maybe not, are wanted in a certain place. The giver is whoever makes
  that call and does not matter much. What matters is how the order is fulfilled: by
  building the units or by moving them. Moving is tricky, because moving takes units away
  from places that have no garrison order keeping them. The receiver is really a selection
  of where the units are garrisoned from, which could be the cities. The priority between
  the two ways of fulfilling, which the user called buy versus build, is probably a
  property of the order.
- A target is one base class with a city, a point and a region beneath: a military target
  is a target that a military order mentions as the location to attack, and the place of a
  garrison order is a target too.
- A garrison order holds a place, a number with an optional kind or category, the sources
  the units come from, which are cities that can build and divisions that can give units
  up, and the way of fulfilling, which says whether building or moving is tried first. The
  helper AI never moves a unit that another garrison order is keeping in place.
- An order for a single unit costs 2 more Policy than the orders for armies and
  divisions do, as a starter number, so that ordering every unit alone is the dear way.
- Orders for armies and divisions also take Command, a second kind of points that a
  civilization has fewer of. Cities provide Command, and military buildings add to what a
  city provides: caveman's watchtower supplies 5 more Command each turn.
- A civilization can have 1 army for every 10 cities and 1 division for every 5 cities.
  These limits, like every such number, are constants of the theme and need tuning.
- Policy comes from buildings too, and how much is tuned with care: too much Policy
  makes the game no longer interesting and actually unfun, because there are then too many
  orders in the tree, which is micromanaging again, like the turns at the end of a game of
  Civilization II.
- The tuning of all of these numbers needs many cross checks in which computer players that
  give orders in different ways play each other, like one that orders every unit alone,
  one that orders divisions and cities, and one that gives only high level orders. There is
  much to tune, and finding good numbers will almost require a search like simulated
  annealing, to avoid local maxima. The tools are planned for this.
- With no precedence list, the order that has waited longest wins, and the conflict is still
  flagged in the view of problematic orders. The user first chose a random winner and
  changed that.
- A unit in a division or an army costs 1 Policy, so an order for a single unit costs 3.
- The limits on armies and divisions round up, and a civilization with units always has at
  least 1 army and 1 division. Each theme sets its own numbers: caveman, whose civilizations
  are small, needs smaller numbers than 10 and 5, and classic and SciFi will differ again.
- The classes of order are named for the points the orders take: an order that takes Policy
  points is a PolicyOrder, and an order that takes Command is a CommandOrder. Policy is the
  name the user gave the points that were first called Oversight.
- Which points an order for a single unit takes depends on the unit: moving a settler or an
  engineer takes Policy, and military movements take Command. A command order takes Command
  only. An order to raise units, which a division gives to a city, is a policy order,
  because the city does the work.
- A city that is doing nothing, which is building nothing, adds a bonus to its
  civilization's Policy and Command, maybe just 1 point of each.
- What is built so far: the build order, the raise order, the expand order, the settler
  order, the research order, the garrison order, which only moves units for now, and the
  march order; one kind of target, a city; Policy and Command; armies and divisions with
  their limits; the referee AI for givers, receivers and garrisoned cities; and the helper
  AI's realized orders for settlers. Not built yet: the resolution order, the resources
  policy order, the order for an engineer, orders for a planet, points and regions as
  targets, the sources and the way of fulfilling of a garrison order, categories in a build
  target, the view of problematic orders, the fog of war rule for invalid orders, and
  orders in a saved game.
- An order to retire a unit takes the unit out of the game for good, which a civilization may
  need to keep its upkeep from taking everything. The order is free, and gives nothing back.
  The order can be given to one unit, and retiring a division or an army is free too, which
  retires every unit of the division or the army.
- Orders can assign units to a division, which takes no points. Moving any number of units out
  of one division into another, or into no division, costs 1 Command, a number each theme
  sets. Moving a division to another army costs 50 Command, making a new division 5 Command
  and making a new army 5 Command, each a number the theme sets. These are a type of order
  called an ImmediateReorganization: each is carried out once and paid once, out of the
  Command of the turn it is carried out, and is not given again each turn.
- An ImproveOrder is a build target order for a city: the city builds an engineer, which the
  helper AI sends to build improvements on the tiles of the city, the way an expand order has
  a city build a settler that the helper AI sends to found a city.
- Orders can defend arbitrary areas, not only cities.
- A completed order is set disabled. A disabled order costs no Policy and does nothing, and
  stays in the table as a convenience, so that a person can remove the order or modify the
  order. A computer player will probably just remove a disabled order.
- The referee AI, which is a kind of global part of the engine and belongs to no player,
  marks an order invalid when the order can no longer work, like an order whose target city
  was destroyed. An invalid order costs no Policy and does nothing until the order is
  changed. Disabled and invalid are nearly the same thing, and are modelled as one for now:
  an order is active or inactive, and an inactive order records why.
- An order holds references to the things the order is about, like a target city. When one
  of those things is no longer valid, the order is invalid in a way that cannot be switched
  back on.
- When several levels of the tree give an order, the most specific level wins: an order on a
  single unit, then the unit's division, then the army, then the kind of unit, then the
  civilization.
- The first orders the helper AI learns are what the computer player did tile by tile before
  the helper AI existed: settle at a site, explore, stay inside a city, attack an enemy next
  to the unit when the fight is worth it, and march on a city and take the city.
- The game must be wary of what happens in a real time strategy game like Starcraft, where a
  computer player that can micromanage every unit beats a person who cannot, because a person
  is only in one place at a time. A computer player is not to micromanage: the main AI passes
  orders for armies and divisions to the helper AI.
- Policy keeps any player from micromanaging. An order consumes Policy every turn that
  the order is kept in the table of orders, different orders take different amounts, and a
  player can only use so much each turn. Policy is the civilization's pool of action
  points under its lasting name, and the screens say Policy.
- Mostly the same orders are available in every theme. What each order costs in Policy is
  written in one main document, which a theme overrides: a theme could even make the orders
  for armies free, though probably none will. The document is Python: each order is a class
  with its cost, and a theme overrides a cost on the theme's own class.
- Tuning the strategy of the computer players matters, and the game is also balanced through
  the costs of the tech tree, the costs of units, the resources, and Policy.
- The test games pit a computer player that uses armies and divisions against one that does
  not, to see what the groups are worth.
- No screen for the settings is built yet. A panel that shows the tree can be imagined.

## Computer players

- The computer players are algorithms written for this game. No machine learning is involved.
- A goal of the game is that a game can be played with no person in it at all: every
  civilization is played by a computer player. A person can then read the summaries of the
  game, and replay the game on the map, zoomed out or not.
- A computer player plays its civilization according to the civilization's traits ("Traits"),
  so different civilizations play differently.
- The computer players have personality, and vary: each civilization has feelings about the
  others, like a reputation for who has wronged it, and is motivated in a few directions. Some
  computer players are very logical and strategic, and try to be the best player; some tend to a
  campaign against one other civilization and focus their attention there; some try to be
  peaceful and build up larger armies; some have other strategies, but never dumb ones. All the
  computer players being different, rather than all the same, is what creates differences in a
  game and keeps it from stalemate, unless each is focused on another in a tangled circle of
  conflict.
- Every player, human or computer, is expected to use positional strategy: cities are built
  close by while an empire is built, and a civilization that blocks out another's land hurts its
  reputation with that civilization. A player may attack, but mostly attacks when the player
  can win, judged from the incomplete information the player has.
- A player who is being boxed out, or who sees a gap in the terrain closing, may send a quick
  settler through to found a satellite city, to keep expanding, because military action means
  not investing in the economy, and it is easy to get behind in technology.
- A computer player watches where its workers can make improvements, and sets the work
  priorities of its citizens. Building cities to reach special resources matters, depending on
  the tradeoffs, which must be considered carefully. Terrain matters: most units cannot cross
  mountains quickly, because mountains take more movement points, and the themes will be tweaked
  until that is true everywhere.
- A computer player may choose not to anger civilizations more powerful than itself, from what
  it can infer about their power. More information comes with diplomacy technology, and maybe
  with spy capabilities, which are to be determined.
- A computer player's personality is a handful of numbers on one player class, the
  civilization's traits ("Traits"): how much it values expansion against the army, how far
  below a sure win it will attack, how long it remembers a wrong, how strongly it prefers one
  enemy, how much it values science and research, how much it tries to be nonviolent when it
  can dominate by investing first, and how much it wants to conquer land rather than stay
  smaller and defensible or keep a large military. "Logical and strategic", "campaigner" and
  "peaceful builder" are settings of those numbers, and the traits may more or less be
  randomized when a game starts. No computer player is ever lazy: every one tries to win, each
  by a different strategy. One strategy looks at what the player knows about the map and
  adapts to it.
- The computer player knows the rules of the game and can play any theme that the model can
  define. The player works out what to do from what a theme defines about itself, and no code
  of the player is about winning one theme, like caveman.
- A computer player chooses by scoring, which is positional play: each thing the player could
  do gets a score from principles and from the theme's numbers, and the player does not search
  through what the opponents might reply. A computer player cannot really trust an enemy from
  the enemy's past behavior, and has incomplete information about every opponent. Looking
  ahead may be added later for small local sums, like whether a group of units can take a
  city.
- No computer player is allowed to cheat, and no computer player gets a bonus for being a
  computer player. Bonuses that belong to a civilization may exist later.
- A perfect player is built first: a player whose strategy is always ideal, with no trait
  rolled. The flavors of strategy and personality are learnt from the perfect player, and
  every flavor tries to win, and to win faster.
- A game is meant to follow a curve. The civilizations drop off at a somewhat even rate, the
  defeats well spaced, as a punctuated equilibrium and not as an endless war. One
  civilization is likely to emerge victorious not long after the tech tree is exhausted, maybe
  50 turns at most, and never thousands of turns after. A civilization mostly researches the
  tech tree to win, though finishing the tech tree is not a way to win. The game is tuned
  toward that curve, and a person will later play against the computer players.
- Eventually games of computer players against each other are played to improve all of the
  strategies, and to make the players more unpredictable.
- The game is tuned so that there is a wide variety of fun things to do without too many turns
  between them, and so that a turn does not hold too many action choices, which would be
  frustrating. Tuning that would help is noted whenever the scripted games show it.
- The details are to be discussed, in `AI_STRATEGIES_CAVEMAN.md` for caveman and in a file like
  it for each theme.
- The computer player never knows a theme: it only knows how to play themes, and reads every
  choice from the theme's properties, so that it plays any theme well with no training for
  one. Whether a unit can take a city is a property of the unit.
- A computer player may build air units when it sees enemy units that cannot attack air units
  and it wants to defend its cities. It may need units that can fight air units when there
  are no anti-air units to be had, or when it sees air units and its cities are far apart.
- Air units need more movement than other units.
- A scout is any unit with many movement points. A real scout unit has an attack of 0, so that
  other civilizations are less angry when it is around.
- A civilization cannot send units across another civilization's borders without war. A
  computer player whose traits make it aggressive may be provoked by, among other things,
  units massing near its borders. How is not decided.
- A computer player decides whether to build a world wonder from the warning that another
  civilization has started it: it starts something else when another civilization started
  the wonder first, unless its boldness makes it gamble that the earlier builder is blocked or
  loses the city.
- The main AI is a utility AI: each decision it could make is scored from curves over what the
  civilization knows, the traits are the weights on the curves, and a goal the main AI commits
  to keeps a bonus for some turns, so that it does not change its mind every turn.
- The helper AI breaks each kind of order down into tasks, a task network; reads influence maps
  of strength, threat and borders, refreshed once a turn; moves units by Dijkstra maps, one
  map for each destination; and checks the odds of a fight before each attack.
- The numbers of these algorithms may be tuned by searching, like simulated annealing over many
  games the computer players play. What is not allowed is an opaque model file whose knowledge
  is not code, like a language model or a model a machine learning library produces: why the
  computer player does what it does must always be readable in the code.

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
