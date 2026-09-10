"""Phase 0c (v7 plan §2): fetch published MTGO event decklists.

mtgo.com publishes every League 5-0 dump, Preliminary, Challenge and
Showcase as a page that embeds the full decklists as JSON
(`window.MTGO.decklists.data`).  The month archive
`https://www.mtgo.com/decklists/YYYY/MM` lists 250-450 events per month.

This script walks the month archives, fetches each event page once, and
writes a compact per-event JSON to <out>/<slug>.json:

  {event_id, site_name, description, format, starttime, type,
   player_count, decklists: [{player, loginid, main: [[name, qty]...],
   side: [[name, qty]...]}], winloss: {loginid: [wins, losses]},
   final_rank: {loginid: rank}}

Cost model (measured 2026-09-10): a page nobody has opened renders
server-side in ~25 s; a cached one returns in 0.3 s.  The client is never
the bottleneck, so --workers (default 6) concurrent fetches, each sleeping
--sleep between requests, is the knob; existing files are skipped, so a
rerun only fetches what is new.  Progress goes to <out>/fetch.log.

Run:
    python rl/decklists/fetch_mtgo.py --months 2026-07 2026-08 2026-09
        [--out rl/artifacts/decklists_v1/raw/mtgo] [--sleep 0.5]
        [--formats CMODERN CSTANDARD ...] [--max-events N]
"""
import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE = "https://www.mtgo.com"
UA = "Mozilla/5.0 (CardGuru research; decklist corpus for RL pretraining)"
_HREF = re.compile(r'href="(/decklist/[^"]+)"')
_DATA = re.compile(r"window\.MTGO\.decklists\.data\s*=\s*(\{.*?\})\s*;\s*\n", re.S)


# No system-proxy autodetection (slow on Windows), gzip transfer (event pages
# are 340 KB plain, 37 KB gzipped).
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def get(url, retries=4, timeout=60):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with _OPENER.open(req, timeout=timeout) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return body.decode("utf-8", "replace")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last = e
            time.sleep(2.0 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def cards(items):
    out = []
    for it in items or []:
        a = it.get("card_attributes") or it
        name = a.get("card_name") or it.get("card_name")
        qty = a.get("qty") or it.get("qty")
        if name is None or qty is None:
            continue
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            continue
        out.append([name, qty])
    return out


def compact(d):
    wl = {w["loginid"]: [int(w.get("wins", 0)), int(w.get("losses", 0))]
          for w in d.get("winloss") or [] if "loginid" in w}
    fr = {r["loginid"]: int(r["rank"]) for r in d.get("final_rank") or []
          if "loginid" in r and str(r.get("rank", "")).isdigit()}
    pc = d.get("player_count") or {}
    return {
        "event_id": d.get("event_id"), "site_name": d.get("site_name"),
        "description": d.get("description"), "format": d.get("format"),
        "starttime": d.get("starttime"), "type": d.get("type"),
        "player_count": pc.get("players"),
        "decklists": [{"player": x.get("player"), "loginid": x.get("loginid"),
                       "main": cards(x.get("main_deck")),
                       "side": cards(x.get("sideboard_deck"))}
                      for x in d.get("decklists") or []],
        "winloss": wl, "final_rank": fr,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", nargs="+", required=True, help="YYYY-MM ...")
    ap.add_argument("--out", default=os.path.join(REPO, "rl", "artifacts", "decklists_v1", "raw", "mtgo"))
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--formats", nargs="*", default=None,
                    help="keep only these MTGO format codes (slug prefix match, e.g. modern legacy)")
    ap.add_argument("--max-events", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6,
                    help="parallel event fetches; each worker still sleeps --sleep between requests")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    log = open(os.path.join(args.out, "fetch.log"), "a", encoding="utf-8")

    def say(msg):
        line = time.strftime("%H:%M:%S ") + msg
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    slugs = []
    for ym in args.months:
        y, m = ym.split("-")
        html = get(f"{BASE}/decklists/{y}/{m}")
        found = sorted(set(_HREF.findall(html)))
        say(f"month {ym}: {len(found)} events")
        slugs += found
        time.sleep(args.sleep)
    if args.formats:
        slugs = [s for s in slugs if any(s.split("/")[-1].startswith(f.lower()) for f in args.formats)]
    if args.max_events:
        slugs = slugs[:args.max_events]

    n_new = n_skip = n_fail = n_lists = 0
    todo = []
    for href in slugs:
        slug = href.split("/")[-1]
        if os.path.exists(os.path.join(args.out, slug + ".json")):
            n_skip += 1
        else:
            todo.append((href, slug))

    def fetch_one(item):
        href, slug = item
        t0 = time.time()
        try:
            m = None
            for attempt in range(3):          # a cold page renders in ~25 s; a partial/error page has no data
                html = get(BASE + href)
                m = _DATA.search(html)
                if m:
                    break
                time.sleep(5.0 * (attempt + 1))
            if not m:
                raise RuntimeError("no embedded decklists.data after 3 attempts")
            d = compact(json.loads(m.group(1)))
            with open(os.path.join(args.out, slug + ".json"), "w", encoding="utf-8") as f:
                json.dump(d, f)
            time.sleep(args.sleep)
            log.write("ok %s lists=%d %.1fs\n" % (slug, len(d["decklists"]), time.time() - t0))
            return slug, len(d["decklists"]), None
        except Exception as e:                                   # noqa: BLE001
            time.sleep(args.sleep)
            return slug, 0, str(e)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        for i, (slug, n, err) in enumerate(ex.map(fetch_one, todo)):
            if err:
                n_fail += 1
                say(f"FAIL {slug}: {err}")
                continue
            n_new += 1
            n_lists += n
            if n_new % 25 == 0:
                say(f"{i + 1}/{len(todo)} fetched={n_new} lists={n_lists} skipped={n_skip} failed={n_fail}")
    say(f"DONE events={len(slugs)} fetched={n_new} lists={n_lists} skipped={n_skip} failed={n_fail}")
    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
