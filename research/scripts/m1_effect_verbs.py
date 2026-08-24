"""M1 probe: can oracle text recover the Forge *effect API* vocabulary?

M0 (research/oracle-grammar-m0.md) showed oracle text recovers the ability-kind
inventory at 90.2%. M1 asks the harder question: for each face, can a grammar
name the same effect APIs Forge's scripts encode -- ChangeZone, Pump, Draw,
Token, PutCounter, DealDamage ...

Method differs from M0 in one important way: productions are developed against a
**dev half** and scored on a **held-out half**, split by a stable hash of the
card name. M0 developed and scored on the same faces, so its number was
optimistic by an unknown margin; this one is not.

  Predictor input:  oracle text + type line.
  Ground truth:     the set of `api` values over all nodes of the face
                    (ability roots and SVar sub-abilities alike), minus the
                    control-flow APIs listed in NON_TEXTUAL below.
  Unit:             one face, scored as set precision/recall over APIs.

Sets rather than multisets: M1 asks whether the grammar can *name* the effects,
not yet how many times each fires. Counting is M2's problem, together with the
cost/effect and target-restriction distinctions the adversarial slice turns on.

One production is load-bearing beyond its size: effect verbs are matched only
against the *effect* span of a line, never the cost span. That is the a01
cost-vs-effect distinction from research/graph-vs-flat-ablation.md -- "sacrifice
a creature" left of the colon is a cost, right of it is an effect, and a grammar
that ignores the colon reproduces exactly the BM25 failure the graph tier exists
to avoid.

Usage:
    python3 research/scripts/m1_effect_verbs.py <cards.jsonl[.gz]> [out.json]
    python3 research/scripts/m1_effect_verbs.py <cards.jsonl[.gz]> [out.json] --split dev
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m0_oracle_segment import (  # noqa: E402
    ABILITY_WORD_RE, COST_LEAD_RE, LOYALTY_BRACKET_RE, LOYALTY_RE,
    NAMED_COST_RE, TRIGGER_RE, load_records, oracle_lines,
)

# APIs that are engine control flow or bookkeeping: they have no verb of their
# own in oracle text, so a text grammar cannot be expected to name them and
# scoring against them would measure the wrong thing.
NON_TEXTUAL = {
    "Cleanup",         # tears down temporary continuous effects
    "Charm",           # modal wrapper around 'Choose one --' sub-abilities
    "Effect",          # generic continuous-effect container
    "DelayedTrigger",  # 'at end of turn, ...' scheduling wrapper
    "ImmediateTrigger",
    "RepeatEach", "Repeat",
    "Branch", "GenericChoice",
    "StoreSVar", "NoteCounters", "InternalHaunt",
    "Pull", "DebugTargets",
}


def _p(api: str, pattern: str) -> tuple[str, re.Pattern]:
    return api, re.compile(pattern, re.I)


# Oracle text spells small numbers as words.
NUM = (r"(?:\d+|X|a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
       r"that many|that much|any number of)")
KEYWORD_ALT = (r"flying|trample|haste|vigilance|menace|reach|first strike|"
               r"double strike|deathtouch|lifelink|hexproof|indestructible|"
               r"protection|shroud|defender|fear|intimidate|flash|ward")
# A one-shot pump has a duration; a permanent grant ('creatures you control
# have flying') is a static in Forge, not a Pump node.
DURATION = r"until (?:end of turn|your next turn|end of combat)"


# Effect-verb productions, ordered top-frequency-first (phase 1 §2 build order).
PRODUCTIONS = [
    _p("Draw",        r"\bdraws?\b[^.]{0,30}\bcards?\b"),
    _p("Token",       r"\bcreates?\b[^.]{0,80}\btokens?\b"),
    _p("PutCounter",  r"\bputs?\b[^.]{0,60}\bcounters?\b\s+on\b"),
    _p("DealDamage",  r"\bdeals?\b[^.]{0,40}\bdamage\b"),
    _p("DamageAll",   r"\bdeals?\b[^.]{0,30}\bdamage to each\b"),
    _p("GainLife",    r"\bgains?\b[^.]{0,25}\blife\b"),
    _p("LoseLife",    r"\bloses?\b[^.]{0,25}\blife\b"),
    _p("Destroy",     r"\bdestroys?\b\s+(?:target|that|it|each|up to|all|any)"),
    _p("DestroyAll",  r"\bdestroys?\b\s+all\b"),
    _p("Mana",        r"\badds?\b\s*(?:\{|one mana|two mana|three mana|X mana|"
                      r"that much|an amount of mana|mana of any)"),
    _p("Discard",     r"\bdiscards?\b\s+(?:a|one|two|three|that|those|all|his|her|their|\d|X)"),
    _p("Tap",         r"\btaps?\b\s+(?:target|that|it|up to|another)"),
    # 'enters tapped' is a Tap node hanging off the ETB replacement in Forge.
    _p("Tap",         r"\benters?\b[^.]{0,40}\btapped\b"),
    _p("TapAll",      r"\btaps?\b\s+all\b"),
    _p("Untap",       r"\buntaps?\b\s+(?:target|that|it|up to|another)"),
    _p("UntapAll",    r"\buntaps?\b\s+all\b"),
    _p("Mill",        rf"\bmills?\b\s*{NUM}\b|\bmills?\b\s+cards?\b"),
    _p("Scry",        r"\bscry\b\s*(?:\d|X)"),
    _p("Surveil",     r"\bsurveil\b\s*(?:\d|X)"),
    _p("Sacrifice",   r"\bsacrifices?\b\s+(?:a|an|one|two|three|that|those|all|it|another|\d|X)"),
    _p("SacrificeAll", r"\bsacrifices?\b\s+all\b"),
    _p("Counter",     r"\bcounters?\b\s+(?:target|that|it|all)[^.]{0,30}\bspell"),
    _p("Fight",       r"\bfights?\b"),
    _p("Regenerate",  r"\bregenerates?\b"),
    _p("Attach",      r"\battach\b|\benchants?\b\s+(?:target|that)"),
    _p("Animate",     r"\bbecomes?\b[^.]{0,60}\bcreature\b"),
    # Granting a quoted ability is Animate, not Pump.
    _p("Animate",     rf"\bgains?\b\s+\"[^.]{{0,90}}{DURATION}"),
    _p("Dig",         r"\blooks?\b\s+at\s+the\s+top\b"),
    _p("Dig",         r"\breveals?\b\s+the\s+top\b"),
    _p("Dig",         r"\bexiles?\b\s+the\s+top\b"),
    _p("Explore",     r"\bexplores?\b"),
    _p("Investigate", r"\binvestigates?\b"),
    _p("Clash",       r"\bclash(?:es)?\b"),
    _p("Proliferate", r"\bproliferates?\b"),
    _p("Populate",    r"\bpopulates?\b"),
    _p("Bolster",     r"\bbolsters?\b"),
    _p("Monstrosity", r"\bmonstrosity\b"),
    _p("Adapt",       r"\badapts?\b\s*\d"),
    _p("Amass",       r"\bamass(?:es)?\b"),
    _p("Manifest",    r"\bmanifests?\b"),
    _p("SetState",    r"\btransforms?\b|\bflips?\s+it\b|\bturns?\b[^.]{0,20}\bface up\b"),
    _p("SetLife",     r"\blife total becomes\b"),
    _p("ExchangeLife", r"\bexchanges?\b[^.]{0,25}\blife totals?\b"),
    # A tutor's trailing shuffle is folded into the ChangeZone node's params,
    # so only a standalone shuffle is its own node.
    _p("Shuffle",     r"^(?:(?!\bsearch\b).)*\bshuffles?\b"),
    _p("ChooseCard",  r"\bchooses?\b\s+(?:a|one|two|X)\s+card"),
    _p("ChooseColor", r"\bchooses?\b\s+a\s+color\b"),
    _p("ChooseType",  r"\bchooses?\b\s+a\s+(?:creature\s+)?type\b"),
    _p("NameCard",    r"\bnames?\b\s+a\s+card\b"),
    # 'exile ... you may play it' is the impulse pattern: a Continuous static
    # with MayPlay$ True (phase 1 §5 Q2), not a Play node.
    _p("Play",        r"^(?:(?!\bexile\b).)*\bmay\b\s+(?:play|cast)\b"),
    _p("CopySpell",   r"\bcop(?:y|ies)\b[^.]{0,30}\bspell\b"),
    _p("CopyPermanent", r"\bcop(?:y|ies)\b[^.]{0,40}\b(?:creature|permanent|artifact)\b"),
    # A P/T change is a Pump node only when it is one-shot. A continuous boost
    # ('creatures you control get +1/+1') is an S:Mode$ Continuous static with
    # AddPower$/AddToughness$ params and carries no api at all.
    _p("Pump",        rf"\bgets?\b\s*[+\-−–](?:\d|X)[^.]{{0,60}}(?:{DURATION}|perpetually)"),
    _p("PumpAll",     rf"\b(?:creatures|permanents)\b[^.]{{0,40}}\bget\b\s*[+\-−–]"
                      rf"[^.]{{0,60}}(?:{DURATION}|perpetually)"),
    _p("PumpAll",     rf"\b(?:creatures|permanents)\b[^.]{{0,40}}\bgain\b[^.]{{0,40}}{DURATION}"),
    _p("Debuff",      r"\bloses?\b[^.]{0,40}\b(?:flying|trample|haste|vigilance|"
                      r"first strike|deathtouch|lifelink|hexproof|indestructible)\b"),
    # Pump also covers ability grants ('gains flying') -- phase 1 §6's
    # conflation. A grant only becomes a Pump node when it has a duration;
    # 'creatures you control have flying' is a static, not a Pump.
    _p("Pump",        rf"\bgains?\b\s+(?:{KEYWORD_ALT})\b[^.]{{0,60}}{DURATION}"),
    # ChangeZone is the conflated zone-mover (phase 1 §6): destroy-and-reanimate,
    # bounce, tuck, exile and tutor all collapse into it.
    _p("ChangeZone",  r"\breturns?\b[^.]{0,80}\bto\b[^.]{0,40}\b(?:hand|battlefield|library|graveyard)\b"),
    _p("ChangeZone",  r"\bputs?\b[^.]{0,60}\bon\s+top\s+of\b[^.]{0,30}\blibrar"),
    _p("ChangeZone",  rf"\bexiles?\b\s+(?:target|that|it|up to|the|another|{NUM})"),
    _p("ChangeZone",  r"\bputs?\b[^.]{0,60}\bonto the battlefield\b"),
    _p("ChangeZone",  r"\bsearch(?:es)?\b\s+(?:your|their|his|her)\s+librar"),
    _p("ChangeZoneAll", r"\breturns?\b\s+all\b|\bexiles?\b\s+all\b"),
]

TRIGGER_HEAD_RE = re.compile(
    r"^(?:when|whenever|at)\b[^,]{0,120},\s*", re.I)


def effect_span(line: str) -> str:
    """Return the part of an ability line that is its *effect*.

    Costs are stripped: everything left of an activated ability's colon, and a
    triggered ability's event clause. This is the a01 cost-vs-effect
    distinction -- 'Sacrifice a creature:' is a cost, not a Sacrifice effect.
    """
    line = ABILITY_WORD_RE.sub("", line, count=1)
    if LOYALTY_RE.match(line) or LOYALTY_BRACKET_RE.match(line):
        return line.partition(":")[2]
    head, sep, tail = line.partition(":")
    if sep and len(head) <= 80:
        h = head.strip()
        if COST_LEAD_RE.match(h) or NAMED_COST_RE.match(h):
            return tail
    if TRIGGER_RE.match(line):
        stripped = TRIGGER_HEAD_RE.sub("", line, count=1)
        if stripped != line:
            return stripped
    return line


def predict_apis(rec: dict) -> set[str]:
    found: set[str] = set()
    for line in oracle_lines(rec.get("oracle") or ""):
        span = effect_span(line)
        for api, rx in PRODUCTIONS:
            if rx.search(span):
                found.add(api)
    return found


def truth_apis(rec: dict) -> set[str]:
    return {n["api"] for n in rec["nodes"]
            if n.get("api") and n["api"] not in NON_TEXTUAL}


def split_of(rec: dict) -> str:
    h = hashlib.sha1((rec.get("name") or "").encode("utf-8")).hexdigest()
    return "dev" if int(h, 16) % 2 == 0 else "holdout"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    want = "holdout"
    if "--split" in argv:
        want = argv[argv.index("--split") + 1]

    per_api = collections.defaultdict(collections.Counter)
    faces = exact = subset = 0
    tp_tot = fp_tot = fn_tot = 0
    miss_examples = collections.defaultdict(list)

    for rec in load_records(argv[1]):
        if want != "all" and split_of(rec) != want:
            continue
        t = truth_apis(rec)
        if not t and not (rec.get("oracle") or "").strip():
            continue
        faces += 1
        p = predict_apis(rec)
        tp, fp, fn = p & t, p - t, t - p
        tp_tot += len(tp); fp_tot += len(fp); fn_tot += len(fn)
        if p == t:
            exact += 1
        if t and t <= p:
            subset += 1
        for a in tp: per_api[a]["tp"] += 1
        for a in fp: per_api[a]["fp"] += 1
        for a in fn:
            per_api[a]["fn"] += 1
            if len(miss_examples[a]) < 3:
                miss_examples[a].append({
                    "name": rec.get("name"),
                    "oracle": (rec.get("oracle") or "")[:170]})

    micro_p = 100 * tp_tot / (tp_tot + fp_tot) if tp_tot + fp_tot else 0.0
    micro_r = 100 * tp_tot / (tp_tot + fn_tot) if tp_tot + fn_tot else 0.0
    rows = []
    for api, c in sorted(per_api.items(), key=lambda kv: -(kv[1]["tp"] + kv[1]["fn"])):
        support = c["tp"] + c["fn"]
        rows.append({
            "api": api, "support": support,
            "recall_pct": round(100 * c["tp"] / support, 1) if support else None,
            "precision_pct": round(100 * c["tp"] / (c["tp"] + c["fp"]), 1)
            if (c["tp"] + c["fp"]) else None,
            "fp": c["fp"],
        })

    report = {
        "split": want,
        "faces_scored": faces,
        "exact_api_set_match_pct": round(100 * exact / faces, 2) if faces else None,
        "truth_fully_covered_pct": round(100 * subset / faces, 2) if faces else None,
        "micro_precision_pct": round(micro_p, 2),
        "micro_recall_pct": round(micro_r, 2),
        "api_instances": {"tp": tp_tot, "fp": fp_tot, "fn": fn_tot},
        "excluded_non_textual_apis": sorted(NON_TEXTUAL),
        "per_api": rows,
    }
    out = argv[2] if len(argv) > 2 and not argv[2].startswith("--") else None
    if out:
        full = dict(report)
        full["miss_examples"] = {k: v for k, v in miss_examples.items()}
        with open(out, "w", encoding="utf-8") as f:
            f.write(json.dumps(full, indent=1) + "\n")
    slim = dict(report)
    slim["per_api"] = rows[:30]
    print(json.dumps(slim, indent=1))
    if out:
        print(f"\nfull report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
