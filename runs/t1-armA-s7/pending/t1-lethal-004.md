# Puzzle: `t1-lethal-004`

You are a Magic: The Gathering player facing a single decision. Somewhere
in this position is a line that wins the game THIS TURN. Find it.

**Write your answer to `../answers/t1-lethal-004.txt`** and nothing else: the JSON
array only, no prose. You are standing in for a single model call — do not
run searches, read project files, or use tools; anything extra makes this
run incomparable to an API run.

## The position

It is turn 1. You are player A, in your precombat main phase with priority. Player B is the opponent.

YOU (player A) — life 20
your battlefield:
  - Headwater Sentries {3}{U} 2/5 — Creature — Merfolk Warrior
  - Bane Alley Blackguard {1}{B} 1/3 — Creature — Human Rogue
  - Earth Elemental {3}{R}{R} 4/5 — Creature — Elemental
  - Balduvian Bears {1}{G} 2/2 — Creature — Bear
  - Mountain — Basic Land — Mountain
      text: ({T}: Add {R}.)
your hand:
  - Lightning Bolt {R} — Instant
      text: Lightning Bolt deals 3 damage to any target.

OPPONENT (player B) — life 11
their battlefield:
  - Island — Basic Land — Island (TAPPED)
      text: ({T}: Add {U}.)
  - Island — Basic Land — Island (TAPPED)
      text: ({T}: Add {U}.)
  - Island — Basic Land — Island (TAPPED)
      text: ({T}: Add {U}.)
  - Island — Basic Land — Island (TAPPED)
      text: ({T}: Add {U}.)
  - Merfolk of the Pearl Trident {U} 1/1 — Creature — Merfolk (TAPPED)

## How to answer

Answer with a LINE: a JSON array of action objects, executed in order.
Action vocabulary (all fields required unless marked optional):

  {"do": "cast", "turn": T, "phase": "PRECOMBAT_MAIN" | "POSTCOMBAT_MAIN",
   "player": "A", "card": "Name", "target_player": "A" | "B" (optional)}
      Cast a spell from your hand. Use target_player for spells that
      target a player. Casting taps your untapped lands to pay the cost.
  {"do": "play_land", "turn": T, "phase": ..., "player": "A", "card": "Name"}
  {"do": "activate", "turn": T, "phase": ..., "player": "A",
   "ability": "text prefix, e.g. {T}: Add"}
  {"do": "attack", "turn": T, "player": "A", "attacker": "Name"}
      One entry per attacker. Attacking taps the creature.
  {"do": "block", "turn": T, "player": "A", "blocker": "Name",
   "attacker": "Name"}
      One entry per blocking creature.
  {"do": "wait_stack", "turn": T, "phase": ...}
      Let the stack fully resolve before the next action.
  {"do": "choice" | "target" | "mode", "player": "A", "value": "..."}
      Answers the engine's next question for that player, in order.

Notation for edge cases:
  - Two permanents share a name: suffix a zero-based index by battlefield
    entry order — "Grizzly Bears:1" is the second Bears.
  - You attack and 2+ creatures block one of your attackers: you must
    assign that attacker's combat damage with consecutive choice entries,
    one per blocker in block order: {"do": "choice", "player": "A",
    "value": "X=2"} assigns 2 damage to the next blocker.

Your line is executed by a rules engine exactly as written; the game ends
in a win only if your opponent is dead when it resolves. Use turn 1
for every action's "turn" field.
