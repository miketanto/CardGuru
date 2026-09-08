"""CardGuru CLI.

  python -m cardguru build     --cardsfolder PATH [--canonical INDEX.json] [--pin SHA] [--out data/dataset.jsonl.gz]
  python -m cardguru cardstore [--download] [--scryfall PATH] [--db PATH]
  python -m cardguru join      [--dataset PATH] [--db PATH] [--report PATH] [--resolve-misses]
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
DEFAULT_CARDDB = "data/cards.sqlite"
DEFAULT_SCRYFALL = "data/scryfall-oracle-cards.jsonl.gz"
DEFAULT_ALIASES = "data/aliases.json"


def cmd_build(args):
    t0 = time.time()
    stats = ds.build(args.cardsfolder, args.out, canonical_index=args.canonical,
                     source_pin=args.pin)
    stats["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(stats, indent=1))


def load_color_identity(ci_index: str | None, db_path: str = DEFAULT_CARDDB):
    """Color identity (and the printing-count prior, when available).

    Prefers an explicit --ci-index; otherwise falls back to the Scryfall card
    store. The store has no printing counts — oracle-cards is one row per
    oracle card — so that prior is reported as unavailable rather than
    silently zeroed.
    """
    if ci_index:
        with open(ci_index, encoding="utf-8") as f:
            db = json.load(f)["cards"]
        return ({n: c.get("ci", "") for n, c in db.items()},
                {n: c.get("*", []) for n, c in db.items()}, ci_index)

    from .cardstore import CardStore
    store = CardStore.open(db_path)
    if store is None:
        raise SystemExit(
            f"no color-identity source: pass --ci-index, or build the card "
            f"store with `python -m cardguru cardstore --download`")
    # Scryfall returns "GW"; the rest of the codebase assumes the old index's
    # lowercase convention (recommend.CI_ORDER == "wubrg").
    ci = {row["name"]: (row["color_identity"] or "").lower() for row in
          store.conn.execute("SELECT name, color_identity FROM cards")}
    return ci, {}, db_path


def cmd_cardstore(args):
    from . import join as jn
    from . import cardstore as cs

    snapshot = args.snapshot
    if args.download:
        info = jn.download_bulk(args.scryfall)
        snapshot = snapshot or info["updated_at"]
        print(f"downloaded {info['size'] / 1e6:.1f} MB "
              f"(snapshot {info['updated_at']})", file=sys.stderr)
    t0 = time.time()
    stats = cs.build(args.scryfall, args.db, snapshot_date=snapshot,
                     aliases_path=args.aliases)
    stats["seconds"] = round(time.time() - t0, 1)
    stats["db"] = args.db
    print(json.dumps(stats, indent=1))


def cmd_join(args):
    from . import join as jn
    from .cardstore import CardStore

    store = CardStore.open(args.db)
    if store is None:
        raise SystemExit(f"no card store at {args.db}; run `cardguru cardstore "
                         f"--download` first")
    rep = jn.report(args.dataset, store)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=1, ensure_ascii=False)
            f.write("\n")
    summary = {k: rep[k] for k in
               ("forge_pin", "scryfall_snapshot", "total_faces", "matched",
                "match_rate", "by_class")}
    print(json.dumps(summary, indent=1))
    if args.resolve_misses:
        out = jn.resolve_candidates(rep["misses"], args.candidates)
        print(json.dumps(out, indent=1), file=sys.stderr)


def cmd_similar(args):
    from .similar import similar

    idx = SearchIndex.load(args.dataset)
    rec, query, hits, exact, opts = similar(idx, args.card, limit=args.limit,
                                            ability=args.ability)
    if not exact:
        print(f"# no exact match for {args.card!r} - using {rec['name']!r}",
              file=sys.stderr)
    print(f"# like {rec['name']}  [{rec.get('manaCost')}] {rec.get('types')}")
    print(f"# signature: {json.dumps(query)}", file=sys.stderr)
    for h in hits:
        print(f"{h['name']}  [{h.get('types','')}]")
    print(f"-- {len(hits)} similar", file=sys.stderr)
    if len(opts) > 1 and args.ability is None:
        print(f"-- {rec['name']} has {len(opts)} distinguishable abilities; "
              f"--ability N to match on just one:", file=sys.stderr)
        for i, o in enumerate(opts, 1):
            print(f"     {i}. reaches {o['reaches']:5}  "
                  f"{json.dumps(o['spec'])[:88]}", file=sys.stderr)


def cmd_shapes(args):
    from .shapes import build, overloaded, render_facet

    sh = build(args.dataset, args.out, min_total=args.min_total)
    m = sh["_meta"]
    print(f"{m['modes']} overloaded modes, {m['apis']} overloaded apis "
          f"-> {args.out} ({m['bytes'] / 1024:.0f} KB)")
    if args.facet:
        kind = "api" if args.facet in sh.get("api", {}) else "mode"
        print("\n".join(render_facet(sh, kind, args.facet)))
        return
    print("\nMost overloaded modes (bare mode conflates N distinct meanings):")
    for facet, n, total in overloaded(sh, "mode", args.top):
        print(f"  {n:3} shapes  {total:6} nodes  {facet}")


def cmd_families(args):
    from .families import build, render

    fams = build(args.dataset, args.out)
    m = fams["_meta"]
    print(f"{m['families']} disjunctive families over {m['facets_considered']} "
          f"facets -> {args.out} ({m['bytes'] / 1024:.0f} KB)")
    lines = render(fams, kind=args.kind)
    if args.anchor:
        lines = [l for l in lines if f"[{args.anchor}" in l or f"/{args.anchor}]" in l]
    print("\n".join(lines[:args.top]))


def cmd_serve(args):
    from .server import serve

    serve(args.dataset, args.db, args.questions, args.ontology,
          host=args.host, port=args.port, verbose=args.verbose,
          signals=args.signals)


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
    from .nl_compiler import MODEL, compile_question
    from .repair import make_checker

    # The index is loaded up front now: the compile loop executes each
    # candidate query and repairs on what came back, so it needs the corpus
    # before compiling rather than after.
    idx = SearchIndex.load(args.dataset)
    result = compile_question(args.question, args.ontology,
                              model=args.model or MODEL,
                              use_cache=not args.no_cache,
                              checker=make_checker(idx, args.signals))
    if not result.ok:
        print("compilation failed:", file=sys.stderr)
        for line in result.errors:
            print(f"  {line}", file=sys.stderr)
        sys.exit(1)
    note = f"# compiled query ({len(result.attempts)} attempt(s)"
    if result.checks:
        note += f", execution {result.checks}"
    if result.exhausted:
        note += ", best-effort: retries exhausted"
    print(note + "):", file=sys.stderr)
    print(json.dumps(result.query, indent=1), file=sys.stderr)
    if args.compile_only:
        json.dump(result.query, sys.stdout, indent=1)
        print()
        return
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
    ci, _, _ = load_color_identity(args.ci_index)
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
        ci, printings, src = load_color_identity(args.ci_index)
        if not printings:
            print(f"note: color identity from {src}; printing-count prior "
                  f"unavailable (pass --ci-index to restore it)", file=sys.stderr)
        sg = suggest(idx, by_name, rec, decklist, ci, printings, args.suggest,
                     shape=shape)
        print(f"\n== top {args.suggest} suggested additions "
              f"({sg['candidates_considered']} candidates scored)")
        for s in sg["suggestions"]:
            print(f"  {s['score']:6.1f} ({s['edges']} edges, "
                  f"{s['printings']} printings) {str(s['mv'] or ''):8} {s['card']}"
                  f"  <- {s['picked_for']}")
            print(f"       {'; '.join(s['why'][:2])}")


def cmd_fingerprint(args):
    from .deck import parse_decklist
    from .fingerprint import break_plan, build_fingerprint

    idx = SearchIndex.load(args.dataset)
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)
    with open(args.list, encoding="utf-8") as f:
        decklist = parse_decklist(f.read())
    fp = build_fingerprint(by_name, decklist)
    print(f"# fingerprint: {args.list} - {len(fp['nodes'])} functional cards, "
          f"{len(fp['edges'])} intra-deck edges")

    print("\n== engine spine (dominant edge families)")
    for s in fp["spine"][:5]:
        print(f"  {s['weight']:3}  {s['family']}")
        print(f"       enablers: {', '.join(s['enablers'][:6])}")
        print(f"       payoffs:  {', '.join(s['payoffs'][:6])}")

    print("\n== linchpins (centrality x availability, "
          "+ sole-provider bonus)")
    for name, score in fp["linchpins"][:8]:
        meta = fp["nodes"][name]
        tags = []
        if meta["wincon"]:
            tags.append("wincon")
        tags += meta["interaction"]
        sole = fp["sole_provider"].get(name)
        if sole:
            tags.append(f"SOLE PROVIDER: {sole[0]}")
        print(f"  {score:6}  {name} x{meta['copies']}"
              f"  [{', '.join(tags) or 'engine'}]")

    if fp.get("resource_cuts"):
        print("\n== resource cuts (starve the engine, not the card)")
        for rc in fp["resource_cuts"]:
            print(f"  {rc['note']}")

    print("\n== break plan")
    for plan in break_plan(by_name, fp, top=args.top):
        print(f"\n  {plan['card']}  (score {plan['score']})")
        for w in plan["why_linchpin"][:3]:
            print(f"    linchpin because: {w}")
        for a in plan["avoid"]:
            print(f"    AVOID {a['window']}: {a['note']}")
        for w in plan["windows"]:
            print(f"    open {w['window']}: {w['note']}")
        if plan["ward"]:
            print(f"    note: {plan['ward']}")
        print(f"    preferred cut: {plan['preferred']}")


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


def _puzzle_runner(args):
    """local -> LocalRunner over the card store; xmage -> batch adjudicator."""
    if args.engine == "local":
        from .cardstore import CardStore
        from .localrunner import LocalRunner
        return LocalRunner(CardStore.open(args.db)).run_scenarios
    from .adjudicate import run_scenarios
    from .puzzle import run_scenarios_from_specs
    return lambda specs: run_scenarios_from_specs(specs, run_scenarios,
                                                  args.mage_repo)


def cmd_puzzle_gen(args):
    from .cardstore import CardStore
    from .puzzlegen import generate, write_puzzles

    store = CardStore.open(args.db)
    if store is None:
        sys.exit(f"card store not found at {args.db} "
                 "(build it with: python -m cardguru cardstore)")
    paths = write_puzzles(generate(store, count=args.count, seed=args.seed),
                          args.out)
    print(f"wrote {len(paths)} puzzles to {args.out}/")


def cmd_puzzle_validate(args):
    from .puzzle import load_puzzles

    specs = load_puzzles(args.puzzles)  # raises with the file and reason
    print(f"{len(specs)} puzzle(s) structurally valid")


def cmd_puzzle_admit(args):
    from .puzzle import admit, load_puzzles

    reports = admit(load_puzzles(args.puzzles), runner=_puzzle_runner(args))
    json.dump(reports, sys.stdout, indent=1)
    print()
    rejected = [r for r in reports if not r["admitted"]]
    engines = sorted({r["engine"] for r in reports if r["engine"]})
    print(f"-- {len(reports) - len(rejected)}/{len(reports)} admitted "
          f"(engine: {', '.join(engines) or 'none'})", file=sys.stderr)
    if any(e != "xmage" for e in engines):
        print("-- provisional: not engine-verified; rerun with "
              "--engine xmage before publishing numbers", file=sys.stderr)
    if rejected:
        sys.exit(1)


def cmd_puzzle_grade(args):
    from .puzzle import grade, load_puzzles

    with open(args.lines, encoding="utf-8") as f:
        lines = json.load(f)
    specs = [s for s in load_puzzles(args.puzzles) if s["id"] in lines]
    pairs = [(s, lines[s["id"]]) for s in specs]
    verdicts = grade(pairs, runner=_puzzle_runner(args))
    json.dump(verdicts, sys.stdout, indent=1)
    print()
    wins = sum(1 for v in verdicts if v["win"])
    print(f"-- {wins}/{len(verdicts)} lines win", file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(prog="cardguru")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="parse cardsfolder into a dataset")
    b.add_argument("--cardsfolder", required=True)
    b.add_argument("--canonical", help="canonical card index.json for the name join")
    b.add_argument("--pin", help="source commit/version pin recorded in the dataset")
    b.add_argument("--out", default=DEFAULT_DATASET)
    b.set_defaults(fn=cmd_build)

    cs_ = sub.add_parser("cardstore", help="build the Scryfall card store (attribute tier)")
    cs_.add_argument("--download", action="store_true",
                     help="fetch the current Scryfall oracle-cards bulk file first")
    cs_.add_argument("--scryfall", default=DEFAULT_SCRYFALL)
    cs_.add_argument("--db", default=DEFAULT_CARDDB)
    cs_.add_argument("--aliases", default=DEFAULT_ALIASES,
                     help="hand-reviewed alias table; only status='confirmed' rows apply")
    cs_.add_argument("--snapshot", help="oracle data date stamped into the store")
    cs_.set_defaults(fn=cmd_cardstore)

    jo = sub.add_parser("join", help="report Forge->Scryfall match rate and misses")
    jo.add_argument("--dataset", default=DEFAULT_DATASET)
    jo.add_argument("--db", default=DEFAULT_CARDDB)
    jo.add_argument("--report", default="data/join_report.json")
    jo.add_argument("--resolve-misses", action="store_true",
                    help="query Scryfall fuzzy for each miss; writes review candidates")
    jo.add_argument("--candidates", default="data/alias_candidates.json")
    jo.set_defaults(fn=cmd_join)

    si = sub.add_parser("similar", help='cards structurally like a given card')
    si.add_argument("card")
    si.add_argument("--dataset", default=DEFAULT_DATASET)
    si.add_argument("--limit", type=int)
    si.add_argument("--ability", type=int,
                    help="match on one ability only (see the list printed after a run)")
    si.set_defaults(fn=cmd_similar)

    sp = sub.add_parser("shapes", help="mine param-shape clusters from the dataset")
    sp.add_argument("--dataset", default=DEFAULT_DATASET)
    sp.add_argument("--out", default="data/shapes.json")
    sp.add_argument("--min-total", type=int, default=8)
    sp.add_argument("--top", type=int, default=15)
    sp.add_argument("--facet", help="print the shape table for one mode/api")
    sp.set_defaults(fn=cmd_shapes)

    fm = sub.add_parser("families",
                        help="mine disjunctive api/mode families from the dataset")
    fm.add_argument("--dataset", default=DEFAULT_DATASET)
    fm.add_argument("--out", default="data/families.json")
    fm.add_argument("--kind", choices=("api", "mode"))
    fm.add_argument("--anchor", help="only families with this anchor word")
    fm.add_argument("--top", type=int, default=40)
    fm.set_defaults(fn=cmd_families)

    sv = sub.add_parser("serve", help="web UI for mechanical search")
    sv.add_argument("--dataset", default=DEFAULT_DATASET)
    sv.add_argument("--db", default=DEFAULT_CARDDB)
    sv.add_argument("--questions", default="benchmark/compiled_questions.json",
                    help="preset question library shown in the sidebar")
    sv.add_argument("--ontology", default="research/data/ontology.json")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("-v", "--verbose", action="store_true",
                    help="log every query, compiled output, and zero-hit diagnosis")
    sv.add_argument("--signals", choices=("off", "zero", "full"), default="zero",
                    help="execution feedback in the compile loop (see `ask`)")
    sv.set_defaults(fn=cmd_serve)

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
    a.add_argument("--model", default=None,
                   help="default is the cheapest model; override per call "
                        "or set CARDGURU_MODEL")
    a.add_argument("--no-cache", action="store_true",
                   help="force a live API call instead of reusing a cached compile")
    a.add_argument("--limit", type=int)
    a.add_argument("--explain", action="store_true")
    a.add_argument("--compile-only", action="store_true",
                   help="print the compiled query without running it")
    a.add_argument("--signals", choices=("off", "zero", "full"), default="zero",
                   help="execution feedback in the compile loop: off = retry "
                        "on validation errors only (pre-2026-08 behaviour); "
                        "zero = also repair queries that return no cards; "
                        "full = also report over-narrow parameters")
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
    dk.add_argument("--ci-index", default=None,
                    help="canonical index with color identity + printing counts; defaults to the Scryfall card store")
    dk.add_argument("--dataset", default=DEFAULT_DATASET)
    dk.set_defaults(fn=cmd_deck)

    th = sub.add_parser("threats",
                        help="profile an opposing deck's gameplan and answer it")
    th.add_argument("commander", help="opposing commander name")
    th.add_argument("--list", required=True, help="opposing decklist file")
    th.add_argument("--colors", help="your colors, e.g. WU")
    th.add_argument("--dataset", default=DEFAULT_DATASET)
    th.set_defaults(fn=cmd_threats)

    fp = sub.add_parser("fingerprint",
                        help="per-deck causal graph: what makes it run, "
                             "where to cut it")
    fp.add_argument("--list", required=True, help="decklist file")
    fp.add_argument("--top", type=int, default=3,
                    help="linchpins to build break plans for")
    fp.add_argument("--dataset", default=DEFAULT_DATASET)
    fp.set_defaults(fn=cmd_fingerprint)

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
    rc.add_argument("--ci-index", default=None,
                    help="canonical card index with color identities; defaults to the Scryfall card store")
    rc.add_argument("--dataset", default=DEFAULT_DATASET)
    rc.set_defaults(fn=cmd_recommend)

    st = sub.add_parser("stats", help="dataset statistics")
    st.add_argument("--dataset", default=DEFAULT_DATASET)
    st.set_defaults(fn=cmd_stats)

    pz = sub.add_parser("puzzle", help="decision puzzles: generate, admit, grade")
    pzsub = pz.add_subparsers(dest="puzzle_cmd", required=True)
    pg = pzsub.add_parser("gen", help="generate tier-1 lethal puzzles")
    pg.add_argument("--count", type=int, default=30)
    pg.add_argument("--seed", type=int, default=7)
    pg.add_argument("--out", default="puzzles/t1")
    pg.add_argument("--db", default=DEFAULT_CARDDB)
    pg.set_defaults(fn=cmd_puzzle_gen)
    pv = pzsub.add_parser("validate", help="structural validation of puzzle files")
    pv.add_argument("puzzles", nargs="+")
    pv.set_defaults(fn=cmd_puzzle_validate)
    pa = pzsub.add_parser("admit",
                          help="instrument check: known_good wins, known_bad loses")
    pa.add_argument("puzzles", nargs="+")
    pa.add_argument("--engine", choices=["local", "xmage"], default="local")
    pa.add_argument("--mage-repo", help="XMage checkout for --engine xmage")
    pa.add_argument("--db", default=DEFAULT_CARDDB)
    pa.set_defaults(fn=cmd_puzzle_admit)
    pr = pzsub.add_parser("grade", help="grade proposed lines against puzzles")
    pr.add_argument("puzzles", nargs="+")
    pr.add_argument("--lines", required=True,
                    help="JSON file: {puzzle_id: [actions...]}")
    pr.add_argument("--engine", choices=["local", "xmage"], default="local")
    pr.add_argument("--mage-repo")
    pr.add_argument("--db", default=DEFAULT_CARDDB)
    pr.set_defaults(fn=cmd_puzzle_grade)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
