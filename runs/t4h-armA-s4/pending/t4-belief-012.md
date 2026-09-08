# Puzzle: `t4-belief-012`

You are a Magic: The Gathering player facing a single decision. Somewhere
in this position is a line that wins the game THIS TURN. Find it.

**Write your answer to `../answers/t4-belief-012.txt`** and nothing else: the JSON
array only, no prose. You are standing in for a single model call — do not
run searches, read project files, or use tools; anything extra makes this
run incomparable to an API run.

## The position

It is turn 1. You are player A, in your precombat main phase with priority. Player B is the opponent.

YOU (player A) — life 20
your battlefield:
  - Barbarian Horde {3}{R} 3/3 — Creature — Human Barbarian Soldier
  - Goblin Hero {2}{R} 2/2 — Creature — Goblin
  - Mountain — Basic Land — Mountain
      text: ({T}: Add {R}.)
  - Mountain — Basic Land — Mountain
      text: ({T}: Add {R}.)
your hand:
  - Searing Spear {1}{R} — Instant
      text: Searing Spear deals 3 damage to any target.

OPPONENT (player B) — life 5
their battlefield:
  - Mountain — Basic Land — Mountain
      text: ({T}: Add {R}.)
  - Canal Monitor {4}{B} 5/3 — Creature — Lizard
their hand (known):
  - Lightning Bolt {R} — Instant

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

Rules context: every creature already on the battlefield may attack this
turn — treat battlefield permanents as having been under their controller's
control since the turn began (no summoning sickness on setup-placed
creatures).

The opponent is NOT passive in this position: they will pick their best
legal response to your line (for example, their best block assignment).
Your line only wins if it wins against EVERY response they could make —
a plan that needs them to block badly, or not at all, will lose.

Your line is executed by a rules engine exactly as written; the game ends
in a win only if your opponent is dead when it resolves. Use turn 1 for every action's "turn" field.
