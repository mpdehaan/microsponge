# Installing microsponge

## Setup

microsponge needs Python 3.15 or later. From the top folder checkout of this project, create a
virtual environment and install microsponge into it:

```
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

`make setup` does the same. This adds the `microsponge` command to `.venv/bin`, so it works from
any folder. `-e` makes it use the code in this folder, so changes take effect without installing
again.

## Running

```
.venv/bin/microsponge
```

`./microsponge.sh` and `make run` do the same from the project folder.

## For working on the code

`make hooks` installs the git pre-commit hook, which runs every test before a commit goes in, and
`make test` runs every test. `make` on its own lists the other everyday targets.
