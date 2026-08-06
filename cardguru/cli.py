"""CardGuru CLI.

  python -m cardguru build  --cardsfolder PATH [--canonical INDEX.json] [--pin SHA] [--out data/dataset.jsonl.gz]
  python -m cardguru search QUERY.json [--dataset PATH] [--limit N] [--explain] [--json]
  python -m cardguru show   "Card Name" [--dataset PATH]
  python -m cardguru stats  [--dataset PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import dataset as ds
from .index import SearchIndex, explain

DEFAULT_DATASET = "data/dataset.jsonl.gz"


def cmd_build(args):
    t0 = time.time()
    stats = ds.build(args.cardsfolder, args.out, canonical_index=args.canonical,
                     source_pin=args.pin)
    stats["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(stats, indent=1))


def cmd_search(args):
    with open(args.query, encoding="utf-8") as f:
        spec = json.load(f)
    query = spec["query"] if isinstance(spec, dict) and "query" in spec else spec
    t0 = time.time()
    idx = SearchIndex.load(args.dataset)
    t_load = time.time() - t0
    t0 = time.time()
    hits = list(idx.search(query, limit=args.limit))
    t_search = time.time() - t0
    if args.json:
        out = [{"name": h["record"]["name"], "evidence": h["evidence"]} for h in hits]
        json.dump(out, sys.stdout, indent=1)
        print()
    else:
        if isinstance(spec, dict) and spec.get("description"):
            print(f"# {spec['description']}")
        for h in hits:
            rec = h["record"]
            print(f"{rec['name']}  [{rec.get('types','')}]")
            if args.explain:
                for line in explain(rec, h["evidence"]):
                    print(f"    {line}")
        print(f"-- {len(hits)} faces matched "
              f"(load {t_load:.1f}s, search {t_search:.2f}s)", file=sys.stderr)


def cmd_show(args):
    idx = SearchIndex.load(args.dataset)
    name = args.name.lower()
    for rec in idx.records:
        if (rec.get("name") or "").lower() == name:
            json.dump(rec, sys.stdout, indent=1)
            print()
            return
    print(f"not found: {args.name}", file=sys.stderr)
    sys.exit(1)


def cmd_ask(args):
    from .nl_compiler import compile_question

    result = compile_question(args.question, args.ontology, model=args.model)
    if not result.ok:
        print("compilation failed:", file=sys.stderr)
        for line in result.errors:
            print(f"  {line}", file=sys.stderr)
        sys.exit(1)
    print(f"# compiled query ({len(result.attempts)} attempt(s)):", file=sys.stderr)
    print(json.dumps(result.query, indent=1), file=sys.stderr)
    if args.compile_only:
        json.dump(result.query, sys.stdout, indent=1)
        print()
        return
    idx = SearchIndex.load(args.dataset)
    hits = list(idx.search(result.query, limit=args.limit))
    for h in hits:
        rec = h["record"]
        print(f"{rec['name']}  [{rec.get('types', '')}]")
        if args.explain:
            for line in explain(rec, h["evidence"]):
                print(f"    {line}")
    print(f"-- {len(hits)} faces matched", file=sys.stderr)


def cmd_adjudicate(args):
    from .adjudicate import run_scenarios

    results = run_scenarios(args.scenarios, mage_repo=args.mage_repo)
    if args.cite:
        from . import dataset as ds
        from .cite import Citer, scenario_card_names

        citer = Citer(args.mapping, args.cr)
        _meta, records = ds.load(args.dataset)
        by_name = {}
        for rec in records:
            by_name.setdefault(rec.get("name"), rec)
        for path, result in zip(args.scenarios, results):
            with open(path, encoding="utf-8") as f:
                spec = json.load(f)
            result["citations"] = citer.citations_for_cards(
                scenario_card_names(spec), by_name)
            result["cr_effective"] = citer.cr_effective
    json.dump(results, sys.stdout, indent=1)
    print()
    failed = [r for r in results if r.get("status") != "executed"
              or any(not e.get("pass") for e in r.get("expectations", []))]
    if failed:
        print(f"-- {len(failed)}/{len(results)} scenario(s) errored or missed "
              "expectations", file=sys.stderr)
        sys.exit(1)
    print(f"-- {len(results)} scenario(s) executed, all expectations met",
          file=sys.stderr)


def cmd_answers(args):
    from .answers import find_answers, load_token_scripts

    idx = SearchIndex.load(args.dataset)
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)
    rec = by_name.get(args.threat)
    if not rec:
        print(f"unknown card: {args.threat}", file=sys.stderr)
        sys.exit(1)
    colors = set(args.colors.upper()) if args.colors else None
    res = find_answers(idx, rec, colors=colors,
                       token_scripts=load_token_scripts(args.tokenscripts))
    p = res["threat"]
    traits = [t for t, on in (("hexproof", p["hexproof"]), ("shroud", p["shroud"]),
                              ("indestructible", p["indestructible"]),
                              (str(p["ward"]), bool(p["ward"]))) if on]
    print(f"# {p['name']}  toughness={p['toughness']}  "
          f"{'/'.join(traits) if traits else 'no protection'}")
    for klass, data in res["classes"].items():
        if not data["total"]:
            continue
        print(f"\n{klass}: {data['working']}/{data['total']} work")
        for r in data["top"]:
            mark = {True: "YES ", None: "COND", False: "no  "}[r["works"]]
            print(f"  [{mark}] {r['card']:36} {str(r['manaCost'] or ''):8} "
                  f"{'; '.join(r['reasons'])[:70]}")


def cmd_recommend(args):
    from .recommend import recommend

    idx = SearchIndex.load(args.dataset)
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)
    rec = by_name.get(args.commander)
    if not rec:
        print(f"unknown card: {args.commander}", file=sys.stderr)
        sys.exit(1)
    with open(args.ci_index, encoding="utf-8") as f:
        db = json.load(f)["cards"]
    ci = {n: c.get("ci", "") for n, c in db.items()}
    res = recommend(idx, rec, ci)
    print(f"# {res['commander']}  [color identity: {res['color_identity'] or 'colorless'}]")
    if not res["hooks"]:
        print("no synergy hooks detected")
        return
    for hook, data in res["hooks"].items():
        print(f"\n{hook}: {data['why']}")
        for cname, cl in data["complements"].items():
            print(f"  {cname} ({cl['total']} in-color): {', '.join(cl['top'])}")


def cmd_deck(args):
    from .deck import analyze_deck, parse_decklist

    idx = SearchIndex.load(args.dataset)
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)
    rec = by_name.get(args.commander)
    if not rec:
        print(f"unknown commander: {args.commander}", file=sys.stderr)
        sys.exit(1)
    with open(args.list, encoding="utf-8") as f:
        decklist = parse_decklist(f.read())
    res = analyze_deck(idx, rec, decklist)
    print(f"# {res['commander']} - {res['deck_size']} cards, "
          f"hooks: {', '.join(res['hooks']) or 'none detected'}")
    for hook, data in res["matrix"].items():
        thin = "  [THIN - consider adding]" if data["thin"] else ""
        print(f"\n{hook}: {data['why']}  "
              f"({data['cards_feeding_hook']} cards feed this){thin}")
        for cname, cards in data["classes"].items():
            if cards:
                print(f"  {cname}: {', '.join(cards[:10])}")
    if res["unconnected"]:
        print(f"\nno hook connection ({len(res['unconnected'])}): "
              f"{', '.join(res['unconnected'][:15])}")
    if res["unknown_cards"]:
        print(f"unknown names: {', '.join(res['unknown_cards'][:10])}", file=sys.stderr)

    if args.cross:
        from .deck import cross_synergy
        by_name = {}
        for r in idx.records:
            by_name.setdefault(r.get("name"), r)
        cs = cross_synergy(by_name, rec, decklist)
        print(f"\n== deck-internal cross-synergy: {cs['n_edges']} edges "
              f"across {cs['n_cards']} cards")
        print("engine core (most-connected):")
        for name, deg in cs["engine_core"]:
            print(f"  {deg:3}  {name}")
        seen_pairs = set()
        print("sample edges (non-commander pairs first):")
        commander = res["commander"]
        ordered = sorted(cs["edges"],
                         key=lambda e: (e["src"] == commander or e["dst"] == commander))
        for e in ordered:
            key = (e["src"], e["dst"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            print(f"  {e['src']} <- {e['dst']}  [{e['hook']}/{e['class']}]")
            if len(seen_pairs) >= 20:
                break
        if cs["isolated"]:
            print(f"isolated (no synergy edges): {', '.join(cs['isolated'][:15])}")
        from .deck import find_loops
        loops = find_loops(cs["edges"])
        if loops:
            print(f"synergy loops (cycles in the graph, {len(loops)} found):")
            for lp in loops[:8]:
                print(f"  [{len(lp['edges'])} edges] {' <-> '.join(lp['cards'])}")

    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)

    if args.shape or args.suggest:
        from .deck import deck_shape
        shape = deck_shape(by_name, rec, decklist)
        print(f"\n== deck shape  ({shape['lands']} lands)")
        curve = " ".join(f"{k}:{v}" for k, v in shape["curve"].items())
        print(f"curve (MV:count, 7=7+): {curve}")
        print(f"pips: {shape['pips']}   producing lands: {shape['sources']}")
        for role, cards in shape["roles"].items():
            print(f"  {role:17} {len(cards):2}: {', '.join(cards[:8])}")
        for f in shape["flags"]:
            print(f"  ! {f}")

    if args.goldfish:
        from .goldfish import simulate
        gf = simulate(by_name, rec, decklist, iterations=args.goldfish)
        print(f"\n== goldfish simulation ({gf['iterations']} deals, on the play)")
        print(f"land drops hit: " + "  ".join(
            f"T{t}:{p}%" for t, p in gf["land_drop_pct"].items()))
        print(f"{gf['commander']} (MV {gf['commander_mv']}) castable by: " + "  ".join(
            f"T{t}:{p}%" for t, p in gf["commander_by_turn_pct"].items()))
        print(f"mana screw (<3 lands on T4): {gf['screw_rate_pct']}%")
        print(f"caveats: {gf['caveats']}")

    if args.suggest:
        from .deck import suggest
        with open(args.ci_index, encoding="utf-8") as f:
            db = json.load(f)["cards"]
        ci = {n: c.get("ci", "") for n, c in db.items()}
        printings = {n: c.get("*", []) for n, c in db.items()}
        sg = suggest(idx, by_name, rec, decklist, ci, printings, args.suggest,
                     shape=shape)
        print(f"\n== top {args.suggest} suggested additions "
              f"({sg['candidates_considered']} candidates scored)")
        for s in sg["suggestions"]:
            adj = f"  [{'; '.join(s['adjustments'])}]" if s["adjustments"] else ""
            print(f"  {s['score']:6.1f} ({s['edges']} edges, "
                  f"{s['printings']} printings) {str(s['mv'] or ''):8} {s['card']}{adj}")
            print(f"       {'; '.join(s['why'][:2])}")


def cmd_stats(args):
    idx = SearchIndex.load(args.dataset)
    recs = idx.records
    n_matched = sum(1 for r in recs if r.get("canonicalName"))
    print(json.dumps({
        "meta": getattr(idx, "meta", {}),
        "faces": len(recs),
        "canonical_matched": n_matched,
        "postings_tokens": len(idx.postings),
    }, indent=1))


def main(argv=None):
    p = argparse.ArgumentParser(prog="cardguru")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="parse cardsfolder into a dataset")
    b.add_argument("--cardsfolder", required=True)
    b.add_argument("--canonical", help="canonical card index.json for the name join")
    b.add_argument("--pin", help="source commit/version pin recorded in the dataset")
    b.add_argument("--out", default=DEFAULT_DATASET)
    b.set_defaults(fn=cmd_build)

    s = sub.add_parser("search", help="run a DSL query")
    s.add_argument("query", help="query JSON file")
    s.add_argument("--dataset", default=DEFAULT_DATASET)
    s.add_argument("--limit", type=int)
    s.add_argument("--explain", action="store_true", help="show why each card matched")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_search)

    sh = sub.add_parser("show", help="dump one card's graph record")
    sh.add_argument("name")
    sh.add_argument("--dataset", default=DEFAULT_DATASET)
    sh.set_defaults(fn=cmd_show)

    a = sub.add_parser("ask", help="compile a natural-language question to a query and run it")
    a.add_argument("question")
    a.add_argument("--dataset", default=DEFAULT_DATASET)
    a.add_argument("--ontology", default="research/data/ontology.json")
    a.add_argument("--model", default="claude-opus-5")
    a.add_argument("--limit", type=int)
    a.add_argument("--explain", action="store_true")
    a.add_argument("--compile-only", action="store_true",
                   help="print the compiled query without running it")
    a.set_defaults(fn=cmd_ask)

    ad = sub.add_parser("adjudicate", help="run scenario JSON files through the XMage driver")
    ad.add_argument("scenarios", nargs="+", help="scenario JSON files")
    ad.add_argument("--mage-repo", help="XMage checkout (or env CARDGURU_MAGE_REPO)")
    ad.add_argument("--cite", action="store_true",
                    help="attach CR citations derived from the cards' ability graphs")
    ad.add_argument("--mapping", default="research/data/cr_mapping.json")
    ad.add_argument("--cr", default="research/data/cr_rules.json")
    ad.add_argument("--dataset", default=DEFAULT_DATASET)
    ad.set_defaults(fn=cmd_adjudicate)

    an = sub.add_parser("answers", help="find removal that actually beats a threat")
    an.add_argument("threat", help="threat card name")
    an.add_argument("--colors", help="restrict answers to colors, e.g. WU")
    an.add_argument("--tokenscripts", default=None,
                    help="Forge tokenscripts dir (default: $CARDGURU_TOKENSCRIPTS)")
    an.add_argument("--dataset", default=DEFAULT_DATASET)
    an.set_defaults(fn=cmd_answers)

    dk = sub.add_parser("deck", help="analyze a Commander decklist's hook coverage")
    dk.add_argument("commander", help="commander card name")
    dk.add_argument("--list", required=True, help="decklist text file")
    dk.add_argument("--cross", action="store_true",
                    help="also compute deck-internal cross-synergy edges")
    dk.add_argument("--suggest", type=int, default=0, metavar="N",
                    help="show top-N ranked additions (deck-connectivity score)")
    dk.add_argument("--shape", action="store_true",
                    help="mana curve, color pips vs sources, role quotas")
    dk.add_argument("--goldfish", type=int, default=0, metavar="N",
                    help="Monte Carlo consistency simulation with N deals")
    dk.add_argument("--ci-index", default="/home/user/mse/index/index.json")
    dk.add_argument("--dataset", default=DEFAULT_DATASET)
    dk.set_defaults(fn=cmd_deck)

    rc = sub.add_parser("recommend", help="commander synergy recommendations")
    rc.add_argument("commander", help="commander card name")
    rc.add_argument("--ci-index", default="/home/user/mse/index/index.json",
                    help="canonical card index with color identities")
    rc.add_argument("--dataset", default=DEFAULT_DATASET)
    rc.set_defaults(fn=cmd_recommend)

    st = sub.add_parser("stats", help="dataset statistics")
    st.add_argument("--dataset", default=DEFAULT_DATASET)
    st.set_defaults(fn=cmd_stats)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
