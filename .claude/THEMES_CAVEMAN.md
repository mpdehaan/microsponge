# The theme called caveman

What the user has decided about caveman, the tiny, silly theme that the tests play, and the
numbers Claude chose for it. The model, `GAME_RULES.md`, says how the game works for every theme
and what a theme may decide; this file holds what caveman itself chooses. `CLAUDE.md` imports this
file, so it's in force in every session. `.claude/TESTING.md` says what caveman is for.

## What the user has said

- Caveman is being completed first, before classic, so that the engine has complete tests.
- Caveman is made very good first, before the engine moves on to other themes, while the
  engine stays abstract: nothing in the engine is written for caveman alone.
- Flint may be something a civilization has to expand toward, about 15 tiles at most from the
  first city radius, as the model says of strategic resources ("The map").
- Caveman is only to have all the relationships and features it needs to be complete, simple
  and testable. Caveman can also help to build the early text UI.
- Claude picks good constants for caveman without asking, and asks where help is needed.
- Caveman is kept simple, and has no cows.
- Caveman has one strategic resource, flint, which Claude put in the mountains. Flint, with
  the technology called fire, is required to build the watchtower, which boosts the defense of
  every unit inside its city. City walls, if they come later, give a further boost, and will be
  discussed with the tests for classic.
- Bison and elephants are terrain bonuses on grassland, which give more food when the tile is
  worked, and are required for nothing.
- The units are the settler, the warrior, the worker, captain caveman, slingshot caveman, the
  raft and the angry bird.
- Captain caveman is twice as powerful as the warrior, costs something like twice as much and
  has twice as many hit points. Captain caveman requires the building called barracks, and the
  barracks requires the technology called discipline.
- The raft is the naval unit. A raft can attack, and is super weak. A raft can attack units on
  water and units on land, and cannot attack air units. A raft requires wood, which is obtained
  from forest. A raft can take over a city. A raft requires a building called harbor, and a
  harbor requires a water tile next to the city center.
- The angry bird is the air unit. An angry bird is super weak and cheap to produce, and cannot
  take over a city.
- Slingshot caveman is like a caveman who can attack air units: very good against air units and
  weak against land units, with a different attack value against air units.
- Caveman has a terrain of its own, the tarpit: land units cannot cross a tarpit or build on
  one, a tarpit provides no resources, and a tarpit cannot be removed.
- A worker can cut the trees of a forest tile, which makes the tile grassland, where a farm
  can be built. Cutting the trees takes 3 turns, which Claude chose.
- A technology called agriculture allows the granary and the worker, and what the user first
  called farming is agriculture.
- The watchtower supplies 5 more Command each turn, once Command is built: the points that
  orders for armies and divisions take beside Policy ("Priorities and the helper AI" in
  the model).
- The land starts out unexplored in caveman, so that the tests cover exploring. Caveman has no
  technology that ends the fog of war; the tests add one to a later caveman where they need it.

- A game of caveman of 400 turns is far too long for a game this simple: the user wants
  games over in about half the turns, and the balance tuned toward that first, in this
  order: research, then costs, then the rest.
- The last technology should be researched toward the end of a game, so research costs go
  up.
- Units and buildings should cost the resources a civilization collects, like wood and
  stone, and not only currency, because the bank of currency grows far too large.
- The buildings that technologies allow should give more advantages, so that research is
  worth what research costs, and more buildings should require resources.
- The user suggests a new resource, ivory, which comes from elephants and can be used
  after researching a technology called sewing. Sewing makes a civilization's cities grow
  faster. The details are not decided.
- City walls, if caveman has none yet, require a technology called carpentry, which
  requires forests. How carpentry requires forests is not decided.
