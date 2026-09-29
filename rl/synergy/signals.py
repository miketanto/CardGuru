"""Step 5 of the plan: map parsed scripts to emit / listen signals.

The mapping is keyed on Forge API names, trigger modes, cost verbs,
Count$ expressions and filter syntax -- never on card names. Every
entry in the tables below corresponds to a row in TALLIES.md; see
PRIMITIVES.md for the derivation and for what was left out on purpose.

A signal is an event plus a pattern:
  event    one of EVENTS (the primitive vocabulary)
  sub      counter type for counter events, '' otherwise
  pat      {types, neg, token, side, self}  -- what object it concerns
Emissions and listeners carry a `mech` tag (how the card relates to the
event) which sets tightness, and `src` (the script fragment) so every
edge downstream can explain itself.
"""
import json, re, os, sys, collections

# ---- primitive vocabulary (derived from TALLIES.md; see PRIMITIVES.md) ----
EVENTS = {
    "enter":       "a permanent enters the battlefield",
    "die":         "a permanent goes battlefield -> graveyard",
    "tograve":     "a card is put into a graveyard from anywhere (graveyard grows)",
    "reenter":     "a permanent returns to the battlefield from graveyard/exile (re-triggers ETB)",
    "cast":        "a spell is cast",
    "cast_target_own": "a spell is cast that targets a creature you control",
    "counter+":    "counters are put on a permanent",
    "activate_loyalty": "a loyalty ability is activated",
    "lifegain":    "you gain life",
    "draw":        "you draw a card",
    "discard":     "you discard a card",
    "scry":        "you scry",
    "surveil":     "you surveil",
    "prepare":     "a creature becomes prepared (FRA)",
    "attack":      "a creature attacks",
    "damage":      "damage is dealt",
    "mana":        "mana is produced (resource flow)",
}

# Tightness by mechanism. Trigger > condition > static > cost-consumer;
# intrinsic emissions (a card being a card) are weakest.
LISTEN_T = {"trigger": 1.0, "replacement": 0.9, "condition": 0.8, "cost_mod": 0.9,
            "static": 0.7, "consumes": 0.6, "resource": 0.7}
EMIT_T = {"effect": 1.0, "cost": 1.0, "loyalty": 1.0, "keyword": 0.9,
          "intrinsic": 0.5, "random": 0.6}

GENERIC_HEADS = {"Card", "Permanent", "Any", "Spell", "Object", ""}
KNOWN_BAD_SIDE = {"OppCtrl", "OppOwn", "YouDontCtrl"}


def parse_filter(expr):
    """'Creature.Other+YouCtrl,Planeswalker.YouCtrl' -> list of patterns."""
    out = []
    for alt in (expr or "").split(","):
        alt = alt.strip()
        if not alt:
            continue
        head, _, quals = alt.partition(".")
        q = [x for x in quals.split("+") if x] if quals else []
        pat = {"types": None, "neg": [], "token": None, "side": "any", "self": False,
               "counters": None, "prepared": None}
        if head == "Self" or "Self" in q:
            pat["self"] = True
        if head not in GENERIC_HEADS and head not in ("Self", "Opponent", "You", "Player"):
            pat["types"] = [head]
        for x in q:
            if x.startswith("non") and len(x) > 3 and x[3].isupper():
                pat["neg"].append(x[3:])
            elif x == "token":
                pat["token"] = True
            elif x in ("!token", "nonToken"):
                pat["token"] = False
            elif x in ("YouCtrl", "YouOwn"):
                pat["side"] = "you"
            elif x in KNOWN_BAD_SIDE:
                pat["side"] = "opp"
            elif x.startswith("counters_GE1_"):
                pat["counters"] = x.split("_")[-1]
            elif x == "prepared":
                pat["prepared"] = True
            elif x in ("Artifact", "Creature", "Legendary", "Enchantment", "Land",
                       "Planeswalker", "Instant", "Sorcery") or (x[:1].isupper() and x.isalpha()
                       and x not in ("Other", "Self", "IsRemembered", "IsTargeted")):
                pat.setdefault("also", []).append(x)
        out.append(pat)
    return out or [{"types": None, "neg": [], "token": None, "side": "any", "self": False,
                    "counters": None, "prepared": None}]


