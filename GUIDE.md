# The microsponge guide

This is the guide for people who play microsponge: how the game works in every theme, in plain
words. The themes, each a kind of game the engine can play, have a guide page each, which says
what that theme is like and ends with the tables of its units, buildings, world wonders and tech
tree, generated from the code:

- [GUIDE_CAVEMAN.md](GUIDE_CAVEMAN.md), the tiny, silly theme the tests play
- [GUIDE_CLASSIC.md](GUIDE_CLASSIC.md), historic earth in the style of a civilization game
- [GUIDE_SCIFI.md](GUIDE_SCIFI.md), many planets, space between them and warp portals
- [GUIDE_FANTASY.md](GUIDE_FANTASY.md), dragons, magic and the astral plane
- [GUIDE_PLANETWARS.md](GUIDE_PLANETWARS.md), every civilization alone on a planet of its own

**microsponge is in a very early state, and there is nothing to play yet.** The rules here are
the rules the engine already plays by in its tests; the screens come later, and this guide gains
a chapter on each screen as it arrives. The full, exact rules are in [GAME_RULES.md](GAME_RULES.md),
and anything not in this guide yet is there.

## The shape of a game

A game is played by civilizations, each played by a person or by a computer player, on a map of
square tiles. Each civilization starts with one settler unit and nothing else, and builds its
first city with it. Cities collect resources from the tiles around them, grow citizens, build
units and buildings, and research technology. Units move about the map, explore, build
improvements like farms and roads, and fight.

The civilizations play in turn, one after another, and a turn ends when its player says so. A
game has no last turn unless the person setting up the game asks for one. A civilization has lost
when its last city is taken, or when it has been bankrupt for 50 turns in a row, and when one
civilization is left standing the game is over.

## The map

The map is a grid of square tiles, and a unit can move and attack diagonally as well as straight.
Each tile has a terrain, like grassland, forest, mountains or water, and the terrain decides
what the tile gives when a city works it, what it costs a unit to move onto it, and who can be
there: land units stay on land, naval units stay on water, and air units go over both. A theme
may have terrain that land units cannot cross at all, and some terrain cannot be built on.

Columns wrap from east to west, so that the map is a cylinder, and nothing goes off the top or
the bottom. A map can be very large and a game can have more than one world; in a theme with
space, each world is a planet.

Some tiles carry more than their terrain: a terrain bonus, like a herd of bison on grassland,
gives more of a resource when the tile is worked, and a strategic resource, like iron in the
mountains, lets a civilization that has the tile within its borders build the units and
buildings that require it. Nothing on a tile ever runs out.

## Cities

A city has two parts. The city center is the 5 by 5 tiles in the middle, and the city radius is
the 15 by 15 tiles that belong to the city, with the center in the middle. The center tile has
to be land, at least 13 of the 25 tiles of the center have to be land, and the radii of two
cities can never overlap, so a settler cannot build a city within reach of another city's land.

A city has citizens, and each citizen works one tile of the city radius outside the center,
taking the tile that gives the most food unless the player sets a priority for another resource.
A city grows a citizen when the civilization has held enough food for each of the city's
citizens for enough turns in a row, and holds at most 10 citizens.

A city builds one thing at a time, from a queue the player fills: units, buildings and world
wonders. The cost is paid a part each turn over the turns the thing takes, so that switching to
something else part way has a natural cost, and a part of what was paid comes back. A building
can require a technology, a strategic resource, another building, or water next to the city
center, and a world wonder can be built by one civilization only: a city that is beaten to it
loses what it paid. A settler uses up a citizen of the city that builds it, so a city of one
citizen cannot build one.

Units can go inside a city, up to a number the theme sets, and only the units inside defend it.
A city with no unit inside cannot be attacked at all: a unit of a civilization at war with its
owner, of a kind that takes cities, takes it by walking in, and gets its buildings, while
everything the city was building is lost.

## Resources and the bank

A civilization holds all of its resources in one place, which this guide calls the bank: every
city adds to the bank and spends from it, and no city holds anything of its own. One resource
is the primary resource, called currency. Each turn the cities collect what their worked tiles
give, the citizens eat food, and every unit and building is paid for in currency, and in food for
units. A civilization that ends a turn with no currency is bankrupt, can build nothing that turn,
collects less, and loses the game after 50 bankrupt turns in a row.

