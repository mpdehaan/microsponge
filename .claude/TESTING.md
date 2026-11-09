# How microsponge is tested

The user's rules for the tests: how they're run, what they must cover, how they're written and
where each kind lives. Testing is a standing priority in this project, and it's what keeps the
rate of error-free changes high, so these rules are kept apart from the rules for the code
(`.claude/STYLE.md`) so that they can be reviewed on their own. `CLAUDE.md` imports this file, so
it's in force in every session. `.claude/STYLE.md`'s table "Enforced by the test suite" lists the
code rules that a test enforces, and this file says how the tests themselves are written.

## Running the tests

Tests use the standard library's `unittest`. Run them from the repository root, after the install
in `CLAUDE.md`:

```
./run_tests.sh                # all tests, in parallel
./run_tests.sh test_name ...  # the tests whose module, class or method name contains any of the names, in parallel too
./run_tests.sh --serial       # all tests in one process, the plain unittest way
```

`./run_tests.sh` runs `test/parallel.py`: one process per test class, as many at once as there
are cores, reporting every failure in full and the total count. It exits with a failure if any
class fails, so check its exit code or its last line (`OK` or `FAILED: ...`). A class that runs
past `CLASS_TIMEOUT_SECONDS` (two minutes) is stopped and counted as failed, with a message
saying so, because a test that repeats a step in a loop until something appears can loop for ever
when it never does; a test that waits for something with a loop should check that what it waits
for exists first. `.venv/bin/python -m unittest discover -s test` still works and gives the same
results, just slower. To run one test class on its own, run
`../.venv/bin/python -m unittest test_x.TestY` from inside `test/`, because
`python -m unittest test.test_x` from the root finds the standard library's `test` package
instead. `make test` and `make test-one NAME=...` wrap these.

**No commit goes in without the full suite passing.** `make hooks` links `tools/pre_commit.sh` as
the git pre-commit hook, which runs `./run_tests.sh` before every commit and stops the commit if
anything fails, and the user requires that it stays installed and is never bypassed with
`--no-verify`. Always run the full suite with `./run_tests.sh` before committing, and let the hook
be the backstop. A change that only touches `IDEAS.md` or other documents doesn't need a run of
its own beyond what the hook does, and it's committed on its own, apart from code that's
mid-change.

The suite runs pyflakes over `src/`, `test/` and `tools/` (`test/test_pyflakes.py`), so an unused
import, an undefined name or a name defined twice fails the tests; `pyflakes` is in
`requirements.txt` for that.

## What a change must come with

- **Every behaviour has a test**, and a feature isn't finished until its tests are in: what the
  model, `GAME_RULES.md`, says the game does, what the model objects refuse, and, once there are
  screens, what each screen does when its keys are pressed. The user wants complex, high-coverage
  scenarios, not one happy path.
- **A whole game is played by the tests.** Before any screen is started, the tests can play a
  game from its start to its end with no person and no screen, and the game played that way is
  logical and good. What "good" means for such a game is the user's to say, and Claude asks.
- **The tests have a theme of their own, called caveman.** Caveman is a tiny, silly theme that
  exists for the tests, so that the engine is tested without making up anything in classic or
  SPACE. It does as little as possible: a small world, settler and warrior units, a technology
  that allows the warrior, a technology called wheel that requires stone, which comes from
  mountains, and the world wonders great cave painting and arrangement of rocks, with bonuses.
  Claude may make up the rest of caveman's kinds and choose its numbers, to see what the user
  thinks of them. Caveman lives with the other themes, because the screens may later be allowed
  to play it. The eventual goal is that the computer players play a game of caveman in the tests
  and produce a convincing log of the game, before any screen exists.
- **A shortcut needs tests of both paths.** Any condition-specific optimization, like skipping
  work that would do nothing, is only acceptable with good tests of the case it skips and the
  case it doesn't (`.claude/STYLE.md`, "Performance matters").
- **Rules get rule tests.** A rule about the code's shape is enforced by a test where one can be
  written, listed in `.claude/STYLE.md`'s table, so that it holds as modules are added and
  rearranged rather than by reading.
- **When a constant is removed or renamed**, grep every place that uses it under `src/`, `test/`
  and `tools/` first; pyflakes catches an undefined name, but not a string that changed meaning.
- **A test that looks wrong is an opportunity to ask a question.** Never change a test just so
  that it conforms to new code and passes: work out what it was protecting, make an intelligent
  choice, and where the choice is the user's, ask them.
- **Tests and scripts never fetch anything from the internet.**

## How tests are written

**Tests follow every rule the program does**, and the user requires it: `__slots__`, keyword-only
arguments, the GPLv3 header, named constants and the rest of `.claude/STYLE.md` apply to `test/`
and `tools/` as they do to `src/`. Limits come from the program's constants (a maximum plus one,
not the number written out), a number that means something gets a name, and messages and format
strings are constants. When a test checks text the program shows, like a label, a key's name or a
message, it imports the program's constant for that text (like `MSG_NOTHING_TO_PLAY`) rather than
writing the words out again, so that rewording something in the program doesn't break its tests.
Any string the program defines is the program's constant in a test too, and any other literal a
test needs is a named constant at the top of the test file or a variable, never inline; test data
of the test's own can stay literal.

**Tests use the program's contract.** They work with the objects through their constructors,
getters and setters, never by checking an object's internal data structures directly. A written
file is checked by loading it back with the library that reads it and comparing data, never by
matching fragments of the file's text. Tests that check a specific random outcome set a seed.
Data a test or script needs is kept in the repository as data files, separate from the test code.

When the first screen arrives, its tests run the real program with no terminal and press keys by
their names, and this file gains the rules for them.

## Where the tests live

Everything is directly in `test/`, with no `__init__.py`, because a package with that name would
clash with Python's standard library `test` package, and discovery doesn't reach subfolders
without one. Tests are split by feature, each a file of its own, and shared helpers are modules
beside them:

- **The program.** `test/test_cli.py` (the command line) and `test/test_version.py` (the
  version). Tests of the model objects join them as the model objects are derived from the
  model, `GAME_RULES.md`.
- **The rules.** `test/test_slots.py`, `test/test_keyword_only.py`,
  `test/test_message_constants.py`, `test/test_pyflakes.py`, `test/test_doc_paths.py` and
  `test/test_license_headers.py`.
