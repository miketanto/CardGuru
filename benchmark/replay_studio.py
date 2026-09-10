"""Export a game to a self-contained replay page: an XMage-style board with
real card art, a readable stack with target arrows, the game log, and an
interactive tree of every search / turn plan the pilot made. The page also
has a 1920x1080 presentation mode (`?present=1`) and a scripting API
(`window.__replay`) that replay_video.js drives frame by frame.

Inputs:
  --log     the bridge log (g1.jsonl): decisions, searches (candidates,
            simulated leaves, scores), turn plans, why/plan text.
  --record  the driver's replay record (g1_record.jsonl[.gz], written when
            the game ran with --record): printing-exact snapshots of both
            players' zones, the stack with targets, combat, and the game
            log, each decision stamped with its snapshot id. Optional: an
            old log without a record still exports (names only, no stack
            targets, no game log; images resolved by card name).

Images: by default Scryfall URLs by set code + collector number (the page
falls back to a name lookup and then to a drawn placeholder). With
--images-dir pointing at a fetch_card_images.py cache the page uses local
files (relative paths), or data URIs with --embed-images. --image-stub
draws placeholders only (offline test).

Usage:
  python3 benchmark/replay_studio.py --log g1.jsonl --record g1_record.jsonl.gz \
      --out g1_studio.html --title "..." --subtitle "..." \
      --player-a "Sonnet 5 — Dimir" --player-b "MAD — Dimir" [--images-dir DIR]
"""
import argparse
import base64
import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TEMPLATE = os.path.join(HERE, "replay_studio_template.html")
JS = os.path.join(HERE, "replay_studio.js")

DUR = {"search": 4200, "planning": 4200, "pilot": 2600, "fallback": 1900,
       "plan": 500, "auto": 240, "event": 450}


def short(label, n=44):
    label = re.sub(r"^Cast ", "", label or "")
    label = label.replace("cast Cast ", "cast ")
    return label if len(label) <= n else label[:n - 1] + "…"


# ---------------------------------------------------------------------------
# trees (unchanged from v1)

def build_tree(candidates, scores, chosen_label):
    """Turn a leaf_eval request (candidates with leaves whose `line` encodes
    the path 'candidate | sample | response') into a trie: nodes with
    parent links, per-leaf scores, and per-candidate aggregate values using
    the driver's own rules (worst leaf for unsampled candidates, mean over
    samples of the best response for projected ones)."""
    nodes = [{"id": 0, "parent": None, "depth": 0, "label": "decision",
              "kind": "root"}]
    index = {}
    flat = 0
    cand_ids = []
    for c in candidates:
        label = c.get("label") or "?"
        leaves = c.get("leaves") or []
        cpath = (label,)
        cid = len(nodes)
        nodes.append({"id": cid, "parent": 0, "depth": 1, "label": short(label),
                      "full": label, "kind": "candidate", "n_leaves": len(leaves)})
        index[cpath] = cid
        cand_ids.append(cid)
        per_sample = {}
        vals = []
        for l in leaves:
            line = l.get("line") or label
            parts = [p.strip() for p in line.split(" | ")]
            if parts and parts[0].startswith(label[:20]):
                parts = parts[1:]
            path = cpath
            pid = cid
            for depth, part in enumerate(parts, start=2):
                path = path + (part,)
                if path not in index:
                    nid = len(nodes)
                    nodes.append({"id": nid, "parent": pid, "depth": depth,
                                  "label": short(part, 40), "full": part,
                                  "kind": "branch"})
                    index[path] = nid
                pid = index[path]
            leaf = nodes[pid] if parts else None
            if leaf is None:
                nid = len(nodes)
                leaf = {"id": nid, "parent": cid, "depth": 2, "label": "result",
                        "full": line, "kind": "branch"}
                nodes.append(leaf)
            sc = scores[flat] if scores and flat < len(scores) else l.get("llm_score")
            flat += 1
            leaf["kind"] = "leaf"
            leaf["score"] = sc
            leaf["heuristic"] = l.get("heuristic")
            leaf["life"] = [l.get("our_life"), l.get("opp_life")]
            leaf["our_board"] = l.get("our_board")
            leaf["opp_board"] = l.get("opp_board")
            leaf["hand"] = l.get("our_hand_count")
            leaf["turn"] = l.get("turn")
            leaf["gy"] = [l.get("our_graveyard_count"), l.get("opp_graveyard_count")]
            leaf["mana"] = [l.get("our_mana"), l.get("opp_mana")]
            if sc is not None:
                vals.append(sc)
                if l.get("sample") is not None:
                    k = l["sample"]
                    per_sample[k] = max(per_sample.get(k, float("-inf")), sc)
        agg = None
        rule = None
        if vals:
            if per_sample:
                agg = sum(per_sample.values()) / len(per_sample)
                rule = "mean over samples of best response"
            else:
                agg = min(vals)
                rule = "worst leaf"
        nodes[cid]["agg"] = None if agg is None else round(agg, 1)
        nodes[cid]["rule"] = rule
    chosen = None
    for cid in cand_ids:
        if chosen_label and nodes[cid]["full"] == chosen_label:
            chosen = cid
    if chosen is None:
        best = None
        for cid in cand_ids:
            a = nodes[cid].get("agg")
            if a is not None and (best is None or a > best):
                best, chosen = a, cid
    for n in nodes:
        n["chosen"] = False
    if chosen is not None:
        nodes[chosen]["chosen"] = True
        best_leaf, best_sc = None, None
        for n in nodes:
            if n.get("kind") == "leaf":
                p = n
                while p["parent"] not in (None, 0):
                    p = nodes[p["parent"]]
                if p["id"] == chosen and n.get("score") is not None and (
                        best_sc is None or n["score"] > best_sc):
                    best_leaf, best_sc = n, n["score"]
        if best_leaf:
            best_leaf["chosen"] = True
    return {"nodes": nodes, "chosen": chosen}


