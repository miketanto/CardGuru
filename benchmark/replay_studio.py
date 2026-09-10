"""Export a game log to a self-contained replay page with an animated
decision tree, ready for screen capture (see replay_video.js).

What mage-bench does: a JavaFX observer client renders the board and pipes
frames to FFmpeg, and a separate script uploads the recording to YouTube
afterwards. What we do instead: every decision in our bridge log carries a
full state snapshot, every search carries its candidates, simulated leaves
and the pilot's scores, and every plan carries its steps and rules — so a
browser page can replay the game AND show what the pilot was choosing
between, as an animated tree, without a live client at all. The page has
a presentation mode (`?present=1`, 1920x1080) and a scripting API
(`window.__replay`) that replay_video.js drives frame by frame.

Usage:
  python3 benchmark/replay_studio.py --log research/data/dp/fixed_search_s23/g1.jsonl \
      --out replay.html --title "..." --subtitle "..." \
      --player-a "Sonnet 5 — Dimir" --player-b "MAD — Dimir"
"""
import argparse
import json
import os
import re

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "replay_studio_template.html")


def short(label, n=44):
    label = re.sub(r"^Cast ", "", label or "")
    label = label.replace("cast Cast ", "cast ")
    return label if len(label) <= n else label[:n - 1] + "…"


def build_tree(candidates, scores, chosen_label):
    """Turn a leaf_eval request (candidates with leaves whose `line` encodes
    the path 'candidate | sample | response') into a trie: nodes with
    parent links, per-leaf scores, and per-candidate aggregate values using
    the driver's own rules (worst leaf for unsampled candidates, mean over
    samples of the best response for projected ones)."""
    nodes = [{"id": 0, "parent": None, "depth": 0, "label": "decision",
              "kind": "root"}]
    index = {}   # path tuple -> node id
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
    # chosen: by label if the trace named it, else best aggregate
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
        # mark the best leaf under the chosen candidate
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


def build_frames(log_path):
    rows = [json.loads(l) for l in open(log_path, encoding="utf-8")]
    result = None
    trace = []
    for r in rows:
        if r.get("source") == "result":
            result = r.get("result")
            trace = [t for t in (r.get("minimax_trace") or [])
                     if t.get("mode") == "llm_leaf"]
    # Pair trace entries that involved a pilot call with leaf_eval rows, in order.
    trace_called = [t for t in trace if t.get("leaves_sent", 1) > 0]
    ti = 0
    frames = []
    for r in rows:
        if r.get("source") == "result":
            continue
        req = r.get("request") or {}
        state = req.get("state")
        if not state:
            continue
        resp = r.get("response") or {}
        kind = req.get("kind")
        f = {
            "src": classify(r),
            "turn": req.get("turn"), "phase": req.get("phase"),
            "kind": kind, "active": req.get("active"),
            "state": state,
            "stack": req.get("stack") or [],
            "mana": req.get("mana_available"),
            "response": {k: v for k, v in resp.items() if k not in ("why", "plan")},
            "why": resp.get("why", ""),
            "plan": resp.get("plan", ""),
            "note": r.get("plan_note"),
            "options": [{"index": o.get("index"), "text": o.get("text") or o.get("name")}
                        for o in (req.get("options") or [])],
        }
        if kind == "leaf_eval" and r.get("source") == "llm":
            chosen = None
            if ti < len(trace_called):
                t = trace_called[ti]
                ti += 1
                chosen = t.get("chosen")
            f["tree"] = build_tree(req.get("candidates") or [], resp.get("scores"), chosen)
            f["decision"] = req.get("decision")
            f["leaf_count"] = req.get("leaf_count")
        elif kind == "turn_plan":
            f["tree"] = plan_tree(resp.get("turn_plan"), req.get("whose_turn"))
            f["decision"] = "plan"
        elif "chosen_line" in req:
            f["chosen_line"] = req["chosen_line"]
        frames.append(f)
    return frames, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Replay")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--player-a", default="Pilot (A)")
    ap.add_argument("--player-b", default="MAD (B)")
    args = ap.parse_args()

    frames, result = build_frames(args.log)
    counts = {}
    for f in frames:
        counts[f["src"]] = counts.get(f["src"], 0) + 1
    meta = {"title": args.title, "subtitle": args.subtitle,
            "playerA": args.player_a, "playerB": args.player_b,
            "result": result, "counts": counts}
    html = open(TEMPLATE, encoding="utf-8").read()
    html = html.replace("__TITLE__", args.title)
    html = html.replace("/*__META__*/{}", json.dumps(meta))
    html = html.replace("/*__FRAMES__*/[]", json.dumps(frames).replace("</", "<\\/"))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    trees = sum(1 for f in frames if "tree" in f)
    print(f"wrote {args.out}: {len(frames)} frames, {trees} decision trees, "
          f"{counts}")


if __name__ == "__main__":
    main()
