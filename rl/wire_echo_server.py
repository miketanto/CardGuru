#!/usr/bin/env python3
"""Record the raw policy wire without a model.

Accepts one connection at a time, answers every hello with {"ok":1}, every
consult with {"a":0} (or --pick N, clamped by the k the consult carries when
it can be read), every end with {"ok":1}, and appends every line it receives
and every line it sends, byte for byte, to --out.  Two uses:

  * byte-identity gate (Phase 3a): record the same seeded games from two
    driver builds and `cmp` the files;
  * WIRE-V7 gate: record 100 consults from a -Drl.encoderV=7 driver and run
    rl/wire_validate.py --stream on the file.

Pick 0 is PASS at every v6 site except atkjoint/blkjoint, so the games are
short and deterministic under -Drl.seed.  Nothing here is a policy.
"""
import argparse
import json
import socket


def serve(port, out, pick, max_conns, prefer=None):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(4)
    print(f"wire echo server on :{port} -> {out}", flush=True)
    conns = 0
    with open(out, "ab") as f:
        while max_conns <= 0 or conns < max_conns:
            c, _ = srv.accept()
            conns += 1
            rd = c.makefile("rb")
            for raw in rd:
                f.write(raw)
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                if line.startswith('{"t":"hello"'):
                    rep = b'{"ok":1}\n'
                elif line.startswith('{"t":"consult"'):
                    a = pick
                    if a or prefer is not None:
                        try:
                            m = json.loads(line)
                            k = len(m["c"])
                            a = min(a, k - 1)
                            if prefer is not None and "v7_cand_type" in m:
                                # first candidate of the first preferred WIRE-V7
                                # type present, in the given order (e.g. "2,1" =
                                # cast a spell whenever consulted, else play a
                                # land, else --pick)
                                for pt in prefer:
                                    hits = [i for i, t in enumerate(m["v7_cand_type"]) if t == pt]
                                    if hits:
                                        a = hits[0]
                                        break
                        except Exception:
                            a = 0
                    rep = f'{{"a":{a}}}\n'.encode()
                else:
                    rep = b'{"ok":1}\n'
                f.write(rep)
                f.flush()
                c.sendall(rep)
            c.close()
            print(f"connection {conns} closed", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7777)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pick", type=int, default=0)
    ap.add_argument("--max-conns", type=int, default=0, help="exit after N connections (0 = forever)")
    ap.add_argument("--prefer-type", default=None,
                    help="v7 only: comma-separated WIRE-V7 candidate types in priority order; "
                         "the first candidate of the first type present is chosen, else --pick")
    a = ap.parse_args()
    prefer = [int(x) for x in a.prefer_type.split(",")] if a.prefer_type else None
    serve(a.port, a.out, a.pick, a.max_conns, prefer)