def plan_tree(turn_plan, whose):
    """A turn plan as a tree: steps, attack/blocks, hold, rules, candidates."""
    nodes = [{"id": 0, "parent": None, "depth": 0,
              "label": f"{'my' if whose == 'mine' else 'their'} turn plan",
              "kind": "root"}]

    def add(parent, label, kind="branch", full=None, depth=None):
        nid = len(nodes)
        d = depth if depth is not None else nodes[parent]["depth"] + 1
        nodes.append({"id": nid, "parent": parent, "depth": d, "label": short(label, 46),
                      "full": full or label, "kind": kind, "chosen": False})
        return nid

    tp = turn_plan or {}
    cands = tp.get("candidates")
    if isinstance(cands, list) and cands:
        g = add(0, "candidate lines", "group")
        for c in cands:
            if not isinstance(c, dict):
                continue
            cid = add(g, c.get("label") or "line", "candidate")
            for a in c.get("main1") or []:
                add(cid, f"main 1: {a if isinstance(a, str) else a.get('action')}")
            if c.get("attack"):
                add(cid, f"combat: {c['attack']}")
            for a in c.get("main2") or []:
                add(cid, f"main 2: {a if isinstance(a, str) else a.get('action')}")
    steps = tp.get("steps") or []
    if steps:
        g = add(0, "steps", "group")
        for s in steps:
            if isinstance(s, dict):
                add(g, f"{s.get('phase', 'any')}: {s.get('action') or s.get('do') or ''}")
    if tp.get("attack") and not cands:
        add(0, f"attack: {tp['attack']}", "branch")
    if tp.get("blocks"):
        add(0, f"blocks: {tp['blocks']}", "branch")
    if tp.get("hold"):
        g = add(0, "hold", "group")
        for h in tp["hold"]:
            add(g, str(h))
    rules = tp.get("rules") or []
    if rules:
        g = add(0, "if → then", "group")
        for r in rules:
            if isinstance(r, dict):
                add(g, f"{r.get('if')} → {r.get('then')}")
    if tp.get("chosen_label"):
        for n in nodes:
            if n.get("kind") == "candidate" and n.get("full") == tp["chosen_label"]:
                n["chosen"] = True
    return {"nodes": nodes, "chosen": None}


MENU_KINDS = ("target", "choose", "use", "mode", "announce_x", "choice")


