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
game, which play through the same model objects a person does. So far only the ground under all
of that exists: the command line, the program's text, the version, and the tests that keep the
code's rules.

## The parts

- The top level, `src/microsponge`, holds the entry points and the program's text. `cli.py` is
  the `microsponge` command, and `__main__.py` lets `python -m microsponge` do the same.
  `err_messages.py` holds every error message and `ui_strings.py` every other piece of text the
  program shows.
- `support` is the plumbing the rest stands on: so far, the version.
- `test/` holds the tests, and `tools/` the scripts for working on the code.

The model objects, the themes and the text UI will each be a package of their own, described here
when they exist.

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
