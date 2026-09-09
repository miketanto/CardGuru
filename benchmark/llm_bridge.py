"""Live game with an LLM answering the non-trivial decisions over a spool.

Runs one interactive game (real decks, MAD opponent, minimax attack search,
externalized sub-choices) where trivial decisions are auto-answered (a
priority with nothing castable passes; an empty blockers menu declines) and
every other decision is ESCALATED: the request plus a belief summary is
written to <esc-dir>/req-<n>.json, and the bridge blocks until the LLM (the
orchestrating session) writes <esc-dir>/resp-<n>.json. A response that does
not arrive within --timeout falls back to dumb_policy so the game never
wedges (logged as such).

Every decision — auto, llm, or fallback — appends to --log as one JSONL row
with the full request and response, which is the replay record.
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import believe  # noqa: E402
from cardguru.play import MatchClient, dumb_policy  # noqa: E402

# Rules-and-protocol system context shipped with every escalation, so the
# answering LLM reasons from stated rules rather than memorized Magic. Game
# three was lost partly to facts missing from the request (casting costs,
# the tapped-out crackback); this block states them.
RULES_CONTEXT = """\
You are playing Magic: The Gathering as player A in a live game. Rules facts
that MUST inform every decision:
- Turn order: untap, upkeep, draw, main, combat (declare attackers ->
  declare blockers -> damage), second main, end. Priority passes back and
  forth inside every step; 'pass' advances the game.
- Casting a spell taps your lands automatically to pay its cost. You never
  need to activate mana abilities by hand unless you want floating mana.
- ATTACKING TAPS the attacker (no vigilance here). Tapped creatures CANNOT
  block. Your attackers stay tapped until your next untap step, so an
  all-out attack leaves you unable to block the counter-attack.
- Creatures cast this turn have summoning sickness: they cannot attack
  (state marks them summoning_sick) but they CAN block.
- Blocked attackers deal damage to their blockers, not the player (no
  trample anywhere in these decks). A 1/1 chump-block absorbs the whole hit.
- Combat tricks (pumps) can be cast after blockers are declared.
- State fields: every card shows cost/types/text; 'tapped' and
  'summoning_sick' are authoritative. Trust the option menu for what is
  castable NOW -- if a spell is not offered, you cannot pay for it.
Response schemas by request kind:
  mulligan  -> {"mulligan": true|false}
  priority  -> {"choice": <option index>}      (0 is always pass)
  attackers -> {"attackers": [<option indices>]}   ([] = no attack)
  blockers  -> {"blocks": [[blockerIdx, attackerIdx], ...]}  (two pairs on
               one attacker = double block; [] = no blocks)
  target    -> {"targets": [<option indices>]}
  announce_x-> {"x": <int>}   mode/choice -> {"choice": <index>}   use -> {"use": bool}