def menu_tree(req, resp):
    """A standalone sub-choice prompt as a one-level tree: the prompt, one
    node per option, the pick in gold."""
    kind = req.get("kind")
    prompt = req.get("prompt") or req.get("ability") or kind
    nodes = [{"id": 0, "parent": None, "depth": 0, "label": short(str(prompt), 46),
              "full": str(prompt), "kind": "root"}]
    picked = set()
    if kind == "use":
        picked = {0 if resp.get("use") else 1}
        opts = [{"index": 0, "text": "yes"}, {"index": 1, "text": "no"}]
    else:
        opts = req.get("options") or []
        for k in ("targets", "choice", "x"):
            v = resp.get(k)
            if isinstance(v, list):
                picked = {int(i) for i in v if isinstance(i, (int, float))}
            elif isinstance(v, (int, float)):
                picked = {int(v)}
        if kind == "announce_x":
            opts = [{"index": v, "text": f"X = {v}"} for v in range(req.get("min", 0), req.get("max", 0) + 1)][:12]
    if not opts:
        return None
    chosen = None
    for o in opts:
        nid = len(nodes)
        t = o.get("text") or o.get("name") or "?"
        if o.get("additional_cost"):
            t += f" (+{o['additional_cost']})"
        is_pick = o.get("index") in picked
        nodes.append({"id": nid, "parent": 0, "depth": 1, "label": short(str(t), 44), "full": str(t),
                      "kind": "candidate", "chosen": is_pick})
        if is_pick and chosen is None:
            chosen = nid
    if kind not in ("use", "announce_x") and not picked:
        nid = len(nodes)
        nodes.append({"id": nid, "parent": 0, "depth": 1, "label": "none", "full": "no selection",
                      "kind": "candidate", "chosen": True})
        chosen = nid
    return {"nodes": nodes, "chosen": chosen}


def classify(row):
    src = row.get("source")
    if src == "fallback-timeout":
        return "fallback"
    if src in ("auto", "yield"):
        return "auto"
    if src == "turn_plan":
        return "plan"
    req = row.get("request") or {}
    if req.get("kind") == "leaf_eval":
        return "search"
    if req.get("kind") == "turn_plan":
        return "planning"
    return "pilot"


# ---------------------------------------------------------------------------
# decisions from the bridge log

def load_log(log_path):
    rows = [json.loads(l) for l in open(log_path, encoding="utf-8") if l.strip()]
    result = None
    trace = []
    for r in rows:
        if r.get("source") == "result":
            result = r.get("result")
            trace = [t for t in (r.get("minimax_trace") or [])
                     if t.get("mode") == "llm_leaf"]
    return rows, result, trace


def decision_of(row, trace_called, ti):
    """The decision payload for one logged row; returns (decision, ti)."""
    req = row.get("request") or {}
    resp = row.get("response") or {}
    kind = req.get("kind")
    d = {
        "kind": kind,
        "response": {k: v for k, v in resp.items() if k not in ("why", "plan")},
        "why": resp.get("why", ""),
        "plan": resp.get("plan", ""),
        "note": row.get("plan_note"),
        "options": [{"index": o.get("index"), "text": o.get("text") or o.get("name")}
                    for o in (req.get("options") or [])],
    }
    if kind == "leaf_eval" and row.get("source") == "llm":
        chosen = None
        if ti < len(trace_called):
            t = trace_called[ti]
            chosen = t.get("chosen")
            d["agg_gap"] = t.get("agg_gap")
            d["tie_break"] = t.get("tie_break")
            d["agg_values"] = t.get("agg_values")
            ti += 1
        d["tree"] = build_tree(req.get("candidates") or [], resp.get("scores"), chosen)
        d["aggregation"] = req.get("aggregation")
        d["decision"] = req.get("decision")
        d["leaf_count"] = req.get("leaf_count")
    elif kind == "turn_plan":
        d["tree"] = plan_tree(resp.get("turn_plan"), req.get("whose_turn"))
        d["decision"] = "plan"
    elif "chosen_line" in req:
        d["chosen_line"] = req["chosen_line"]
    elif kind in MENU_KINDS and row.get("source") in ("llm", "fallback-timeout"):
        d["tree"] = menu_tree(req, resp)
        d["decision"] = "menu"
    return d, ti


# ---------------------------------------------------------------------------
# record (v2)

