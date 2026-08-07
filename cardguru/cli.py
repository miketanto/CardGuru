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
                       token_scripts=load_token_scripts(args.tokenscripts),
                       limit_per_class=500 if args.deck else 8)
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
        for r in data["top"][:8]:
            mark = {True: "YES ", None: "COND", False: "no  "}[r["works"]]
            print(f"  [{mark}] {r['card']:36} {str(r['manaCost'] or ''):8} "
                  f"{'; '.join(r['reasons'])[:70]}")

    if args.deck:
        from .answers import answer_density
        from .deck import mana_value, parse_decklist
        with open(args.deck, encoding="utf-8") as f:
            decklist = parse_decklist(f.read())
        deck_names = {n for n, _c in decklist}
        working = {r["card"] for data in res["classes"].values()
                   for r in data["top"] if r["works"] is True}
        deck_answers = working & deck_names
        threat_turn = max(mana_value(rec.get("manaCost")) or 1, 1)
        ad = answer_density(decklist, deck_answers, threat_turn,
                            iterations=args.sim or 5000)
        print(f"\n== answer density vs {p['name']} (expected on turn {threat_turn})")
        print(f"working answers in your deck ({len(deck_answers)}): "
              f"{', '.join(sorted(deck_answers)) or 'NONE'}")
        for t, pct in ad["p_have_answer_by_turn"].items():
            marker = "  <- threat arrives" if t == threat_turn else ""
            print(f"  P(answer in hand by T{t}): {pct}%{marker}")
        arrival = ad["p_have_answer_by_turn"].get(threat_turn, 0)
        if arrival < 60:
            print(f"  ! ANSWER DEFICIT: {arrival}% at arrival vs 60% target - "
                  f"add more working answers")


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
        print(f"\n== deck shape  ({shape['lands']} lands, "
              f"gameplan: {shape['gameplan']})")
        curve = " ".join(f"{k}:{v}" for k, v in shape["curve"].items())
        print(f"curve (MV:count, 7=7+): {curve}")
        print(f"pips: {shape['pips']}   producing lands: {shape['sources']}")
        for role, d in shape["roles"].items():
            eff = shape["effective_roles"][role]
            parts = []
            if d["engines"]:
                parts.append(f"engines: {', '.join(d['engines'][:6])}")
            if d["one_shot"]:
                parts.append(f"one-shot: {', '.join(d['one_shot'][:6])}")
            print(f"  {role:17} eff {eff:2}: {'; '.join(parts)}")
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
        print(f"dead turns: " + "  ".join(
            f"T{t}:{p}%" for t, p in gf["dead_turn_pct"].items()))
        print(f"avg mana: " + "  ".join(
            f"T{t}:{m}" for t, m in gf["avg_mana_by_turn"].items()))
        print(f"mana screw (<3 lands on T4): {gf['screw_rate_pct']}%")
        for v in gf["verdicts"]:
            print(f"  ! {v}" if "DEFICIT" in v else f"  {v}")
        print(f"caveats: {gf['caveats']}")

    if args.cuts or args.fix:
        from .deck import cross_synergy, cuts as find_cuts
        from .deck import deck_shape as _shape_fn
        shape2 = shape if (args.shape or args.suggest) else _shape_fn(by_name, rec, decklist)
        cs2 = cross_synergy(by_name, rec, decklist)
        cut_rows = find_cuts(by_name, rec, decklist, cs2["edges"], shape2,
                             top_n=max(args.cuts or 8, 8))
        if args.cuts:
            print(f"\n== top {args.cuts} cut candidates")
            for r in cut_rows[:args.cuts]:
                print(f"  {r['cut_score']:6.1f}  {r['card']:32} "
                      f"({'; '.join(r['reasons'])})")
        if args.fix:
            from .deck import prescribe
            rx = prescribe(by_name, rec, decklist, shape2, cut_rows)
            b = rx["baseline"]
            key_t = max(b["commander_mv"], 1)
            print(f"\n== prescriptions (measured by re-simulation, "
                  f"{b['iterations']} deals each)")
            print(f"baseline: on-curve {b['commander_by_turn_pct'].get(key_t)}%, "
                  f"T3 drops {b['land_drop_pct'][3]}%, screw {b['screw_rate_pct']}%")
            if not rx["variants"]:
                print(rx.get("note", ""))
            for v in rx["variants"]:
                d = v["delta"]
                a = v["after"]
                print(f"\n  RX: {v['label']}")
                print(f"      cut: {', '.join(v['cut'])}")
                print(f"      on-curve {a['commander_on_curve']}% "
                      f"({d['commander_on_curve']:+.1f}), "
                      f"T3 drops {a['t3_land_drop']}% ({d['t3_land_drop']:+.1f}), "
                      f"screw {a['screw_rate']}% ({d['screw_rate']:+.1f})")
                remaining = [x for x in a["verdicts"] if "DEFICIT" in x]
                print(f"      remaining deficits: "
                      f"{len(remaining)} ({'; '.join(remaining) or 'none'})"
                      if remaining else "      all consistency targets met")

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
            print(f"  {s['score']:6.1f} ({s['edges']} edges, "
                  f"{s['printings']} printings) {str(s['mv'] or ''):8} {s['card']}"
                  f"  <- {s['picked_for']}")
            print(f"       {'; '.join(s['why'][:2])}")


