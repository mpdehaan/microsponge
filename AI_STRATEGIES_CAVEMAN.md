# How a computer player could win a game of caveman

Ideas for the algorithm that plays caveman as a computer player, written as a conversation between
the user and Claude about how each of them would try to win, and kept up to date as the code and
the ideas about the theme change. The model, `GAME_RULES.md`, says what the game is;
`.claude/THEMES_CAVEMAN.md` says what caveman is and holds its numbers; this file says how to play
it well. A file like this one is written for each theme, as `AI_STRATEGIES_<THEME>.md`. The
computer players are algorithms written by hand in this project, never machine learning, and
never Claude playing the game.

## What the computer player is for, first

- The first goal is a test script in which several computer players play a game of caveman
  against each other, starting with 2 players and a turn limit, with no person and no screen.
- The script shows whether an algorithmic player can win, is efficient, and does not think too
  long on a turn.
- Winning, for now, means conquering the other side: a civilization has lost when its last city
  is taken, and the game ends when one civilization is left.

## What the game rewards, in caveman's numbers

Everything below follows from the model and from caveman's numbers, and changes when they do.

- A civilization starts with one settler and 50 currency. Building a city is the only way to
  earn anything: a city of one citizen gives 2 currency and 2 food from its worked grassland
  tile plus 2 food the village itself produces each turn, 1 research point, and 2 action points
  to the civilization's pool, which is 4 on its own.
- Every unit costs 1 currency and 1 food each turn to support. A city of one citizen pays for
  about two units out of its own income, so an army is paid for by cities, and a civilization
  with 0 currency for 50 turns in a row loses. Food matters the same way: citizens eat 1 food
  each, and a city grows only while the civilization holds 5 food for each citizen of the city.
- Research is slow: 1 point per city per turn, and nothing else, until the great cave painting.
  Clubs, which allows the warrior, takes 10 turns with one city and 5 with two. Discipline, which
  allows the barracks and then captain caveman, takes 40 points. Fire, for the watchtower, takes
  20, and the watchtower also needs flint within the borders.
- A unit has 2 action points a turn, so it moves 2 grassland tiles, and the pool allows 3 unit
  moves a turn with one city and 4 with two. The two starting positions of the test world are
  about 30 tiles apart, so an army takes about 15 turns to arrive, longer through forest.
- Fights are long: a warrior needs 5 attacks to kill a warrior, and takes a fifth of its attack
  back each time. Captain caveman kills a warrior in 2 attacks and a captain caveman in 4. A unit
  inside a city heals 3 hit points a turn, outside 1. Behind a watchtower a warrior defends with
  3 instead of 2, so a warrior needs 7 attacks to kill it.
- A city holds 3 units inside, and only the units inside defend it. A city with no unit inside
  is taken by walking in, and the taker gets the buildings. The angry bird cannot take a city.
- A settler costs a citizen, and a city of one citizen cannot build one; a city grows a citizen
  after 5 turns of enough food, then every 10.

## How Claude would try to win

The player is a list of rules tried in order each turn, a priority list, with no search ahead,
so that a turn costs about as long as walking the units and cities once.

1. **Found the city at once.** On turn 1 the settler builds the city where it stands; searching
   for a better tile costs turns that nothing repays.
2. **Grow the economy before the army.** The first builds are what makes more income: let the
   city grow to 2 citizens, build a settler, and found a second city on open grassland a city
   radius away, in the direction of the enemy if the ground allows, so that the border is closer
   to the enemy and the second city doubles research and action points. A third city is worth
   it while the turn limit is far off.
3. **Research in this order:** clubs, then discipline, then fire. Clubs gives the warrior, the
   first unit that can fight. Discipline gives the barracks and captain caveman, which wins
   fights twice as fast and holds a city against warriors. Fire gives the watchtower, worth
   building only when flint is within the borders. Agriculture, the granary and farms are for a
   player that is behind on food, which the test world's grassland rarely causes.
4. **Keep one unit inside each city at all times.** An empty city is lost to any unit that walks
   in, and a unit inside heals fast. The defender is the unit with the best defense available,
   captain caveman when there is a barracks.
5. **Build the army only as fast as the income carries it.** Never let support costs exceed
   income less a margin: with 1 currency of support per unit, a civilization with two cities of
   one citizen each can afford about three units beyond its defenders. A player that goes
   bankrupt loses to the clock.
6. **Attack with a group, never alone.** Gather three attackers next to the own city, declare war,
   and walk together toward the enemy city, each unit 2 tiles a turn. A lone warrior is killed
   by the defenders' strike back and by the city's healing. On arrival, stand next to the city
   center, attack with every unit every turn, and keep attacking the same city until no unit is
   inside, then walk in with a unit that can take cities. Units below half their hit points
   step back and heal for a turn when the group can spare them.