def type_set(types_line):
    return [t for t in (types_line or "").split() if t not in ("Legendary", "Basic", "Snow")] + \
           (["Legendary"] if "Legendary" in (types_line or "") else [])


def concrete(types, token=False, side="you", **kw):
    p = {"types": list(types), "neg": [], "token": token, "side": side, "self": False,
         "concrete": True, "counters": None, "prepared": None}
    p.update(kw)
    return p


def load_token_types(tokendir):
    info = {}
    if not tokendir or not os.path.isdir(tokendir):
        return info
    for fn in os.listdir(tokendir):
        if not fn.endswith(".txt"):
            continue
        txt = open(os.path.join(tokendir, fn), encoding="utf-8", errors="replace").read()
        m = re.search(r"^Types:(.*)$", txt, re.M)
        mana = [l for l in txt.splitlines() if l.startswith("A:") and "Mana" in l.split("|")[0]]
        amt = 0
        for l in mana:
            a = re.search(r"Amount\$\s*(\d+)", l)
            prod = re.search(r"Produced\$\s*([^|]+)", l)
            n = int(a.group(1)) if a else max(1, len((prod.group(1) if prod else "C").split()) if prod and "Combo" not in prod.group(1) else 1)
            amt = max(amt, n)
        info[fn[:-4]] = {"types": type_set(m.group(1)) if m else [], "mana": amt,
                         "sac_mana": any("Sac<" in l for l in mana)}
    return info


class Card:
    def __init__(self, rec, token_info):
        self.rec = rec
        self.name = rec["name"]
        self.faces = rec["faces"]
        self.emits, self.listens = [], []
        self.token_info = token_info
        self.types = sorted({t for f in self.faces for t in type_set(f["types"])})
        self.front_types = type_set(self.faces[0]["types"])
        self.cmc = self.faces[0]["cmc"]
        self.keywords = sorted({k.split(":")[0] for f in self.faces for k in f["keywords"]})
        self.prepare = rec.get("alt_mode") == "Prepare"

    def E(self, event, pat, mech, src, sub="", **extra):
        self.emits.append({"event": event, "sub": sub, "pat": pat, "mech": mech, "src": src, **extra})

    def L(self, event, pats, mech, src, sub="", **extra):
        for p in pats:
            if p.get("side") == "opp":
                continue  # an opponent-side listener is interaction, not synergy
            self.listens.append({"event": event, "sub": sub, "pat": p, "mech": mech, "src": src, **extra})


def self_pat(card, face_types):
    return {"types": face_types, "neg": [], "token": False, "side": "you", "self": True,
            "counters": None, "prepared": None}


def count_listens(card, expr, mech, src, face_types):
    """Count$... -> what the card wants more of. `expr` is the text after Count$."""
    head = re.match(r"[A-Za-z]+", expr)
    head = head.group(0) if head else ""
    rest = expr[len(head):].strip()
    rest = rest.split("/")[0].strip()
    if head == "ValidGraveyard":
        card.L("tograve", parse_filter(rest), mech, src)
    elif head == "Valid":
        card.L("enter", parse_filter(rest), mech, src)
    elif head == "ValidHand":
        card.L("draw", parse_filter(""), mech, src)
    elif head == "YouScryThisTurn":
        card.L("scry", parse_filter(""), mech, src)
    elif head == "YouSurveilThisTurn":
        card.L("surveil", parse_filter(""), mech, src)
    elif head == "LifeYouGainedThisTurn":
        card.L("lifegain", parse_filter(""), mech, src)
    elif head == "YouDrewThisTurn":
        card.L("draw", parse_filter(""), mech, src)
    elif head.startswith("ThisTurnEntered"):
        m = re.match(r"ThisTurnEntered_(\w+?)_from_(\w+?)_(.*)", expr)
        if m:
            dest, orig, filt = m.groups()
            if dest == "Graveyard" and orig == "Battlefield":
                card.L("die", parse_filter(filt), mech, src)
            elif dest == "Graveyard":
                card.L("tograve", parse_filter(filt), mech, src)
            elif dest == "Battlefield":
                card.L("enter", parse_filter(filt), mech, src)
    elif head.startswith("ThisTurnCast"):
        card.L("cast", parse_filter(expr.split("_", 1)[1] if "_" in expr else ""), mech, src)
    elif head.startswith("ThisTurnActivated") and "Loyalty" in expr:
        card.L("activate_loyalty", parse_filter(""), mech, src)
    elif head in ("CardCounters", "CounterNum"):
        sub = expr.split(".")[1].split("/")[0] if head == "CardCounters" and "." in expr else "*"
        card.L("counter+", [self_pat(card, face_types)], mech, src, sub=sub.upper())
    elif head == "xPaid":
        card.L("mana", parse_filter(""), "resource", src, demand="X")
    elif head == "Domain":
        card.L("enter", parse_filter("Land.YouCtrl"), mech, src)


