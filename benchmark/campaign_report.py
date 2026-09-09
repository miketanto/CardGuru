"""Render the campaign results as a single self-contained HTML report.

Usage:
  python3 benchmark/campaign_report.py research/data/campaign \
      --out campaign_report.html
"""
import argparse
import json
import os
from collections import defaultdict

TPL_HEAD = """<title>Stackwise Campaign</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root { --bg:#101613; --surface:#1A231D; --surface2:#141C17; --line:#2C382F;
    --ink:#E9EDE7; --muted:#94A29A; --faint:#5F6E64; --red:#DF6A48;
    --green:#82B36C; --gold:#E3BE66; --bad:#D4756B; }
  * { box-sizing:border-box; }
  html { color-scheme:dark; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font-family:"IBM Plex Sans",Arial,sans-serif; font-size:15px; line-height:1.55; }
  .shell { max-width:1000px; margin:0 auto; padding:30px 20px 70px; }
  h1 { font-family:"Fraunces",Georgia,serif; font-size:30px; margin:0 0 6px; }
  h2 { font-family:"Fraunces",Georgia,serif; font-size:20px; margin:34px 0 10px; }
  .sub { color:var(--muted); font-size:14px; max-width:78ch; }
  table { border-collapse:collapse; width:100%; margin-top:10px; font-size:14px; }
  th,td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-size:12px; text-transform:uppercase;
       letter-spacing:.05em; font-weight:600; }
  td.num { font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; }
  .bar { display:inline-block; height:9px; border-radius:5px; background:var(--green);
         vertical-align:middle; margin-right:7px; min-width:2px; }
  .bar.zero { background:var(--faint); }
  .wrap { overflow-x:auto; }
  .card { background:var(--surface); border:1px solid var(--line); border-radius:10px;
          padding:14px 16px; margin-top:12px; }
  .card h3 { margin:0 0 6px; font-size:14px; letter-spacing:.03em;
             text-transform:uppercase; color:var(--muted); }
  code { font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--gold); }
  ul { margin:8px 0 0; padding-left:20px; } li { margin:4px 0; }
  .muted { color:var(--muted); }
</style>
<div class="shell">
"""


def load(path):
    rows = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    camp = load(os.path.join(args.dir, "campaign.jsonl"))
    cells = defaultdict(lambda: {"W": 0, "L": 0, "E": 0, "wall": [],
                                 "a": "", "b": "", "play": [0, 0],
                                 "draw": [0, 0], "turns": []})
    for r in camp:
        c = cells[r["cell"]]
        c["a"], c["b"] = r.get("deck_a", ""), r.get("deck_b", "")
        c["wall"].append(r.get("wall_s", 0))
        res = r.get("result") or {}
        if res.get("status") != "completed":
            c["E"] += 1
            continue
        won = res.get("winner") == "A"
        c["W" if won else "L"] += 1
        c["turns"].append(res.get("turns", 0))
        c["play" if r.get("start") == "A" else "draw"][0 if won else 1] += 1

    rows = []
    for name, c in cells.items():
        n = c["W"] + c["L"]
        rate = 100 * c["W"] / n if n else 0
        avg = sum(c["wall"]) / len(c["wall"]) / 60 if c["wall"] else 0
        turns = sum(c["turns"]) / len(c["turns"]) if c["turns"] else 0
        rows.append(
            f"<tr><td>{esc(c['a'])} <span class='muted'>vs</span> {esc(c['b'])}</td>"
            f"<td class='num'>{c['W']}W&ndash;{c['L']}L</td>"
            f"<td class='num'><span class='bar{' zero' if not rate else ''}' "
            f"style='width:{max(2, rate)}px'></span>{rate:.0f}%</td>"
            f"<td class='num'>{c['play'][0]}&ndash;{c['play'][1]}</td>"
            f"<td class='num'>{c['draw'][0]}&ndash;{c['draw'][1]}</td>"
            f"<td class='num'>{turns:.0f}</td>"
            f"<td class='num'>{avg:.0f} min</td>"
            f"<td class='num'>{c['E'] or ''}</td></tr>")

    tot_w = sum(c["W"] for c in cells.values())
    tot_l = sum(c["L"] for c in cells.values())
    tot_wall = sum(sum(c["wall"]) for c in cells.values())

    html = [TPL_HEAD]
    html.append("<h1>Stackwise Campaign</h1>")
    html.append(
        f"<div class='sub'>Haiku piloting real decks against XMage's MAD AI "
        f"(ComputerPlayer7, skill 6) through the escalation bridge, with "
        f"LLM-scored combat search. {tot_w + tot_l} completed games, "
        f"{tot_wall / 3600:.1f} hours of play, zero API spend.</div>")
    html.append("<h2>Results by matchup</h2><div class='wrap'><table>"
                "<tr><th>Pilot deck vs opponent</th><th>Record</th>"
                "<th>Win rate</th><th>On play</th><th>On draw</th>"
                "<th>Avg turns</th><th>Avg length</th><th>Errors</th></tr>")
    html.extend(rows)
    html.append(f"<tr><td><b>All matchups</b></td><td class='num'><b>{tot_w}W"
                f"&ndash;{tot_l}L</b></td><td class='num'><b>"
                f"{100 * tot_w / max(1, tot_w + tot_l):.0f}%</b></td>"
                f"<td colspan='4'></td><td></td></tr>")
    html.append("</table></div>")
    html.append("</div>")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"{args.out}: {tot_w + tot_l} games across {len(cells)} matchups")


if __name__ == "__main__":
    main()
