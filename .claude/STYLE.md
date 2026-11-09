# How microsponge's code is written

These are the rules for anyone, or anything, that edits the code and its tests, with the reasons
behind them. They're the user's, and they're deliberate. `ARCHITECTURE.md` explains the design
these rules serve, under "The rules the code keeps". `CLAUDE.md` imports this file, so it's in
force in every session. Where a test enforces a rule, it's named; a rule with no test beside it is
kept by reading.

## Enforced by the test suite

| Rule | Enforced by |
| --- | --- |
| Every class declares `__slots__`, each class in a hierarchy its own, even `()`. Dataclasses are `@dataclass(slots=True, kw_only=True)`. Exceptions: classes that only hold constants, their own or inherited, like a theme's kinds, and subclasses of classes from outside microsponge. | `test/test_slots.py` |
| Every function and method takes its arguments by keyword where a call passes more than one or any optional one: a bare `*` before the parameters. In `src/`, `test/` and `tools/`. Exceptions are listed in the test: Python's special methods, methods Textual or `unittest` call positionally, forwarders and nested functions. | `test/test_keyword_only.py` |
| Every string the program shows or raises is a constant: `ERR_` in `src/microsponge/err_messages.py`, `MSG_` in `src/microsponge/ui_strings.py`, and nowhere else. No module defines a `HELP_` constant until the module of help text arrives with the first screen. | `test/test_message_constants.py` |
| No unused import, undefined name or name defined twice, in `src/`, `test/` or `tools/`. | `test/test_pyflakes.py` |
| Every source, test, tool and screenshot path named in the documents exists. | `test/test_doc_paths.py` |
| Every Python file and shell script starts with the GPLv3 header. | `test/test_license_headers.py` |

## The rules, and why

The user wants the code easy for people to maintain without AI: plain code, comments that explain
why, tests that read clearly. Object orientation is a design goal throughout, and the user wants
the design very good, with intelligent use of base classes. Readability comes first everywhere:
the user wants the code refactorable and free of duplication, and speed is dealt with only where
it becomes a localized problem ("Performance matters" below). These rules apply to the program,
the tests and `tools/` alike.

**A theme is Python code.** Each theme, each kind of game the engine can play (the model,
`GAME_RULES.md`, "Themes"), is a subpackage of a `themes` package, written as Python classes and
never as a configuration file: the theme's tech tree, its units, its resources and every other
choice the theme makes. The base classes are common to every theme and live outside `themes`, and
they do the work, so that a theme's own classes are very sparse and easy for people or AI to be
creative with. Inside a theme, subclassing is allowed. What goes into a theme is the user's to
choose: no sample unit, civilization or anything else in a theme is written without asking
(`.claude/COMMUNICATION.md`, "Who decides what").

**Packages say what each part is for.** So far there is `engine/`, the model objects every theme
shares, `themes/`, a package for each theme, and `support/`, the plumbing, beside the top
level's entry points (`cli.py`, `__main__.py`) and the two text modules, `err_messages.py` and
`ui_strings.py`. New modules go in the package that says what they're for, and a new group of them
gets a package of its own, whose `__init__.py` docstring says what the package is for. Files that
grow past several screens are split where behaviour groups logically, as a matter of cohesion
rather than line counts. Scripts worth running again live in `tools/`, with a docstring saying
what for and how, never in a temporary folder.

**The engine is kept in categories.** The base classes shared by every theme live in an `engine`
package, which is split into subpackages, one for each larger topic, so that the code stays
categorized as it grows. The user will occasionally ask for these to be refactored. The name
`model` is not used for a package, because the model is the document `GAME_RULES.md`.

**A theme reads at a glance.** Each theme is a subpackage of `themes`. The classes in a theme are
very readable and very concise: tight, self explanatory, and with few comments, because a theme
that needs comments to be understood isn't plain enough.

**The world is low-level data.** The map is going to be huge and may hold many worlds, and the
user wants the world's data structure blindingly fast. So the map is arrays of mostly integers,
which can hold nested arrays and can be as low level as speed needs, and not an object for each
tile. The kinds a theme defines, like a kind of unit, are raw data while the program runs, and
static classes do the work on that data, like controlling units. The same low-level shape is what
a saved game holds. The tiles of every world and the units are raw integer data, since there are
very many of them, and the game, each civilization and each city are ordinary objects with
getters and setters, since there are few. Each array is read and written only by the one class
that owns it, so that a change of layout touches one class.