def mana_amount(p):
    a = p.get("Amount", "1")
    if a.isdigit():
        n = int(a)
    else:
        n = 2  # variable amount; treat as a modest surplus
    prod = p.get("Produced", "C")
    if not prod.startswith(("Combo", "Any", "Chosen")) and " " in prod:
        n = max(n, len(prod.split()))
    return n


def mana_colors(p):
    prod = p.get("Produced", "C")
    if prod.startswith(("Any", "Chosen")):
        return list("WUBRG")
    return sorted({ch for ch in prod if ch in "WUBRG"})


def analyse(card):
    for fi, f in enumerate(card.faces):
        ft = type_set(f["types"])
        is_perm = any(t in ft for t in ("Creature", "Artifact", "Enchantment", "Planeswalker", "Land", "Battle"))
        is_spell = "Land" not in ft
        # ---- intrinsic emissions: what being this card does to game state ----
        if is_spell:
            cp = concrete(ft, prepared=True if (card.prepare and fi == 1) else None)
            card.E("cast", cp, "intrinsic", f"cast {f['name']}")
        if is_perm:
            card.E("enter", concrete(ft), "intrinsic", f"{f['name']} enters")
            if "Creature" in ft:
                card.E("attack", concrete(ft), "intrinsic", f"{f['name']} can attack")
        if any(t in ft for t in ("Instant", "Sorcery")):
            card.E("tograve", concrete(ft), "intrinsic", f"{f['name']} resolves to graveyard")

        # ---- keywords ----
        for kw in f["keywords"]:
            k = kw.split(":")[0].strip()
            if k == "Prowess":
                card.L("cast", parse_filter("Card.nonCreature"), "trigger", "K:Prowess")
            elif k == "Convoke":
                card.L("enter", parse_filter("Creature.YouCtrl"), "cost_mod", "K:Convoke")
            elif k == "Flashback":
                card.L("tograve", [self_pat(card, ft)], "consumes", "K:Flashback")
            elif k == "TypeCycling" or k == "Cycling":
                card.E("discard", concrete(ft), "keyword", f"K:{k}")
                card.E("tograve", concrete(ft), "keyword", f"K:{k}")
                card.E("draw", concrete([]), "keyword", f"K:{k}")
            elif k == "etbCounter":
                ct = kw.split(":")[1] if ":" in kw else "P1P1"
                card.E("counter+", self_pat(card, ft), "keyword", f"K:{kw}", sub=ct.upper())
            elif k == "Lifelink":
                card.E("lifegain", concrete([]), "keyword", "K:Lifelink")
        if card.prepare and fi == 0:
            card.L("prepare", [self_pat(card, ft)], "trigger", "Prepare card: re-prepared by others")

        # which SVars feed a self cost reduction (edge type = cost modification)
        cost_svars = set()
        for ab in f["abilities"]:
            if ab["kind"] == "S" and ab["api"] == "ReduceCost":
                amt = ab["params"].get("Amount", "")
                if not amt.isdigit():
                    cost_svars.add(amt)

        for ab in f["abilities"]:
            analyse_ability(card, f, ft, ab, cost_svars)

        for sv, raw in f["svars"].items():
            for m in re.finditer(r"Count\$(\S+(?: [^|]+)?)", raw):
                mech = "cost_mod" if sv in cost_svars else "condition"
                count_listens(card, m.group(1).strip(), mech, f"SVar:{sv}:{raw[:60]}", ft)


