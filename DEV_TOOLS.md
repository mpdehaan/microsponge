# Developer tools

The tools for looking at how the game plays, for tuning. Each tool is a script in `tools/` with
a `make` target, run from the top folder after the install in `INSTALL.md`. This file says how
to run each one and how to read what comes out. More tools are added here as they are written.

## Quick start

Play a game of caveman with three computer players for 400 turns, and open the results in
the browser:

```
make game-page THEME=caveman SEED=1 CIVILIZATIONS=3 TURNS=400
```

Print the same results as text in the terminal, from the log that command wrote:

```
make game-report THEME=caveman SEED=1
```

Open the page of a game already played again, without playing the game again:

```
.venv/bin/python tools/game_report.py logs/caveman_seed1.json --open
```

Change `SEED` for a different game. The same seed always plays the same game.

## The game log: play a game and look at everything that happened

Three steps, or one command that does all three.

```
make game-page THEME=caveman SEED=1 CIVILIZATIONS=3 TURNS=400
```

That plays the game, writes the log to `logs/caveman_seed1.json`, writes the page
`logs/caveman_seed1.html` and opens the page in the default browser. The same seed always
plays the same game, so a change to a number of the theme can be judged by running the same
seed before and after. A game of 400 turns takes about half a minute. `logs/` is not in git.

The steps one at a time:

```
make game-log THEME=caveman SEED=1 CIVILIZATIONS=3 TURNS=400   # play, and write logs/caveman_seed1.json
make game-report THEME=caveman SEED=1                          # print the timelines and the tables
make game-report THEME=caveman SEED=1 FORMAT=--markdown        # the same, with Markdown tables
.venv/bin/python tools/game_report.py logs/caveman_seed1.json --html   # write the page
.venv/bin/python tools/game_report.py logs/caveman_seed1.json --open   # write the page and open it
```

`make game-report LOG=some/file.json` reads any log file by its path.

### What the log holds

The log is one JSON file, written by `src/microsponge/support/game_log.py`. The log does not
hold every move, which would be a huge file. The log holds:

- `events`: each city founded or taken, each technology learnt, each war declared, each world
  wonder finished and each defeat, with the turn.
- `units`: one entry for every unit that ever existed, with its kind, its civilization, the
  turn the unit was made, the turn the unit was gone and whether the unit was lost or built a
  city, the level the unit started at and ended at, how many tiles the unit moved, how many
  turns the unit lived and how many of those turns the unit spent inside a city.
- `cities`: one entry for every city, with who founded the city and when, who held the city at
  the end, its citizens and its buildings.
- `series`: one number for each civilization at the end of each turn, for each of these:
  cities, citizens, the bank of the primary resource, units, technologies, buildings, hit
  points of military units, military units inside a city, average level of military units,
  Policy had, Policy the active orders take, Command had, Command the active orders take,
  strength, and the score with its four parts.
- `unit_kinds`: for every kind of unit of the theme, how many units of that kind each
  civilization had at the end of each turn, the settlers and the workers too. Every kind is
  there, even one no civilization ever had.
- `improvements`: for every kind of improvement of the theme that stays on its tile, like
  caveman's farm, how many of that kind were on the tiles of each civilization's city radii at
  the end of each turn. Work that changes the terrain and leaves nothing on the tile, like
  caveman's clearing, is not counted.
- `banks`: for every resource the theme's civilizations collect, food among them, how much each
  civilization held at the end of each turn.
- `built`: every building a city finished, with the turn, the civilization and the city. A
  city that changes hands keeps its buildings, which are not counted again.
- `orders`: for each civilization and each kind of order, the turns an order of the kind was
  given, and the first and the last turn an order of the kind was in use. The orders the
  helper AI makes for itself are not counted.
- `tallies`, in each civilization: the attacks its units made and the units they killed, for
  each kind of unit. A kill counts for the attacker that killed a defender, or for the unit
  whose strike back killed the attacker.
- `forces`: for each civilization, the turns it made each division and army, and the turns it
  retired units, divisions and armies. A unit that was retired ends as `retired` in `units`.
- `civilizations`: each civilization's name, its traits and whether the civilization lost.

### Strength and score

Strength is counted fresh each turn: the hit points of the civilization's military units,
plus the technologies the civilization knows, plus its citizens, plus the buildings in its
cities. Strength goes up and down, and its chart shows the rise and fall of each civilization.

The score adds up over the turns. Each turn, the military score grows by the hit points of
the military units, the science score by the technologies known, the population score by the
citizens, and the development score by the buildings. The score is the four added together,
and its chart shows what may decide a winner. These are rough first numbers, to be refined.

### What the report shows

- A timeline for each civilization: the cities founded, taken and lost, the wars, the world
  wonders, the turn the civilization was strongest, and the place the civilization ended in.
