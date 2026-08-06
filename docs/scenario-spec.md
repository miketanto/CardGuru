# Scenario spec (engine-neutral adjudication input)

A scenario is a JSON object describing a board state, a scripted sequence of actions and
decisions, a stop point, and optional expectations. The XMage driver
(`driver/CardGuruScenarioRunner.java`) executes it in strict-choose mode — every decision must
be scripted, any unscripted decision fails the run — and emits an outcome JSON. The spec
deliberately avoids engine-specific vocabulary so a second engine could run the same files.

```json
{
  "id": "lindblum-impulse",
  "description": "Impulse exile hitting an adventure land",
  "players": {
    "A": {
      "life": 20,
      "battlefield": [{"card": "Mountain", "count": 6}],
      "hand": ["Reckless Impulse"],
      "graveyard": [],
      "exile": [],
      "library_top": ["Lindblum, Industrial Regency", "Grizzly Bears"]
    },
    "B": {"life": 20}
  },
  "actions": [
    {"do": "cast",      "turn": 1, "phase": "PRECOMBAT_MAIN",  "player": "A", "card": "Reckless Impulse"},
    {"do": "wait_stack","turn": 1, "phase": "PRECOMBAT_MAIN"},
    {"do": "cast",      "turn": 1, "phase": "POSTCOMBAT_MAIN", "player": "A", "card": "Mage Siege"},
    {"do": "wait_stack","turn": 1, "phase": "POSTCOMBAT_MAIN"},
    {"do": "play_land", "turn": 1, "phase": "POSTCOMBAT_MAIN", "player": "A", "card": "Lindblum, Industrial Regency"}
  ],
  "stop": {"turn": 1, "phase": "END_TURN"},
  "expect": [
    {"check": "permanent_count", "player": "A", "card": "Wizard Token", "count": 1},
    {"check": "permanent_count", "player": "A", "card": "Lindblum, Industrial Regency", "count": 1},
    {"check": "tapped", "card": "Lindblum, Industrial Regency", "value": true},
    {"check": "exile_count", "player": "A", "card": "Grizzly Bears", "count": 1}
  ]
}
```

## Fields

**players** — `"A"` and `"B"`. Per player: `life` (default 20), `battlefield`
(list of `{"card", "count"?, "tapped"?}`), `hand`, `graveyard`, `exile` (lists of card names),
`library_top` (first element = top of library; implies no initial shuffle).

**actions** — executed in scripted order:

| `do` | Fields | Meaning |
|---|---|---|
| `cast` | turn, phase, player, card, [target_player] | Cast a spell (adventure faces by face name). `target_player` names a player the spell targets — use it instead of a `target` action for player-targeted spells |
| `play_land` | turn, phase, player, card | Take the land drop |
| `activate` | turn, phase, player, ability | Activate; `ability` is a text prefix, e.g. `"{T}: Add"` |
| `attack` | turn, player, attacker | Declare an attacker |
| `block` | turn, player, blocker, attacker | Declare a block |
| `wait_stack` | turn, phase | Let the stack fully resolve before the next action |
| `choice` | player, value | Answer the next decision (`"Yes"`/`"No"`/option text) |
| `target` | player, value | Answer the next target selection |
| `mode` | player, value | Answer the next modal choice (1-based index as string) |

`choice`/`target`/`mode` entries are queued per player and consumed in order as the engine
asks — this is what makes runs deterministic under strict mode.

**stop** — `{"turn": N, "phase": PHASE}`. Phases: `UPKEEP`, `DRAW`, `PRECOMBAT_MAIN`,
`BEGIN_COMBAT`, `DECLARE_ATTACKERS`, `DECLARE_BLOCKERS`, `COMBAT_DAMAGE`, `POSTCOMBAT_MAIN`,
`END_TURN`.

**expect** (optional) — checks recorded pass/fail in the outcome (they never abort the run):
`permanent_count` (player, card, count) · `exile_count` · `graveyard_count` · `hand_count`
(player, count) · `battlefield_count` (player, count — total permanents; useful when token
names vary) · `life` (player, value) · `tapped` (card, value) · `power_toughness`
(player, card, power, toughness).

## Outcome JSON

```json
{
  "id": "lindblum-impulse",
  "status": "executed",            // or "error" (unimplemented card, unscripted choice, engine exception)
  "error": null,
  "millis": 11449,
  "engine": "xmage",
  "expectations": [{"check": "permanent_count", "pass": true, "detail": "..."}, ...],
  "state": {
    "A": {"life": 20,
           "battlefield": [{"name": "Wizard Token", "tapped": false, "power": 0, "toughness": 1}, ...],
           "graveyard": ["Reckless Impulse"], "exile": ["Grizzly Bears"], "hand_count": 0},
    "B": {...}
  }
}
```

`status: "error"` is a first-class outcome — it is how the product knows to fall back to
retrieval-only answers instead of shipping a wrong simulation. Unimplemented cards fail at
setup with the engine's own message; cards on a set's `unfinished` list can be pre-screened
via `research/data/xmage_unfinished.json`.

## Running

```bash
# copy the driver into an XMage checkout (once)
cp driver/CardGuruScenarioRunner.java \
   <mage>/Mage.Tests/src/test/java/org/mage/test/serverside/

# batch-run every scenario in a directory
python -m cardguru adjudicate scenarios/*.json --mage-repo <mage>
```

The driver batches all scenarios through one JVM (reset between scenarios); marginal cost per
scenario is ~0.1–12s depending on complexity, after ~40s of JVM+DB warmup per batch.
