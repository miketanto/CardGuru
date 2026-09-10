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
            if request.get("kind") == "leaf_eval":
                # A yield attached to a search reply must not swallow the
                # escalation of the SAME window: when the driver cannot use
                # the scores (short list, cast unwound) it re-asks this
                # window as a plain priority decision, and auto-passing that
                # is how sonnet went eight turns without playing a land.
                self.active["skip"] = (request.get("turn"),
                                       request.get("phase"))
            return until
        return None

    def covers(self, request):
        y = self.active
        if not y:
            return False
        if request.get("kind") != "priority":
            self.active = None
            return False
        if y.get("skip") == (request.get("turn"), request.get("phase")):
            y["skip"] = None
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


PHASE_CLASS = {
    "Upkeep": "upkeep", "Draw": "draw", "Precombat Main": "main1",
    "Begin Combat": "combat", "Declare Attackers": "combat",
    "Declare Blockers": "combat", "Combat Damage": "combat",
    "End Combat": "combat", "Postcombat Main": "main2", "End Turn": "end",
}
PHASE_ORDER = ["upkeep", "draw", "main1", "combat", "main2", "end"]

# Event vocabulary the bridge can detect from consecutive requests. The
# pilot writes rules against these; anything it cannot express falls to
# "otherwise", whose default is ask.
EVENT_VOCAB = [
    "they_cast:<card name | removal | counter | creature | any>",
    "they_block:<my attacker name | any>",
    "no_block:<my attacker name | any>",
    "my_creature_lost:<name | any>",
    "enemy_creature_gained:<name | any>",
    "life_below:<N>",
    "they_tapped_out",
    "otherwise",
]
ACTION_VOCAB = [
    "pass", "ask", "cast <card name>", "play <land name>",
    "activate <ability text fragment>", "attack_all", "attack_none",
    "attack <name, name>", "no_block", "block <blocker>-><attacker>; ...",
    "any cast/activate may add ' @ <target name>'",
]


