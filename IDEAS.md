# Ideas

The user's ideas for later, recorded by Claude, with what each one would mean for the code. It's
also where the user asks what they want to do and what would need to change as a result, so each
idea notes its implications: what it touches, what it depends on, and what's still undecided.
Nothing here is finished: Claude removes an idea as soon as it's built, without being asked, and
trims the finished parts out of an idea that's partly built, keeping only what's still to do.
Ideas are added when the user asks.

Ideas are marked **HIGH PRIORITY** or **low priority** where the user has said so. Everything
else is unranked. Anything marked **In progress**, started but not finished, counts as a
priority without being marked one: when the user asks what to do next, name the unfinished work
first, before any idea that hasn't been started.

## Unranked

### Seeded replay: proving that a change altered nothing

The same seed and the same moves, played again, would always give the same game. A game could
then be recorded as its seed and its moves, replayed before and after a refactoring or a speedup,
and the two results compared, which would prove that the change altered nothing, or show the turn
where the games part. The user will deal with this when implementation starts.

What it would mean for the code:

- Every random draw in the game goes through one seeded source from the first model object on.
  No model object calls Python's own `random` functions directly, since one stray draw makes a
  replay differ.
- The computer players are part of the replay, so their algorithms either draw from that source
  too, or from a seeded source of their own so that a change to a computer player can't change
  what the rest of the game rolls.
- Nothing in a turn may depend on an order that Python doesn't promise, like the order of a set.
- The state of a game needs a form that two runs can be compared in.

Still undecided: what a recording holds, whether a computer player's moves are recorded or worked
out again on replay, how two states are compared, and whether a rule test should forbid direct
use of `random` outside the one source.

### Transport units, aerial and land based

Units that carry other units, both aerial and land based, to consider later.

What it would mean for the code:

- The model says that only one unit may occupy a tile at any time. A transport with a unit
  aboard puts two units on one tile, so the model would need to say how a carried unit counts.
- Loading and unloading would be actions, so they would spend action points, and a destination
  order would need to know whether a unit travels by itself or aboard a transport.

Still undecided: everything about how a transport works.

### A range for siege units

Consider giving the catapult and the cannon of classic a range of 2 tiles and the howitzer a range
of 3, so that they attack from further than the next tile. Eventually the howitzer's range may be
made much, much longer.

What it would mean for the code:

- The model says a unit attacks a unit on a tile next to its own, for now, and that an attack
  costs the straight or the diagonal base. A range would need a rule for which tiles are within
  it and what an attack from further away costs, and `Combat.problem_attacking()` would take the
  range of the kind instead of asking for the next tile.
- Whether a unit struck from 2 tiles away can strike back would need deciding.

### Tuning the growth rates of cities, and every other number

The turns a city needs to grow at each size have to be tuned for good gameplay. The same is true
of every coefficient in a theme. The tuning will eventually be done for caveman.

What it would mean for the code:

- The growth numbers are constants of the theme's city (`GROWTH_TURNS`, `GROWTH_FOOD` and
  `MAX_CITIZENS`), so tuning changes a theme and not the engine.
- Tuning needs whole games to judge by, so it waits for the computer players and the log of a
  game that the tests produce.

Still undecided: what good gameplay means in numbers, like how many turns a game of caveman
should take and how large its villages should get.

### FROM_CIV.md: how the rules differ from FreeCiv

A document called `FROM_CIV.md` that says how the rules of the game are possibly different from
FreeCiv in major ways, and what is unique about the rules. The top casually mentions that the
interface is different and links to the guide. The rest is mostly about the rules and the
definitions in abstract terms. Guides for the tech trees, the units and the nature of classic,
SciFi, fantasy, PlanetWars and caveman are then generated separately. Not to be done now.

What it would mean for the documents:

- The document is generated from the model, `GAME_RULES.md`, so it waits until the model is
  further along, and it links to `GUIDE.md`, which does not exist until there are screens.
- Saying how FreeCiv differs means looking at what FreeCiv's rules are, which Claude may do
  occasionally, without copying FreeCiv's design.
- The guides for each theme come from the theme files in `.claude/` and from the themes'
  Python classes, so a tool could generate the lists of units and technologies.

Still undecided: whether the document is kept current by hand or regenerated, and how the guides
for each theme are named.

### A map viewer for saved games, before the whole text UI

Before the whole text UI needs building, the test code can save game files for scenarios, and
the central component that shows the map can be built on its own. A test UI that uses only that
component could then step through the turns of a scenario and show what each turn looks like.
The work needs some discussion of the text UI, helps to make some early decisions about the
screens, and helps to judge later whether the computer players are good and whether what happens
in a game makes sense.

What it would mean for the code:

- The tests that play a scenario would save the game after each turn, or keep one file for each
  turn, so the scenario's saved games have to be kept somewhere and regenerated when the saved
  game's format changes.
- Stepping through turns needs either a file for each turn or a way to replay a game from its
  orders, which the idea "Seeded replay" above would give.
- The map component would be the first use of Textual, so Textual joins the dependencies then,
  and the rules for testing a screen join `.claude/TESTING.md`.
- The order in which the game is designed says that a screen is built only after a whole game can
  be played by the tests, and that the user walks Claude through each screen first. The viewer
  shows a game and takes no orders, and the user decides whether the viewer counts as a screen
  for that rule.

Still undecided: what the map component shows at each zoom level, how the viewer steps between
turns, and where the scenario files live.
