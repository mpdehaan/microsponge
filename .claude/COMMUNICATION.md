# How Claude and the user work together

These are the user's rules for how Claude talks to them and works with them on microsponge, kept
apart from the rules for the code (`.claude/STYLE.md`) so that they can be reviewed on their own.
`CLAUDE.md` imports this file, so it's in force in every session.

## The user's words

- The model is the document `GAME_RULES.md`: what the game is and how it's played, thought of as
  the rule book of a strategy game that was a board game. "Add this to the model" means write it
  into `GAME_RULES.md`.
- Model objects, or models, are code: the classes derived from the model.
- Rules, as in "your rules", are Claude's rules: `CLAUDE.md` and the files in `.claude/`. The
  word is kept for those, which is why what the game does is called the model and not the rules.
- AI, about the game, is the computer players: algorithms that the user and Claude choose and
  write by hand in this project. It never means machine learning, a language model or Claude.
- A worker is a unit on the map that builds improvements, like roads. A citizen is one of the
  people of a city, and citizens are who collect resources. Claude never writes "worker" for a
  citizen.
- Currency is the primary resource, which the user first called gold. Claude doesn't write "the
  stock" for what a civilization holds of its resources: the user doesn't know the word. The
  user's own word for what a civilization holds is the bank of the civilization.
- A strategic resource is a resource like iron that is not collected and not consumed: a
  civilization with the resource within its borders can build the units that require the
  resource. Claude first called these controlled resources, and the user's word is strategic.
- AP is short for action points. The user may write AP, and the screens may write AP too.
- A city is always called a city when Claude talks to the user, even where a test plays a theme
  that has another word for a city. For caveman, Claude may write City("village") where the
  theme's word matters.
- Classic is the theme of historic earth in the style of a civilization game, the first one
  being developed. The user says "in classic" or, for another theme, something like "in scifi",
  to say which theme they're working on, and is talking about classic unless they say otherwise.
  What the user decides about one theme is kept in that theme's file, `.claude/THEMES_CLASSIC.md`
  for classic, `.claude/THEMES_SCIFI.md` for SciFi, the theme inspired by Stargate, which was
  first called SPACE, `.claude/THEMES_FANTASY.md` for fantasy, `.claude/THEMES_PLANETWARS.md` for PlanetWars and
  `.claude/THEMES_CAVEMAN.md` for caveman, and what holds for every theme is kept in the model.

## Who decides what

- The user makes every design decision about the game and has a strong say in the architecture.
  Claude asks for clarification where something is unclear and is free to suggest ideas, but a
  suggestion is built only once the user has agreed to it.
- Claude adds no creative ideas of its own without asking the user first, and never makes up
  sample units, civilizations or anything else that belongs in a theme without asking: what goes
  into a theme is the user's to choose.
- The game is designed in this order. The user describes the game, and everything the user says
  about how the game works is recorded when it's said, in the model, `GAME_RULES.md`, or in the
  theme's file, because the model classes are constructed from those records. The model objects,
  which are object oriented, are derived from the model and agreed. Before any screen is started,
  a whole game can be played entirely by the tests, and the game played that way is logical and
  good, which also helps to plan the screens. Only then is any screen built, and the user walks
  Claude through how each screen works before it's built.
- microsponge is not FreeCiv and is not a clone of FreeCiv, which the user doesn't play. Claude
  may occasionally look at what features FreeCiv has, and never copies FreeCiv's design.
- The user establishes the balance of units in conversation, as rough comparisons like "a
  legion is about 4 times stronger than a warrior", and Claude is to get used to that and still
  be able to control the numbers. Claude helps to turn the comparisons into numbers, may use
  FreeCiv's data to help while bearing in mind that the mechanics here are different, and
  checks the result with `tools/balance.py`. The balance conversations are kept in each theme's
  file, which the guide for that theme is later written from.
- Eventually the user will ask Claude to suggest units from FreeCiv to flesh out classic.
  Caveman comes first, so that the engine has complete tests.
- Claude always asks the user before incorporating any idea Claude has read about from another
  game, whichever game that is, and says which game the idea comes from. Nothing from another
  game goes into the model, a theme's file, `IDEAS.md` or the code until the user has said yes to
  that idea.
- Rough ideas from Civilization II and Alpha Centauri may be asked about in that way, but
  microsponge is only a homage and is not to come too close to either.
- The user is mostly not looking to change plans already made: a suggestion fills a gap the
  model leaves open, and a suggestion that would change something already in the model says so.

## Building and committing

- Commit directly to main when asked, as you go, with the full suite passing through the
  pre-commit hook, and never push unless asked in that conversation.
- A message that asks the user a question ends the turn: no building until they answer and agree.
- Flag names and layouts that don't fit, and suggest better ones. Point out where a feature that
  already exists does what's being asked, or where a new thing should look like an existing one,
  because consistency and usability matter more to the user than novelty.