- The user asked Claude to recommend other technologies for caveman, and chose from Claude's
  recommendations:
  - Clubs stays, and caveman's warrior is renamed the clubber.
  - Fire stays.
  - Agriculture allows only the worker and the farm, and no longer the granary.
  - Sewing and carpentry, the user's own ideas, go in, and leadership and discipline stay.
  - Claude's shamanism goes in as a technology called church of the cave bear.
  - Claude's barter goes in, though the user is a little worried about adding to the income
    of currency.
  - Claude's star lore goes in as a technology called astrology, which requires church of the
    cave bear and leadership.
  - The arrangement of rocks makes the upkeep of every unit 1 currency less.
  - Claude's stone tools and pottery were not taken.
- The upkeep of a unit in currency goes up, to maybe 5, and the cost of every unit goes up by
  5 currency.
- A game of caveman is tuned so that one civilization usually remains by about turn 200, and
  the highest score wins when more than one remains at the last turn.
- Ivory is not banked: like flint and poppies, a civilization has ivory or does not, and has
  it while elephants are within its borders and it knows sewing. Stone and wood are still
  collected and banked.
- To stop currency piling up: a working citizen earns 1 currency instead of 2, research past
  the end of the tech tree no longer turns into currency, and every building costs 2 currency
  of upkeep instead of 1.
- That left caveman too poor to fight, so a unit's upkeep is 2 currency instead of 5. Units
  eat no food: each city stores its own food and grows a citizen when the store is full.
- The user wants to know which buildings and world wonders give no benefit, with suggestions
  of what each should do.
- Caveman has a resource called poppies, and a unit called the wild clubber, which can be
  built after learning church of the cave bear, and is about twice as good as the clubber.
  Captain caveman is half again better than the wild clubber.

## The numbers Claude chose

These choices of Claude's fill the gaps the user left in the decisions above, for the user to
confirm or change after seeing a game:

- The granary requires sewing, since agriculture no longer allows it.
- Carpentry requires nothing for now, and city walls cost wood, which only forest gives, which
  is how carpentry requires forests until the user says otherwise. City walls: 20 currency,
  20 wood and 30 stone, 6 turns, 1 currency to support, armor class 1 better, and walls.
- Church of the cave bear requires fire and leadership, and allows the cave bear shrine: 30
  currency and 10 stone, 5 turns, 1 currency to support, 2 research points.
- Barter requires sewing and leadership, and allows the trading post: 30 currency, and ivory
  within the borders, 5 turns, 2 currency to support, 10 percent more currency in its city, which is less
  than the 20 percent Claude first suggested, because of the user's worry about income.
- Sewing makes every city of the civilization grow a citizen 1 turn sooner, and elephants
  provide ivory within the borders once the civilization knows sewing.
- Leadership requires fire, and discipline requires leadership.
- Astrology allows the arrangement of rocks.
- Research points: clubs 15, fire 15, agriculture 20, sewing 50, carpentry 50, leadership 50,
  discipline 90, church of the cave bear 90, barter 100, astrology 200.
- Unit upkeep is 2 currency, and no food. A village stores 10 food for each citizen; the
  granary and sewing each take 2 off each citizen's share. Unit costs: settler 15 currency, clubber 15,
  worker 15, slingshot caveman 20, angry bird 15, raft 15 and 10 wood, wild clubber 30,
  captain caveman 40.
- Poppies are a strategic resource on grassland, and the wild clubber requires poppies within
  the borders beside church of the cave bear: 4d4, armor class 8, 20 hit points, worth 4, 5
  turns. Captain caveman is now 6d4, armor class 8, 30 hit points, worth 6.

Each line is the attack dice, the armor class, the hit points and the experience worth, then the
cost and the turns to build. Every unit costs 2 currency to support each turn and has
2 action points. A level adds 2 percent of the kind's hit points, rounded down over the levels
gained, so a level 20 warrior has 13 hit points and a level 20 captain caveman 27.

