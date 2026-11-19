# Glossary

The key terms of microsponge, as the user uses them, so that Claude and the user mean the same
thing by a word. `CLAUDE.md` imports this file, so it's in force in every session. A new key
term is added here when the user settles on the word.

## The project

- The model is the document `GAME_RULES.md`: what the game is and how it's played, thought of as
  the rule book of a strategy game that was a board game. "Add this to the model" means write it
  into `GAME_RULES.md`.
- Model objects, or models, are code: the classes derived from the model.
- Rules, as in "your rules", are Claude's rules: `CLAUDE.md` and the files in `.claude/`. The
  word is kept for those, which is why what the game does is called the model and not the rules.
- Classic is the theme of historic earth in the style of a civilization game, the first one
  being developed. The user says "in classic" or, for another theme, something like "in scifi",
  to say which theme they're working on, and is talking about classic unless they say otherwise.
  What the user decides about one theme is kept in that theme's file, `.claude/THEMES_CLASSIC.md`
  for classic, `.claude/THEMES_SCIFI.md` for SciFi, the theme inspired by Stargate, which was
  first called SPACE, `.claude/THEMES_FANTASY.md` for fantasy, `.claude/THEMES_PLANETWARS.md` for PlanetWars and
  `.claude/THEMES_CAVEMAN.md` for caveman, and what holds for every theme is kept in the model.
- The Game Expert is an expert Claude can consult for opinions when the user says to: a
  PhD-level expert in game theory who loves turn based strategy games, Go and Chess and is an
  absolute grandmaster at all of them, and who knows the history of real time strategy games
  and everything that has been added to games in both genres. Claude can tell The Game Expert
  all about the game, and The Game Expert knows nothing of the code. Claude does not consult
  The Game Expert until the user says so.

## The players

- AI, about the game, is the computer players: algorithms that the user and Claude choose and
  write by hand in this project. It never means machine learning, a language model or Claude:
  no opaque model file whose knowledge is not code. Tuning the numbers of the hand-written
  algorithms by searching, like simulated annealing, is allowed.
- The helper AI is the layer that carries out orders: the helper AI is what touches the units
  and the cities, for a person and for a computer player alike. For now the helper AI is
  mostly a pass through.
- The Hand is the internal name for a helper AI, after the Hand of the King in Game of
  Thrones: the player's Hand, the computer's Hand, the computer AI's Hand, or the Hand AI,
  which all mean the same thing. The Hand is an internal detail, used in discussion and in
  code, and is never shown to a player on any screen.
- The main AI is the part of a computer player that adjusts the strategy, the way a person
  would, and asks the helper AI to carry the strategy out. The main AI cannot touch the units
  and the cities.
- The referee AI is a global part of the engine that belongs to no player. The referee AI
  marks an order invalid when the order can no longer work.
- An order is what a player asks the helper AI to do with a unit, a group, a kind of unit, a
  city or the civilization. The orders in force are kept in a table.
- The giver of an order is the thing in the game the order comes from, and the receiver is
  the thing ordered to do something. An order is never from the player. A destination or a
  target is part of what the order says, and is not the receiver.
- Control points are the points orders take, in two kinds, Policy and Command: in code,
  ControlPoints with the subclasses Policy and Command. The user wants them modelled this
  way, and not as purposes.
- Policy, or policy points, is what a civilization spends on policy orders, and is what was
  called the civilization's action points, then oversight points and then Oversight. The
  screens and Claude say Policy. When the user says Oversight or oversight points, the user
  means Policy.
- Command, or command points, is what a civilization spends on command orders: the military
  orders for armies, divisions and single military units. A civilization has less Command
  than Policy. Cities provide
  Command, and military buildings add to it.
- AP is short for action points, which belong to a unit: what a unit spends to move and to
  attack. The user may write AP, and the screens may write AP too.
- To micro, or to micromanage, is to give every unit its own orders every turn. The game is
  designed so that no player, a person or a computer player, wins by micromanaging.

## The things in the game

- A city is always called a city when Claude talks to the user, even where a test plays a theme
  that has another word for a city. For caveman, Claude may write City("village") where the
  theme's word matters.
- An army is a group of units that a player defines, and a division is a smaller group inside
  an army. "Divisions" is the user's working name. Army and division are the engine's words,
  and a theme has words of its own for both.
- An engineer is a unit on the map that improves terrain, by building improvements like roads
  and farms. Engineer is a role, not a kind of unit: caveman's kind of unit with that role is
  called the worker. A citizen is one of the people of a city, and citizens are who collect
  resources. Claude never writes "worker" for a citizen.
- A purpose is what a building or a unit is for, like defense or science. A kind can serve
  many purposes.
- A PolicyOrder is an order that takes Policy, and a CommandOrder is an order that takes
  Command.
- Every order class has a name that ends in Order, because orders are modelled as object
  oriented classes: BuildTargetOrder is the order class for what Claude had been calling a
  BuildTarget, one thing an order aims to have built. Class names like BuildTarget are fine to talk in for now, and the names a
  screen shows are worked out later. Claude does not describe the model in words that assume
  a particular screen, like "row".
- A MilitaryTarget is a location to attack. A MilitaryTarget is not an order: an order
  mentions a MilitaryTarget. A target can be a city, a point or a region.
- A ResourcesPolicyOrder is the order for what the citizens look for first, like food first.
  The user first called this ResourcesTarget, and renamed the order so that "target" only
  means something like a position on the map.
- An ImproveOrder is the order for a city to build an engineer, which the helper AI sends to
  improve the city's tiles.
- A BuildOrder is the order attached to a city that lists the buildings to build, in order
  of priority. Claude first called this a BuildingsOrder.
- A base is a city that a division lists as a place that can build units for the division.
- Currency is the primary resource, which the user first called gold. Claude doesn't write "the
  stock" for what a civilization holds of its resources: the user doesn't know the word. The
  user's own word for what a civilization holds is the bank of the civilization.
- A strategic resource is a resource like iron that is not collected and not consumed: a
  civilization with the resource within its borders can build the units that require the
  resource. Claude first called these controlled resources, and the user's word is strategic.