def load_record(path):
    op = gzip.open if path.endswith(".gz") else open
    meta, cards, snaps, events, end = {}, {}, {}, [], None
    with op(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            t = r.get("t")
            if t == "snap":
                snaps[r["id"]] = r
            elif t == "event":
                events.append(r)
            elif t == "card":
                cards[r["key"]] = r
            elif t == "meta":
                meta = r
            elif t == "end":
                end = r
    return {"meta": meta, "cards": cards, "snaps": snaps, "events": events, "end": end}


OBJ_ID = re.compile(r"object_id='([0-9a-f]{8})")


def event_ids(e):
    return sorted(set(OBJ_ID.findall(e.get("html") or "")))


TAGS = re.compile(r"<[^>]+>")


def untag(s):
    return TAGS.sub("", s) if isinstance(s, str) else s


def board_of(snap):
    stack = []
    for it in snap.get("stack") or []:
        it = dict(it)
        it["rules"] = untag(it.get("rules"))
        stack.append(it)
    return {"players": snap.get("players") or {}, "stack": stack,
            "combat": snap.get("combat") or []}


def board_sig(snap):
    """What must change for an event snapshot to earn its own frame."""
    ps = snap.get("players") or {}
    return (tuple((s, (p.get("life"), len(p.get("hand") or []),
                       tuple(sorted(c.get("id") for c in p.get("battlefield") or [])),
                       len(p.get("graveyard") or []), len(p.get("exile") or [])))
                  for s, p in sorted(ps.items())),
            tuple(x.get("id") for x in snap.get("stack") or []),
            len(snap.get("combat") or []))


def build_frames_v2(rows, trace, record, event_frames):
    snaps = record["snaps"]
    events_by_snap = {}
    for e in record["events"]:
        events_by_snap.setdefault(e["snap"], []).append(e)
    trace_called = [t for t in trace if t.get("leaves_sent", 1) > 0]
    ti = 0
    decisions = {}       # snapshot id -> list of (src, decision)
    unlinked = 0
    for r in rows:
        if r.get("source") == "result":
            continue
        req = r.get("request") or {}
        if not req.get("state") and req.get("kind") != "turn_plan":
            continue
        d, ti = decision_of(r, trace_called, ti)
        sid = req.get("snapshot_id")
        if sid is None or sid not in snaps:
            unlinked += 1
            continue
        decisions.setdefault(sid, []).append((classify(r), d))
    frames = []
    pending_events = []
    last_sig = None
    ids = sorted(snaps)
    for k, sid in enumerate(ids):
        s = snaps[sid]
        evs = events_by_snap.get(sid, [])
        decs = decisions.get(sid, [])
        sig = board_sig(s)
        step_key = (s.get("turn"), s.get("step"))
        next_step = None
        if k + 1 < len(ids):
            n = snaps[ids[k + 1]]
            next_step = (n.get("turn"), n.get("step"))
        keep = bool(decs) or s.get("trigger") == "end"
        if not keep:
            if event_frames == "all":
                keep = True
            elif event_frames == "step":
                keep = sig != last_sig or next_step != step_key
        if not keep:
            pending_events.extend(evs)
            continue
        base = {"snap": sid, "turn": s.get("turn"), "phase": s.get("phase"),
                "step": s.get("step"), "active": s.get("active"), "priority": s.get("priority"),
                "board": board_of(s),
                "events": [{"n": e["n"], "text": e.get("text", ""), "ids": event_ids(e)}
                           for e in pending_events + evs]}
        pending_events = []
        last_sig = sig
        if not decs:
            frames.append(dict(base, src="event", kind=None, decision=None))
            continue
        for j, (src, d) in enumerate(decs):
            f = dict(base, src=src, kind=d.get("kind"), decision=d)
            if j > 0:
                f["events"] = []
            frames.append(f)
    return frames, unlinked


# ---------------------------------------------------------------------------
# fallback (v1 logs, no record)

def adapt_v1_state(state, stack_strings):
    """The v1 per-request state -> v2 board shape (names only)."""
    players = {}
    name_ids = {}
    for side in ("A", "B"):
        s = state.get(side) or {}
        bf = []
        for i, c in enumerate(s.get("battlefield") or []):
            cid = f"{side}:{c.get('name')}#{i}"
            name_ids.setdefault(c.get("name"), cid)
            o = {"id": cid, "key": "N/" + (c.get("name") or "?"), "name": c.get("name")}
            for k in ("tapped", "summoning_sick", "attacking"):
                if c.get(k):
                    o["sick" if k == "summoning_sick" else k] = True
            if c.get("power") is not None:
                o["power"], o["toughness"] = c.get("power"), c.get("toughness")
            if c.get("blocking"):
                o["blocking_names"] = c["blocking"]
            if c.get("types"):
                o["types"] = [t.strip() for t in re.split(r"[ —-]+", c["types"]) if t.strip()]
            bf.append(o)
        hand = None
        if s.get("hand") is not None:
            hand = [{"id": f"{side}:h{i}", "key": "N/" + (c.get("name") or "?"), "name": c.get("name")}
                    for i, c in enumerate(s.get("hand") or [])]
        p = {"life": s.get("life"), "library": None,
             "battlefield": bf,
             "graveyard": [{"id": f"{side}:g{i}", "key": "N/" + n, "name": n}
                           for i, n in enumerate(s.get("graveyard") or [])],
             "exile": []}
        if hand is not None:
            p["hand"] = hand
        else:
            p["hand_count"] = s.get("hand_count")
        players[side] = p
    for side in ("A", "B"):
        for o in players[side]["battlefield"]:
            if "blocking_names" in o:
                o["blocking"] = [name_ids.get(n, n) for n in o.pop("blocking_names")]
    stack = []
    for i, t in enumerate(stack_strings or []):
        m = re.match(r"^(.*?) \((ours|theirs)\)(?: \[(.*)\])?$", t)
        name, who, types = (m.group(1), m.group(2), m.group(3)) if m else (t, "ours", "")
        stack.append({"id": f"s{i}", "name": name, "key": "N/" + name, "ability": False,
                      "controller": "A" if who == "ours" else "B",
                      "types": (types or "").split(), "targets": []})
    return {"players": players, "stack": stack, "combat": []}


def build_frames_v1(rows, trace):
    trace_called = [t for t in trace if t.get("leaves_sent", 1) > 0]
    ti = 0
    frames = []
    cards = {}
    for r in rows:
        if r.get("source") == "result":
            continue
        req = r.get("request") or {}
        state = req.get("state")
        if not state:
            continue
        for side in state.values():
            for zone in ("battlefield", "hand"):
                for c in side.get(zone) or []:
                    if isinstance(c, dict) and c.get("name"):
                        key = "N/" + c["name"]
                        rec = cards.setdefault(key, {"key": key, "name": c["name"]})
                        for k in ("cost", "types", "text"):
                            if c.get(k) and k not in rec:
                                rec[k] = c[k]
            for n in side.get("graveyard") or []:
                if isinstance(n, str):
                    cards.setdefault("N/" + n, {"key": "N/" + n, "name": n})
        d, ti = decision_of(r, trace_called, ti)
        frames.append({"snap": None, "turn": req.get("turn"), "phase": req.get("phase"),
                       "step": None, "active": req.get("active"), "priority": None,
                       "board": adapt_v1_state(state, req.get("stack")),
                       "events": [], "src": classify(r), "kind": req.get("kind"), "decision": d})
    out_cards = {}
    for key, rec in cards.items():
        out_cards[key] = {"key": key, "name": rec["name"], "mana_cost": rec.get("cost"),
                          "type_line": rec.get("types"), "types": (rec.get("types") or "").split(),
                          "rules": [rec["text"]] if rec.get("text") else []}
    return frames, out_cards


# ---------------------------------------------------------------------------
# images

def image_candidates(card, size, images_dir, manifest, embed, stub, out_dir):
    """Ordered image sources for one card record."""
    if stub:
        return []
    key = card.get("key")
    if manifest is not None:
        ent = manifest.get(key) or {}
        fn = ent.get(size) or ent.get("small")
        if fn:
            path = os.path.join(images_dir, fn)
            if embed:
                with open(path, "rb") as f:
                    return ["data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")]
            return [os.path.relpath(path, out_dir).replace(os.sep, "/")]
    from fetch_card_images import image_urls
    return [u for u in image_urls(card, size) if "/cards/search?" not in u]