def target_pats(p, default_self_types):
    for key in ("ValidTgts", "Defined", "ValidCards", "ValidCard", "ChangeType"):
        v = p.get(key)
        if v:
            if v in ("Self", "Card.Self") or v.startswith("Self"):
                return [{"types": default_self_types, "neg": [], "token": False, "side": "you",
                         "self": True, "counters": None, "prepared": None}]
            if v in ("You", "Player", "Opponent", "Targeted", "Remembered", "Enchanted",
                     "Equipped", "TriggeredCard", "ParentTarget"):
                return parse_filter("")
            return parse_filter(v)
    return [{"types": default_self_types, "neg": [], "token": False, "side": "you", "self": True,
             "counters": None, "prepared": None}]


def analyse_ability(card, f, ft, ab, cost_svars):
    k, head, api, p = ab["kind"], ab["head"], ab["api"], ab["params"]
    src = f"{k}{':'+ab['id'] if ab['id'] else ''} {head}${api}"
    cost = p.get("Cost", "")
    is_loyalty = "LOYALTY" in cost or p.get("Planeswalker") == "True"

    # ---- costs: emissions (sac / discard / exile) and consumption ----
    if cost:
        for m in re.finditer(r"(\w+)<([^>]*)>", cost):
            verb, arg = m.group(1), m.group(2)
            parts = arg.split("/")
            filt = parts[1] if len(parts) > 1 else "Card"
            if verb == "Sac":
                if "CARDNAME" in filt or filt == "Self":
                    card.E("die", self_pat(card, ft), "cost", f"{src} Cost$ Sac self")
                else:
                    pats = parse_filter(filt)
                    for pp in pats:
                        pp["side"] = "you"
                        card.E("die", pp, "cost", f"{src} Cost$ Sac<{arg}>")
                    card.L("enter", pats, "consumes", f"{src} Cost$ Sac<{arg}> (needs fodder)")
            elif verb == "Discard":
                card.E("discard", concrete([]), "cost", f"{src} Cost$ Discard")
                card.E("tograve", {"types": None, "neg": [], "token": False, "side": "you",
                                   "self": False, "counters": None, "prepared": None},
                       "random", f"{src} Cost$ Discard")
                card.L("draw", parse_filter(""), "consumes", f"{src} Cost$ Discard (needs cards)")
            elif verb == "ExileFromGrave":
                if "CARDNAME" in filt:
                    card.L("tograve", [self_pat(card, ft)], "consumes", f"{src} exile self from graveyard")
                else:
                    card.L("tograve", parse_filter(filt), "consumes", f"{src} Cost$ ExileFromGrave<{arg}>")
            elif verb == "AddCounter" and "LOYALTY" in arg:
                card.E("counter+", self_pat(card, ft), "loyalty", f"{src} Cost$ +loyalty", sub="LOYALTY")
            elif verb == "SubCounter":
                ct = parts[1].upper() if len(parts) > 1 else "*"
                card.L("counter+", [self_pat(card, ft)], "consumes", f"{src} Cost$ -{ct}", sub=ct)
            elif verb == "tapXType":
                card.L("enter", parse_filter(filt), "consumes", f"{src} Cost$ tapXType<{arg}>")
        mana_part = " ".join(t for t in cost.split() if "<" not in t and t not in ("T", "Q"))
        gen = sum(int(t) for t in mana_part.split() if t.isdigit())
        pips = sum(1 for t in mana_part.split() if not t.isdigit() and t != "X")
        if head == "AB" and not is_loyalty and ("X" in mana_part.split() or gen + pips >= 4):
            card.L("mana", parse_filter(""), "resource", f"{src} mana sink Cost$ {cost}",
                   demand="X" if "X" in mana_part.split() else gen + pips)
    if is_loyalty and head == "AB":
        card.E("activate_loyalty", concrete(ft), "loyalty", f"{src} loyalty ability")
    if p.get("ActivationZone") == "Graveyard":
        card.L("tograve", [self_pat(card, ft)], "consumes", f"{src} ActivationZone$ Graveyard")

    for key in ("ConditionPresent", "IsPresent"):
        if p.get(key):
            zone = p.get("PresentZone", "Battlefield")
            ev = "tograve" if zone == "Graveyard" else "enter"
            card.L(ev, parse_filter(p[key]), "condition", f"{src} {key}$ {p[key]}")
    if p.get("Condition") == "Threshold":
        card.L("tograve", parse_filter("Card.YouOwn"), "condition", f"{src} Threshold")

    # ---- triggers: listeners ----
    if k == "T" or (k == "SVar" and head == "Mode" and "Execute" in p):
        vc = p.get("ValidCard", "")
        pats = parse_filter(vc)
        if api in ("ChangesZone", "ChangesZoneAll"):
            o, d = p.get("Origin", "Any"), p.get("Destination", "Any")
            if pats and pats[0]["self"] and len(pats) == 1:
                if d == "Battlefield":
                    card.L("reenter", [self_pat(card, ft)], "trigger", f"{src} self ETB ({o}->{d})")
                elif o == "Battlefield" and d == "Graveyard":
                    card.L("die", [self_pat(card, ft)], "trigger", f"{src} self dies")
            else:
                pats = [x for x in pats if not x["self"]]
                if d == "Battlefield":
                    card.L("enter", pats, "trigger", f"{src} {o}->{d} {vc}")
                elif o == "Battlefield" and d == "Graveyard":
                    card.L("die", pats, "trigger", f"{src} {o}->{d} {vc}")
                elif d == "Graveyard":
                    card.L("tograve", pats, "trigger", f"{src} {o}->{d} {vc}")
        elif api == "SpellCast":
            if "Opponent" in p.get("ValidActivatingPlayer", "") or "Opponent" in p.get("ValidPlayer", ""):
                return
            vsa = p.get("ValidSA", "")
            if "IsTargeting" in vsa:
                card.L("cast_target_own", parse_filter(""), "trigger", f"{src} {vsa}")
            elif vc.strip() == "Card.Self":
                pass
            else:
                card.L("cast", pats, "trigger", f"{src} {vc}")
        elif api == "AbilityCast":
            vsa = p.get("ValidSA", "") + p.get("ValidActivatingPlayer", "")
            if "Loyalty" in vsa and "OppCtrl" not in vsa:
                card.L("activate_loyalty", parse_filter(""), "trigger", f"{src} {vsa}")
        elif api.startswith("CounterAdded"):
            card.L("counter+", pats, "trigger", f"{src} {vc}", sub=p.get("CounterType", "*").upper())
        elif api == "LifeGained":
            card.L("lifegain", parse_filter(""), "trigger", src)
        elif api == "Scry":
            card.L("scry", parse_filter(""), "trigger", src)
        elif api == "Surveil":
            card.L("surveil", parse_filter(""), "trigger", src)
        elif api in ("Discarded", "DiscardedAll"):
            card.L("discard", parse_filter(""), "trigger", src)
        elif api in ("Attacks",):
            if not (pats[0]["self"] and len(pats) == 1):
                card.L("attack", pats, "trigger", f"{src} {vc}")
        elif api == "BecomesTarget":
            card.L("cast_target_own", parse_filter(""), "trigger", src)
        elif api == "TapsForMana":
            card.L("mana", parse_filter(vc), "trigger", f"{src} {vc}")
        return

    # ---- statics ----
    if k == "S":
        if api == "Continuous":
            aff = p.get("Affected", "")
            if aff and not aff.startswith(("Card.Self", "Self")) and "EnchantedBy" not in aff \
                    and "EquippedBy" not in aff and "AttachedBy" not in aff:
                for pp in parse_filter(aff):
                    if pp.get("counters"):
                        card.L("counter+", [pp], "static", f"S:Continuous Affected$ {aff}", sub=pp["counters"])
                    else:
                        card.L("enter", [pp], "static", f"S:Continuous Affected$ {aff}")
        elif api in ("ReduceCost", "RaiseCost"):
            vc = p.get("ValidCard", "")
            if vc and vc not in ("Card.Self",):
                for pp in parse_filter(vc):
                    act = p.get("Activator", "You")
                    if api == "RaiseCost" and "Opponent" in act:
                        continue
                    card.E("cost_mod", pp, "effect", f"S:{api} ValidCard$ {vc} Amount$ {p.get('Amount','')}",
                           sign=-1 if api == "ReduceCost" else +1)
        return
    if k == "R":
        if api == "AddCounter":
            card.L("counter+", parse_filter(p.get("ValidCard", "")), "replacement", f"R:{api}",
                   sub=p.get("CounterType", "*").upper())
        elif api == "CreateToken":
            card.L("enter", parse_filter("Card.token+YouCtrl"), "replacement", f"R:{api}")
        return

    if head not in ("AB", "SP", "DB"):
        return

    # ---- effects: emitters ----
    tp = target_pats(p, ft)
    if api in ("PutCounter", "PutCounterAll"):
        ct = p.get("CounterType", "P1P1").upper()
        for pp in tp:
            card.E("counter+", pp, "effect", f"{src} {ct}", sub=ct)
        if any(not x["self"] and x.get("side") != "opp" for x in tp):
            card.L("enter", [x for x in tp if not x["self"]], "consumes", f"{src} needs a target")
    elif api == "Empower":
        t = p.get("Type", "")
        pw = concrete(["Planeswalker", t], token=True)
        card.E("enter", pw, "effect", f"{src} Empower {t} (creates token)")
        card.E("counter+", concrete(["Planeswalker", t], token=True), "effect", f"{src} Empower {t}", sub="LOYALTY")
        card.E("activate_loyalty", pw, "random", f"{src} Empower {t} token has loyalty abilities")
    elif api == "Proliferate":
        card.E("counter+", parse_filter("Permanent.YouCtrl")[0], "effect", src, sub="*")
    elif api == "Token":
        for ts in p.get("TokenScript", "").split(","):
            ts = ts.strip()
            info = card.token_info.get(ts, {"types": [], "mana": 0})
            card.E("enter", concrete(info["types"], token=True), "effect", f"{src} {ts}")
            if info.get("mana"):
                card.E("mana", concrete(info["types"], token=True), "effect", f"{src} {ts} makes mana",
                       amount=info["mana"], colors=list("WUBRG") if info["mana"] >= 3 else ["R", "G"] if "heartwood" in ts else list("WUBRG"))
    elif api == "Mana":
        if "Land" in ft and mana_amount(p) < 2:
            return  # a land tapping for one is the baseline, not a flow
        card.E("mana", concrete(ft), "effect", f"{src} Produced$ {p.get('Produced')} x{mana_amount(p)}",
               amount=mana_amount(p), colors=mana_colors(p))
    elif api == "Draw":
        if "Opponent" not in p.get("Defined", ""):
            card.E("draw", concrete([]), "effect", src)
    elif api == "Discard":
        d = p.get("Defined", "") + p.get("ValidTgts", "")
        if "Opponent" in d or "Targeted" in d:
            return
        card.E("discard", concrete([]), "effect", src)
        card.E("tograve", {"types": None, "neg": [], "token": False, "side": "you", "self": False,
                           "counters": None, "prepared": None}, "random", f"{src} discard")
    elif api == "Mill":
        card.E("tograve", {"types": None, "neg": [], "token": False, "side": "you", "self": False,
                           "counters": None, "prepared": None}, "random", src)
    elif api == "Surveil":
        card.E("surveil", concrete([]), "effect", src)
        card.E("tograve", {"types": None, "neg": [], "token": False, "side": "you", "self": False,
                           "counters": None, "prepared": None}, "random", f"{src} (may bin)")
    elif api == "Scry":
        card.E("scry", concrete([]), "effect", src)
    elif api == "GainLife":
        if "Opponent" not in p.get("Defined", ""):
            card.E("lifegain", concrete([]), "effect", src)
    elif api in ("Destroy", "DestroyAll", "Fight", "DamageAll"):
        for pp in tp:
            if pp["self"]:
                continue
            q = dict(pp); q["side"] = "any" if q["side"] == "any" else q["side"]
            card.E("die", q, "random", f"{src} {p.get('ValidTgts', p.get('ValidCards', ''))}")
    elif api == "DealDamage":
        card.E("damage", concrete([]), "effect", src)
    elif api == "Sacrifice":
        d = p.get("Defined", "") + p.get("ValidTgts", "")
        if "Opponent" in d or "Player" in d:
            return
        card.E("die", {"types": [p.get("SacValid", "Creature").split(".")[0]], "neg": [], "token": None,
                       "side": "you", "self": False, "counters": None, "prepared": None}, "effect", src)
    elif api in ("ChangeZone", "ChangeZoneAll"):
        o, d = p.get("Origin", ""), p.get("Destination", "")
        pats = parse_filter(p.get("ChangeType") or p.get("ValidTgts") or p.get("Defined", "") or "Card")
        if "Graveyard" in o:
            card.L("tograve", pats, "consumes", f"{src} {o}->{d}")
        if d == "Battlefield":
            for pp in pats:
                card.E("enter", pp, "effect", f"{src} {o}->{d}")
                if o in ("Graveyard", "Exile") or "Graveyard" in o:
                    card.E("reenter", pp, "effect", f"{src} {o}->{d}")
            if o == "Library" and any((x["types"] or [""])[0].startswith("Land") for x in pats):
                card.E("mana", concrete(["Land"]), "effect", f"{src} ramp", amount=1, colors=list("WUBRG"))
        if d == "Graveyard":
            for pp in pats:
                card.E("tograve", pp, "effect", f"{src} {o}->{d}")
    elif api == "AlterAttribute" and "Prepared" in p.get("Attributes", ""):
        if p.get("Activate", "True") != "False" and p.get("Defined", "Self") not in ("Self",):
            card.E("prepare", parse_filter("Creature.YouCtrl")[0], "effect", f"{src} prepares {p.get('Defined')}")
        elif p.get("Defined") and p.get("Defined") != "Self":
            card.E("prepare", parse_filter("Creature.YouCtrl")[0], "effect", f"{src} prepares {p.get('Defined')}")
    elif api in ("Pump", "PutCounter", "Animate", "Attach"):
        pass
    if head == "SP" and "ValidTgts" in p:
        vt = p["ValidTgts"]
        if "Creature" in vt and "OppCtrl" not in vt and api in ("Pump", "PutCounter", "Animate", "Attach", "Protection", "PumpAll"):
            card.E("cast_target_own", concrete(ft), "effect", f"{src} targets {vt}")
    if head == "SP" and api == "Pump" and "ValidTgts" in p and "OppCtrl" not in p["ValidTgts"]:
        pass


