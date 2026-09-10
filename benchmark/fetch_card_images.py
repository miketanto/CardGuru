"""Prefetch Scryfall card images for a replay record so the replay page (and
video capture) can run offline and without hammering Scryfall.

Reads one or more replay records (g1_record.jsonl[.gz], written by the
driver's GameRecorder) or v1 game logs (names only), resolves each printing
to a Scryfall image URL by set code + collector number (the same scheme
XMage's own downloader uses), downloads `small` and `normal` sizes into a
cache directory, and writes `images.json` mapping each printing key to the
local files. replay_studio.py reads that manifest with --images-dir.

Usage:
  python3 benchmark/fetch_card_images.py --record research/data/x/g1_record.jsonl.gz \
      [--images-dir research/data/card_images] [--sizes small,normal] [--dry-run]
  python3 benchmark/fetch_card_images.py --log research/data/dp/fixed_search_s23/g1.jsonl ...
"""
import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "CardGuru-replay/1.0 (+https://github.com/miketanto/cardguru)"
API = "https://api.scryfall.com"

# XMage -> Scryfall set-code aliases (XMage's ScryfallImageSupportCards has
# the full table; these are the ones that matter for our meta decks; extend
# as failures show up in --dry-run / the fetch log).
SET_ALIASES = {"CON": "con", "DD3EVG": "evg", "DD3DVD": "dvd", "DD3GVL": "gvl",
               "DD3JVC": "jvc"}


def scry_number(num):
    """XMage collector number -> Scryfall form (ScryfallApiCard transform)."""
    return (num or "").replace("*", "★").replace("+", "†").replace("Ph", "Φ")


def image_urls(card, size="small"):
    """Ordered candidate URLs for one card record ({set, number, name, token, back?})."""
    urls = []
    name = card.get("name") or ""
    setc = (card.get("set") or "").strip()
    num = scry_number(card.get("number"))
    face = "&face=back" if card.get("_back") else ""
    if setc and num and not card.get("token") and num != "0":
        s = SET_ALIASES.get(setc.upper(), setc.lower())
        urls.append(f"{API}/cards/{s}/{urllib.parse.quote(num)}?format=image&version={size}{face}")
        urls.append(f"{API}/cards/{s}/{urllib.parse.quote(num)}?format=image&version={size}"
                    f"&include_variations=true{face}")
    if name:
        q = urllib.parse.quote(name)
        if card.get("token"):
            tq = urllib.parse.quote('!"' + name + '" t:token')
            urls.append(f"{API}/cards/search?q={tq}&unique=art&order=released")
        urls.append(f"{API}/cards/named?exact={q}&format=image&version={size}{face}")
    return urls


def read_cards(record_paths, log_paths):
    """Printing records keyed by key (from records) or name (from v1 logs)."""
    cards = {}
    for rp in record_paths:
        op = gzip.open if rp.endswith(".gz") else open
        with op(rp, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.startswith('{"t":"card"'):
                    continue
                r = json.loads(line)
                cards[r["key"]] = r
                if r.get("back"):
                    b = dict(r["back"])
                    b["token"] = False
                    b["_back"] = True
                    cards[r["key"] + "/back"] = b
    for lp in log_paths:
        with open(lp, encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                st = (row.get("request") or {}).get("state") or {}
                for side in st.values():
                    for zone in ("battlefield", "hand"):
                        for c in side.get(zone) or []:
                            n = c.get("name") if isinstance(c, dict) else c
                            if n:
                                cards.setdefault("N/" + n, {"name": n, "key": "N/" + n})
                    for n in side.get("graveyard") or []:
                        if isinstance(n, str):
                            cards.setdefault("N/" + n, {"name": n, "key": "N/" + n})
    return cards


def slug(key):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", key)


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def resolve_token(search_url, size):
    data, _ = fetch(search_url)
    js = json.loads(data.decode("utf-8"))
    for c in js.get("data") or []:
        uris = c.get("image_uris") or ((c.get("card_faces") or [{}])[0].get("image_uris") or {})
        if uris.get(size):
            return uris[size]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="append", default=[])
    ap.add_argument("--log", action="append", default=[])
    ap.add_argument("--images-dir", default=os.path.join("research", "data", "card_images"))
    ap.add_argument("--sizes", default="small,normal")
    ap.add_argument("--sleep", type=float, default=0.12, help="seconds between requests")
    ap.add_argument("--dry-run", action="store_true", help="print URLs, download nothing")
    args = ap.parse_args()
    if not args.record and not args.log:
        ap.error("give --record and/or --log")
    sizes = [s.strip() for s in args.sizes.split(",") if s.strip()]
    cards = read_cards(args.record, args.log)
    os.makedirs(args.images_dir, exist_ok=True)
    manifest_path = os.path.join(args.images_dir, "images.json")
    manifest = {}
    if os.path.exists(manifest_path):
        manifest = json.load(open(manifest_path, encoding="utf-8"))
    done = fails = 0
    for key, card in sorted(cards.items()):
        entry = manifest.setdefault(key, {})
        for size in sizes:
            fn = f"{slug(key)}_{size}.jpg"
            path = os.path.join(args.images_dir, fn)
            if entry.get(size) and os.path.exists(path):
                continue
            urls = image_urls(card, size)
            if args.dry_run:
                print(f"{key} [{size}]:")
                for u in urls:
                    print("   ", u)
                continue
            ok = False
            for u in urls:
                try:
                    if "/cards/search?" in u:
                        u = resolve_token(u, size)
                        time.sleep(args.sleep)
                        if not u:
                            continue
                    data, ctype = fetch(u)
                    if not ctype.startswith("image/") or len(data) < 1000:
                        continue
                    with open(path, "wb") as f:
                        f.write(data)
                    entry[size] = fn
                    entry["source_url"] = u
                    ok = True
                    done += 1
                    break
                except Exception as e:      # 404, 429, network: try the next form
                    if "429" in str(e):
                        time.sleep(2.0)
                finally:
                    time.sleep(args.sleep)
            if not ok:
                fails += 1
                print(f"  no image for {key} ({card.get('name')})", file=sys.stderr)
        if not args.dry_run:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=1, sort_keys=True)
    if not args.dry_run:
        print(f"{done} images fetched, {fails} missing; manifest {manifest_path}")


if __name__ == "__main__":
    main()