def cmd_threats(args):
    from .answers import load_token_scripts
    from .deck import parse_decklist
    from .threats import analyze_opponent

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
    colors = set(args.colors.upper()) if args.colors else None
    res = analyze_opponent(idx, by_name, rec, decklist, colors,
                           token_scripts=load_token_scripts())
    print(f"# opposing deck: {args.commander} - gameplan: {res['gameplan']}")
    top_hooks = list(res["hook_counts"].items())[:5]
    print(f"hook profile: {', '.join(f'{h}({c})' for h, c in top_hooks)}")
    print(f"\nkey threats (synergy centrality + enabler weight):")
    for name, score in res["key_threats"]:
        d = res.get("key_detail", {}).get(name, {})
        extra = f"  ({d['enabler_why']})" if d.get("enabler_why") else ""
        print(f"  {score:3}  {name}{extra}")
    if res["loops"]:
        print(f"\nloops to break:")
        for lp in res["loops"][:3]:
            print(f"  {' <-> '.join(lp['cards'])}")
    print(f"\n== coverage answers: work vs ALL {len(res['surgical'])} key threats "
          f"({res['coverage_pool']} in-color)")
    for c in res["coverage_answers"]:
        print(f"  {c}")
    print(f"\n== surgical answers (your colors: {args.colors or 'any'})")
    for s in res["surgical"]:
        flags = f"  [{'/'.join(s['profile_flags'])}]" if s["profile_flags"] else ""
        print(f"\n{s['threat']} (centrality {s['centrality']}){flags}")
        for a in s["answers"]:
            print(f"  {a['card']:32} [{a['class']}] {a['reason'][:60]}")
    sw = res.get("sweeper_sizing")
    if sw:
        print(f"\n== sweeper sizing (their toughness curve)")
        print(f"  {sw['tier']} damage clears {sw['kills']}/{sw['bodies']} bodies "
              f"({sw['kill_pct']}%)"
              + (f"; survivors: {', '.join(sw['survivors'])}" if sw["survivors"] else ""))
        print(f"  cheapest at tier: {', '.join(sw['examples'])}")
    mv = res.get("mv_sweep")
    if mv:
        print(f"\n== mana-value sweep (their cost curve - the other sizing axis)")
        print(f"  destroy MV<={mv['tier']} clears {mv['kills']}/{mv['bodies']} bodies "
              f"({mv['kill_pct']}%); full clear at MV<={mv['full_clear_x']}"
              + (f"; survivors at tier: {', '.join(mv['survivors'])}"
                 if mv["survivors"] else ""))
        for ex in mv["examples"]:
            print(f"  {ex['card']:32} {ex['note']}")

    swc = res.get("stack_window") or {}
    if swc.get("closers") or swc.get("self_uncounterable"):
        print(f"\n== stack window contests (how counterable is their deck)")
        for c in swc.get("closers", []):
            print(f"  {c['count']}x {c['card']}: GRANTS uncounterability to "
                  f"other spells - counterspells unreliable while it's up")
        for c in swc.get("self_uncounterable", []):
            print(f"  {c['count']}x {c['card']}: can't be countered itself")

    print(f"\n== systemic disruption (vs a {res['gameplan']} gameplan)")
    for cname, data in res["systemic"].items():
        print(f"  {cname} ({data['total']} in-color): {', '.join(data['top'])}")

    from .intuition import axis_profile, hate_for_axes
    prof = axis_profile(by_name, rec, decklist)
    print(f"\n== derived axis hate (the deck's scaling axes, and what throttles them)")
    for h in hate_for_axes(idx, prof, colors, min_signal=4):
        print(f"\n{h['axis']}: {h['why']}")
        for cname, data in h["hate"].items():
            if data["total"]:
                print(f"  {cname} ({data['total']} in-color): {', '.join(data['top'])}")


