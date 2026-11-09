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

### The rules for capturing a city

How a city is captured is undetermined and is to be discussed.

What it would mean for the code:

- It touches what the model already says about cities: a city is 5 by 5 tiles, units of another
  civilization may enter its city radius only when the two are friendly or at war, and many units
  can surround it.
- A captured city changes which civilization owns it, so whatever a city holds, its buildings
  and its production queue, needs a rule for what the new owner gets. The model already says two
  things: a world wonder is captured with its city, and where the captured city's radius
  overlaps another city's radius, the older city keeps the tile, for now.

Still undecided: everything about how a capture happens.