**The map is layers, and each layer has a constant.** A world holds one layer for each fact about
its tiles, like the terrain or the unit on each tile, and each layer is a list of rows of
integers: a world of 500 by 500 tiles with 10 layers is 10 arrays of 500 by 500. Each layer has a
constant of its own, a number that never changes and is what a saved game calls the layer, so
that the format is future proof. When a feature is taken out, its layer's constant is retired and
never used for anything else.

**A saved game is JSON, mostly numbers.** A saved game is written as JSON and holds few strings:
mostly integers, plus a dictionary that says what each id means, like which id is the phalanx,
so that a game saved by one version can be loaded by a later one. The format is designed ahead
for themes that change after the game is released. A saved game also records the version it
requires, and when the format changes in a way old files can't follow, that required version
moves, and files from before it are refused: there is no upgrade code, for now.

**Behaviour lives on the object that owns the data.** Everything about computing, checking or
changing one kind of object is on that object's class, so that a reader finds everything about
one kind of object in one place. Prefer code that reads at the level of the problem, with small,
well-named methods and shared helpers for repeated shapes, over low-level code that reads like
"Python written in assembly".

**Objects talk through explicit methods.** A class changes another's data only through a method
like `set_name(name)`, which validates what it's given with the same check as the constructor, and
reads it only through one like `get_name()`, never through descriptors, properties or other
accessor magic, so that what happens is visible where it happens. A class has the getters and
setters that other code, tests included, reads and changes it through, and no more, so its
accessors show its contract. A class of values that should never change is immutable by having no
setters. Which classes are immutable is the user's decision as the model objects are derived.

**Every class declares `__slots__`**, so that no data member can be added by mistake, and each
class in a hierarchy declares its own, even `()`. Dataclasses use
`@dataclass(slots=True, kw_only=True)`. The exceptions are classes that only hold constants, and
subclasses of classes from outside microsponge, like Textual's screens, enums and exceptions.
`id` is read-only where a class has one.

**Arguments go by keyword.** Functions and methods take their arguments by keyword wherever a call
passes more than one, or any optional one: the parameters go after a bare `*`, so that a call names
what it passes and Python refuses a missing, extra or misspelled argument at the call rather than a
`None` check finding it later. The exceptions, listed in `test/test_keyword_only.py`, are Python's
own special methods like `__get__` and `__round__`; methods that Textual or `unittest` call with
their own positional arguments, like `on_key` and `compose`; forwarders that pass
`*arguments, **named` through; and functions nested inside another, which are callbacks with a
local contract. The rule costs a little time on every call, and that is accepted. A class stays
positional for speed only when the user agrees that a measured hot path needs it, and it's then
listed in the test's `FAST_CLASSES`, which is empty.

**Every string used as a value or a name in code is a named constant**, never written out where
it's used, so that typos can't happen and its meaning is clear: a file key, a setting, a kind, a
mode, a key name, an option of the command line. A constant used by only one file is defined at
the top of that file, and one shared between files goes in a module of the package that says what
the constants are, such as one for defaults and one for limits. The same goes for numbers with a
meaning: a named minimum and maximum rather than 0 and 100, and error messages built from those
constants. Each constant is defined on its own line, never several at once with tuple syntax like
`LOW, HIGH = 0, 100`, which the user finds hard to read. A constant nothing imports is removed.
`tools/loose_strings.py src` lists every string literal left inside a function or class, and
should report nothing. Literal braces in a template are doubled.

**Every piece of text the program shows or raises is a constant**, written as a template and
filled in with `.format()` where it's used, so that wording can be edited in one place and kept
consistent. This covers the text UI too: a screen's labels, field names, key legends, column
headings, prompts, dialog titles, notes, marks, box-drawing characters and styles are all
constants. Three prefixes say what a string is for, with no exceptions: `ERR_` for an error
message, which is anything that says what went wrong, whether raised, printed or shown on a
screen, including a dialog's title; `MSG_` for every other user-visible string that isn't part of
a data format; and `HELP_` for a screen's help text. Every `ERR_` constant lives in
`src/microsponge/err_messages.py` and every `MSG_` constant in `src/microsponge/ui_strings.py`,
each grouped under a comment naming the module that uses them and kept in that order, so that all
the wording can be read in one place. Every `HELP_` constant will live in one module of help
text, which arrives with the first screen: one multi-line string per screen in which a line is a
line on the screen and a blank line is a blank line, so that help can be edited by hand without
touching code. Strings that aren't text for people, like key names, file modes and a data
format's names, keep their own descriptive names in their own modules. Text only for people, like
docstrings and comments, stays where it is.

