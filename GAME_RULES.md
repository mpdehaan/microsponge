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
- Starting a new game also means choosing where in time the game starts. The technologies line
  up with a timeline, and a game that starts after a technology's time on the timeline starts
  with that technology already known.

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
  as people do, so the memory of a generation changes about every 80 years, which is 960 turns
  at one month a turn, and a memory can clear after that time.
- How much a deed matters to a civilization depends on that civilization's traits.
- The game can help a player see the history between civilizations.
- A civilization that another civilization has discovered can be contacted, if the appropriate
  technology has been researched.
- It may be possible to make another civilization an ally, at least temporarily.
- A civilization can have at most 3 allies, in a game of 7 civilizations.

## How a game ends

- A game ends when one civilization is the only one remaining.
- A game that was given an ending year, at setup or by a test, also ends at that year.
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
- A civilization holds its resources in one place: every city of the civilization adds to the
  same stock and spends from the same stock. There are no separate stocks for each city, so that
  the game stays playable.
- One resource of a theme is its primary resource.
- An area of the map that can be mined holds several resources at once, and the game can tell
  how much of each resource the area holds.
- A theme decides, for each type of tile, whether a resource there is infinite or not, and when a
  resource is not infinite, the random range that the amount is likely to fall in.
- A civilization collects resources from the resource tiles in its area with workers. A city
  has workers, and gets more of them as the size of the city grows.
- Workers are never managed by hand. A city assigns its workers to the city's tiles by itself,
  following the priorities in the city's settings.
- An improvement built on certain tiles that hold resources may make it possible to harvest the
  resources there faster.
- Various resources may be revealed around the map based on the tech tree.
- Every metal alloy needs its components.
- Buildings take resources.

## The tech tree

- Each theme can have a different tech tree. The tech tree of classic is to be discussed soon.
- A civilization that is slow at researching the tech tree automatically gets a technology it
  has not discovered 500 years later.
- A civilization can also acquire a technology through trade. Trading technology is not allowed
  very often: each civilization can give away a technology only about once every 100 turns, so
  that allies cannot farm technology together.
- A civilization has a pool of research points.
- The research points of a civilization are based on the number of cities the civilization has,
  and on certain buildings in those cities. The theme decides which buildings.

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
- In SPACE, crossing the poles of a world may require a certain level of technology, and only
  when the world has ice caps. A civilization may be futuristic enough to start with that level,
  depending on where in time the game starts.
- A theme may have several worlds, such as planets, and the grid of a planet can be small.
- A theme may have portals, which let a unit jump from one world to another.
- A theme may have space: a map that is also a grid, where the planets are, and where ships
  travel between planets. The planets are distributed over space in a way similar to how the
  random map generator builds a world.
- What such a theme chooses is kept in the theme's file, `.claude/THEMES_SPACE.md` for SPACE, the theme
  inspired by Stargate.

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
- The city radii of two cities of the same civilization may overlap. A tile that two city radii
  both cover belongs to the older city, for now.
- When a city is captured and its city radius overlaps the city radius of another city, the same
  calculation decides which city keeps each tile: the older city keeps the tile, for now.
- The size of a city allows many units to surround it.
- Generally a unit may not enter the city radius of another civilization's city at all, unless
  the two are friendly or in a state of war.
- A city has citizens. A city grows more citizens over time, when there has been enough food for
  enough turns in a row.
- A city can build only one thing at a time, one thing in a turn.
- The cost of what a city builds is paid a part each turn, not all at once, so that switching a
  city to build something else has a natural cost.
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
- Settler units build cities.

## World wonders

- A world wonder is something only one civilization can build.
- A world wonder is captured with the city that holds the world wonder.

## Units

- A unit may perform various actions. Settler units can build cities, and combat units can
  fight.
- Every kind of unit is defined by the theme. A player does not design custom units.
- Every unit has upkeep, paid every turn from the stock of the unit's civilization: a cost in
  gold and a cost in food. Each cost is a fixed amount for each unit, and the amount depends on
  the civilization's type of government.
- A unit may be given a destination order, which the computer then carries out, and this is so
  for a person's own units too. There can be other types of orders.
- A land unit is not amphibious unless its kind of unit says so. A unit may or may not be
  amphibious.
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
- The tiles are squares, because a grid of hexagons is difficult to draw. A unit can move and
  attack diagonally, and the idea being considered is that moving or attacking diagonally costs
  1.4 times as many action points.
- The idea of the civilization's pool is that a civilization cannot move all of its units in a
  turn, only so many, so that a player has to make good choices.
- A theme configures where the action points of a civilization come from. Each city that is
  built could come with a number of action points, and buildings could give action points too.

## Combat

- Each unit has hit points.
- Each unit has attack points and defense points.
- A unit heals a small amount every turn, and heals more inside a city.
- A land unit gets a defense bonus from the terrain the land unit is on.
- Air units have advantages.
- Units do not gain experience from fighting. There are no veteran units.
- Combat needs more discussion, and attacking a city needs planning in more detail.

## Turns

- Each turn represents one month of a standard year, in every theme, for now.
- A game has a starting year, which the theme decides.
- A game has no ending year, unless the person setting up the game asks for one, or a test wants
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
- The history record is summarized at the end of each year, then summarized again at a higher
  level every 20 years, and again every 100 years, the way monitoring data keeps less detail the
  further back in time it goes.

## Computer players

- The computer players are algorithms written for this game. No machine learning is involved.
- A computer player plays its civilization according to the civilization's traits ("Traits"),
  so different civilizations play differently.
- The details are to be discussed.

## Not decided yet

- What a city may not cover up.
- The situations in which a city adds action points to its civilization's pool or uses them up.
- How far a civilization sees units, and what gives it sight.
- How land becomes explored.
- How happiness works.
- The tech tree of classic.
- The categories that points are scored in.
- The types of government, and the upkeep in gold and in food that each sets for a unit.
- The list of traits, how a game gives a civilization its traits, and what makes traits change.
- The bonus of each civilization.
- Which kinds of attack and affront the history record counts.
- How big the impact of each kind of deed is, and how fast the impact declines over the 80 years.
- Whether there are spy networks.
- How research points are spent on technologies.
- The timeline of the technologies, and what the 500 years are counted from.
- Whether every world is a polar world, and what the other kinds of world are.
- How much food is enough for a city to grow, for how many turns in a row, and how citizens and
  workers relate.
- How big the defense bonus of each terrain is, and what the advantages of air units are.
- The diplomacy system.
- How far an aerial unit may travel, and what counts as its home.
- How combat is worked out from attack points, defense points and hit points.
- How a city is attacked, and how the units inside the city take part.
- How a unit leaves a city.
- Whether moving and attacking diagonally does cost 1.4 times as many action points.
- The priorities in a city's settings, and the improvements that can be built on tiles.
- How allies are made and lost, and how allies win together.
- What happens to what was already paid when a city switches to build something else.
- How the turn order is defined, how many turns a change of government skips, and the other
  requirements or penalties.
- What difficulty means.
- The rules for capturing a city, noted in `IDEAS.md`.
- Transport units, noted in `IDEAS.md`.
