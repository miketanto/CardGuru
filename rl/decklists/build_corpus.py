"""Phase 0c (v7 plan §2): build the decklist corpus `rl/artifacts/decklists_v1`.

Input: per-event JSON from rl/decklists/fetch_mtgo.py (raw/mtgo/*.json)
plus the repo's own lists (rl/*.dck, decks/*.txt).  Output:

  decklists.jsonl.gz  one line per unique mainboard:
      {id, source, event, format, date, split, n_main, n_side,
       main: [[card_id, qty] ...], side: [[card_id, qty] ...],
       main_names: [[name, qty] ...], unresolved: [name ...],
       dup_count, wins, losses}
      card_id indexes rl/artifacts/cards_v1 (index.json names -> id);
      unresolved names get card_id -1 and are listed.
  unresolved.tsv      name \\t occurrences (for extending name rules)
  README.md           the gate readout

Dedup: identical (sorted) mainboards collapse to one record; dup_count
keeps the multiplicity (league 5-0 dumps repeat the same stock list).
Split: 10% held out, grouped by event so a list and its near-copies
from the same event never straddle the boundary.

Gate (plan §2, 0c): >= 3,000 lists -> masked-card objective is in.  The
number this file reports as the gate is the strict one: unique
constructed (60-card, non-singleton) mainboards with every name
resolved.  Totals and per-format counts are reported alongside.

Run:  python rl/decklists/build_corpus.py [--raw rl/artifacts/decklists_v1/raw/mtgo]
"""
import argparse
import glob
import gzip
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "rl", "cards"))
from cardguru.dataset import norm_name          # noqa: E402
from build_index import parse_deck              # noqa: E402

SINGLETON_FORMATS = {"duel-commander", "commander", "brawl", "standard-brawl"}
_SLUG = re.compile(r"^(?P<fmt>[a-z-]+?)-(?:challenge|league|preliminary|showcase|super-qualifier|qualifier|last-chance|premier|rc-qualifier|mocs|open|trial|championship|finals|playoff|eternal-weekend|magic-online-championship)[a-z0-9-]*?-(?P<date>20\d\d-\d\d-\d\d)")


def slug_meta(slug):
    m = _SLUG.match(slug)
    if m:
        return m.group("fmt"), m.group("date")
    d = re.search(r"20\d\d-\d\d-\d\d", slug)
    fmt = slug.split("-20")[0] if "-20" in slug else slug
    fmt = re.sub(r"-(challenge|league|preliminary|showcase).*$", "", fmt)
    return fmt, (d.group(0) if d else None)


