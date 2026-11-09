# The theme called classic

What the user has decided about classic, the theme that models historic earth in the style of a
civilization game. The model, `GAME_RULES.md`, says how the game works for every theme and what a
theme may decide; this file holds what classic itself chooses. `CLAUDE.md` imports this file, so
it's in force in every session. Each theme gets a file like this one, named after the theme, and
these files may later be used to write the guide for people who play the game.

Nothing is added here that the user hasn't said: no unit, civilization, building or technology of
classic is made up (`.claude/COMMUNICATION.md`, "Who decides what").

## Resources

- The primary resource of classic is currency, which is what the user first called gold.
- The other resources of classic that are collected are food, wood, stone and metal.
- All the metal resources are lumped together and called metal, the way Civilization II does
  it, which was the user's choice. Metal is usually found in mountain tiles, and a mine is the
  improvement that increases the amount of metal a tile produces. A mine does not block any
  strategic resource from being accessed.
- Bronze just needs metal: a bronze age military unit needs metal, not the components of
  bronze.
- Iron is a strategic resource, like in Civilization II ("Resources" in the model): when iron
  is within the borders of a civilization, the civilization is able to build all the units that
  require iron, and the iron is not consumed.
- Iron is relatively common in mountain areas.
- A legion, which is a unit, needs the resource iron, and also costs an amount of metal.
- Metal is mined, goes into what the civilization holds and is consumed there by what is built
  with metal. Metal is a resource from the mountains that have metal, which is not all
  mountains, and a mine on such a tile gives more. A mountain tile never runs out of metal.
- The mountains that have metal are marked by a terrain bonus, which cannot be removed for
  now, because a worker cannot blow away a mountain. In the code the terrain bonus is the class
  `MetalDeposit` in `src/microsponge/themes/classic/terrain_bonuses.py`, shown as "metal
  deposit", to tell it from the resource metal; Claude chose that name and the user has not
  confirmed it. How much metal the bonus gives is not decided.
- Stone is a resource from mountains, collected like metal. Almost nothing is going to use
  stone in classic unless something is thought of: stone may be a resource that is no longer
  needed after the stone age is gone, and civilizations may have ages that make some earlier
  steps not required, kept limited for now.
- Gold and uranium are other mountain resources, as placeholders to start with. Other types of
  terrain may have silk. FreeCiv may be looked at for ideas. Gold, uranium and silk are
  strategic resources, because every resource that is not food, metal or wood is, for now.
- Water tiles inside a city may provide extra fish.

## Terrain

- Desert tiles cannot produce food.
- Once irrigation is discovered, a desert tile next to water can be converted to grassland, and
  then produces 1 food. The water can be a river tile or a lake tile, but not an ocean tile,
  because the ocean is salt water.
- So classic has at least these terrains: desert, grassland, mountains, river, lake and ocean.

## The tech tree

The tech tree of classic must absolutely include these, and the user will talk about what else:

- iron working
- literacy
- fortification, which allows city walls
- bronze working
- computers
- industrialization
- sanitation
- irrigation
- the internet

## Units

Classic must absolutely include these units. What each can do is for a later discussion, and the
user will talk with Claude about Claude's suggestions for other units to fill in between them:

- settler
- scout
- warrior, a basic unit
- phalanx
- legion
- catapult
- knights
- cannon
- fighter plane
- bomber
- stealth bomber
- cruise missile
- nuclear missile
- drone
- anti-missile platform
- anti-air platform
- musketeer
- infantry
- howitzer, added to match the cannon

What the musketeer and the infantry require in the tech tree is left undefined for now.

Cannons and catapults do not strike back when attacked, and neither does the howitzer. Every
other unit of classic strikes back, unless the user says otherwise.

The catapult, the cannon and the howitzer all bypass city walls, and each has a defense of just 1
and a hit point of just 1.

## Balance

The user establishes the balance of the units in conversation, as rough numbers, and wants
Claude's help to balance them (`.claude/COMMUNICATION.md`, "Who decides what"). No numbers are in
the code of classic yet.

- A legion is about 4 times stronger than a warrior.
- A phalanx is in between the warrior and the legion: a phalanx has 2 times the hit points of a
  warrior and 2 times the defense.
- A legion is well rounded, and has enough hit points that a phalanx must attack a legion twice.
- A musketeer is 5 times more powerful in attack and defense than a legion.
- Infantry is 5 times more powerful than a musketeer.
- A cannon is 3 times more powerful than a catapult, and a howitzer 3 times more powerful than
  a cannon. These are the first numbers in the code of classic: Claude gave the catapult an
  attack of 6, so the cannon has 18 and the howitzer 54, to be balanced with the rest of
  classic's numbers later. `make balance THEME=classic` shows the howitzer finishing most units
  in one attack, which is meaningless until the other units have numbers.

## World wonders

The world wonders of classic are these, and that's it for now:

- the pyramids
- the great wall
- the manhattan project, which is required to unlock nuclear weapons
- the library of alexandria
- the seven wonders of the world as commonly defined: the great pyramid, which is the pyramids
  above, the hanging gardens of babylon, the statue of zeus at olympia, the temple of artemis
  at ephesus, the mausoleum at halicarnassus, the colossus of rhodes and the lighthouse of
  alexandria

## Space

- A city of classic can launch up to three satellites into the space around Earth, which
  provide bonuses ("Space" in the model). What the bonuses are, and what launches a satellite,
  is not decided.

## Buildings

- The research points of a civilization in classic are based on the number of its cities, and on
  its libraries, colleges and research centers. So classic has at least these buildings: the
  library, the college and the research center.
- A bank increases the income in currency of its city by 20 percent each turn, for now.
- City walls are a building, researched by the technology called fortification, and require
  stone. Claude chose a cost of 30 stone and a defense boost of 50 percent for the units inside,
  to be balanced later. City walls are bypassed by the catapult, the cannon and the howitzer.

## Not decided yet

- Whether land starts out unexplored in classic.
- Which other units need iron.
- What uses stone, and whether civilizations have ages.
- How much metal a metal deposit gives.
- How much metal a legion costs.
- Who converts a desert tile to grassland, and how long the conversion takes.
- The rest of the tech tree, and how its technologies depend on each other.
- What each unit can do, and the other units.
- The civilizations a player chooses from.
- The other buildings.
