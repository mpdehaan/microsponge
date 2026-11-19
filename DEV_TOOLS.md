# Developer tools

The tools for looking at how the game plays, for tuning. Each tool is a script in `tools/` with
a `make` target, run from the top folder after the install in `INSTALL.md`. This file says how
to run each one and how to read what comes out. More tools are added here as they are written.

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

The page shows the same timelines and tables, with a chart of every series. The charts are
drawn by Chart.js, which the page loads from the internet when the page is opened; with no
internet the page still shows the timelines and the tables.

### Asking a new question

Every table is a function in `src/microsponge/support/game_log_report.py` that reads the data
of a log, so a new question about a game is a new function there, listed in `tables()`. A new
number to chart is a new name in `Series` in `game_log.py`, counted in `GameLog.count()`, and
a line in `CHARTS` in `game_log_page.py`. A log written before the change has to be written
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
