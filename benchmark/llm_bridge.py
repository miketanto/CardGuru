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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--deck-a", default="mono_red_aggro")
    ap.add_argument("--deck-b", default="mono_green_stompy")
    ap.add_argument("--esc-dir", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--timeout", type=float, default=100.0)
    args = ap.parse_args()

    os.makedirs(args.esc_dir, exist_ok=True)
    corpus = believe.load_corpus()
    rng = random.Random(0)
    seq = {"n": 0}

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

    def policy(request):
        kind = request.get("kind")
        if kind == "priority" and not any(
                o.get("action") == "activate"
                for o in request.get("options", [])):
            resp = {"choice": 0}
            log({"source": "auto", "request": request, "response": resp})
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
        log({"source": source, "request": request, "response": resp})
        return resp

    with MatchClient(args.mage_repo, minimax=True, subchoices=True,
                     deck_a=args.deck_a, deck_b=args.deck_b) as m:
        result = m.play(policy)
        trace = m.read_trace()
    log({"source": "result", "result": result, "minimax_trace": trace})
    with open(os.path.join(args.esc_dir, "DONE"), "w") as f:
        json.dump(result, f)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