- The scores at the end, the highest first.
- The cities each civilization founded, took, lost and held.
- The units of each civilization by kind: how many were made and lost, the average turns
  lived and tiles moved, the percent of turns spent inside a city, and whether the units
  gained levels.
- The average Policy and Command each civilization had, beside what its orders took.
- The buildings each civilization held at the end.

The page has a row of tabs under its title, and clicking a tab shows what is in it:

- Score: the chart of how many other civilizations each civilization is at war with, from none
  to every other civilization of the game, the chart of strength each turn, which is the rise and fall of each civilization,
  and the chart of the score, which may decide a winner, both drawn large, then the four parts
  of the score.
- Cities: cities, citizens and technologies known, and the bank of every resource a
  civilization collects, food among them, each in a chart of its own.
- Units: a table of the units each civilization made of each kind, with the turns of the first
  and the last, a table of what the units of each kind of each civilization did, the attacks
  they made, the tiles they moved, the units they killed and how many were lost, and a table of the divisions and armies each civilization made and the units,
  divisions and armies it retired, with the first and the last turn of each; then units in
  all, one chart for each kind of unit, of the units of that kind each civilization had, then
  hit points of military units, military units inside a city and the average level of military
  units. A kind no civilization ever had in the game has no chart.
- Buildings: a table of how many of each building each civilization built, with the turns it
  finished the first and the last, and the chart of buildings.
- Improvements: one chart for each kind of improvement, of how many each civilization had on
  the tiles of its city radii. A kind no civilization ever had has no chart, and when no
  improvement was built at all, the tab says so in a sentence.
- Orders: a table of how many orders of each kind each civilization gave, with the first and
  the last turn an order of the kind was in use, and a chart for each kind of order of how many
  each civilization gave in each 10 turns. A standing order is given once and stays in force,
  so most bars are on the first turns.
- Control points: Policy had, Policy the active orders take, Command had and Command the
  active orders take.
- Timelines: the timeline of each civilization.
- Tables: the tables of the report.

The tab shown is kept in the address of the page, like `logs/caveman_seed1.html#units`, so a
reload stays on the same tab and a link can open one. Hovering over a chart shows the number
of every civilization on that turn, and each civilization keeps one color in every chart. The
charts are drawn by Chart.js, which the page loads from the internet when the page is opened;
with no internet the page still shows the timelines and the tables.

### Asking a new question

Every table is a function in `src/microsponge/support/game_log_report.py` that reads the data
of a log, so a new question about a game is a new function there, listed in `tables()`. A new
number to chart is a new name in `Series` in `game_log.py`, counted in `GameLog.count()`, and
a line in the list of charts of its tab in `game_log_page.py`, like `CITY_CHARTS`, which
`tabs_of()` puts in the tabs. A log written before the change has to be written
again.

## The other tools

`make` on its own lists every target. In short:

- `make game THEME=caveman SEED=1 CIVILIZATIONS=3 TURNS=300` plays a game and prints its story
  with charts drawn in plain characters, with no file written.
- `make balance THEME=caveman` shows how many attacks each unit needs against each other unit.
- `make unit-report`, `make building-report`, `make wonder-report` and `make tech-report`, each
  with `THEME=caveman`, list a theme's kinds with their properties.
- `make map THEME=caveman SEED=7 CIVILIZATIONS=3` prints a world the map generator makes.
- `make guides` refreshes the generated appendix of every theme guide.

## Planned tools

Two tools the user has asked for, not built yet.

### The effectiveness report

A report that finds what in a theme does nothing or too little: units that are made but
rarely attack or kill, or that lose more than they are worth; buildings that give nothing, or
that are built and change nothing a game measures; technologies that allow nothing and give
nothing; resources that nothing costs or requires. It reads both the theme's properties and
the logs of games the computer players played.

### The optimizer

A tool that searches for better numbers for a theme, for caveman first and for classic and the
other themes once they are playable. It searches a few numbers rather than every constant:
later things, buildings and units alike, cost more than early ones by how deep they sit in the
tech tree, as a base and a growth rate per level for each kind of cost, with upkeep, income,
growth and unit strength beside them. Each set of numbers is judged by games the computer
players play, against criteria of a good game that the user and Claude review from time to
time: games that end with a winner in about 200 turns, civilizations exterminated now and
then, the last technology near the end, everything used, short fights, no piles of currency,
no early peak in a village's size, steady things to do, and fairness between places in the
turn order and between traits. It runs for a set time, and searches by simulated annealing with
restarts: it sometimes accepts worse numbers on purpose to escape a local best, and starts
again from the best found now and then. Every candidate is played on the same seeds, with the
games run side by side, and the best numbers are checked on seeds it did not search with. and reports: it never
changes a theme. When the user asks Claude to run it, Claude suggests what to change from the
report, and the user and Claude run it again, with other pairs of numbers or other ideas of
what depth means, as many times as it takes. It is built after the computer player's expand
orders, several divisions and the first steps of the utility AI, so that it tunes against a
computer player worth tuning against.