7. **Replace losses from the nearest city.** The city nearest the front builds warriors, or
   captain caveman when it has a barracks, as long as the income allows; the other cities grow
   and build settlers.
8. **Pick research every turn and never leave a city idle.** The game forces a pick, and a city
   with an empty queue wastes turns. When nothing above wants anything, the city builds a
   warrior if the income allows and a settler otherwise.

## How the user would try to win

- The user would use positional strategy, and thinks everyone else should as well: cities need
  to be close by, if they can be, while an empire is built. Another civilization blocking out
  the land is a little bad for that civilization's reputation; the user may attack over it, but
  mostly attacks when the attack can be won, remembering that all sides have incomplete
  information under the fog of war and may not have seen all the terrain yet.
- If the user thought they were being boxed out, or saw a terrain gap closing that cut them off
  from part of the map, the user would try to build a satellite city later, sending a quick
  settler through to found a city there, to keep expanding: military action means not investing
  in the economy, and it is easy to get behind in technology.
- The user would watch the workers wherever an improvement can be made, and the work priorities
  of the citizens, and would weigh carefully whether building a city to get a special resource
  is worth its tradeoffs.
- The user would not anger civilizations more powerful than their own, inferring their power
  from what can be seen, with more to go on once diplomacy technology and maybe spy capabilities
  exist.

## How the computer players differ from one another

The user wants variance programmed in, so that no two computer players are the same player:

- Each computer player has feelings: a reputation it keeps of who has wronged it, which
  motivates it in a few directions.
- Some computer players are very logical and strategic and simply try to be the best player.
  Some tend to a campaign against one other civilization and focus their attention there, which
  should keep the game from stalemate unless each is focused on another in a tangled circle.
  Some try to be peaceful and build up larger armies. Others have other strategies, but never
  dumb ones.
- The user suggests an odd number of civilizations, three at first, so that two equal players
  do not simply trade blows.
- A player's personality is a handful of numbers on one player class, the civilization's
  traits: how much it values expansion against the army, how far below a sure win it will
  attack, how long it remembers a wrong, how strongly it prefers one enemy, how much it values
  science and research, how much it tries to be nonviolent when it can dominate by investing
  first, and how much it wants to conquer land rather than stay smaller and defensible or keep
  a large military. "Logical and strategic", "campaigner" and "peaceful builder" are settings
  of those numbers, which may more or less be randomized when a game starts.
- No player is ever lazy: every one tries to win, each by a different strategy. One strategy
  looks at what the player knows about the map and adapts to it.
- The players of each theme are subclasses of a common player, so the flavors and the ideas
  carry over while the decisions suit each theme; caveman has less technology than the others.
- The user is open to really clever strategies from Claude, and eventually games of players
  against each other will be used to improve every strategy and make the players less
  predictable.

## What Claude expects to go wrong, and how to see it

- Two players running the same rules reach the same army at the same time and trade attacks for
  many turns: the log should show how many turns a siege takes and how many units each side
  loses, so that the rules, or the numbers in caveman, can be tuned.
- A player that expands too much is rich but defenseless when the other arrives early; a player
  that attacks early with warriors loses them against a healing defender. The balance between
  rules 2, 5 and 6 is the whole game, and the first version will pick fixed thresholds that the
  log will show to be right or wrong.
- The action point pool is small: with 4 plus 2 a city, a player with many units cannot move them
  all, so the army should be as small as wins, and the rules should spend the pool on the units
  at the front first.

## How to measure a game

- The log records, for each turn, what each civilization built, researched, moved and attacked,
  with the outcome of each attack, and what each civilization holds, so that a person can read
  how the game went and a test can check that it went the way the rules intend.
- A game is measured by who won and in how many turns, how long each turn took to compute, how
  many units each side lost, and when the first city was founded, the first warrior built, the
  war declared and the first attack made.

## What the first script shows

- The first script runs up to 100 turns, with no failure criteria yet, and prints a summary
  report of every computer player: when it built each of its cities, when it researched each
  technology, and how many of each kind of unit it made and lost. "Good", for now, means that
  some side is actually going to win.
- The script also notes the tuning that would make the game more fun: fewer turns between the
  variety of things there are to do, and not too many action choices on any one turn.

## What is built first, in order

The damage roll with dice and caveman's new numbers, then the fog of war and the view a player
reads, then the players with their traits, then the simple map generator, the scripted game and
its report.

## Not decided yet

- The dice each unit of caveman rolls, and the new hit points of caveman's units.
- The vision radius of a city.
- How the traits are randomized when a game starts, and in what ranges.