class TurnPlanner:
    """Contingent turn plans: one pilot call per turn produces steps and
    if->then rules; the bridge executes them against the menus and state
    diffs and escalates only what the plan did not cover.

    Every window used to be an independent question, so a turn with 25
    priority windows cost 25 answers to what was really one decision
    ("hold Drowner unless they tap out"). The plan is that decision written
    once. Safety rule: an event with no matching rule escalates; it never
    silently passes."""

    REMOVAL_WORDS = ("destroy target", "exile target", "gets -", "deals",
                     "put two stun counters")
    COUNTER_WORDS = ("counter target",)

    def __init__(self, log, escalate, card_ref):
        self.log = log
        self.escalate = escalate
        self.card_ref = card_ref          # name -> {types, text}
        self.plan = None
        self.plan_key = None              # (turn, active)
        self.done = set()
        self.snap = None
        self.pending_target = None
        self.asked_loose = set()          # (turn, phase, castables) asked once
        self.stats = {"plans": 0, "by_plan": 0, "escalated": 0,
                      "events_unhandled": 0}

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _creatures(side):
        return [c for c in (side or {}).get("battlefield", [])
                if isinstance(c, dict) and "power" in c]

    @staticmethod
    def _norm(s):
        return (s or "").lower().strip()

    def _snapshot(self, request):
        st = request.get("state") or {}
        a, b = st.get("A") or {}, st.get("B") or {}
        return {"my_creatures": [c["name"] for c in self._creatures(a)],
                "enemy_creatures": [c["name"] for c in self._creatures(b)],
                "life": a.get("life", 20),
                "stack_seen": tuple(request.get("stack") or [])}

    def _spell_class(self, name):
        ref = self.card_ref.get(name) or {}
        text = self._norm(ref.get("text", ""))
        types = self._norm(ref.get("types", ""))
        if "creature" in types:
            return "creature"
        if any(w in text for w in self.COUNTER_WORDS):
            return "counter"
        if any(w in text for w in self.REMOVAL_WORDS):
            return "removal"
        return "unknown"

    def _events(self, request):
        """Events since the last snapshot, each as (type, arg)."""
        ev = []
        if not self.snap:
            return ev
        st = request.get("state") or {}
        a, b = st.get("A") or {}, st.get("B") or {}
        stack = [s for s in (request.get("stack") or []) if "(theirs)" in s]
        for s in stack:
            if s not in self.snap["stack_seen"]:
                name = s.split(" (")[0]
                ev.append(("they_cast", name))
        mine = [c["name"] for c in self._creatures(a)]
        for n in self.snap["my_creatures"]:
            if mine.count(n) < self.snap["my_creatures"].count(n):
                ev.append(("my_creature_lost", n))
        theirs = [c["name"] for c in self._creatures(b)]
        for n in theirs:
            if theirs.count(n) > self.snap["enemy_creatures"].count(n):
                ev.append(("enemy_creature_gained", n))
        if a.get("life", 20) < self.snap["life"]:
            ev.append(("life_below", a.get("life", 20)))
        lands_up = [p for p in b.get("battlefield", [])
                    if isinstance(p, dict) and "power" not in p
                    and not p.get("tapped")]
        if request.get("active") == "A" and not lands_up \
                and self.snap.get("they_had_mana", True):
            ev.append(("they_tapped_out", None))
        # Blocks: visible on my turn once blockers are declared.
        if request.get("active") == "A" and request.get("phase") in (
                "Declare Blockers", "Combat Damage") and not self.snap.get("blocks_seen"):
            attackers = [c for c in self._creatures(a) if c.get("attacking")]
            if attackers:
                blocked = set()
                for c in self._creatures(b):
                    for n in c.get("blocking") or []:
                        blocked.add(n)
                for c in attackers:
                    ev.append(("they_block" if c["name"] in blocked else "no_block",
                               c["name"]))
                self.snap["blocks_seen"] = True
        return ev

    def _match_rule(self, event):
        etype, arg = event
        otherwise = None
        for rule in (self.plan or {}).get("rules") or []:
            cond = self._norm(rule.get("if"))
            if ":" in cond:
                ctype, carg = cond.split(":", 1)
            else:
                ctype, carg = cond, "any"
            if ctype in ("otherwise", "else", "default", "any"):
                # Explicit catch-all: the pilot chose what happens to events
                # it did not enumerate. Only consulted after specific rules.
                otherwise = otherwise or rule
                continue
            if ctype != etype:
                continue
            if etype == "life_below":
                try:
                    if arg < int(carg):
                        return rule
                except ValueError:
                    pass
                continue
            if etype == "they_cast" and carg in ("removal", "counter", "creature"):
                if self._spell_class(arg) == carg:
                    return rule
                continue
            if carg in ("any", "") or (arg and carg in self._norm(arg)):
                return rule
        return otherwise

    def _find_option(self, request, action):
        """Map an action string to an option index, or None."""
        act = self._norm(action)
        target = None
        if " @ " in act:
            act, target = act.split(" @ ", 1)
        opts = request.get("options") or []
        if act in ("pass", ""):
            return 0, None
        verb, _, rest = act.partition(" ")
        rest = rest.strip()
        for o in opts:
            t = self._norm(o.get("text"))
            if o.get("action") != "activate":
                continue
            if verb == "cast" and t.startswith("cast ") and rest and rest in t:
                return o["index"], target
            if verb == "play" and t.startswith("play ") and rest and rest in t:
                return o["index"], target
            if verb == "activate" and rest and rest in t and not t.startswith("cast "):
                return o["index"], target
        return None, None

    # ---- plan acquisition ---------------------------------------------
    def ensure_plan(self, request):
        key = (request.get("turn"), request.get("active"))
        if key == self.plan_key:
            return
        # My own turn's plan is written AFTER the draw: at the first window
        # in precombat main or later. Upkeep and draw windows run on the
        # previous (reactive) plan's rules — turn 9 of the first plan game
        # planned "Swamp, Preacher" at upkeep, drew Deep-Cavern Bat, and
        # passed postcombat with the Bat castable because no step named it.
        if request.get("active") == "A" and PHASE_CLASS.get(
                request.get("phase"), "main1") in ("upkeep", "draw"):
            return
        self.plan_key = key
        self.plan = None
        self.done = set()
        self.pending_target = None
        mine = request.get("active") == "A"
        preq = {"kind": "turn_plan", "turn": request.get("turn"),
                "phase": request.get("phase"), "active": request.get("active"),
                "whose_turn": "mine" if mine else "theirs",
                "mana_available": request.get("mana_available"),
                "state": request.get("state"), "stack": request.get("stack"),
                "menu_now": request.get("options"),
                "event_vocabulary": EVENT_VOCAB, "action_vocabulary": ACTION_VOCAB}
        resp = self.escalate(preq)
        plan = (resp or {}).get("turn_plan") if isinstance(resp, dict) else None
        if isinstance(plan, dict):
            self.plan = plan
            self.stats["plans"] += 1
        self.snap = self._snapshot(request)
        b = (request.get("state") or {}).get("B") or {}
        self.snap["they_had_mana"] = any(
            isinstance(p, dict) and "power" not in p and not p.get("tapped")
            for p in b.get("battlefield", []))
        self.log({"source": "llm", "request": preq, "response": resp,
                  "plan_stats": dict(self.stats)})

    def adopt(self, resp, request):
        """A pilot reply to an escalation may carry a revised turn_plan."""
        plan = resp.get("turn_plan") if isinstance(resp, dict) else None
        if isinstance(plan, dict):
            self.plan = plan
            self.done = set()
        self.snap = self._snapshot(request)

    # ---- execution -----------------------------------------------------
    def answer(self, request):
        """Return (response, note) if the plan decides this window, else None."""
        if not self.plan:
            return None
        kind = request.get("kind")
        events = self._events(request)
        for ev in events:
            rule = self._match_rule(ev)
            if rule is None:
                self.stats["events_unhandled"] += 1
                self.snap = self._snapshot(request)   # fire once
                return None
            then = self._norm(rule.get("then"))
            self.snap = self._snapshot(request)
            if then == "ask":
                return None
            if kind == "priority":
                idx, target = self._find_option(request, then)
                if idx is None:
                    return None
                self.pending_target = target
                return {"choice": idx}, f"rule {rule.get('if')} -> {then}"
            if kind == "attackers":
                r = self._attack_answer(request, then)
                if r is not None:
                    return r, f"rule {rule.get('if')} -> {then}"
                return None
            if kind == "blockers":
                r = self._block_answer(request, then)
                if r is not None:
                    return r, f"rule {rule.get('if')} -> {then}"
                return None
            return None
        if kind == "priority":
            if request.get("active") != "A":
                return {"choice": 0}, "their turn, no rule fired"
            phase = PHASE_CLASS.get(request.get("phase"), "any")
            steps = self.plan.get("steps") or []
            for i, step in enumerate(steps):
                if i in self.done:
                    continue
                sp = self._norm(step.get("phase") or "any")
                if sp not in ("any", phase):
                    # A step for an earlier phase that never fired: its
                    # assumption broke, ask rather than skip it silently.
                    if sp in PHASE_ORDER and phase in PHASE_ORDER \
                            and PHASE_ORDER.index(sp) < PHASE_ORDER.index(phase):
                        self.done.add(i)
                        return None
                    continue
                act = step.get("action") or step.get("do") or ""
                if self._norm(act) in ("pass", "hold", ""):
                    self.done.add(i)
                    continue
                idx, target = self._find_option(request, act)
                if idx is None:
                    self.done.add(i)
                    return None            # not on the menu: escalate
                self.done.add(i)
                self.pending_target = target
                return {"choice": idx}, f"step {i}: {act}"
            # No step left for this phase. If a spell or land is castable
            # that the plan neither named nor listed under "hold", ask once:
            # this is how a card drawn after planning gets a decision.
            if phase in ("main1", "main2"):
                held = [self._norm(h) for h in (self.plan.get("hold") or [])]
                planned = [self._norm(s.get("action") or s.get("do") or "")
                           for s in steps]
                loose = []
                for o in request.get("options") or []:
                    t = self._norm(o.get("text"))
                    if o.get("action") != "activate" or not (
                            t.startswith("cast ") or t.startswith("play ")):
                        continue
                    name = t.split(" ", 1)[1]
                    if any(h and h in name for h in held):
                        continue
                    if any(p and p.split(" ", 1)[-1] in name for p in planned):
                        continue
                    loose.append(name)
                if loose:
                    sig = (request.get("turn"), phase, tuple(sorted(loose)))
                    if sig not in self.asked_loose:
                        self.asked_loose.add(sig)
                        return None
            return {"choice": 0}, "no pending step this phase"
        if kind == "attackers":
            r = self._attack_answer(request, self.plan.get("attack"))
            return (r, f"attack: {self.plan.get('attack')}") if r is not None else None
        if kind == "blockers":
            r = self._block_answer(request, self.plan.get("blocks"))
            return (r, f"blocks: {self.plan.get('blocks')}") if r is not None else None
        if kind == "target" and self.pending_target:
            want = self._norm(self.pending_target)
            self.pending_target = None
            for o in request.get("options") or []:
                if want in self._norm(o.get("text")):
                    return {"targets": [o["index"]]}, f"target hint {want}"
            return None
        return None

    def _attack_answer(self, request, spec):
        opts = request.get("options") or []
        if spec is None:
            return None
        s = spec if isinstance(spec, list) else self._norm(str(spec))
        if s in ("ask", ""):
            return None
        if s in ("attack_all", "all"):
            return {"attackers": [o["index"] for o in opts]}
        if s in ("attack_none", "none"):
            return {"attackers": []}
        names = s if isinstance(s, list) else [n.strip() for n in
                                              s.replace("attack ", "", 1).split(",")]
        picked = [o["index"] for o in opts
                  if any(self._norm(n) and self._norm(n) in self._norm(o.get("name"))
                         for n in names)]
        return {"attackers": picked}

    def _block_answer(self, request, spec):
        if spec is None:
            return None
        s = spec if isinstance(spec, list) else self._norm(str(spec))
        if s in ("ask", ""):
            return None
        if s in ("no_block", "none"):
            return {"blocks": []}
        pairs = s if isinstance(s, list) else [p.strip() for p in
                                              s.replace("block ", "", 1).split(";")]
        blockers = request.get("blockers") or []
        attackers = request.get("attackers") or []
        out = []
        for p in pairs:
            if isinstance(p, (list, tuple)) and len(p) == 2:
                bname, aname = p
            elif isinstance(p, str) and "->" in p:
                bname, aname = p.split("->", 1)
            else:
                continue
            bi = next((b["index"] for b in blockers
                       if self._norm(bname) in self._norm(b.get("name"))), None)
            ai = next((a["index"] for a in attackers
                       if self._norm(aname) in self._norm(a.get("name"))), None)
            if bi is not None and ai is not None:
                out.append([bi, ai])
        return {"blocks": out}


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
    ap.add_argument("--turn-plan", action="store_true",
                    help="contingent turn plans: one pilot call per turn, the "
                         "bridge executes steps and if->then rules and "
                         "escalates only uncovered events (also switched on "
                         "by cardguru.turn_plan=true in CARDGURU_DRIVER_PROPS)")
    args = ap.parse_args()

    os.makedirs(args.esc_dir, exist_ok=True)
    corpus = believe.load_corpus()
    rng = random.Random(0)
    seq = {"n": 0}
    seen_cards: set = set()
    card_ref_all: dict = {}     # every card fact seen this game, for the planner

    def compact_state(request):
        """Full facts for every card VISIBLE in this request go into
        card_reference; the state itself carries name/tapped/pt/sick only.

        This used to send a card's text once per game and never again, which
        made "re-read what this card does" impossible — the pilot could only
        memorise, and anything it forgot was gone. Worse, pilot_daemon starts
        a FRESH session on its third retry, wiping every reference the game
        had sent so far; from that point the pilot was playing off card names
        alone. Re-sending what is currently on screen costs a few hundred
        tokens against the ~24k of fixed per-call overhead, and buys a pilot
        that can always look."""
        reference = {}

        def strip(card):
            name = card.get("name")
            if name:
                seen_cards.add(name)
                ref = {k: card[k] for k in ("cost", "types", "text",
                                            "power", "toughness") if k in card}
                if ref:
                    reference[name] = ref
                    card_ref_all[name] = ref
            return {k: card[k] for k in ("name", "tapped", "power",
                                         "toughness", "summoning_sick",
                                         "can_block", "status",
                                         "attacking", "blocking")
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

    # The pilot's standing intention, carried between decisions.
    #
    # A game is ~150 independent questions, and nothing used to travel
    # between them except whatever the pilot happened to still have in
    # conversation context. So it could not hold a plan: "keep Cut Down for
    # their Preacher", "do not tap out while they have {1}{U} open", "race
    # now, their board is empty" are all decisions ABOUT LATER WINDOWS, and
    # every later window arrived with no memory that the decision was made.
    # The pilot may set "plan" on any response; it is echoed back on every
    # subsequent request until it replaces it (or clears it with "").
    #
    # This lives in the harness rather than in the conversation on purpose:
    # pilot_daemon starts a fresh session on its third retry, and a plan
    # held only in context would vanish exactly when the pilot is already
    # confused.
    plan = {"text": None}

    def escalate(request):
        seq["n"] += 1
        n = seq["n"]
        payload = {"seq": n, "request": request,
                   "belief": belief_summary(request)}
        if plan["text"]:
            payload["standing_plan"] = plan["text"]
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
                        resp = json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass
                else:
                    if isinstance(resp, dict) and "plan" in resp:
                        p = resp.get("plan")
                        plan["text"] = p.strip() if isinstance(p, str) \
                            and p.strip() else None
                    return resp
            time.sleep(0.2)
        return None

    gate = YieldGate()

    # Turn-plan mode (A/B against per-window search): one env var switches
    # both sides — the driver stops searching at every window and just sends
    # menus; the bridge asks for a plan per turn and executes it.
    turn_plan_on = args.turn_plan or (
        "cardguru.turn_plan=true" in os.environ.get("CARDGURU_DRIVER_PROPS", ""))
    planner = TurnPlanner(log, escalate, card_ref_all) if turn_plan_on else None

    def policy(request):
        kind = request.get("kind")
        if kind == "priority" and not any(
                o.get("action") == "activate"
                for o in request.get("options", [])):
            resp = {"choice": 0}
            log({"source": "auto", "request": request, "response": resp})
            return resp
        if planner is not None:
            if kind in ("priority", "attackers", "blockers", "target"):
                planner.ensure_plan(request)
                hit = planner.answer(request)
                if hit is not None:
                    resp, note = hit
                    planner.stats["by_plan"] += 1
                    log({"source": "turn_plan", "request": request,
                         "response": resp, "plan_note": note})
                    return resp
                planner.stats["escalated"] += 1
        elif gate.covers(request):
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
        if planner is not None and planner.plan is not None:
            request = dict(request)
            request["turn_plan"] = planner.plan
            request["turn_plan_note"] = ("this window was not covered by your "
                                         "turn_plan; answer it, and optionally "
                                         "return a revised \"turn_plan\"")
        resp = escalate(request)
        source = "llm"
        if resp is None:
            resp = dumb_policy(request)
            source = "fallback-timeout"
        until = resp.pop("yield_until", None) if isinstance(resp, dict) else None
        until = gate.set(until, request) if planner is None else None
        if planner is not None and isinstance(resp, dict):
            planner.adopt(resp, request)
        log({"source": source, "request": request, "response": resp,
             **({"yield_set": until} if until else {}),
             **({"plan_stats": dict(planner.stats)} if planner else {})})
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
