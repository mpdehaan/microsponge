# How microsponge is put together

This is a tour of microsponge's code for people who want to understand how it works without
editing it: what the parts are and the rules the code keeps. [GAME_RULES.md](GAME_RULES.md) is the
model, which says what the game is and how it's played, and `CLAUDE.md` holds the rules whoever
edits the code follows, with the detailed notes beside it in `.claude/`.

## The idea in one paragraph

What the game is and how it's played is written down first, in `GAME_RULES.md`, which is called
the model. The model objects, the classes that hold a game and apply the model, are derived from
that document and know nothing about screens. microsponge is an engine with themes, each a kind of
game: the base classes are common to every theme, and a theme is a package of short Python classes
built on them, never a configuration file. The text UI is built on the model objects afterwards,
and is the only part that draws anything. The computer players are algorithms written for this
game, which play through the same model objects a person does. So far the ground under all of
that exists, the command line, the program's text, the version and the tests that keep the
code's rules, and on it the first model objects: the kinds a theme builds on, the world, the
units, the cities and what they build, the civilizations and their research, the game, its
turns and the saved game.

## The parts

- The top level, `src/microsponge`, holds the entry points and the program's text. `cli.py` is
  the `microsponge` command, and `__main__.py` lets `python -m microsponge` do the same.
  `err_messages.py` holds every error message and `ui_strings.py` every other piece of text the
  program shows.
- `support` is the plumbing the rest stands on: the version, small helpers for text and
  numbers, and the reports the tools print and the theme guides include: tables of text
  (`tables.py`), the command line the theme tools share (`theme_tools.py`), the reports on a
  theme's units, buildings, world wonders and tech tree (`kind_reports.py`), the balance
  report (`balance_report.py`) and the generated appendix of each theme's guide (`guides.py`).
- `engine` holds the model objects every theme shares, in a package for each topic:
  - `kinds` has the base classes a theme builds on: terrain, resource, technology, the kinds of
    unit, building and world wonder, improvement, the city spec and the theme itself. It also has the
    catalog, which gives each kind of a theme a number for the length of a game.
  - `world` is one map of tiles.
  - `units` holds every unit of a game, the rules for units, and the rules for a unit that
    builds an improvement.
  - `cities` has the city, the rules for building one and for the units inside, the harvest,
    which is the tile each citizen takes and what a city collects, and production: the units
    and buildings a city builds, paid for a part each turn.
  - `civilizations` has the civilization: what it holds, what it knows, its action points and
    its wars, research, which is the one technology a civilization researches with the
    research points it gathers, and the strategic resources within its borders.
  - `game` ties one game together: the turn, whose turn it is, the civilizations, the worlds,
    the cities and the units.
  - `turns` starts a game, does the work of ending a turn, and has every order a civilization
    gives on its turn.
  - `saving` writes a game to a file and reads one back.
- `themes` holds a package for each theme: caveman, the tiny theme the tests play, and the first
  stubs of classic, SciFi, fantasy and PlanetWars.
- `test/` holds the tests, and `tools/` the scripts for working on the code and on the balance
  of a theme's units: the reports on a theme, which also print Markdown for the guides, and
  `theme_guides.py`, which regenerates the appendix of every `GUIDE_<THEME>.md`.

The text UI will be a package of its own, described here when it exists.

## How a game is held

- **A theme is short classes.** A kind, like the warrior, is a class that only sets what differs
  from its base, and is never made into an object. A theme lists its kinds.
- **The map is layers of numbers.** A world holds one grid of integers for each fact about its
  tiles, like the terrain or the unit on each tile, not an object for each tile, so that a huge
  map stays small and fast. A world wraps around from east to west and has edges at the top and
  the bottom.
- **The units are columns of numbers.** A unit is a number, and each fact about the units, like
  the kind or the hit points, is a list indexed by that number.
- **One class owns each array.** Only the world touches the layers and only the units touch the
  columns, so a change of layout touches one class.
- **Everything a player does is an order.** Moving a unit, building a city, declaring war and
  ending the turn are each one method of one class, which checks whose turn it is and the action
  points before anything changes. The screens and the computer players will give the same
  orders, so neither can do what the other cannot.
- **A saved game is JSON, mostly numbers.** Each layer and column is saved under a number of its
  own that never changes, and the file records the name of every kind's number, so a game saved
  by one version loads after a theme has reordered its kinds or added to them. The file also
  records the version it requires, and a file from before the format last changed is refused.

## The rules the code keeps

These are the things a reader will notice everywhere, and they're deliberate:

- **Objects talk through methods.** A class reads another's data with a getter and changes it
  with a setter that checks the value. No class reaches into another's fields, and there are no
  properties, so what happens is visible where it happens.
- **Behaviour lives with its data.** Everything about one kind of object is on that object's
  class, so there is one place to look.
- **Every class lists what it holds.** Each class declares its data members, so a misspelled
  name is an error rather than a new member.
- **Calls name what they pass.** A function that takes more than one argument takes them by
  keyword, so a call reads on its own and a wrong argument is refused at the call.
- **Every word the program shows is a constant.** Error messages are in one file and the rest of
  the program's words in another, so wording can be read and edited in one place. The same goes
  for strings used as names in the code and for numbers with a meaning, like the limits of a
  range.
- **The rules are tested.** Where a rule about the code's shape can be checked by a test, it is,
  so the rule holds as the code grows. `.claude/STYLE.md` lists each rule with its test.

## How a change usually goes

A decision about the game is made and written into `GAME_RULES.md`, the model objects that carry
the decision are agreed, and then the objects and their tests are written together. No commit goes in unless
every test passes, which a git hook enforces.