def main():
    parsed, tokendir, out = sys.argv[1:4]
    tok = load_token_types(tokendir)
    cards = []
    for rec in json.load(open(parsed, encoding="utf-8")):
        c = Card(rec, tok)
        analyse(c)
        # mana demand from the card's own cost: top end and X spells
        mc = c.faces[0]["mana_cost"] or ""
        if "Land" not in c.front_types:
            if "X" in mc.split():
                c.L("mana", parse_filter(""), "resource", f"ManaCost {mc} (X spell)", demand="X")
            elif c.cmc >= 5:
                c.L("mana", parse_filter(""), "resource", f"ManaCost {mc} (MV {c.cmc})", demand=c.cmc)
        cards.append({"name": c.name, "types": c.types, "front_types": c.front_types, "cmc": c.cmc,
                      "colors": sorted({x for fc in c.faces for x in fc["colors"]}),
                      "mana_cost": c.faces[0]["mana_cost"], "keywords": c.keywords,
                      "rarity": rec["rarity"], "prepare": c.prepare,
                      "oracle": " // ".join(fc["oracle"] or "" for fc in c.faces),
                      "deck_has": [x for fc in c.faces for x in fc["other"].get("DeckHas", [])],
                      "deck_hints": [x for fc in c.faces for x in fc["other"].get("DeckHints", [])
                                     + fc["other"].get("DeckNeeds", [])],
                      "emits": c.emits, "listens": c.listens})
    json.dump(cards, open(out, "w"), indent=1, ensure_ascii=False)
    ce = collections.Counter(e["event"] + (":" + e["sub"] if e["sub"] else "") for c in cards for e in c["emits"])
    cl = collections.Counter(l["event"] + (":" + l["sub"] if l["sub"] else "") for c in cards for l in c["listens"])
    print("emit  ", dict(ce.most_common()))
    print("listen", dict(cl.most_common()))


if __name__ == "__main__":
    main()