Add a short "why" field to every response; it is logged, not sent to the engine.
"""


class YieldGate:
    """Client-side yield (mage-bench semantics): the pilot may attach
    "yield_until": "my_turn" | "end_of_turn" to any response; the bridge
    then auto-passes priority windows in-process until the target point,
    breaking early — so the decision escalates — if the situation changes:
    the opponent gains a creature, our life drops, or a non-priority
    decision arrives."""

    def __init__(self):
        self.active = None

    @staticmethod
    def _enemy(request):
        b = (request.get("state") or {}).get("B") or {}
        return sum(1 for c in b.get("battlefield", []) if "power" in c)

    @staticmethod
    def _life(request):
        a = (request.get("state") or {}).get("A") or {}
        return a.get("life", 20)

    @staticmethod
    def _holds_instant(request):
        """Do we hold an instant with untapped lands to cast it? Checked on
        the un-compacted request, which still carries card types."""
        a = (request.get("state") or {}).get("A") or {}
        hand = a.get("hand") or []
        has = any(isinstance(c, dict) and "Instant" in str(c.get("types", ""))
                  for c in hand)
        if not has:
            return False
        return any(not p.get("tapped") and "Land" in str(p.get("types", ""))
                   for p in a.get("battlefield", []))

    # Opponent-turn windows where instant-speed interaction actually matters.
    INTERACTION_WINDOWS = ("Declare Attackers", "Declare Blockers", "End Turn")

    def set(self, until, request):
        if until in ("my_turn", "end_of_turn"):
            self.active = {"until": until, "turn": request.get("turn"),
                           "enemy": self._enemy(request),
                           "life": self._life(request)}
            return until
        return None

    def covers(self, request):
        y = self.active
        if not y:
            return False
        if request.get("kind") != "priority":
            self.active = None
            return False
        if self._enemy(request) > y["enemy"] or self._life(request) < y["life"]:
            self.active = None
            return False
        # A yield must not swallow the windows where holding up an instant
        # is the whole point. Dimir g1: the pilot yielded past six windows
        # holding Cut Down with four untapped lands. Wake it at the
        # opponent's combat and end step whenever it can actually act.
        if request.get("active") == "B" \
                and request.get("phase") in self.INTERACTION_WINDOWS \
                and self._holds_instant(request):
            self.active = None
            return False
        turn, phase, active = (request.get("turn"),
                               request.get("phase"), request.get("active"))
        if y["until"] == "end_of_turn":
            if turn != y["turn"]:
                self.active = None
                return False
        else:  # my_turn
            if turn != y["turn"] and active == "A" and phase not in (
                    "Untap", "Upkeep", "Draw"):
                self.active = None
                return False
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--deck-a", default="mono_red_aggro")
    ap.add_argument("--deck-b", default="mono_green_stompy")
    ap.add_argument("--esc-dir", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--search", choices=["none", "attacks", "llm"],
                    default="none",
                    help="combat search: 'attacks' = in-JVM minimax with "
                         "heuristic leaves; 'llm' = rollouts at both combat "
                         "decisions with LLM-scored leaves (leaf_eval "
                         "requests); default none (LLM picks directly)")
    ap.add_argument("--minimax", action="store_true",
                    help="legacy alias for --search attacks")
    ap.add_argument("--seed", type=int, default=None,
                    help="fix the shuffle (both opening hands) for paired "
                         "or repeatable games")
    ap.add_argument("--opp-think-secs", type=int, default=None,
                    help="MAD wall-clock search limit; the driver defaults it "
                         "high so the node cap binds (18 = stock XMage)")
    ap.add_argument("--compact", action="store_true",
                    help="persistent-pilot mode: no per-request rules context, "
                         "card oracle text sent once per name (card_reference), "
                         "state stripped to name/tapped/pt/sick afterwards")
    args = ap.parse_args()

    os.makedirs(args.esc_dir, exist_ok=True)
    corpus = believe.load_corpus()
    rng = random.Random(0)
    seq = {"n": 0}
    seen_cards: set = set()

    def compact_state(request):
        """First appearance of a card name -> full facts into card_reference;
        afterwards the state carries name/tapped/pt/summoning_sick only."""
        reference = {}

        def strip(card):
            name = card.get("name")
            if name and name not in seen_cards:
                seen_cards.add(name)
                ref = {k: card[k] for k in ("cost", "types", "text",
                                            "power", "toughness") if k in card}
                if ref:
                    reference[name] = ref
            return {k: card[k] for k in ("name", "tapped", "power",
                                         "toughness", "summoning_sick",
                                         "can_block", "status")
                    if k in card}

        state = request.get("state") or {}
        for side in state.values():
            if isinstance(side.get("battlefield"), list):
                side["battlefield"] = [strip(c) for c in side["battlefield"]]
            if isinstance(side.get("hand"), list):
                side["hand"] = [strip(c) if isinstance(c, dict) else c
                                for c in side["hand"]]
        return reference

    def log(row):
        row["ts"] = round(time.time(), 1)
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def belief_summary(request):
        b = (request.get("state") or {}).get("B", {})
        seen = [p.get("name") for p in b.get("battlefield", [])
                if p.get("name")] + list(b.get("graveyard", []))
        if not corpus or not seen:
            return None
        try:
            return believe.response_probability(seen, corpus, hand_size=7,
                                                k=100, rng=rng)
        except Exception:
            return None

    def escalate(request):
        seq["n"] += 1
        n = seq["n"]
        payload = {"seq": n, "request": request,
                   "belief": belief_summary(request)}
        if args.compact:
            ref = compact_state(request)
            if ref:
                payload["card_reference"] = ref
        else:
            payload["context"] = RULES_CONTEXT
        tmp = os.path.join(args.esc_dir, f"req-{n}.json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1)
        os.rename(tmp, os.path.join(args.esc_dir, f"req-{n}.json"))
        resp_path = os.path.join(args.esc_dir, f"resp-{n}.json")
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            if os.path.exists(resp_path):
                # The answerer may not write atomically: reading between
                # creat and the final byte gives empty/partial JSON. Treat
                # that as not-ready and poll again (game one died to this).
                try:
                    with open(resp_path, encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass
            time.sleep(0.2)
        return None

    gate = YieldGate()

    def policy(request):
        kind = request.get("kind")
        if kind == "priority" and not any(
                o.get("action") == "activate"
                for o in request.get("options", [])):
            resp = {"choice": 0}
            log({"source": "auto", "request": request, "response": resp})
            return resp
        if gate.covers(request):
            resp = {"choice": 0}
            log({"source": "yield", "request": request, "response": resp})
            return resp
        # Blockers requests carry their menu in 'blockers'/'attackers', not
        # 'options' — checking 'options' here silently auto-declined every
        # block in the first demo game (the turn-16 Titanic Growth for 8).
        if kind == "blockers" and not request.get("blockers"):
            resp = {"blocks": []}
            log({"source": "auto", "request": request, "response": resp})
            return resp
        resp = escalate(request)
        source = "llm"
        if resp is None:
            resp = dumb_policy(request)
            source = "fallback-timeout"
        until = resp.pop("yield_until", None) if isinstance(resp, dict) else None
        until = gate.set(until, request)
        log({"source": source, "request": request, "response": resp,
             **({"yield_set": until} if until else {})})
        return resp

    mode = "attacks" if args.minimax else args.search
    mode = None if mode == "none" else mode
    with MatchClient(args.mage_repo, minimax=mode, subchoices=True,
                     deck_a=args.deck_a, deck_b=args.deck_b,
                     seed=args.seed,
                     opp_think_secs=args.opp_think_secs) as m:
        result = m.play(policy)
        trace = m.read_trace()
    log({"source": "result", "result": result, "minimax_trace": trace})
    with open(os.path.join(args.esc_dir, "DONE"), "w") as f:
        json.dump(result, f)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
