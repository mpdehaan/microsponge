# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

microsponge is a turn based strategy game of the kind called 4X, written in Python and played in a text UI built on Textual. The name is a reference to an episode of Pinky and the Brain, because Pinky and the Brain is about world domination. It's a flexible engine with themes, each a kind of game, and the first theme, called classic, models historic earth in the style of a civilization game. It is not FreeCiv and not a clone of FreeCiv. The user makes every design decision and has a strong say in the architecture (`.claude/COMMUNICATION.md`, "Who decides what"). `GAME_RULES.md` is the definition of the game, which the user calls the model: every decision about the game is written there first, the model objects, which are the code and are object oriented, are derived from the model, and no screen is built before the model objects. The computer players, which the user calls the AI, are algorithms written by hand in this project, never machine learning, a language model or Claude. The Python classes underneath are internal: no person is expected to use them as an API, so they can change freely to suit the game. It's at the very start: the model has its first decisions, and there are no model objects and no screens yet, only the project's rules, the tests that enforce them and a command that says there is nothing to play. The third-party dependencies are `pyflakes` and `pycodestyle`, pinned in `requirements.txt`, which `setup.py` also reads; Textual joins them with the first screen. The package is `microsponge`, in `src/microsponge`, and the code and its tests import it by that name, so it has to be installed (as below) before anything runs.

## Where everything is

- `.claude/COMMUNICATION.md`: how Claude works with the user: who decides what, committing, asking, numbering questions and explaining changes.
- `.claude/STYLE.md`: every rule for the code and the documents, with its reason and the test that enforces it.
- `.claude/TESTING.md`: how the tests are run, what a change must come with, how tests are written and where each kind lives.
- `.claude/UX.md`: the user's rules for how the text UI behaves. It holds only what the user has said so far, until the user walks Claude through the screens.
- `.claude/THEMES_CLASSIC.md`: what the user has decided about the theme called classic. Each theme gets a file like it.
- `.claude/THEMES_SPACE.md`: what the user has decided about SPACE, a later theme inspired by Stargate, recorded so that the engine allows for it.
- `GAME_RULES.md`: the model, which says what the game is and how it's played in every theme, for people and for Claude alike, written from the user's decisions.
- `IDEAS.md`: the user's ideas for later, kept by Claude, with what each would mean for the code.
- `ARCHITECTURE.md`, `PHILOSOPHY.md`, `README.md` and `INSTALL.md` are for people, and the user edits them by hand too.

Everything in `.claude/` is for Claude: it holds what the user doesn't need to read, and the six files above are imported at the end of this file, so they load in every session. When the model objects exist, a file of reference notes on the model objects joins them, and one on the screens when the screens exist. `test/test_doc_paths.py` checks that every source path these documents name exists.

## License

The project is licensed under GPLv3, with the full text in `LICENSE`. Every Python file and shell script, including new and empty ones, starts with the standard GPLv3 header, copied from any existing source file, whose first line is `# microsponge: a strategy game`. Put it above the module docstring, and below a script's `#!` line. `test/test_license_headers.py` checks it.

## Commands

`Makefile` at the root wraps everything below, and `make` lists its targets: `setup`, `run`, `test`, `test-one NAME=...`, `pyflakes`, `pep8` (a look, not a rule), `loose-strings`, `hooks` and `clean`. A new everyday command gets a target there too. Set up the virtual environment once. This also installs the `microsponge` command, which `setup.py` points at `microsponge.cli:main`, and `-e` makes it use the code here rather than a copy:

```
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

`.claude/TESTING.md` says how the tests are run and written. In short: `./run_tests.sh` runs the whole suite in parallel, and no commit goes in without it passing, which the pre-commit hook that `make hooks` installs enforces and the user requires.

`tools/` keeps the scripts worth running again. Run them from the top folder:

```
.venv/bin/python tools/loose_strings.py src      # string literals inside functions, which should be constants
```

Two more arrive with the code they need: a tool that redraws the diagrams in `ARCHITECTURE.md` from the packages, once there are packages worth drawing, and a tool that takes screenshots of the real screens for the documents, once there is a screen. Each gets a `make` target and a test that its output is current.

## Version

`src/microsponge/support/version.py` holds `VERSION`, a string of three whole numbers separated by dots, like `1.0.2`, which `setup.py` reads and the command line shows. Versions are compared number by number with `version_numbers()`, never as decimals. Bump the last number in every commit that changes Python code under `src/`, and leave the first two to the user.

## Working with the user

@.claude/COMMUNICATION.md

## The rules

@.claude/STYLE.md

## Testing

@.claude/TESTING.md

## How the text UI behaves

@.claude/UX.md

## The theme called classic

@.claude/THEMES_CLASSIC.md

## The theme called SPACE

@.claude/THEMES_SPACE.md