**A theme's own words stay in the theme.** What a theme calls something, like village for a
city, is a naming override of that theme: a constant on the theme's own class, in the theme's
subpackage, and never in `ui_strings.py`. The engine's default word, like city, is an `MSG_`
constant like any other text.

**A line whose purpose isn't obvious gets a name.** A regular expression or a long expression is
given a function or method whose name says what it means. That includes list and dictionary
comprehensions: anything more than a plain copy or filter goes in a function or method whose name
says its purpose, even if it's one line.

**Tests follow every rule the program does**, and the user requires it: every rule on this page
applies to `test/` and `tools/` as it does to `src/`. How the tests are run, what a change must
come with, how tests are written and where each kind lives are in `.claude/TESTING.md`.

**Performance matters.** The computer players have to play their turns quickly on very large
maps, so the time a turn takes is watched as the model objects are written. The way to speed is
efficient choices made smartly: the right data structure and the right algorithm, and work that
isn't done twice. Every rule on this page holds everywhere, in the engine as in the themes, and a
rule gives way to pure speed only where speed has become a localized problem, shown by measuring,
and only in that place, with the user's agreement. The user considered optimizing everything
outside the themes for pure speed and decided against it, because code that breaks the rules for
speed is harder to refactor and invites duplication. The user is never okay with a
condition-specific optimization, like skipping work that would do nothing, unless the case it
skips and the case it doesn't both have good tests.

**Nothing is written twice.** The user wants the code refactorable and free of duplication:
shared behaviour goes in a base class or a helper with a name that says what it's for, and when a
second copy of something would be written, the first is made shareable instead.

**Files.** Every Python file and shell script starts with the GPLv3 header, below a `#!` line and
above the module docstring, opening with `# microsponge: a strategy game`. Where tests go is in
`.claude/TESTING.md`.

**Each change carries its documentation.** A decision about the game is written into the model,
`GAME_RULES.md`, when it's made, before anything is built on it, and a change to the game changes
`GAME_RULES.md` in the same commit, in the words the game shows on screen, never code names that
differ.
`ARCHITECTURE.md` is a tour of the code for people who won't edit it, kept true the same way.
The model and the theme files are the user describing the game to Claude, so they read as rules.
`GUIDE.md`, the guide for people who play the game, will explain everything in them in a
friendlier way, and is written from them. When there are screens, the guide is kept true with
every change to a screen, a setting or a key, and the documents show screenshots taken from the real
screens by a tool, regenerated when a screen changes or the user asks. When there are packages
worth drawing, the diagrams in `ARCHITECTURE.md` come from the code by a tool, and a test checks
that they're current. A change to a rule on this page updates this file. An idea in `IDEAS.md` is
removed as soon as it's built, without being asked, and the finished parts are trimmed out of an
idea that's partly built; check it whenever a feature lands, since a change often finishes an idea
noted under another heading, and add to it only when the user asks. When a module moves or is
renamed, every path that names it in `CLAUDE.md`, `.claude/`, `ARCHITECTURE.md`, `GAME_RULES.md`,
`README.md` and `IDEAS.md` moves with it, which `test/test_doc_paths.py` checks. Decisions are
recorded without their dates unless the date explains a reversal. A change to Python under `src/`
bumps the last number of `VERSION`; commits that only change docs, notes or tests don't.

**Working with the user** is covered by `.claude/COMMUNICATION.md`: who decides what, committing,
asking before building, numbering questions, and how changes are explained.

## What this project doesn't take from PEP 8

The suite runs pyflakes, which finds mistakes, and not pycodestyle, which enforces layout.
`make pep8` runs pycodestyle for a look, and `setup.cfg` lists what it leaves out: long lines
(E501), because a line runs as long as it needs to read as one thought; the blank-line counts
around definitions (E302, E305); and a blank line at the end of a file (W391). What's left is
worth a look, but nothing pycodestyle reports is a rule unless it's on this page.