def finish_cards(cards, args, out_dir):
    manifest = None
    if args.images_dir and os.path.exists(os.path.join(args.images_dir, "images.json")):
        manifest = json.load(open(os.path.join(args.images_dir, "images.json"), encoding="utf-8"))
    out = {}
    for key, c in cards.items():
        cc = dict(c)
        cc.pop("t", None)
        if cc.get("rules"):
            cc["rules"] = [untag(r) for r in cc["rules"]]
        cc["img_small"] = image_candidates(c, "small", args.images_dir, manifest,
                                           args.embed_images, args.image_stub, out_dir)
        cc["img_normal"] = image_candidates(c, "normal", args.images_dir, manifest,
                                            args.embed_images, args.image_stub, out_dir)
        if c.get("back") and c["back"].get("set"):
            bk = dict(c["back"])
            bk["key"] = f"{bk.get('set')}/{bk.get('number')}"
            bk["_back"] = True
            if bk["key"] not in cards and bk["key"] not in out:
                out[bk["key"]] = {
                    "key": bk["key"], "name": bk.get("name"),
                    "img_small": image_candidates(bk, "small", args.images_dir, manifest,
                                                  args.embed_images, args.image_stub, out_dir),
                    "img_normal": image_candidates(bk, "normal", args.images_dir, manifest,
                                                   args.embed_images, args.image_stub, out_dir)}
            cc["back"] = dict(c["back"], key=bk["key"])
        out[key] = cc
    return out


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--record", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Replay")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--player-a", default="Pilot (A)")
    ap.add_argument("--player-b", default="MAD (B)")
    ap.add_argument("--images-dir", default=None, help="fetch_card_images.py cache (images.json)")
    ap.add_argument("--embed-images", action="store_true", help="inline cached images as data URIs")
    ap.add_argument("--image-stub", action="store_true", help="no image URLs; drawn placeholders only")
    ap.add_argument("--event-frames", choices=["all", "step", "none"], default="step",
                    help="which game-log snapshots become frames (default: one per step or board change)")
    args = ap.parse_args()

    rows, result, trace = load_log(args.log)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    unlinked = 0
    if args.record:
        record = load_record(args.record)
        frames, unlinked = build_frames_v2(rows, trace, record, args.event_frames)
        cards = dict(record["cards"])
        version = 2
        if record.get("end") and not result:
            result = record["end"].get("result")
    else:
        frames, cards = build_frames_v1(rows, trace)
        version = 1
    for i, f in enumerate(frames):
        f["i"] = i
        f["dur"] = DUR.get(f["src"], 1500)
    counts = {}
    for f in frames:
        counts[f["src"]] = counts.get(f["src"], 0) + 1
    timeline = []
    for f in frames:
        d = f.get("decision")
        if d and f["src"] not in ("auto", "plan"):
            agg = None
            t = d.get("tree")
            if t and t.get("chosen") is not None:
                agg = t["nodes"][t["chosen"]].get("agg")
            timeline.append({"i": f["i"], "src": f["src"], "turn": f["turn"], "agg": agg})
    meta = {"title": args.title, "subtitle": args.subtitle, "playerA": args.player_a,
            "playerB": args.player_b, "result": result, "counts": counts,
            "timeline": timeline, "version": version}
    cards_out = finish_cards(cards, args, out_dir)

    html = open(TEMPLATE, encoding="utf-8").read()
    js = open(JS, encoding="utf-8").read().replace("</script", "<\\/script")
    html = html.replace("__TITLE__", args.title)
    html = html.replace("/*__META__*/{}", json.dumps(meta).replace("</", "<\\/"))
    html = html.replace("/*__FRAMES__*/[]", json.dumps(frames).replace("</", "<\\/"))
    html = html.replace("/*__CARDS__*/{}", json.dumps(cards_out).replace("</", "<\\/"))
    html = html.replace("/*__JS__*/", js)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    trees = sum(1 for f in frames if f.get("decision") and f["decision"].get("tree"))
    print(f"wrote {args.out}: {len(frames)} frames, {trees} decision trees, {counts}, "
          f"{len(cards_out)} cards, v{version}" + (f", {unlinked} unlinked decisions" if unlinked else ""))


if __name__ == "__main__":
    main()
