"""13a flash check, Nowhere to Run ({1}{B}, flash): opponent-turn PRIORITY consults with it in my hand and
>= 2 untapped own lands. Tally untapped land sets and whether it was offered; print the top sets."""
import collections
import json
import sys

tal = collections.Counter()
for p in sys.argv[1:]:
    for raw in open(p, "rb"):
        if b'"t":"consult"' not in raw or b"Nowhere to Run" not in raw:
            continue
        m = json.loads(raw)
        ct = m.get("v7_cand_type") or []
        g = m.get("v7_game") or []
        if not (set(ct) & {1, 2, 3}) or not (len(g) > 1 and g[1] < 0.5):
            continue
        ents = m.get("v7_ent") or []
        names = m.get("v7_ent_name") or []
        refs = m.get("v7_cand_refers") or [[] for _ in ct]
        if not any(i < len(names) and names[i] == "Nowhere to Run" and e[1] > 0.5 and e[7] > 0.5
                   for i, e in enumerate(ents)):
            continue
        lands = sorted(names[i] for i, e in enumerate(ents)
                       if i < len(names) and e[0] > 0.5 and e[7] > 0.5 and e[30] > 0.5 and e[22] < 0.5)
        if len(lands) < 2:
            continue
        offered = sorted({names[r - 3] for k, t in enumerate(ct) if t == 2 for r in refs[k] if 0 <= r - 3 < len(names)})
        off = "Nowhere to Run" in offered
        tal[f"{'offered' if off else 'NOT'}|lands={'+'.join(lands)}|other={','.join(x for x in offered if x != 'Nowhere to Run')}"] += 1
print("FLASH5|files=%d|offered=%d|not=%d" % (len(sys.argv[1:]), sum(v for k, v in tal.items() if k.startswith("offered")),
                                            sum(v for k, v in tal.items() if k.startswith("NOT"))))
for k, v in tal.most_common(6):
    print(f"FLASH5|{v}|{k}"[:220])