## Research

A civilization researches one technology at a time, and must always have picked one while any is
left to research. Each city gives research points every turn, and so do some buildings; when the
points reach what the technology takes, the civilization knows it, and what the technology allows
can be built. Points past what a technology takes are lost, and once everything is known the
points become currency. A technology can require other technologies, and the tech tree of each
theme is in its guide.

## Action points

Everything a unit does costs action points, written AP, from two pools at once: the unit's own,
which is small, and the civilization's, which the theme sets and each city adds to. Both refill
every turn. Moving one tile costs 1, or more onto hard terrain like mountains or forest;
attacking costs 1; building a city, starting an improvement, and going into or out of a city each
cost 1. Choosing what to build, choosing what to research, setting a city's priority, declaring
war and ending the turn are free. Because the civilization's pool is small, a civilization cannot
move every unit every turn, and has to choose.

## Units

Every kind of unit is defined by its theme: what it costs to build and to support each turn,
how many turns it takes, what technology, building or strategic resource it requires, how many
action points it has, and how it fights. The guide of each theme lists them. A worker unit builds
improvements on tiles, like a farm, over a number of turns, and some work changes the terrain.

A unit is a land unit, a sea unit, an air unit or a space unit. The class decides where the unit
can be and whom it can hit: by default a land unit or a sea unit cannot hit an air unit, and a
kind of unit that can, like a slingshot, says so. A unit that cannot hit another cannot defend
against it either.

## Fighting

An attack is made on a unit on the next tile, or on a city whose center is next to the attacker,
and only on a civilization the attacker's own is at war with. The attack is a roll of dice: every
kind of unit has attack dice, written the tabletop way, like 2d4 for two four-sided dice or
2d6+4 for two six-sided dice and 4 more, and some kinds roll extra dice against one class of
unit, like a slingshot against air units.

The defender's armor class takes some of the roll away. An armor class is a number from 10 down,
and lower is better: 10 is no armor and lets the whole roll through, every point below 10 takes
10 percent off, rounded up, so that 5 lets half through, and 0 or better lets through only the
chip damage of 1 that every attack does. What is left comes off the defender's hit points, and a
unit whose hit points reach 0 is gone. Nothing moves onto the tile of a destroyed unit.

A unit that is attacked strikes back, unless its kind does not or cannot hit the attacker's
class: it rolls its own dice, half of the roll goes through the attacker's armor, and the attacker
takes the rest. When a city is attacked, the unit inside with the best armor class is the one
hit, and the unit inside with the strongest dice that can hit the attacker is the one that
strikes back. Defensive buildings, like a watchtower or city walls, make the armor class of every
unit inside better, and some kinds of unit, like a catapult, ignore city walls.

Units heal every turn, a little outside a city and more inside one, up to the hit points of a
whole unit at their level.

## Levels and experience

Every unit starts at level 1 and can reach level 20. A unit gains a little experience for every
attack it makes, half as much for every attack it survives, and more for a kill, whether it
killed attacking or struck an attacker down: the worth of the kind it killed, which is less for
weaker kinds, plus the level of the unit killed. Level 2 comes at 10
experience, level 3 at 30, level 4 at 60, and so on up to level 20 at 1900. Each level adds a few
hit points, a small share of the kind's hit points that the theme sets; at levels 5 and 15 the
armor class gets 1 better; and at levels 10 and 20 every roll gets 1 more. A level 20 unit is
about half again as strong as a level 1 unit of the same kind, no more. A unit that goes up a
level keeps its wounds and gains the new hit points on top. Some buildings, like a barracks,
start the units built in their city at level 2.

## Diplomacy, visibility and computer players

Civilizations are at peace until one declares war on another, and a unit may not enter the
territory of a civilization its own is not at war with or friendly with. The fog of war hides
units: a civilization sees only what is within the vision of its units and cities, and remembers
the terrain it has seen. The computer players play by the same rules, see only what their units
see, and each has a personality of its own, so that no two play the same way. More on all of
these arrives with the screens.