def cmd_windows(args):
    from .intuition import answer_windows

    idx = SearchIndex.load(args.dataset)
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)
    rec = by_name.get(args.card)
    if not rec:
        print(f"unknown card: {args.card}", file=sys.stderr)
        sys.exit(1)
    w = answer_windows(rec)
    print(f"# answer windows for {w['card']}")
    for x in w["windows"]:
        print(f"  OPEN  {x['window']:10} -> {x['answer']}")
        print(f"        ({x['reason']})")
    for x in w["closed"]:
        print(f"  SHUT  {x['window']:10} ({x['reason']})")


def cmd_gaps(args):
    from .gaps import mine_gaps

    idx = SearchIndex.load(args.dataset)
    report = mine_gaps(idx.records, top_n=args.top)
    print(f"cards: {report['total_cards']}, concept-uncovered: "
          f"{report['uncovered_cards']} "
          f"({100 * report['uncovered_cards'] / report['total_cards']:.1f}%)")
    print("top unexplained structural clusters (candidate concepts):")
    for c in report["clusters"]:
        print(f"  {c['uncovered_cards']:5}  {c['signature']:40} "
              f"e.g. {', '.join(c['examples'][:3])}")


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
    an.add_argument("--deck", default=None,
                    help="decklist file: simulate P(holding a working answer) "
                         "when the threat arrives")
    an.add_argument("--sim", type=int, default=0,
                    help="iterations for --deck answer-density simulation")
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
    dk.add_argument("--cuts", type=int, default=0, metavar="N",
                    help="show top-N cut candidates (low synergy, no needed role)")
    dk.add_argument("--fix", action="store_true",
                    help="prescribe swaps for measured deficits and re-simulate")
    dk.add_argument("--ci-index", default="/home/user/mse/index/index.json")
    dk.add_argument("--dataset", default=DEFAULT_DATASET)
    dk.set_defaults(fn=cmd_deck)

    th = sub.add_parser("threats",
                        help="profile an opposing deck's gameplan and answer it")
    th.add_argument("commander", help="opposing commander name")
    th.add_argument("--list", required=True, help="opposing decklist file")
    th.add_argument("--colors", help="your colors, e.g. WU")
    th.add_argument("--dataset", default=DEFAULT_DATASET)
    th.set_defaults(fn=cmd_threats)

    gp = sub.add_parser("gaps",
                        help="mine unexplained structural clusters (candidate concepts)")
    gp.add_argument("--top", type=int, default=30)
    gp.add_argument("--dataset", default=DEFAULT_DATASET)
    gp.set_defaults(fn=cmd_gaps)

    wd = sub.add_parser("windows",
                        help="where can this threat be interacted with at all")
    wd.add_argument("card", help="threat card name")
    wd.add_argument("--dataset", default=DEFAULT_DATASET)
    wd.set_defaults(fn=cmd_windows)

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