- The user edits the wording of messages themselves, so a change doesn't need to name the `MSG_`,
  `ERR_` or `HELP_` constants it touched.
- An idea in `IDEAS.md` is removed as soon as it's built, without being asked, and ideas are added
  to it only when the user asks. Nothing in it is started or proposed unprompted: the user picks
  what to do from it, one item at a time.
- Decisions are recorded without their dates unless the date explains a reversal.
- When the user asks for a rule, or gives an instruction meant to last, it's discussed first, and
  then written into the repository's rules rather than into Claude's memory, which a reset can
  lose: into the `.claude/` file whose topic it belongs to (this file for how Claude and the user
  work together, `STYLE.md` for the code, `TESTING.md` for the tests, `UX.md` for how the text UI
  behaves), into the model, `GAME_RULES.md`, when it's about the game, into a theme's file like
  `THEMES_CLASSIC.md` when it's about one theme, and into `CLAUDE.md` only when it's about the
  project as a whole. `CLAUDE.md` stays short and orderly, and each other file stays on
  its topic.

## Discussing a feature

- In a discussion, concerns and questions share one running list of numbers, continued across
  replies rather than starting again at 1, so that the user can answer "on 11, yes" and both can
  see which numbers are still open. The reply lists what's unresolved by number at the end. Once
  every number is resolved, the next question may start again from 1. A number is never reused
  while anything numbered is open, and one reply never holds two lists that both start at 1:
  proposals, concerns, findings and questions put to the user all take numbers from the same
  running sequence, so that "1" means one thing. A reply that numbers its proposals 1 to 3 and
  its open questions 1 and 2 gets the answer "1 and 2", which can't be told apart.
- When Claude fills in an answer the user didn't give, it says which number it assumed and asks
  them to confirm.
- The user is not to be overwhelmed: a reply asks about five questions at most, the most
  important first, and when there are more, the rest wait until those are answered, and nothing
  is built in the meantime.
- Questions come one subject at a time. When a reply covers separate pieces of work, like a part
  of the model and a change to a screen, it asks its questions about one of them and waits until
  every one of those is settled before asking about the next, rather than listing the questions
  of both at once. The user finds batches that mix subjects too long to answer, and the
  follow-ups that come of them longer still.
- Each open question or concern repeats enough of its context to be understood on its own, even
  when that repeats an earlier message: a short reminder that depends on memory of the thread is
  harder to read than a longer one that doesn't. When a question is asked again, or an earlier
  one is referred to by number, the original question is reposted in full, updated with what has
  been learnt since, never shortened to a phrase: the user doesn't scroll up, so a number with a
  few words after it is unreadable. The same goes for the list of what's open at the end of a
  reply: that list restates every open question in full, as a complete question the user can
  answer from the list alone, never as a number with a phrase after it. The user has asked for
  this twice, and it is required.
- Claude writes in complete sentences, with the context a reader needs, the way an educated
  person talks, and not in shorthand. A list of nouns with no verb, like "Refused: an empty
  tile, an own unit, a kind the attacker cannot hit", is not a sentence and is not written;
  the same content reads "An attack is refused when the tile is empty, when the unit on the
  tile belongs to the attacker's own civilization, and when the attacker's kind cannot hit the
  kind of unit on the tile."
- What Claude says about a theme's unit is said of that theme: "in caveman, the angry bird
  cannot take a city" is about caveman's angry bird, and never a statement about angry birds
  in every theme. A property, like a unit that cannot take cities, is what the engine
  generalizes; the units that have the property are each theme's own.
- Usability and interface points are explained in terms of what the user would see and press, in
  the words the game uses on screen, naming the existing feature they build on. Code names come
  after, if they're needed at all.
- Pronouns are kept out of explanations and examples: write the name of the thing rather than
  "it", "this", "its" or "there", because the user can't tell which of several things a pronoun
  means, and an example that needs rereading to be understood is no example. Each example is
  complete: it says what the screen or the game holds before, which key is pressed where, and
  what is seen after. This rule is the one most often broken, and the user wants it stressed: a
  question's choices are named in full in the question itself, never as "all of them" or "the
  ones present", and the thing a question is about is introduced before the question is asked,
  not explained after it. So not "All of them, or only the ones present?" followed by a paragraph
  saying what "them" are, but "The F1 help screen could list every key of the game, or only the
  keys that work on the screen F1 was pressed on. Which?"
- A thing on the screen is named by what it is and where it is, never by a bare word like "the
  bar" or "the grid" that more than one thing answers to, and the same goes for the cursor: say
  which row, column or cell holds it. Where a word could still mean more than one thing, write
  "for example" and give one.
- Recaps say what was built, what was left out and why, and what's next, so that a reader who only
  sees the last message has the whole picture.
- A proposed change of wording comes as a general proposal with concrete before and after
  examples, so that the user can judge it on real messages.
- Software components go by their formal names: `__init__` and the like are special methods,
  never dunders, and so on for everything that has a proper name.
