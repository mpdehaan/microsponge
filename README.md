# microsponge

microsponge is a turn based strategy game of the kind called 4X, written in Python and played in
a text UI.

**microsponge is in a very early state. Do not expect to play it yet.** The first parts of the
engine exist, and there is nothing to play.

## Setup

[INSTALL.md](INSTALL.md) says how to create a virtual environment and install microsponge and its
`microsponge` command.

## How it's played

[GUIDE.md](GUIDE.md) is the guide for people who play the game: how every theme is played, with
a page for each theme, like [GUIDE_CAVEMAN.md](GUIDE_CAVEMAN.md), that says what the theme is
like and lists its units, buildings, world wonders and tech tree.

## How it's built

[GAME_RULES.md](GAME_RULES.md) is the model: what the game is and how it's played, which the code
is derived from.

[PHILOSOPHY.md](PHILOSOPHY.md) says what the game is for.

[ARCHITECTURE.md](ARCHITECTURE.md) explains how the code is put together, for people who want to
understand it without editing it.

## Tests

```
make test
```

`make` on its own lists the other everyday targets.

## License

microsponge is licensed under the GNU General Public License, version 3 or any later version. See
[LICENSE](LICENSE) for details.