- settler: no attack, 10, 5, worth 1. 10 currency and a citizen, 6 turns.
- clubber, which was called the warrior: 2d6, 8, 10, worth 2. 15 currency, 3 turns. Requires clubs.
- worker: no attack, 10, 5, worth 1. 10 currency, 3 turns. Requires agriculture.
- captain caveman: 4d6, 8, 15, worth 4. 40 currency, 6 turns. Requires a barracks.
- wild clubber: 3d6, 8, 13, worth 3. 30 currency, 5 turns. Requires church of the cave bear
  and poppies. Claude read "twice as good" as twice the attack times the hit points of the
  clubber, and captain caveman as half again that of the wild clubber.
- slingshot caveman: 2d4, and 2 extra dice against air units, 8, 8, worth 2. 20 currency,
  3 turns. Requires clubs.
- raft: 2d4, 9, 8, worth 1. 15 currency and 10 wood, 4 turns. Requires a harbor.
- angry bird: 2d4, 10, 6, worth 1, 6 action points and a vision of 7, because the user
  wants air units to fly a lot. 15 currency, 2 turns.
- barracks: 30 currency, 5 turns, 1 currency to support. Requires discipline, which takes 40
  research points. The barracks starts the units built in its city at level 2, which the user
  decided for caveman as for classic.
- harbor: 30 currency, 5 turns, 1 currency to support. Requires no technology.
- leadership: a technology the user asked for, which the chieftain's hut requires. It takes 25
  research points, which Claude chose, between fire at 20 and agriculture at 30. Caveman now
  has five technologies: clubs, agriculture, leadership, discipline and fire.
- chieftain's hut: 20 currency, 4 turns, 1 currency to support. Requires leadership. The
  chieftain's hut gives its civilization 2 more Policy each turn. The user asked for the
  building, for one to a city, as with every building, and for a reasonably small amount,
  and Claude chose 2: caveman gives a civilization 4 Policy, each village 2 more, and the
  arrangement of rocks 1 more.
- Command: caveman gives a civilization 3 Command and each village 2 more, which Claude
  chose, and the watchtower 5 more, which the user chose. A village that builds nothing adds
  1 Policy and 1 Command, which the user proposed for every theme.
- Armies and divisions: a civilization may have 1 army for every 4 villages and 1 division
  for every 2, rounding up and always 1 of each, which Claude chose because caveman's
  civilizations are small.
- Orders cost what the engine says for the first test: a policy order 1, a command order 1
  for each unit, and an order for one unit alone 2 more.
- forest: gives 1 wood, and costs 2 to move into.
- watchtower: 20 currency, 5 turns, 1 currency to support. Requires fire, which takes 20
  research points, and flint within the borders. The watchtower makes the armor class of every
  unit inside 1 better, which Claude chose.
- bison: 1 more food from the tile. elephants: 2 more food.
- The test world has flint on its one mountain tile, inside the second civilization's first
  city radius, and bison and elephants on grassland far from both civilizations' first cities.

## Balance

The user finds 5 warrior-to-warrior battle turns far too long, and wants units to die in a
reasonable number of attacks, usually 3 at most rather than the 8 that was possible: evenly
matched units kill one another in a few attacks, and unmatched units often fall in one unless
fortified.

`tools/balance.py caveman` shows how many attacks each unit needs against each other unit on
average rolls. With the numbers above, no fight between level 1 units takes more than 4
attacks: a clubber needs 2 against a clubber and 3 against captain caveman or the wild clubber,
captain caveman needs 1 against a clubber and 2 against captain caveman, and slingshot caveman,
the raft and the angry bird need 4 against captain caveman.

City defense, which the user asked to be stronger: every village makes the armor class of every
unit inside 1 better with no building, the watchtower 2 better, and the arrangement of rocks 1
better in its village.

World wonders, which the user found gave too little: the great cave painting costs 120
currency over 16 turns and gives 4 research points, 2 Policy and 10 percent more currency in
its village; the arrangement of rocks costs 60 currency and 30 stone over 16 turns and gives 2
currency, 3 Policy, 3 Command, 1 better armor class in its village and 1 currency off every
unit's upkeep.