class Resolver:
    """MTGO card names -> cards_v1 ids, with the known spelling quirks."""

    def __init__(self, index_path):
        idx = json.load(open(index_path, encoding="utf-8"))
        self.names = idx["names"]
        self.version = idx["version"]
        self.misses = Counter()

    def _try(self, name):
        return self.names.get(norm_name(name))

    def __call__(self, name):
        cands = [name]
        if "/" in name and " // " not in name:
            a, b = name.split("/", 1)
            cands += [f"{a.strip()} // {b.strip()}", a.strip()]
        if " // " in name:
            cands.append(name.split(" // ")[0].strip())
        cands.append(re.sub(r"\s*\([^)]*\)\s*$", "", name))
        cands.append(name.replace("’", "'"))
        for c in cands:
            cid = self._try(c)
            if cid is not None:
                return cid
        self.misses[name] += 1
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.path.join(REPO, "rl", "artifacts", "decklists_v1", "raw", "mtgo"))
    ap.add_argument("--index", default=os.path.join(REPO, "rl", "artifacts", "cards_v1", "index.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "rl", "artifacts", "decklists_v1"))
    ap.add_argument("--holdout", type=float, default=0.10)
    ap.add_argument("--gate", type=int, default=3000)
    args = ap.parse_args()
    res = Resolver(args.index)

    raw_lists = []                      # (source, event, fmt, date, main, side, wins, losses)
    n_events = 0
    for path in sorted(glob.glob(os.path.join(args.raw, "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        slug = d.get("site_name") or os.path.basename(path)[:-5]
        fmt, date = slug_meta(slug)
        n_events += 1
        for x in d.get("decklists") or []:
            wl = (d.get("winloss") or {}).get(x.get("loginid")) or [None, None]
            raw_lists.append(("mtgo", slug, fmt, date, x["main"], x["side"], wl[0], wl[1]))
    for path in sorted(glob.glob(os.path.join(REPO, "rl", "*.dck")) + glob.glob(os.path.join(REPO, "decks", "*.txt"))):
        cnt = Counter()
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"^\s*(?:SB:\s*)?(\d+)x?\s+(?:\[[^\]]*\]\s+)?(.+?)\s*$", line.strip())
                if m and not line.startswith(("NAME:", "LAYOUT:")):
                    cnt[m.group(2)] += int(m.group(1))
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        raw_lists.append(("repo", rel, "xmage-ladder", "2026-09-10", [[n, q] for n, q in cnt.items()], [], None, None))

    by_key = {}
    order = []
    for src, ev, fmt, date, main, side, w, l in raw_lists:
        key = tuple(sorted((norm_name(n), q) for n, q in main))
        if key in by_key:
            by_key[key]["dup_count"] += 1
            continue
        rec = {"source": src, "event": ev, "format": fmt, "date": date,
               "main_names": main, "side_names": side, "wins": w, "losses": l,
               "dup_count": 1}
        by_key[key] = rec
        order.append(rec)

    fmt_counts = Counter()
    gate_lists = 0
    out_rows = []
    for i, rec in enumerate(order):
        main = [[res(n), q] for n, q in rec["main_names"]]
        side = [[res(n), q] for n, q in rec["side_names"]]
        unresolved = sorted({n for (cid, _), (n, _) in zip(main, rec["main_names"]) if cid < 0})
        n_main = sum(q for _, q in main)
        singleton = rec["format"] in SINGLETON_FORMATS or (
            bool(main) and n_main >= 98 and max(q for _, q in main) == 1)
        h = int(hashlib.sha1(rec["event"].encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        split = "heldout" if h < args.holdout else "train"
        constructed = (not singleton) and 60 <= n_main <= 80
        clean = constructed and not unresolved
        if clean:
            gate_lists += 1
        fmt_counts[rec["format"]] += 1
        out_rows.append({
            "id": i, "source": rec["source"], "event": rec["event"],
            "format": rec["format"], "date": rec["date"], "split": split,
            "constructed": constructed, "clean": clean,
            "n_main": n_main, "n_side": sum(q for _, q in side),
            "main": main, "side": side,
            "main_names": rec["main_names"], "unresolved": unresolved,
            "dup_count": rec["dup_count"], "wins": rec["wins"], "losses": rec["losses"],
        })

    os.makedirs(args.out, exist_ok=True)
    with gzip.open(os.path.join(args.out, "decklists.jsonl.gz"), "wt", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(args.out, "unresolved.tsv"), "w", encoding="utf-8") as f:
        for n, c in res.misses.most_common():
            f.write(f"{n}\t{c}\n")

    n_total = len(raw_lists)
    n_unique = len(out_rows)
    n_clean_heldout = sum(1 for r in out_rows if r["clean"] and r["split"] == "heldout")
    total_slots = sum(q for r in out_rows for _, q in r["main"])
    unresolved_slots = sum(q for r in out_rows for cid, q in r["main"] if cid < 0)
    go = gate_lists >= args.gate
    lines = [
        "# decklists_v1 — decklist corpus for deck-context pretraining (v7 L1)",
        "",
        f"Built by `rl/decklists/build_corpus.py` from `raw/mtgo/*.json` "
        f"(`rl/decklists/fetch_mtgo.py`, mtgo.com published event decklists) "
        f"plus the repo's own lists. Card ids index `{res.version}`.",
        "",
        "| count | value |", "|---|---|",
        f"| events fetched | {n_events} |",
        f"| lists, total | {n_total} |",
        f"| lists, unique mainboards | {n_unique} |",
        f"| **unique constructed lists with every name resolved (the gate)** | **{gate_lists}** |",
        f"| of which held out (10%, by event) | {n_clean_heldout} |",
        f"| mainboard card slots unresolved | {unresolved_slots} / {total_slots} ({100.0 * unresolved_slots / max(1, total_slots):.2f}%) |",
        f"| distinct unresolved names | {len(res.misses)} (top in `unresolved.tsv`) |",
        "",
        "## Per format (unique lists)", "", "| format | lists |", "|---|---|",
    ] + [f"| {k} | {v} |" for k, v in fmt_counts.most_common()] + [
        "",
        f"**Gate 0c: {'GO' if go else 'NO-GO'}** — {gate_lists} ≥ {args.gate}: {go}. "
        + ("Masked-card-in-deck (1c, 2b) is in." if go else "1c dropped; deck context trained in RL only."),
        "",
        "Fields: see the module docstring of `rl/decklists/build_corpus.py`. "
        "`constructed` = 60–80-card, non-singleton format; `clean` = constructed and fully resolved. "
        "Player handles are not stored.",
    ]
    with open(os.path.join(args.out, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"events={n_events} total={n_total} unique={n_unique} gate_clean_constructed={gate_lists} "
          f"heldout={n_clean_heldout} unresolved_slots={unresolved_slots}/{total_slots} "
          f"distinct_unresolved={len(res.misses)} gate={'GO' if go else 'NO-GO'}")
    for n, c in res.misses.most_common(15):
        print(f"  unresolved: {n!r} x{c}")
    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())
