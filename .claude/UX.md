# How the text UI behaves

The user's rules for what every screen, dialog and message of the text UI does, kept apart from
the rules for the code (`.claude/STYLE.md`) so that they can be reviewed on their own. `CLAUDE.md`
imports this file, so it's in force in every session.

This file is nearly empty on purpose. The model objects come before any screen, and the user
walks Claude through how each screen works before it's built (`.claude/COMMUNICATION.md`, "Who
decides what"). Each rule the user gives about how the text UI behaves is written here when it's
agreed, and nothing about a screen is assumed before then.

## What the user has said so far

- The interface is a text UI built on Textual, in a console. The game assumes and requires a
  pretty big console window.
- The map is shown as a grid, and `[` and `]` zoom in and out.
- The arrow keys move a cursor over the map, and the cursor control has to be good.
- A sidebar shows the details of what the cursor is on. Tab switches the sidebar between
  different views, and a view may also change how the map is drawn.
- On an area that can be mined, the game tells how much of each resource the area holds.
- An outline can be drawn around each city radius, and another outline around each city center.
- In various views, the names of the cities are shown.
- At the zoom levels that show more of the map, what is inside a city or a region needs a clever
  way of being shown. The user wants Claude's help with what might make sense, as suggestions for
  the user to choose from, and will ask Claude to draw examples when the screens are discussed.
- Each civilization is shown in a color of its own.
- There are diplomacy screens. The traits of another civilization may be shown in a window
  there, which may always be available to a civilization that has a spy network.
- The game can help a player see the history between civilizations.
- The units of another civilization are drawn only where the player's civilization can see
  them, because of the fog of war.
- In a theme with space, switching to space is a view.
- A city that is set to build nothing is easy to see somewhere.
- When a city's production queue is empty, the game asks what to build.
- When a unit is finished, the player may choose the tile the unit is placed on, with a cursor
  that can only reach the tiles that surround the city center.
- The screens may be a lot of work.
- There is a hotkey bar, which shows the keys that work.
- F1 opens a help screen and F2 opens an about screen.
