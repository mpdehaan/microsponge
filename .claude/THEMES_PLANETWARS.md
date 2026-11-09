# The theme called PlanetWars

What the user has decided about PlanetWars, a theoretical theme, a template of a game in which
every civilization starts alone on a planet of its own. The model, `GAME_RULES.md`, says how the
game works for every theme and what a theme may decide, under "Worlds" and "Space" for this one;
this file holds what the theme itself chooses. `CLAUDE.md` imports this file, so it's in force in
every session.

Nothing is added here that the user hasn't said (`.claude/COMMUNICATION.md`, "Who decides what").
Classic is being developed first; this theme is recorded so that the engine allows for it.

## What the user has said

- Everybody starts with one city on a planet that is only big enough for that city, and
  everyone has a different planet. There may be empty planets.
- There is a colony ship. When a colony ship hits a world, the colony ship can spawn a
  settler, with some future rules to be figured out: spawning may cost extra population, may
  spawn multiple settlers, and may give the player some choice about where to land.
- Space transports may behave in a similar way, giving people a chance to choose where to
  land, but land defenses, the anti space defenses, may be able to shoot a space transport
  down.
- The units include at least the settler, the colony ship and the space transport. In the
  code the colony ship and the space transport are space units.

## What Claude chose, to be confirmed

- The stub allows 1 to 50 planets, like SciFi, because a theme has to say its fewest and
  most worlds. The engine has no rule yet that a game has at least as many planets as
  civilizations, or that a planet is only big enough for one city.

## Not decided yet

- The rules of the colony ship: what spawning a settler costs, how many settlers, and the
  choice of where to land.
- Which anti space defenses shoot down a space transport, and how.
- Everything else about the theme.
