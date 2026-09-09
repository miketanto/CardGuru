"""Turn one game log into a review digest of the pilot's real decisions.

This is the input to a blunder review (mage-bench's analysis pass, built
from data we already log). It keeps only decisions where the pilot had a
genuine choice and renders each with enough context to judge it: the board
on both sides, the menu it saw, what it picked, and the reason it gave.

Excluded as forced or uninteresting: bridge auto-passes and yields, timeout
fallbacks, menus with a single legal option, and priority windows whose only
options are mana abilities. Combat/main-phase searches (leaf_eval) are kept
and rendered as the candidate lines with the pilot's own 0-100 scores, since
mis-scoring a line is exactly the kind of mistake worth catching.

Usage:
  python3 benchmark/review_game.py research/data/mirror/g1.jsonl [--out x.md]
"""
import argparse
import json
import os


def board(side):
    if not side:
        return "—"
    creatures, lands, untapped = [], 0, 0
    for c in side.get("battlefield", []):
        name = c.get("name", "?")
        if "power" in c:
            bits = f"{name} {c['power']}/{c['toughness']}"
            if c.get("tapped"):
                bits += " (tapped)"
            elif c.get("summoning_sick"):
                bits += " (sick)"
            creatures.append(bits)
        else:
            lands += 1
            if not c.get("tapped"):
                untapped += 1
    body = ", ".join(creatures) if creatures else "no creatures"
    return f"{body} | {lands} lands ({untapped} untapped)"


def hand(side):
    h = side.get("hand")
    if isinstance(h, list):
        names = [c.get("name") if isinstance(c, dict) else str(c) for c in h]
        return ", ".join(n for n in names if n) or "empty"
    return f"{side.get('hand_count', '?')} cards"


def chosen_text(req, resp):
    kind = req.get("kind")
    opts = req.get("options") or []
    if kind == "priority":
        i = resp.get("choice", 0)
        if i == 0:
            return "PASS"
        t = next((o.get("text") for o in opts if o.get("index") == i), None)
        return t or f"option {i}"
    if kind == "attackers":
        idx = resp.get("attackers") or []
        if not idx:
            return "no attacks"
        names = [o.get("name") for o in opts if o.get("index") in idx]
        return "attack with " + ", ".join(n for n in names if n)
    if kind == "blockers":
        pairs = resp.get("blocks") or []
        if not pairs:
            return "no blocks"
        bl = {o.get("index"): o.get("name") for o in (req.get("blockers") or [])}
        at = {o.get("index"): o.get("name") for o in (req.get("attackers") or [])}
        return "; ".join(f"{bl.get(b, b)} blocks {at.get(a, a)}"
                         for b, a in pairs)
    if kind in ("target", "choose"):
        idx = resp.get("targets") or []
        names = [o.get("text") or o.get("name")
                 for o in opts if o.get("index") in idx]
        return "target " + ", ".join(n for n in names if n)
    if kind == "mulligan":
        return "MULLIGAN" if resp.get("mulligan") else "keep"
    return json.dumps({k: v for k, v in resp.items() if k != "why"})


def is_real_choice(row):
    """Did the pilot actually have a decision to make here?"""
    if row.get("source") != "llm":
        return False          # auto-pass, yield, or timeout fallback
    resp = row.get("response") or {}
    if str(resp.get("why", "")).startswith("batch:"):
        return False          # runner-forced starting player, not judgment
    req = row.get("request") or {}
    kind = req.get("kind")
    if kind == "leaf_eval":
        return True
    opts = req.get("options") or []
    if kind == "priority":
        real = [o for o in opts
                if o.get("action") == "activate"
                and "Add {" not in str(o.get("text", ""))]
        return len(real) >= 1          # pass-vs-act is a real choice
    if kind == "blockers":
        return bool(req.get("blockers")) and bool(req.get("attackers"))
    if kind == "attackers":
        return len(opts) >= 1
    return len(opts) > 1 or kind == "mulligan"


def render_leaf_eval(req, resp):
    scores = resp.get("scores") or []
    lines, i = [], 0
    for c in req.get("candidates", []):
        leaves = c.get("leaves", [])
        vals = scores[i:i + len(leaves)]
        i += len(leaves)
        worst = min(vals) if vals else None
        detail = "; ".join(
            f"{l.get('line')}: us {l.get('our_life')} vs {l.get('opp_life')}"
            for l in leaves)
        lines.append(f"    - `{c.get('label')}` scored **{worst}** ({detail})")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows = []
    for line in open(args.log, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    result = next((r.get("result") for r in rows
                   if r.get("source") == "result"), None)
    total = sum(1 for r in rows if r.get("request"))
    kept = [r for r in rows if is_real_choice(r)]

    out = []
    out.append(f"# Decision review — {os.path.basename(args.log)}\n")
    winner = (result or {}).get("winner")
    out.append(f"Result: **{'pilot won' if winner == 'A' else 'pilot lost' if winner == 'B' else 'unfinished'}**"
               f" in {(result or {}).get('turns', '?')} turns. "
               f"{len(kept)} real decisions out of {total} requests "
               f"(the rest were forced, auto-passed, or yielded).\n")
    out.append("Rate each decision **questionable / minor / moderate / major**, "
               "or leave it alone if it was right. Say what should have been "
               "done instead and why.\n")

    for r in kept:
        req, resp = r.get("request") or {}, r.get("response") or {}
        st = req.get("state") or {}
        a, b = st.get("A") or {}, st.get("B") or {}
        kind = req.get("kind")
        out.append(f"\n## Turn {req.get('turn')} — {req.get('phase')} "
                   f"[{kind}{'/' + req.get('decision') if kind == 'leaf_eval' and req.get('decision') else ''}]")
        out.append(f"- Life: pilot **{a.get('life')}** vs MAD **{b.get('life')}**")
        out.append(f"- Pilot board: {board(a)}")
        out.append(f"- Pilot hand: {hand(a)}")
        out.append(f"- MAD board: {board(b)}")
        if kind == "leaf_eval":
            out.append("- Engine simulated these lines; pilot scored the "
                       "resulting boards (candidate value = worst leaf, "
                       "highest wins):")
            out.append(render_leaf_eval(req, resp))
        else:
            opts = req.get("options") or []
            if opts:
                menu = "; ".join(
                    f"[{o.get('index')}] {o.get('text') or o.get('name')}"
                    for o in opts[:12])
                out.append(f"- Menu: {menu}")
            out.append(f"- **Chose: {chosen_text(req, resp)}**")
        why = resp.get("why")
        if why:
            out.append(f"- Pilot's reasoning: \"{str(why)[:300]}\"")

    text = "\n".join(out) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{args.out}: {len(kept)} decisions kept of {total} requests")
    else:
        print(text)


if __name__ == "__main__":
    main()
