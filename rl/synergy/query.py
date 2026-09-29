"""What works with this card?

  python3 query.py "Chandra, Torch of Defiance"            # top 15 under full
  python3 query.py chandra --type resource --k 20          # substring match, one edge type
  python3 query.py "Inspired Tethermage" --scheme rarity

Each neighbour shows direction: `feeds ->` (this card emits what it
listens for), `<- fed by` (the reverse), and the primitives involved.
"""
import argparse, collections, json, sys

ap = argparse.ArgumentParser()
ap.add_argument("card")
ap.add_argument("--scheme", default="full", choices=["uniform", "tight", "rarity", "full"])
ap.add_argument("--type", choices=["state", "resource", "cost"])
ap.add_argument("--k", type=int, default=15)
ap.add_argument("--no-intrinsic", action="store_true", help="drop edges from intrinsic emissions")
a = ap.parse_args()

edges = json.load(open("fra_edges.json", encoding="utf-8"))
names = sorted({x["a"] for x in edges} | {x["b"] for x in edges})
hit = [n for n in names if n.lower() == a.card.lower()] or [n for n in names if a.card.lower() in n.lower()]
if not hit:
    sys.exit(f"no card matching {a.card!r}")
if len(hit) > 1:
    print("ambiguous:", "; ".join(hit)); hit = hit[:1]
me = hit[0]

best = {}  # (other, direction, prim, type) -> edge
for x in edges:
    if a.type and x["type"] != a.type:
        continue
    if a.no_intrinsic and x["emit_mech"] == "intrinsic":
        continue
    if x["a"] == me:
        k = (x["b"], "feeds ->", x["prim"], x["type"])
    elif x["b"] == me:
        k = (x["a"], "<- fed by", x["prim"], x["type"])
    else:
        continue
    if k not in best or x["w"][a.scheme] > best[k]["w"][a.scheme]:
        best[k] = x
score = collections.defaultdict(float); why = collections.defaultdict(list)
for (o, d, p, t), x in best.items():
    score[o] += x["w"][a.scheme]
    why[o].append((x["w"][a.scheme], d, p, t, x["emit"], x["listen"]))
print(f"{me} — top {a.k} under {a.scheme}" + (f", {a.type} edges only" if a.type else ""))
for o, s in sorted(score.items(), key=lambda kv: -kv[1])[:a.k]:
    print(f"  {s:.3f}  {o}")
    for w, d, p, t, e, l in sorted(why[o], reverse=True)[:2]:
        print(f"         {d} {p} ({t}): {e[:60]} → {l[:60]}")
