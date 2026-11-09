# The theme called caveman

What the user has decided about caveman, the tiny, silly theme that the tests play, and the
numbers Claude chose for it. The model, `GAME_RULES.md`, says how the game works for every theme
and what a theme may decide; this file holds what caveman itself chooses. `CLAUDE.md` imports this
file, so it's in force in every session. `.claude/TESTING.md` says what caveman is for.

## What the user has said

- Caveman is being completed first, before classic, so that the engine has complete tests.
- Caveman is only to have all the relationships and features it needs to be complete, simple
  and testable. Caveman can also help to build the early text UI.
- Claude picks good constants for caveman without asking, and asks where help is needed.
- Caveman is kept simple, and has no cows.
- Caveman has one strategic resource, flint, which Claude put in the mountains. Flint, with
  the technology called fire, is required to build the watchtower, which boosts the defense of
  every unit inside its city by 25 percent. City walls, if they come later, give a further
  boost, and will be discussed with the tests for classic.
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

## The numbers Claude chose

Each line is attack, defense and hit points, then the cost and the turns to build. Every unit
costs 1 currency and 1 food to support each turn and has 2 action points.

- settler: 0, 1, 10. 10 currency and a citizen, 6 turns.
- warrior: 6, 2, 20. 10 currency, 3 turns. Requires clubs.
- worker: 0, 1, 10. 10 currency, 3 turns. Requires agriculture.
- captain caveman: 12, 2, 40. 20 currency, 6 turns. Requires a barracks.
- slingshot caveman: 4 against land and sea units and 8 against air units, 2, 20. 15 currency,
  3 turns. Requires clubs.
- raft: 4, 1, 10. 10 currency and 10 wood, 4 turns. Requires a harbor.
- angry bird: 4, 0, 10. 10 currency, 2 turns.
- barracks: 30 currency, 5 turns, 1 currency to support. Requires discipline, which takes 40
  research points.
- harbor: 30 currency, 5 turns, 1 currency to support. Requires no technology.
- forest: gives 1 wood, and costs 2 to move into.
- watchtower: 20 currency, 5 turns, 1 currency to support. Requires fire, which takes 20
  research points, and flint within the borders. The 25 percent raises the defense of a unit
  inside from 2 to 3, rounding up, which Claude chose.
- bison: 1 more food from the tile. elephants: 2 more food.
- The test world has flint on its one mountain tile, inside the second civilization's first
  city radius, and bison and elephants on grassland far from both civilizations' first cities.

## Balance

`tools/balance.py caveman` shows how many attacks each unit needs against each other unit. With
the numbers above, a warrior needs 5 attacks against a warrior and 10 against captain caveman,
and captain caveman needs 2 against a warrior and 4 against captain caveman. Outside what the
model asks of balance ("Combat"): captain caveman finishes a settler, a worker or a raft in one
attack, and slingshot caveman and the angry bird each need 20 attacks against captain caveman,
which is what being weak against land and super weak come to.
